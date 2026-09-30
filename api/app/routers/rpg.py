"""Character sheet and boss fights (the quiz, as a turn-based fight)."""
from __future__ import annotations

import datetime as dt
import random
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from registrar import profile as prof_mod  # noqa: E402
from registrar.curriculum import Quest  # noqa: E402

from .. import rpg
from ..session import current_member

router = APIRouter(tags=["rpg"])
NAMEPLATE_COLORS = ["#7A8C7E", "#B5714B", "#3D7DD8", "#8E6CCF", "#D9824A", "#D9534F", "#4FA36C", "#C85C8E", "#4AA3B5", "#D4AF37"]


async def character_payload(request: Request, uid: int, major: str) -> dict:
    rdb = request.app.state.rpg
    await rdb.ensure_character(uid)
    have = {g["slot"] for g in await rdb.gear(uid)}
    for item in rpg.starter_kit(major):            # every slot gets a plain starter piece, once
        if item["slot"] not in have:
            await rdb.add_gear(uid, item, None, equip=True)
    inputs = await rdb.stat_inputs(uid)
    stats = rpg.stats_from(inputs["done"], inputs["first"], inputs["approved"], inputs["reads"], inputs["streak"])
    gear = await rdb.gear(uid)
    equipped = [g for g in gear if g["equipped"]]
    totals = rpg.gear_totals(equipped)
    return {
        "stats": stats, "stat_blurb": rpg.STAT_BLURB, "gear_totals": totals,
        "equipped": {g["slot"]: g for g in equipped},
        "inventory": gear, "cosmetics": await rdb.cosmetics(uid), "nameplate_colors": NAMEPLATE_COLORS,
        "slots": rpg.SLOTS, "major": major,
    }


@router.get("/me/character")
async def character(request: Request, member=Depends(current_member)):
    u = await request.app.state.db.user(member["id"])
    return await character_payload(request, member["id"], (u or {}).get("major", "undecided"))


class CharacterPatch(BaseModel):
    equip: int | None = None
    nameplate: str | None = None
    banner: str | None = None
    featured: list[int] | None = None
    appearance: dict[str, str] | None = None      # body, skin, face, hair, hair_color... (art pack ids)


