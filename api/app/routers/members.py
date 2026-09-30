"""Other members' player cards (members only, unless the owner made theirs public) and the leaderboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..session import current_member, current_member_or_none
from .me import nameplate, rank_color
from .rpg import card_payload

router = APIRouter(tags=["members"])


@router.get("/members/{uid}")
async def member_card(uid: int, request: Request, viewer=Depends(current_member_or_none)):
    db = request.app.state.db
    if await db.user(uid) is None:
        raise HTTPException(404, "No such member.")
    card = await card_payload(request, uid, viewer)
    if viewer is None and not card["public"]:
        raise HTTPException(401, "Log in with Discord first.")
    card["mine"] = bool(viewer and viewer["id"] == uid)
    return card


@router.get("/leaderboard")
async def leaderboard(request: Request, period: str = "week", _=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    days = {"week": 7, "month": 30, "all": None}.get(period, 7)
    rows = await db.leaderboard(days)
    return {"period": period, "rows": [
        {"id": r["discord_id"], "xp": r["xp"], "rank": r["rank"], "rank_title": nameplate(cat, r["rank"], r["major"]),
         "rank_color": rank_color(cat, max(r["rank"], 0)),
         "major_title": cat.majors.get(r["major"], {}).get("title", r["major"])} for r in rows]}
