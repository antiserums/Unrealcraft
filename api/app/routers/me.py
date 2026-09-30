"""The logged-in member: profile, path, next quest, specializations."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from registrar.curriculum import TIERS, Catalog, UserState  # noqa: E402

from ..serializers import quest_summary
from ..session import current_member

router = APIRouter(prefix="/me", tags=["me"])
MAX_EXTRAS = 6


def nameplate(cat: Catalog, rank: int, major: str) -> str:
    """Rank title; from Expert up the primary specialization joins the plate: 'Expert · Level Design'."""
    if rank < 0:
        return "Orientation"
    title = cat.ranks[rank]["title"]
    if 3 <= rank < 6 and major and major != "undecided":
        return f"{title} · {cat.title_of(major)}"
    return title


def rank_color(cat: Catalog, rank: int) -> str:
    return cat.ranks.get(rank, {}).get("color") or "#7A8C7E"


def specializations_payload(cat: Catalog, state: UserState) -> list[dict]:
    """The member's specializations, primary first."""
    return [{"key": k, "title": cat.title_of(k), "primary": k == state.major} for k in state.specializations]


def profile_payload(cat: Catalog, member: dict | None, u: dict, state: UserState, medals: list[dict], role: str | None = None) -> dict:
    """`role` is a staff role (admin, developer, mentor) or None; staff get their title in place of the player rank."""
    from ..staff import nameplate_for
    rank, major = u["rank"], u["major"]
    plate = nameplate_for(role)
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
        "specialization": major, "specialization_title": cat.title_of(major), "specializations": specializations_payload(cat, state),
        "rank": rank, "rank_title": plate[0] if plate else nameplate(cat, rank, major),
        "rank_color": plate[1] if plate else rank_color(cat, max(rank, 0)), "staff": role,
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


async def me_payload(request: Request, member: dict) -> dict:
    db, cat = request.app.state.db, request.app.state.catalog
    u, state, _ = await db.user_state(member["id"])
    from ..staff import is_admin, role_of
    payload = profile_payload(cat, member, u, state, await db.medals(member["id"]), role=role_of(member))
    payload["recent_xp"] = await db.xp_recent(member["id"], 15)
    payload["known"] = await db.user(member["id"]) is not None
    from .review import access_for
    a = await access_for(request, member)
    payload["admin"] = is_admin(member)
    payload["review"] = {"can": a["can_review"], "mentor": a["mentor"],
                         "pending": len(await request.app.state.rpg.pending_submissions()) if a["can_review"] else 0}
    payload["letters_unread"] = await request.app.state.rpg.unread_letters(member["id"], staff=payload["admin"] or a["can_review"])
    payload["specialization_options"] = [{"key": k, "title": v.get("title", k), "blurb": v.get("blurb", "")}
                                         for k, v in cat.specializations.items() if k != "undecided"]
    # what the member chose to wear on their card, for the home page and the top bar (no card fetch needed)
    from .. import rpg as rpg_rules
    from .rpg import _unlock_all, entitlement_options, member_ctx
    cos = await request.app.state.rpg.cosmetics(member["id"])
    opts = entitlement_options(request, await member_ctx(request, member["id"]), int(u.get("rank", -1)), role_of(member), _unlock_all(member))
    frame = rpg_rules.pick_owned(opts["avatar_frame"], cos.get("avatar_frame"))
    title = rpg_rules.pick_owned(opts["title"], cos.get("title"))
    payload["avatar_frame"], payload["avatar_frame_art"] = frame["id"], frame.get("art")
    payload["title"] = None if title["id"] == rpg_rules.DEFAULT_TITLE else title["name"]
    payload["nameplate"] = rpg_rules.pick_owned(opts["nameplate"], cos.get("nameplate"))["value"]
    return payload


@router.get("")
async def me(request: Request, member=Depends(current_member)):
    return await me_payload(request, member)


