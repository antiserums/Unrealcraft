"""The logged-in member: profile, path, next quest. Read-only in phase 1."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from registrar.curriculum import TIERS, Catalog, UserState  # noqa: E402

from ..serializers import quest_summary
from ..session import current_member

router = APIRouter(prefix="/me", tags=["me"])


def nameplate(cat: Catalog, rank: int, major: str) -> str:
    """Rank title; from Expert up the major is the specialty and joins the plate: 'Expert · Level Design'."""
    if rank < 0:
        return "Orientation"
    title = cat.ranks[rank]["title"]
    if 3 <= rank < 6 and major and major != "undecided":
        return f"{title} · {cat.majors.get(major, {}).get('title', major)}"
    return title


def rank_color(cat: Catalog, rank: int) -> str:
    return cat.ranks.get(rank, {}).get("color") or "#7A8C7E"


def profile_payload(cat: Catalog, member: dict | None, u: dict, state: UserState, medals: list[dict]) -> dict:
    rank, major = u["rank"], u["major"]
    target = rank + 1
    nxt = cat.ranks.get(target)
    ok, missing = cat.rank_requirements_met(state, target) if (target in cat.ranks or target == 0) else (False, [])
    ids = [m for m in missing if not m.startswith("tier:")]
    tier_left = [m for m in missing if m.startswith("tier:")]
    lo = cat.ranks.get(rank, {}).get("xp", 0) if rank >= 0 else 0
    hi = nxt["xp"] if nxt else None
    tier_prog = None
    if rank >= 1:
        done, need, avail, tier = cat.tier_progress(state, rank)
        tier_prog = {"done": done, "need": need, "available": avail, "tier": tier, "name": TIERS[tier]["name"],
                     "emoji": TIERS[tier]["emoji"], "color": TIERS[tier]["color"]}
    return {
        "id": u["discord_id"], "name": member["name"] if member else None, "avatar": member["avatar"] if member else None,
        "major": major, "major_title": cat.majors.get(major, {}).get("title", major), "minor": u.get("minor"),
        "rank": rank, "rank_title": nameplate(cat, rank, major), "rank_color": rank_color(cat, max(rank, 0)),
        "xp": u["xp"], "xp_floor": lo, "xp_next": hi,
        "streak_days": u.get("streak_days", 0), "ue_version": u.get("ue_version"),
        "rank_since": u.get("rank_since"), "member_since": u.get("created_at"),
        "next_rank": ({"n": target, "title": nxt["title"], "xp": nxt["xp"], "opens": nxt.get("opens"),
                       "xp_to_go": max(0, nxt["xp"] - u["xp"]), "required_left": len(ids),
                       "tier_left": int(tier_left[0].split(":")[2]) if tier_left else 0,
                       "requirements_met": ok and u["xp"] >= nxt["xp"], "human_review": bool(nxt.get("human_review"))}
                      if nxt else None),
        "tier_progress": tier_prog,
        "medals": medals,
        "done_count": len(state.done),
    }


@router.get("")
async def me(request: Request, member=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    u, state, _ = await db.user_state(member["id"])
    payload = profile_payload(cat, member, u, state, await db.medals(member["id"]))
    payload["recent_xp"] = await db.xp_recent(member["id"], 15)
    payload["known"] = await db.user(member["id"]) is not None
    from .review import access_for
    a = await access_for(request, member)
    from .admin import is_admin
    payload["admin"] = is_admin(member)
    payload["review"] = {"can": a["can_review"], "mentor": a["mentor"],
                         "pending": len(await request.app.state.rpg.pending_submissions()) if a["can_review"] else 0}
    return payload


@router.get("/next")
async def next_quest(request: Request, member=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    u, state, _ = await db.user_state(member["id"])
    pick = cat.pick(state)
    return {"main": quest_summary(cat, pick.main, u["major"]) if pick.main else None, "reason": pick.reason,
            "electives": [quest_summary(cat, q, u["major"]) for q in pick.electives],
            "adjacent": quest_summary(cat, pick.adjacent, u["major"]) if pick.adjacent else None,
            "remaining_minutes": cat.remaining_minutes(state)}


@router.get("/path")
async def path(request: Request, member=Depends(current_member)):
    """The personal path as data: sections of quests with a status each, plus the locked next rank."""
    db, cat = request.app.state.db, request.app.state.catalog
    u, state, prog = await db.user_state(member["id"])
    major = u["major"]
    pick = cat.pick(state)
    now_id = pick.main.id if pick.main else None

    def row(q, tag: str | None = None) -> dict:
        d = quest_summary(cat, q, major)
        d["status"] = "done" if q.id in state.done else ("now" if q.id == now_id else
                                                          ("skipped" if q.id in state.skipped else "todo"))
        d["tag"] = tag
        return d

    sections = []
    if state.rank < 0 or any(q.id not in state.done for q in cat.orientation()):
        sections.append({"key": "orientation", "title": "Orientation", "quests": [row(q) for q in cat.orientation()]})
    sections.append({"key": "spine", "title": "Starter Quests (everyone)", "quests": [row(q) for q in cat.spine()]})
    for r in range(1, max(state.rank, 0) + 1):
        title = cat.ranks.get(r, {}).get("title", f"Rank {r}")
        qs = [row(q) for q in cat.required(major, r)]
        for g in cat.taster_groups(major, r):
            group = [cat.quests[x] for x in g if x in cat.quests]
            qs += [row(q, "taster: pick one" if len(group) > 1 else "taster") for q in group]
        done, need, avail, tier = cat.tier_progress(state, r)
        sections.append({"key": f"rank{r}", "title": f"Rank {r} · {title}", "rank": r, "quests": qs,
                         "tier": {"done": done, "need": need, "available": avail, "tier": tier,
                                  "name": TIERS[tier]["name"], "emoji": TIERS[tier]["emoji"]} if need else None})

    nxt_n = max(state.rank, 0) + 1
    locked = None
    if nxt_n in cat.ranks:
        cfg = cat.ranks[nxt_n]
        req = [q for q in cat.required(major, nxt_n) if not q.capstone]
        tasters = [[{"id": x, "title": cat.quests[x].raw["title"]} for x in g if x in cat.quests]
                   for g in cat.taster_groups(major, nxt_n)]
        cap = cat.capstone(major, nxt_n)
        gate_tier = None
        if nxt_n >= 2:
            _, need, _, tier = cat.tier_progress(state, nxt_n - 1)
            if need:
                gate_tier = {"need": need, "name": TIERS[tier]["name"]}
        locked = {"n": nxt_n, "title": cfg["title"], "xp": cfg["xp"], "opens": cfg.get("opens"),
                  "gate_tier": gate_tier, "quests": [quest_summary(cat, q, major) for q in req],
                  "tasters": tasters, "capstone": cap}
    return {"major": major, "major_title": cat.majors.get(major, {}).get("title", major), "rank": state.rank,
            "sections": sections, "locked": locked, "now": now_id, "reason": pick.reason}
