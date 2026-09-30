"""The mentor inbox: pending turn-ins, their details, and verdicts. Mirrors the bot's Quests.review rules exactly:

  mentors (staff mentor role, rank 6, admins) decide alone: pass | changes | fail
  peers (rank 2+) may review quests below their own rank; one peer can bounce (changes/fail), two approve to pass,
  except the `peer` route (rank 2 quests) where one approval passes; peer reviews earn XP up to a daily cap;
  `human` route (rank 5+) needs a mentor; nobody reviews their own work; one action per reviewer per submission.
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
    """What this member may review. `peer_max_rank` is the highest quest rank they can peer-review (-1 = none)."""
    u = await request.app.state.db.user(member["id"])
    rank = int(u["rank"]) if u else -1
    ids = _roles()
    session_roles = {int(r) for r in member.get("roles", []) if str(r).isdigit()}
    mentor = member["id"] in settings.admin_ids or bool(member.get("dev")) or \
        bool(session_roles & {i for i in (ids["mentor"], ids["rank6"]) if i})
    peer_max = rank - 1 if rank >= 2 else -1
    return {"mentor": mentor, "peer_max_rank": peer_max, "rank": rank, "can_review": mentor or peer_max >= 0}


def _eligible(access: dict, s: dict, q, uid: int) -> str | None:
    """None if the member may act on this submission, else the reason they cannot (same wording as the bot)."""
    if s["user_id"] == uid:
        return "You can't review your own work."
    if access["mentor"]:
        return None
    if s["route"] == "human":
        return "Rank 5+ work needs a human mentor."
    if q.rank > access["peer_max_rank"]:
        return "You can't review this rank yet."
    return None


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
        "approvals": sum(1 for a in actions if a["is_peer"] and a["verdict"] == "approve"),
        "needs": 1 if s["route"] == "peer" else 2,
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
        raise HTTPException(403, "Reviews open at Apprentice rank 2 for quests below your own, and for mentors.")
    rdb = request.app.state.rpg
    pending = [await _item(request, s, access, member["id"]) for s in await rdb.pending_submissions()]
    recent = [await _item(request, s, access, member["id"]) for s in await rdb.decided_submissions(20)]
    return {"access": access, "pending": pending, "recent": recent}


@router.get("/submissions/{sid}")
async def detail(sid: int, request: Request, member=Depends(current_member)):
    access = await access_for(request, member)
    if not access["can_review"]:
        raise HTTPException(403, "Reviews open at Apprentice rank 2 for quests below your own, and for mentors.")
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
    is_mentor = access["mentor"]
    rules = cat.xp_rules.get("peer_review", {})
    if not is_mentor:
        cap = rules.get("daily_cap", 3)
        if await rdb.xp_count_today(uid, "peer_review:") >= cap:
            raise HTTPException(429, f"Peer review cap reached ({cap}/day).")
    is_peer = not is_mentor
    pv = "approve" if (is_peer and body.verdict == "pass") else body.verdict
    if not await rdb.add_review_action(sid, uid, pv, is_peer, notes):
        raise HTTPException(409, "You already reviewed this one.")
    if is_peer:
        await rdb.add_xp(uid, rules.get("xp", 15), f"peer_review:{sid}")

    final = None
    if is_mentor or body.verdict in ("changes", "fail") or s["route"] == "peer":
        final = body.verdict
    elif await rdb.peer_approvals(sid) >= 2:
        final = "pass"
    if not final:
        return {"final": None, "approvals": await rdb.peer_approvals(sid), "needs": 2, "message": f"Approve recorded ({await rdb.peer_approvals(sid)}/2)."}

    await rdb.decide(sid, final, uid, notes)
    xp = 0
    if final == "pass":
        u = await db.user(s["user_id"])
        xp, _ = await complete_quest(request, s["user_id"], q, u or {"rank": -1})
    await rdb.emit("submission_decided", s["user_id"], {"submission": sid, "verdict": final, "reviewer": uid,
                                                       "reviewer_name": member.get("name"), "notes": notes, "quest": q.id})
    return {"final": final, "quest_xp": xp, "message": f"Recorded: {final}."}