@router.patch("/me/character")
async def patch_character(body: CharacterPatch, request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    await rdb.ensure_character(member["id"])
    if body.equip is not None and not await rdb.equip(member["id"], body.equip):
        raise HTTPException(404, "No such item.")
    cos = await rdb.cosmetics(member["id"])
    if body.nameplate is not None:
        if body.nameplate not in NAMEPLATE_COLORS:
            raise HTTPException(400, "Pick a color from the palette.")
        cos["nameplate"] = body.nameplate
    if body.banner is not None:
        cos["banner"] = body.banner[:40]
    if body.featured is not None:
        cos["featured"] = body.featured[:3]
    if body.appearance is not None:
        clean = {k[:24]: v[:48] for k, v in body.appearance.items() if isinstance(v, str)}
        cos["appearance"] = {**cos.get("appearance", {}), **clean}
    await rdb.set_cosmetics(member["id"], cos)
    u = await request.app.state.db.user(member["id"])
    return await character_payload(request, member["id"], (u or {}).get("major", "undecided"))


@router.post("/me/quests/{qid}/read")
async def mark_read(qid: str, request: Request, member=Depends(current_member)):
    """Called when a reading link is opened. Feeds the Lore stat; one per quest."""
    if qid not in request.app.state.catalog.quests:
        raise HTTPException(404, "No such quest.")
    new = await request.app.state.rpg.mark_read(member["id"], qid)
    return {"ok": True, "new": new}


# ------------------------------------------------------------------ fights
def _question_view(q: Quest, state: dict) -> dict:
    i = state["i"]
    item = q.quiz[i]
    order = state["orders"][i]
    return {"index": i, "total": len(q.quiz), "q": item["q"], "choices": [item["choices"][k] for k in order],
            "hint": None if state.get("debuff") == "blinded" else _hint(q, i), "debuff": state.get("debuff"),
            "asked_at": time.time()}


def _hint(q: Quest, i: int) -> str | None:
    subjects = q.raw.get("subjects") or []
    return f"It readies a question about {subjects[i % len(subjects)].replace('-', ' ')}." if subjects else None


def _public(state: dict, q: Quest, boss: dict, char: dict, question: dict | None) -> dict:
    total = len(q.quiz)
    return {
        "fight_id": state["fight_id"],
        "quest": {"id": q.id, "title": q.raw["title"], "xp": q.xp, "verify_type": q.raw.get("verify_type")},
        "boss": boss,
        "you": {"vitality": char["stats"]["vitality"], "wounds": state["wounds"], "wounds_allowed": boss["wounds_allowed"],
                "dodge_pct": char["gear_totals"]["dodge"], "dodge_used": state["dodges"] > 0,
                "cleanse": bool(char["gear_totals"]["cleanse"]), "steady_available": state["steady_available"],
                "craft": char["stats"]["craft"] + char["gear_totals"]["craft"], "focus": char["stats"]["focus"],
                "crit_pct": rpg.crit_chance(char["stats"]["focus"], char["gear_totals"].get("focus", 0), None)},
        "hits": state["right"] + state["dodges"], "hits_to_win": boss["hits_to_win"], "turn": state["i"] + 1, "total": total,
        "first_try": state["first_try"], "log": state["log"][-6:], "question": question, "result": state.get("result"),
        "outcome": state.get("outcome"),
    }


@router.post("/me/quests/{qid}/fight")
async def start_fight(qid: str, request: Request, member=Depends(current_member)):
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    q = cat.quests.get(qid)
    if not q or not q.quiz:
        raise HTTPException(404, "No boss here. This quest has no quiz.")
    u, state_u, prog = await db.user_state(member["id"])
    if q.rank > max(state_u.rank, 0) and q.rank >= 0:
        raise HTTPException(403, "This room is locked until you rank up.")
    # No cooldown after a loss: the reading is right there, try again when ready.
    char = await character_payload(request, member["id"], u["major"])
    attempts = await db.quiz_attempts(member["id"], qid)
    rng = random.Random()
    boss = rpg.boss_for(q)
    state = {
        "orders": [rng.sample(range(len(it["choices"])), len(it["choices"])) for it in q.quiz],
        "i": 0, "right": 0, "wounds": 0, "dodges": 0, "debuff": None, "log": [], "first_try": len(attempts) == 0,
        "steady_available": char["stats"]["resolve"] >= 7, "asked_at": time.time(), "crit_xp": 0, "answers": [],
    }
    fid = await rdb.create_fight(member["id"], qid, state)
    state["fight_id"] = fid
    await rdb.save_fight(fid, state)
    state["log"].append({"kind": "intro", "text": f"{boss['name']} {boss['verb']}. {boss['intro']}"})
    return _public(state, q, boss, char, _question_view(q, state))


class Turn(BaseModel):
    answer: int          # position in the shown choice order
    seconds: float | None = None


@router.get("/fights/{fid}")
async def get_fight(fid: int, request: Request, member=Depends(current_member)):
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    f = await rdb.fight(fid)
    if not f or f["member_id"] != member["id"]:
        raise HTTPException(404, "No such fight.")
    import json
    state = json.loads(f["state"]); state["fight_id"] = fid
    q = cat.quests[f["quest_id"]]
    u = await db.user(member["id"])
    char = await character_payload(request, member["id"], u["major"])
    boss = rpg.boss_for(q)
    question = _question_view(q, state) if f["result"] is None and state["i"] < len(q.quiz) else None
    state["result"] = f["result"]
    return _public(state, q, boss, char, question)


@router.post("/fights/{fid}/turn")
async def turn(fid: int, body: Turn, request: Request, member=Depends(current_member)):
    import json
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    f = await rdb.fight(fid)
    if not f or f["member_id"] != member["id"]:
        raise HTTPException(404, "No such fight.")
    if f["result"]:
        raise HTTPException(409, "This fight is over.")
    state = json.loads(f["state"]); state["fight_id"] = fid
    q = cat.quests[f["quest_id"]]
    u = await db.user(member["id"])
    char = await character_payload(request, member["id"], u["major"])
    boss = rpg.boss_for(q)
    rng = random.Random()
    i = state["i"]
    item = q.quiz[i]
    order = state["orders"][i]
    if not 0 <= body.answer < len(order):
        raise HTTPException(400, "Pick one of the four choices.")
    chosen = order[body.answer]
    right = chosen == item["answer_index"]
    events: list[dict] = []
    debuff = state.get("debuff")
    if debuff and char["gear_totals"]["cleanse"]:
        debuff = None
        events.append({"kind": "cleanse", "text": rpg.boss_line(boss, "cleanse", rng)})
    state["debuff"] = None
    if right:
        state["right"] += 1
        crit_pct = rpg.crit_chance(char["stats"]["focus"], char["gear_totals"].get("focus", 0), body.seconds)
        crit = rng.randint(1, 100) <= crit_pct
        dmg = 10 + 2 * (char["stats"]["craft"] + char["gear_totals"]["craft"])
        if debuff == "weakened":
            dmg //= 2
        bonus_xp = 0
        if crit:
            dmg *= 2
            bonus_xp = min(rng.randint(2, 5), max(0, rpg.CRIT_XP_DAILY_CAP - await rdb.crit_xp_today(member["id"])))
            if bonus_xp:
                await rdb.add_xp(member["id"], bonus_xp, f"crit:{q.id}")
                state["crit_xp"] += bonus_xp
        events.append({"kind": "crit" if crit else "hit", "text": rpg.boss_line(boss, "crit" if crit else "hit", rng),
                       "damage": dmg, "bonus_xp": bonus_xp, "explain": item.get("explain", "")})
    else:
        dodge_pct = char["gear_totals"]["dodge"]
        if state["dodges"] == 0 and dodge_pct and rng.randint(1, 100) <= dodge_pct:
            state["dodges"] = 1
            events.append({"kind": "dodge", "text": rpg.boss_line(boss, "dodge", rng),
                           "explain": item.get("explain", ""), "correct": order.index(item["answer_index"])})
        elif state["steady_available"]:
            state["steady_available"] = False
            state["wounds"] += 0.5
            events.append({"kind": "steady", "text": rpg.boss_line(boss, "steady", rng),
                           "explain": item.get("explain", ""), "correct": order.index(item["answer_index"])})
        else:
            state["wounds"] += 1
            events.append({"kind": "wound", "text": rpg.boss_line(boss, "wound", rng),
                           "explain": item.get("explain", ""), "correct": order.index(item["answer_index"])})
        if state["wounds"] <= boss["wounds_allowed"] and i + 1 < len(q.quiz):
            state["debuff"] = rpg.debuff_for(None, rng)
            d = rpg.DEBUFFS[state["debuff"]]
            events.append({"kind": "debuff", "text": f"{d['name']}: {d['text']}", "debuff": state["debuff"]})
    state["answers"].append({"i": i, "chosen": chosen, "right": right})
    state["log"] += events
    state["i"] = i + 1

    total = len(q.quiz)
    # Score for the record: right answers plus the one dodged attack (gear may afford a dodge, by design).
    # A "steady" half-wound is visual only: the miss still counts, so Resolve never changes the outcome.
    score = state["right"] + state["dodges"]
    misses = state["i"] - score
    result = None
    if misses > boss["wounds_allowed"]:
        result = "lose"
    elif state["i"] >= total:
        result = "win" if score >= boss["hits_to_win"] else "lose"
    question = None
    if result:
        state["result"] = result
        await rdb.save_fight(fid, state, result)
        await _finish(request, member["id"], q, score, total, result == "win", state["first_try"], state, events, rng)
    else:
        await rdb.save_fight(fid, state)
        state["asked_at"] = time.time()
        question = _question_view(q, state)
    out = _public(state, q, boss, char, question)
    out["events"] = events
    return out


async def _finish(request: Request, uid: int, q: Quest, score: int, total: int, passed: bool, first_try: bool,
                  state: dict, events: list[dict], rng: random.Random) -> None:
    """Mirror of the bot's Quiz.finish + Quests.complete, minus Discord. The bot picks up the event."""
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    boss = rpg.boss_for(q)
    await rdb.log_quiz(uid, q.id, score, total, passed)
    if not passed:
        events.append({"kind": "lose", "text": rpg.boss_line(boss, "lose", rng)})
        state["outcome"] = {"passed": False, "score": score, "total": total}
        return
    await rdb.set_progress(uid, q.id, "quiz_passed", quiz_passed=True)
    await rdb.add_fact(uid, f"quiz.{q.id}")
    bonus = 0
    if first_try:
        bonus = round(q.xp * cat.xp_rules.get("quiz_first_try_bonus_pct", 20) / 100)
        await rdb.add_xp(uid, bonus, f"quiz_bonus:{q.id}")
    events.append({"kind": "win", "text": rpg.boss_line(boss, "win", rng)})
    import json
    prof = json.loads(await db.kv_get(uid, "profile") or "{}")
    u = await db.user(uid)
    test_out = q.spine and first_try and prof_mod.can_test_out(prof)
    completed, loot, xp = False, None, 0
    if q.raw.get("verify_type") == "quiz" or test_out:
        xp, loot = await complete_quest(request, uid, q, u)
        completed = True
    await rdb.emit("quiz_passed", uid, {"quest": q.id, "score": score, "total": total, "first_try": first_try})
    state["outcome"] = {"passed": True, "score": score, "total": total, "first_try_bonus": bonus, "crit_xp": state.get("crit_xp", 0),
                        "completed": completed, "quest_xp": xp, "loot": loot, "tested_out": bool(test_out and q.raw.get("verify_type") != "quiz"),
                        "next": "next" if completed else ("action" if q.raw.get("verify_type") == "action" else "submit")}
    await rdb.save_fight(state["fight_id"], state, "win")


async def complete_quest(request: Request, uid: int, q: Quest, u: dict) -> tuple[int, dict | None]:
    """Single path for a quest becoming done on the website: XP, streak, medal, loot, event for the bot."""
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    done = {qid for qid, p in (await db.progress(uid)).items() if p["status"] == "done"}
    if q.id in done:
        return 0, None
    xp = q.xp
    if u["rank"] >= 3 and u.get("seal") and q.raw.get("seal") == u["seal"]:
        xp = round(xp * cat.xp_rules.get("in_seal_multiplier_rank3plus", 1.25))
    await rdb.set_progress(uid, q.id, "done")
    await rdb.add_xp(uid, xp, f"quest:{q.id}")
    await rdb.touch_streak(uid)
    if q.rank >= 0:
        await rdb.grant_medal(uid, "first_blood")
    loot = rpg.roll_loot(q, u["major"], random.Random())
    if loot and (not loot.get("set_piece") or not await rdb.has_item(uid, loot["key"])):
        loot["id"] = await rdb.add_gear(uid, loot, q.id)
    else:
        loot = None
    await rdb.emit("quest_completed", uid, {"quest": q.id, "xp": xp, "loot": loot["name"] if loot else None})
    return xp, loot


@router.post("/fights/{fid}/retreat")
async def retreat(fid: int, request: Request, member=Depends(current_member)):
    import json
    rdb = request.app.state.rpg
    f = await rdb.fight(fid)
    if not f or f["member_id"] != member["id"]:
        raise HTTPException(404, "No such fight.")
    if f["result"] is None:
        await rdb.save_fight(fid, json.loads(f["state"]), "retreat")
    return {"ok": True}


@router.get("/catalog/quests/{qid}/boss")
async def boss(qid: str, request: Request):
    q = request.app.state.catalog.quests.get(qid)
    if not q:
        raise HTTPException(404, "No such quest.")
    return rpg.boss_for(q)
