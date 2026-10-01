"""Claim the chest: submit proof of work on the website. Reviews happen on the site; Discord is not involved."""
from __future__ import annotations

import datetime as dt
import json
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from registrar import checks  # noqa: E402

from ..config import settings
from ..session import current_member
from .rpg import complete_quest

router = APIRouter(tags=["submit"])
MAX_FILES, MAX_BYTES = 4, 8 * 1024 * 1024
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
# short clips, for proof that only shows in motion (a platform moving, an animation playing)
VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}
MAX_VIDEOS, MAX_VIDEO_BYTES = 2, 50 * 1024 * 1024
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
               ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}


def looks_like_video(data: bytes, ext: str) -> bool:
    """The file starts the way its type says: MP4 and MOV carry "ftyp" (or an older QuickTime atom) at byte 4, WebM
    starts with the EBML mark. Keeps a renamed file of another kind out of the uploads folder."""
    if ext == ".webm":
        return data[:4] == b"\x1a\x45\xdf\xa3"
    return data[4:8] in (b"ftyp", b"moov", b"mdat", b"free", b"wide")
DISCORD_LINK = re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/\d+/\d+/\d+")


def route_for(quest_rank: int, verify_type: str) -> str:
    if verify_type == "action":
        return "auto"
    if quest_rank <= 1:
        return "auto" if verify_type == "quiz" else "honor"
    if quest_rank == 2:
        return "peer"
    if quest_rank <= 4:
        return "mentor"
    return "human"


def problems_for(q, facts: set[str], text: str, files: list[UploadFile]) -> list[str]:
    out = [f"Not seen yet: {m}" for m in checks.facts_missing(q, facts)]
    cks = [it.check for it in checks.items(q) if it.kind == "submit"]
    if not cks and q.raw.get("verify_type") in checks.SUBMIT_DEFAULTS:
        cks = [checks.SUBMIT_DEFAULTS[q.raw["verify_type"]]]
    for c in cks:
        if "attachment" in c and c["attachment"] == "image" and not files:
            out.append("Attach at least one screenshot or a short clip.")
        if "attachment" in c and c["attachment"] == "video" and "http" not in text and not any(f.content_type in VIDEO_TYPES for f in files):
            out.append("This quest wants a video: attach a short clip, or paste a link to it in the text.")
        if "min_length" in c and len(text.strip()) < c["min_length"]:
            out.append(f"Write at least {c['min_length']} characters (you wrote {len(text.strip())}).")
        if "link" in c and not DISCORD_LINK.search(text):
            out.append("Paste the Discord message link (right-click the message → Copy Message Link).")
    return [p for p in out if p]


