"""Other members' profiles (members only) and the leaderboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..session import current_member
from .me import nameplate, profile_payload, rank_color

router = APIRouter(tags=["members"])


@router.get("/members/{uid}")
async def member_profile(uid: int, request: Request, _=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    if await db.user(uid) is None:
        raise HTTPException(404, "No such member.")
    u, state, _ = await db.user_state(uid)
    return profile_payload(cat, None, u, state, await db.medals(uid))


@router.get("/leaderboard")
async def leaderboard(request: Request, period: str = "week", _=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    days = {"week": 7, "month": 30, "all": None}.get(period, 7)
    rows = await db.leaderboard(days)
    return {"period": period, "rows": [
        {"id": r["discord_id"], "xp": r["xp"], "rank": r["rank"], "rank_title": nameplate(cat, r["rank"], r["seal"], r["major"]),
         "rank_color": rank_color(cat, max(r["rank"], 0), r["seal"]),
         "major_title": cat.majors.get(r["major"], {}).get("title", r["major"])} for r in rows]}
