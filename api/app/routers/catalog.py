"""Public curriculum endpoints. Anyone can browse; logging in personalizes (flavor, checklist state)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..session import current_member_or_none
from ..serializers import majors_meta, quest_full, quest_summary

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/majors")
async def majors(request: Request):
    return majors_meta(request.app.state.catalog)


@router.get("/quests")
async def quests(request: Request, major: str | None = None, tier: str | None = None, track: str | None = None,
                 subject: str | None = None, rank: int | None = None, q: str | None = None,
                 member=Depends(current_member_or_none)):
    cat = request.app.state.catalog
    my_major = None
    if member:
        u = await request.app.state.db.user(member["id"])
        my_major = u["major"] if u else None
    out = []
    for quest in cat.sorted(cat.quests.values()):
        if not cat.available(quest):
            continue
        own = bool(major) and bool(cat.counts_for(quest, major))
        if major and not own and major not in quest.adjacent_for:
            continue
        if tier and quest.difficulty != tier:
            continue
        if track and quest.track != track:
            continue
        if rank is not None and quest.rank != rank:
            continue
        if subject and subject.lower() not in {s.lower() for s in quest.raw.get("subjects") or []}:
            continue
        if q and q.lower() not in (quest.id + " " + quest.raw["title"]).lower():
            continue
        d = quest_summary(cat, quest, my_major)
        d["cross"] = bool(major) and not own          # shown for this major only as cross-training
        out.append(d)
    out.sort(key=lambda d: d["cross"])                 # the major's own quests first, cross-training after
    return {"count": len(out), "quests": out}


@router.get("/quests/{qid}")
async def quest(qid: str, request: Request, member=Depends(current_member_or_none)):
    cat = request.app.state.catalog
    quest = cat.quests.get(qid)
    if not quest or not cat.available(quest):
        raise HTTPException(404, "No such quest.")
    major, facts, progress = "undecided", set(), None
    if member:
        db = request.app.state.db
        u, state, prog = await db.user_state(member["id"])
        major, facts = u["major"], await db.facts(member["id"])
        p = prog.get(qid)
        progress = {"status": p["status"] if p else None, "quiz_passed": bool(p and p["quiz_passed"]),
                    "completed_at": p["completed_at"] if p else None,
                    "unlocked": quest.rank <= max(state.rank, 0) or quest.rank < 0,
                    "quiz_attempts": len(await db.quiz_attempts(member["id"], qid)),
                    "submissions": await db.submissions(member["id"], qid)}
    return {"quest": quest_full(cat, quest, major, facts), "progress": progress}


@router.get("/subjects")
async def subjects(request: Request):
    cat = request.app.state.catalog
    counts: dict[str, int] = {}
    for q in cat.quests.values():
        for s in q.raw.get("subjects") or []:
            counts[s] = counts.get(s, 0) + 1
    return {"subjects": sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))}