class SpecializationPatch(BaseModel):
    primary: str | None = None        # the specialization that drives ranks and the nameplate; "undecided" allowed
    extras: list[str] | None = None   # further specializations whose quests count as yours


@router.patch("/specializations")
async def set_specializations(body: SpecializationPatch, request: Request, member=Depends(current_member)):
    """Primary plus extras. The bot still maps the primary to its Discord role; extras live on the site only."""
    db, rdb, cat = request.app.state.db, request.app.state.rpg, request.app.state.catalog
    valid = set(cat.specializations)
    await rdb.ensure_character(member["id"])
    u = await db.user(member["id"])
    primary = u["major"]
    if body.primary is not None:
        if body.primary not in valid:
            raise HTTPException(400, "Pick a specialization from the list.")
        primary = body.primary
    extras = None
    if body.extras is not None:
        extras = list(dict.fromkeys(e for e in body.extras if e != primary))
        bad = [e for e in extras if e not in valid or e == "undecided"]
        if bad:
            raise HTTPException(400, f"Not a specialization: {', '.join(bad)}.")
        if len(extras) > MAX_EXTRAS:
            raise HTTPException(400, f"Up to {MAX_EXTRAS} extra specializations.")
    if primary != u["major"]:
        await rdb.set_user(member["id"], major=primary)
    if extras is not None:
        await rdb.kv_set(member["id"], "web.specializations", json.dumps(extras))
    elif primary != u["major"]:                      # the new primary leaves the extras
        _, state, _ = await db.user_state(member["id"])
        await rdb.kv_set(member["id"], "web.specializations", json.dumps([e for e in state.extras if e != primary]))
    _, now, _ = await db.user_state(member["id"])
    await rdb.emit("specialization_set", member["id"], {"primary": now.major, "extras": now.extras})   # the bot swaps roles
    if body.primary is not None:
        from .. import progress
        await progress.add_fact(request, member["id"], "spec.chosen")
    return await me_payload(request, member)


@router.get("/next")
async def next_quest(request: Request, member=Depends(current_member)):
    db, cat = request.app.state.db, request.app.state.catalog
    _, state, _ = await db.user_state(member["id"])
    pick = cat.pick(state)
    return {"main": quest_summary(cat, pick.main, state) if pick.main else None, "reason": pick.reason,
            "electives": [quest_summary(cat, q, state) for q in pick.electives],
            "adjacent": quest_summary(cat, pick.adjacent, state) if pick.adjacent else None,
            "remaining_minutes": cat.remaining_minutes(state)}


@router.get("/path")
async def path(request: Request, member=Depends(current_member)):
    """The personal path as data: sections of quests with a status each, plus the locked next rank."""
    db, cat = request.app.state.db, request.app.state.catalog
    from .. import progress
    await progress.add_fact(request, member["id"], "site.path")
    u, state, prog = await db.user_state(member["id"])
    major = u["major"]
    pick = cat.pick(state)
    now_id = pick.main.id if pick.main else None

    def row(q, tag: str | None = None) -> dict:
        d = quest_summary(cat, q, state)
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
                  "gate_tier": gate_tier, "quests": [quest_summary(cat, q, state) for q in req],
                  "tasters": tasters, "capstone": cap}
    return {"specialization": major, "specialization_title": cat.title_of(major), "specializations": specializations_payload(cat, state),
            "rank": state.rank, "sections": sections, "locked": locked, "now": now_id, "reason": pick.reason}


@router.get("/stats")
async def stats(request: Request, member=Depends(current_member)):
    """Numbers for the home page: the member's own, plus the guild's this week."""
    rdb = request.app.state.rpg
    return {"me": await rdb.member_stats(member["id"]), "guild": await rdb.guild_stats()}


@router.get("/stats/series")
async def stats_series(request: Request, days: int = 30, member=Depends(current_member)):
    """The same numbers day by day, for the graphs under the tiles."""
    return await request.app.state.rpg.stats_series(member["id"], days)