@router.post("/me/quests/{qid}/submit")
async def submit(qid: str, request: Request, member=Depends(current_member), text: str = Form(""),
                 ue_version: str = Form(""), files: list[UploadFile] = File(default=[])):
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    uid = member["id"]
    q = cat.quests.get(qid)
    if not q:
        raise HTTPException(404, "No such quest.")
    await rdb.ensure_character(uid)
    u, state, prog = await db.user_state(uid)
    from ..staff import unlock_all
    if q.rank > max(state.rank, 0) and not unlock_all(member):
        raise HTTPException(403, "This dungeon is locked until you rank up.")
    if q.id in state.done:
        raise HTTPException(409, "Already done. The chest is empty.")
    if q.id == "O5":
        if text.strip().upper() != "READY":
            raise HTTPException(400, "For O5 the proof is literally READY.")
        from .. import progress
        await progress.add_fact(request, uid, "submit.O5")        # the practice quest finishes itself on this fact
        return {"status": "practice", "message": "Practice done. A real turn-in works the same way."}
    if q.raw.get("verify_type") == "action":
        raise HTTPException(400, "Nothing to send here. This one ticks itself when you do it on the site.")
    if q.quiz and not (prog.get(qid) or {}).get("quiz_passed"):
        raise HTTPException(409, "Beat the boss first.")
    subs = await db.submissions(uid, qid)
    last_fail = next((s for s in subs if s["status"] == "fail" and s["decided_at"]), None)
    cooldown = int(cat.xp_rules.get("submit_cooldown_after_fail_min", 120))
    if last_fail and dt.datetime.utcnow() - dt.datetime.fromisoformat(last_fail["decided_at"]) < dt.timedelta(minutes=cooldown):
        raise HTTPException(429, f"A reviewer marked the last one Fail. Wait {cooldown} min and use the time to fix it.")
    if any(s["status"] == "pending" for s in subs):
        raise HTTPException(409, "You already sent this one. A reviewer is looking at it.")
    files = [f for f in files if f and f.filename]
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"At most {MAX_FILES} files.")
    for f in files:
        if f.content_type not in IMAGE_TYPES and f.content_type not in VIDEO_TYPES:
            raise HTTPException(400, f"{f.filename}: only images (PNG, JPG, WEBP, GIF) or video clips (MP4, WEBM, MOV).")
    if sum(f.content_type in VIDEO_TYPES for f in files) > MAX_VIDEOS:
        raise HTTPException(400, f"At most {MAX_VIDEOS} video clips.")
    problems = problems_for(q, await db.facts(uid), text, files)
    if problems:
        raise HTTPException(422, "; ".join(problems))

    # store the files: data/uploads/<uid>/<random>.<ext>, served at /uploads/<uid>/<name> (members only).
    # Every file is checked before the first one is written, so a refused upload leaves nothing behind.
    folder = settings.uploads_dir / str(uid)
    folder.mkdir(parents=True, exist_ok=True)
    ready: list[tuple[str, bytes]] = []
    for f in files:
        video = f.content_type in VIDEO_TYPES
        ext = VIDEO_TYPES[f.content_type] if video else IMAGE_TYPES[f.content_type]
        limit = MAX_VIDEO_BYTES if video else MAX_BYTES
        data = await f.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(400, f"{f.filename} is larger than {limit // (1024 * 1024)} MB." + (" Keep clips to about 30 seconds." if video else ""))
        if video and not looks_like_video(data, ext):
            raise HTTPException(400, f"{f.filename} does not look like a video file.")
        ready.append((secrets.token_urlsafe(12) + ext, data))
    urls = []
    for name, data in ready:
        (folder / name).write_bytes(data)
        urls.append(f"{settings.web_origin}/api/uploads/{uid}/{name}")
    if ue_version.strip():
        await db.conn.execute("UPDATE users SET ue_version=? WHERE discord_id=?", (ue_version.strip()[:20], uid))
        await db.conn.commit()
    payload = {"text": text.strip(), "attachments": urls, "ue_version": ue_version.strip() or u.get("ue_version"), "via": "web"}
    route = route_for(q.rank, q.raw.get("verify_type", "screenshot"))
    cur = await db.conn.execute("INSERT INTO submissions(user_id, quest_id, payload, route) VALUES (?,?,?,?)",
                                (uid, qid, json.dumps(payload), route))
    sid = cur.lastrowid
    await db.conn.commit()
    await rdb.set_progress(uid, qid, "submitted")
    if route in ("auto", "honor"):
        await db.conn.execute("UPDATE submissions SET status='pass', decided_at=datetime('now'), notes=? WHERE id=?", (route, sid))
        await db.conn.commit()
        xp, loot = await complete_quest(request, uid, q, u)
        await rdb.emit("submission_accepted", uid, {"submission": sid, "quest": qid, "route": route})
        return {"status": "accepted", "submission": sid, "xp": xp, "loot": loot,
                "message": f"Chest opened. +{xp} XP." + (f" New outfit: {loot['name']}." if loot else "")}
    await rdb.emit("submission_created", uid, {"submission": sid, "quest": qid, "route": route})
    who = {"peer": "a peer (Rank 2+) or a mentor", "mentor": "a mentor or two peers", "human": "a human mentor"}[route]
    return {"status": "pending", "submission": sid, "route": route,
            "message": f"Sent. The chest opens when {who} accepts it. Target turnaround is under 48 hours."}


@router.get("/uploads/{uid}/{name}")
async def upload(uid: int, name: str, _=Depends(current_member)):
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.(png|jpg|webp|gif|mp4|webm|mov)", name):
        raise HTTPException(404, "Not found.")
    p: Path = settings.uploads_dir / str(uid) / name
    if not p.is_file():
        raise HTTPException(404, "Not found.")
    # the type comes from our own extension, never from the file: the browser must not guess
    return FileResponse(p, media_type=MEDIA_TYPES[p.suffix], headers={"X-Content-Type-Options": "nosniff"})
