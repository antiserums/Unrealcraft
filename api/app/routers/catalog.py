"""Public curriculum endpoints. Anyone can browse; logging in personalizes (flavor, checklist state)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..session import current_member_or_none
from ..serializers import quest_full, quest_summary, specializations_meta

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/specializations")
async def specializations(request: Request):
    return specializations_meta(request.app.state.catalog)


@router.get("/quests")
async def quests(request: Request, specialization: str | None = None, tier: str | None = None,
                 subject: str | None = None, rank: int | None = None, q: str | None = None,
                 member=Depends(current_member_or_none)):
    cat = request.app.state.catalog
    who = None
    if member:
        _, who, _ = await request.app.state.db.user_state(member["id"])
    out = []
    for quest in cat.sorted(cat.quests.values()):
        if not cat.available(quest):
            continue
        if specialization and not (quest.in_specialization(specialization) or specialization in quest.taster_for):
            continue
        if tier and quest.difficulty != tier:
            continue
        if rank is not None and quest.rank != rank:
            continue
        if subject and subject.lower() not in {s.lower() for s in quest.raw.get("subjects") or []}:
            continue
        if q and q.lower() not in (quest.id + " " + quest.raw["title"]).lower():
            continue
        out.append(quest_summary(cat, quest, who))
    return {"count": len(out), "quests": out}


def _admin(member: dict | None) -> bool:
    from ..staff import unlock_all
    return unlock_all(member)


@router.get("/quests/{qid}")
async def quest(qid: str, request: Request, member=Depends(current_member_or_none)):
    cat = request.app.state.catalog
    quest = cat.quests.get(qid)
    if not quest or not cat.available(quest):
        raise HTTPException(404, "No such quest.")
    who, facts, progress = None, set(), None
    if member:
        db = request.app.state.db
        _, state, prog = await db.user_state(member["id"])
        who, facts = state, await db.facts(member["id"])
        p = prog.get(qid)
        progress = {"status": p["status"] if p else None, "quiz_passed": bool(p and p["quiz_passed"]),
                    "completed_at": p["completed_at"] if p else None,
                    "unlocked": quest.rank <= max(state.rank, 0) or quest.rank < 0 or _admin(member),
                    "quiz_attempts": len(await db.quiz_attempts(member["id"], qid)),
                    "submissions": await db.submissions(member["id"], qid)}
    return {"quest": quest_full(cat, quest, who, facts), "progress": progress}


@router.get("/subjects")
async def subjects(request: Request):
    cat = request.app.state.catalog
    counts: dict[str, int] = {}
    for q in cat.quests.values():
        for s in q.raw.get("subjects") or []:
            counts[s] = counts.get(s, 0) + 1
    return {"subjects": sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))}


@router.get("/stats")
async def guild_stats(request: Request):
    """Guild-wide numbers for the guest home page (no login needed, nothing personal)."""
    return await request.app.state.rpg.guild_stats()
