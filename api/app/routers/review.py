"""The mentor inbox: pending turn-ins, their details, and verdicts.

Only mentors review: the staff mentor role, rank 6, ADMIN_IDS, or a local dev login. One verdict decides:
pass | changes | fail. Nobody reviews their own work. The bot's Quests.review enforces the same rule on Discord.
The bot picks up `submission_decided` events to update the Discord turn-in post and queue card."""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from registrar import checks  # noqa: E402

from ..config import settings
from ..serializers import quest_summary
from ..session import current_member
from .rpg import complete_quest

router = APIRouter(prefix="/review", tags=["review"])
VERDICTS = ("pass", "changes", "fail")


def _roles() -> dict:
    """Role ids the bot uses, read from its unlocks.yaml. Missing file or ids -> 0, which never matches."""
    try:
        data = yaml.safe_load(Path(settings.unlocks_path).read_text(encoding="utf-8")) or {}
    except OSError:
        data = {}
    roles = data.get("roles") or {}
    return {"mentor": int(((roles.get("staff") or {}).get("mentor")) or 0), "rank6": int(((roles.get("rank") or {}).get(6)) or 0)}


async def access_for(request: Request, member: dict) -> dict:
    """Whether this member may review. Mentors only: staff mentor role, rank 6, ADMIN_IDS or a dev login."""
    u = await request.app.state.db.user(member["id"])
    rank = int(u["rank"]) if u else -1
    ids = _roles()
    session_roles = {int(r) for r in member.get("roles", []) if str(r).isdigit()}
    mentor = member["id"] in settings.admin_ids or bool(member.get("dev")) or \
        bool(session_roles & {i for i in (ids["mentor"], ids["rank6"]) if i})
    return {"mentor": mentor, "rank": rank, "can_review": mentor}


def _eligible(access: dict, s: dict, q, uid: int) -> str | None:
    """None if the member may act on this submission, else the reason they cannot (same wording as the bot)."""
    if s["user_id"] == uid:
        return "You can't review your own work."
    return None if access["mentor"] else "Only mentors, admins and devs review work."


async def _item(request: Request, s: dict, access: dict, uid: int) -> dict:
    cat, rdb = request.app.state.catalog, request.app.state.rpg
    q = cat.quests.get(s["quest_id"])
    try:
        payload = json.loads(s["payload"] or "{}")
    except ValueError:
        payload = {"text": s["payload"]}
    actions = await rdb.review_actions(s["id"])
    return {
        "id": s["id"], "status": s["status"], "route": s["route"], "created_at": s["created_at"], "decided_at": s.get("decided_at"),
        "notes": s.get("notes"), "reviewer_id": s.get("reviewer_id"),
        "member": {"id": s["user_id"], "name": await rdb.kv_get(s["user_id"], "web.name"),
                   "avatar": await rdb.kv_get(s["user_id"], "web.avatar"), "rank": s.get("member_rank"), "major": s.get("member_major")},
        "quest": quest_summary(cat, q) if q else {"id": s["quest_id"], "title": s["quest_id"]},
        "payload": payload,
        "reviewed_by_me": any(a["reviewer_id"] == uid for a in actions),
        "blocked": _eligible(access, s, q, uid) if q else "Unknown quest.",
    }


@router.get("/access")
async def access(request: Request, member=Depends(current_member)):
    a = await access_for(request, member)
    a["pending"] = len(await request.app.state.rpg.pending_submissions()) if a["can_review"] else 0
    return a


@router.get("/queue")
async def queue(request: Request, member=Depends(current_member)):
    access = await access_for(request, member)
    if not access["can_review"]:
        raise HTTPException(403, "Only mentors, admins and devs review work.")
    rdb = request.app.state.rpg
    pending = [await _item(request, s, access, member["id"]) for s in await rdb.pending_submissions()]
    recent = [await _item(request, s, access, member["id"]) for s in await rdb.decided_submissions(20)]
    return {"access": access, "pending": pending, "recent": recent}


@router.get("/submissions/{sid}")
async def detail(sid: int, request: Request, member=Depends(current_member)):
    access = await access_for(request, member)
    if not access["can_review"]:
        raise HTTPException(403, "Only mentors, admins and devs review work.")
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    s = await rdb.submission(sid)
    if not s:
        raise HTTPException(404, "No such submission.")
    u = await db.user(s["user_id"])
    s["member_rank"], s["member_major"] = (u["rank"], u["major"]) if u else (None, None)
    item = await _item(request, s, access, member["id"])
    q = cat.quests.get(s["quest_id"])
    item["quest_detail"] = {
        "done_when": q.raw.get("done_when") if q else None, "do": q.raw.get("do") if q else None,
        "checklist": [{"text": it.text, "kind": it.kind} for it in checks.items(q)] if q else [],
        "verify_type": q.raw.get("verify_type") if q else None,
    }
    item["actions"] = [{**a, "name": await rdb.kv_get(a["reviewer_id"], "web.name")} for a in await rdb.review_actions(sid)]
    item["previous"] = [x for x in await db.submissions(s["user_id"], s["quest_id"]) if x["id"] != sid]
    item["access"] = access
    return item


class Verdict(BaseModel):
    verdict: str
    notes: str | None = None


@router.post("/submissions/{sid}")
async def review(sid: int, body: Verdict, request: Request, member=Depends(current_member)):
    if body.verdict not in VERDICTS:
        raise HTTPException(400, "Verdict must be pass, changes or fail.")
    notes = (body.notes or "").strip()[:1000] or None
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    uid = member["id"]
    access = await access_for(request, member)
    s = await rdb.submission(sid)
    if not s or s["status"] != "pending":
        raise HTTPException(409, "That submission is closed.")
    q = cat.quests.get(s["quest_id"])
    if not q:
        raise HTTPException(404, "Unknown quest.")
    if (why := _eligible(access, s, q, uid)):
        raise HTTPException(403, why)
    if not await rdb.add_review_action(sid, uid, body.verdict, False, notes):
        raise HTTPException(409, "You already reviewed this one.")
    final = body.verdict
    await rdb.decide(sid, final, uid, notes)
    xp = 0
    if final == "pass":
        u = await db.user(s["user_id"])
        xp, _ = await complete_quest(request, s["user_id"], q, u or {"rank": -1})
    await rdb.emit("submission_decided", s["user_id"], {"submission": sid, "verdict": final, "reviewer": uid,
                                                       "reviewer_name": member.get("name"), "notes": notes, "quest": q.id})
    return {"final": final, "quest_xp": xp, "message": f"Recorded: {final}."}
