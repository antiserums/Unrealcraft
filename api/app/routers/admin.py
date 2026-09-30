"""The admin panel: look up any member, grant or clear quests, set ranks, give XP or medals, reset an account,
and see what the site is doing (stats, the events the bot mirrors, the admin log).

Who: Discord ids in ADMIN_IDS (api/.env) and local dev-login sessions. Every action is written to admin_log.
Rank changes emit `rank_set` so the bot swaps the member's Discord roles."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..serializers import quest_summary
from ..session import current_member
from .rpg import card_payload

router = APIRouter(prefix="/admin", tags=["admin"])


def is_admin(member: dict) -> bool:
    return member["id"] in settings.admin_ids or bool(member.get("dev"))


def admin_only(member=Depends(current_member)) -> dict:
    if not is_admin(member):
        raise HTTPException(403, "Admins only. Add your Discord id to ADMIN_IDS in api/.env.")
    return member


@router.get("")
async def overview(request: Request, _=Depends(admin_only)):
    rdb, cat = request.app.state.rpg, request.app.state.catalog
    return {"stats": {**await rdb.stats(), "quests_in_catalog": len(cat.quests)},
            "db_path": str(settings.db_path), "curriculum_dir": str(settings.curriculum_dir),
            "admin_ids": sorted(settings.admin_ids), "events": await rdb.events_tail(30), "log": await rdb.admin_log_tail(30),
            "pending": await rdb.pending_submissions(20)}


@router.get("/members")
async def members(request: Request, q: str = "", _=Depends(admin_only)):
    return {"members": await request.app.state.rpg.search_members(q)}


@router.get("/members/{uid}")
async def member(uid: int, request: Request, admin=Depends(admin_only)):
    db, rdb, cat = request.app.state.db, request.app.state.rpg, request.app.state.catalog
    u = await db.user(uid)
    if not u:
        raise HTTPException(404, "No such member. They appear here after pressing Start Questing on Discord or logging in.")
    card = await card_payload(request, uid, admin)
    prog = await rdb.progress_rows(uid)
    return {
        "user": u, "card": {k: card[k] for k in ("name", "avatar", "rank_title", "rank_color", "major_title", "worn", "achievements_earned", "achievements_total", "cosmetics")},
        "progress": [{**p, "quest": quest_summary(cat, cat.quests[p["quest_id"]]) if p["quest_id"] in cat.quests else None} for p in prog],
        "medals": await db.medals(uid), "xp_recent": await db.xp_recent(uid, 30), "submissions": await db.submissions(uid),
        "ranks": [{"n": n, "title": r["title"], "xp": r["xp"]} for n, r in sorted(cat.ranks.items())],
        "majors": sorted(k for k in cat.majors.keys()),
    }


class QuestAction(BaseModel):
    quest_id: str
    action: str = "done"           # done | clear
    xp: bool = True                # give the quest's XP when marking done


@router.post("/members/{uid}/quests")
async def quest(uid: int, body: QuestAction, request: Request, admin=Depends(admin_only)):
    db, rdb, cat = request.app.state.db, request.app.state.rpg, request.app.state.catalog
    q = cat.quests.get(body.quest_id.strip().upper())
    if not q:
        raise HTTPException(404, "No such quest id.")
    if not await db.user(uid):
        raise HTTPException(404, "No such member.")
    if body.action == "clear":
        await rdb.clear_progress(uid, q.id)
        await rdb.admin_log(admin["id"], "clear_quest", uid, {"quest": q.id})
        return {"ok": True, "message": f"{q.id} cleared."}
    await rdb.ensure_character(uid)
    await rdb.set_progress(uid, q.id, "done", quiz_passed=True)
    if body.xp:
        await rdb.add_xp(uid, q.xp, f"admin:{q.id}")
    await rdb.emit("quest_completed", uid, {"quest": q.id, "xp": q.xp if body.xp else 0, "outfit": None, "admin": True})
    await rdb.admin_log(admin["id"], "grant_quest", uid, {"quest": q.id, "xp": body.xp})
    return {"ok": True, "message": f"{q.id} marked done{' with XP' if body.xp else ''}."}


class RankAction(BaseModel):
    rank: int
    major: str | None = None


@router.post("/members/{uid}/rank")
async def rank(uid: int, body: RankAction, request: Request, admin=Depends(admin_only)):
    db, rdb, cat = request.app.state.db, request.app.state.rpg, request.app.state.catalog
    if not await db.user(uid):
        raise HTTPException(404, "No such member.")
    if body.rank < -1 or body.rank > 6:
        raise HTTPException(400, "Rank is -1 (Orientation) to 6.")
    fields: dict = {"rank": body.rank}
    if body.major is not None:
        if body.major not in cat.majors:
            raise HTTPException(400, "No such major.")
        fields["major"] = body.major
    u = await db.user(uid)
    xp_floor = cat.ranks.get(body.rank, {}).get("xp", 0) if body.rank >= 0 else 0
    if u["xp"] < xp_floor:
        fields["xp"] = xp_floor           # a rank below its XP floor would demote itself on the next check
    await rdb.set_user(uid, **fields)
    await rdb.conn.execute("UPDATE users SET rank_since=datetime('now') WHERE discord_id=?", (uid,))
    await rdb.conn.commit()
    await rdb.emit("rank_set", uid, {"rank": body.rank, "admin": True})
    await rdb.admin_log(admin["id"], "set_rank", uid, fields)
    return {"ok": True, "message": f"Rank set to {body.rank}. The bot will swap the Discord roles within a minute."}


class XpAction(BaseModel):
    amount: int
    reason: str = "admin"


@router.post("/members/{uid}/xp")
async def xp(uid: int, body: XpAction, request: Request, admin=Depends(admin_only)):
    if not await request.app.state.db.user(uid):
        raise HTTPException(404, "No such member.")
    if not -100000 < body.amount < 100000 or body.amount == 0:
        raise HTTPException(400, "Amount must be a non-zero number.")
    await request.app.state.rpg.add_xp(uid, body.amount, f"admin:{body.reason[:40]}")
    await request.app.state.rpg.admin_log(admin["id"], "add_xp", uid, {"amount": body.amount, "reason": body.reason[:40]})
    return {"ok": True, "message": f"{body.amount:+} XP."}


class MedalAction(BaseModel):
    key: str
    remove: bool = False


@router.post("/members/{uid}/medal")
async def medal(uid: int, body: MedalAction, request: Request, admin=Depends(admin_only)):
    rdb = request.app.state.rpg
    if not await request.app.state.db.user(uid):
        raise HTTPException(404, "No such member.")
    key = body.key.strip()[:40]
    if body.remove:
        await rdb.remove_medal(uid, key)
    else:
        await rdb.grant_medal(uid, key)
    await rdb.admin_log(admin["id"], "medal", uid, {"key": key, "remove": body.remove})
    return {"ok": True, "message": f"Medal {key} {'removed' if body.remove else 'granted'}."}


class ResetAction(BaseModel):
    confirm: str
    delete_user: bool = False


@router.post("/members/{uid}/reset")
async def reset(uid: int, body: ResetAction, request: Request, admin=Depends(admin_only)):
    if body.confirm != str(uid):
        raise HTTPException(400, "Type the member id to confirm.")
    counts = await request.app.state.rpg.reset_member(uid, keep_user=not body.delete_user)
    await request.app.state.rpg.admin_log(admin["id"], "reset", uid, {"deleted": counts, "user_deleted": body.delete_user})
    if not body.delete_user:
        await request.app.state.rpg.emit("rank_set", uid, {"rank": -1, "admin": True})
    return {"ok": True, "message": "Reset. " + ", ".join(f"{k} {v}" for k, v in counts.items() if v), "deleted": counts}


@router.get("/quests")
async def quest_lookup(request: Request, q: str = "", _=Depends(admin_only)):
    cat = request.app.state.catalog
    needle = q.strip().lower()
    hits = [x for x in cat.quests.values() if needle and (needle in x.id.lower() or needle in x.raw["title"].lower())][:20]
    return {"quests": [quest_summary(cat, x) for x in hits]}
