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


async def character_payload(request: Request, uid: int, u: dict) -> dict:
    """Stats (computed, hidden), the outfits this member owns (granted idempotently from progress), and the one worn."""
    rdb, cat, db = request.app.state.rpg, request.app.state.catalog, request.app.state.db
    await rdb.ensure_character(uid)
    major = u.get("major", "undecided")
    inputs = await rdb.stat_inputs(uid)
    stats = rpg.stats_from(inputs["done"], inputs["first"], inputs["approved"], inputs["reads"], inputs["streak"])
    sets = rpg.build_sets(cat)
    _, state, _ = await db.user_state(uid)
    earned = {a["key"] for a in rpg.achievements_for(cat, inputs, state.done, await db.medals(uid)) if a["earned"]}
    new_sets = []
    owned = await rdb.outfits(uid)
    for st in rpg.unlocked_now(sets, rank=u.get("rank", -1), earned=earned):
        if st["id"] not in owned:
            src = st["unlock"].get("key") or (f"rank:{st['unlock']['n']}" if st["unlock"]["type"] == "rank" else "starter")
            if await rdb.grant_outfit(uid, st["id"], str(src)):
                new_sets.append(st["id"])
    owned = await rdb.outfits(uid)
    cos = await rdb.cosmetics(uid)
    ids = {st["id"] for st in sets}
    worn = cos.get("outfit") if cos.get("outfit") in owned and cos.get("outfit") in ids else rpg.STARTER_SET
    catalog = []
    for st in sets:
        d = {k: v for k, v in st.items() if k != "unlock"}
        d["owned"] = st["id"] in owned
        d["earned_at"] = owned[st["id"]]["earned_at"] if d["owned"] else None
        d["hint"] = st["unlock"].get("hint")
        d["worn"] = st["id"] == worn
        catalog.append(d)
    style = cos.get("style") if cos.get("style") in rpg.STYLES else "melee"
    body = (cos.get("appearance") or {}).get("body") or "body_a"
    return {"stats": stats, "worn": next(c for c in catalog if c["worn"]), "style": style, "body": body,
            "outfits": catalog, "new_outfits": new_sets, "cosmetics": cos, "nameplate_colors": NAMEPLATE_COLORS,
            "slots": rpg.SLOTS, "styles": rpg.STYLES, "major": major}


@router.get("/me/character")
async def character(request: Request, member=Depends(current_member)):
    u, _, _ = await request.app.state.db.user_state(member["id"])
    return await character_payload(request, member["id"], u)


async def achievements_payload(request: Request, uid: int) -> list[dict]:
    rdb, cat, db = request.app.state.rpg, request.app.state.catalog, request.app.state.db
    await rdb.ensure_character(uid)
    inputs = await rdb.stat_inputs(uid)
    _, state, _ = await db.user_state(uid)
    return rpg.achievements_for(cat, inputs, state.done, await db.medals(uid))


@router.get("/me/achievements")
async def my_achievements(request: Request, member=Depends(current_member)):
    return {"achievements": await achievements_payload(request, member["id"])}


async def card_payload(request: Request, uid: int, session: dict | None) -> dict:
    """The player card: who they are, what they wear, what they chose to show. Shared by /me/card and /members/{id}."""
    from .me import profile_payload
    db, cat, rdb = request.app.state.db, request.app.state.catalog, request.app.state.rpg
    u, state, _ = await db.user_state(uid)
    medals = await db.medals(uid)
    who = session if session and session["id"] == uid else None
    p = profile_payload(cat, who, u, state, medals)
    if not who:
        p["name"] = await rdb.kv_get(uid, "web.name")
        p["avatar"] = await rdb.kv_get(uid, "web.avatar")
    char = await character_payload(request, uid, u)
    ach = rpg.achievements_for(cat, await rdb.stat_inputs(uid), state.done, medals)
    earned = [a for a in ach if a["earned"]]
    cos = char["cosmetics"]
    featured = [a for k in cos.get("featured", []) for a in earned if a["key"] == k][:3] or earned[-3:]
    options = rpg.cosmetic_catalog(int(u.get("rank", -1)), {a["key"] for a in earned})
    plate = rpg.pick_owned(options["nameplate"], cos.get("nameplate"))
    return {**p, "worn": char["worn"], "style": char["style"], "body": char["body"], "cosmetics": cos,
            "nameplate": plate["value"], "nameplate_id": plate["id"],
            "avatar_frame": rpg.pick_owned(options["avatar_frame"], cos.get("avatar_frame"))["id"],
            "card_frame": rpg.pick_owned(options["card_frame"], cos.get("card_frame"))["id"],
            "cosmetic_options": options,
            "motto": cos.get("banner") or "", "public": bool(cos.get("public")),
            "achievements_earned": len(earned), "achievements_total": len(ach), "featured": featured,
            "nameplate_colors": NAMEPLATE_COLORS, "earned_achievements": earned}


@router.get("/me/card")
async def my_card(request: Request, member=Depends(current_member)):
    return await card_payload(request, member["id"], member)


class CharacterPatch(BaseModel):
    wear: str | None = None
    nameplate: str | None = None
    banner: str | None = None                      # the motto on the player card
    avatar_frame: str | None = None                # card cosmetics, see rpg.AVATAR_FRAMES / CARD_FRAMES
    card_frame: str | None = None
    featured: list[str] | None = None              # up to three achievement keys shown on the card
    public: bool | None = None                     # card visible without logging in
    style: str | None = None                       # melee (sword + shield) | caster (staff + orb)
    appearance: dict[str, str] | None = None      # body (body_a | body_b); more once the pack's renderer is ported


@router.patch("/me/character")
async def patch_character(body: CharacterPatch, request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    await rdb.ensure_character(member["id"])
    cos = await rdb.cosmetics(member["id"])
    if body.wear is not None:
        if body.wear not in await rdb.outfits(member["id"]):
            raise HTTPException(403, "You have not earned that outfit yet.")
        cos["outfit"] = body.wear
    u0, state0, _ = await request.app.state.db.user_state(member["id"])
    earned0 = {a["key"] for a in rpg.achievements_for(request.app.state.catalog, await rdb.stat_inputs(member["id"]), state0.done,
                                                       await request.app.state.db.medals(member["id"])) if a["earned"]}
    options = rpg.cosmetic_catalog(int(u0.get("rank", -1)), earned0)
    for field, kind in (("nameplate", "nameplate"), ("avatar_frame", "avatar_frame"), ("card_frame", "card_frame")):
        want = getattr(body, field)
        if want is None:
            continue
        hit = next((c for c in options[kind] if want in (c["id"], c.get("value"))), None)
        if not hit:
            raise HTTPException(400, "Pick one from the list.")
        if not hit["owned"]:
            raise HTTPException(403, f"Not unlocked yet: {hit['hint']}.")
        cos[field] = hit["id"]
    if body.banner is not None:
        cos["banner"] = body.banner[:40]
    if body.featured is not None:
        cos["featured"] = [k[:40] for k in body.featured[:3]]
    if body.public is not None:
        cos["public"] = body.public
    if body.style is not None:
        if body.style not in rpg.STYLES:
            raise HTTPException(400, "Pick sword and shield, or staff and orb.")
        cos["style"] = body.style
    if body.appearance is not None:
        clean = {k[:24]: v[:48] for k, v in body.appearance.items() if isinstance(v, str)}
        cos["appearance"] = {**cos.get("appearance", {}), **clean}
    await rdb.set_cosmetics(member["id"], cos)
    if any(x is not None for x in (body.banner, body.featured, body.public, body.nameplate, body.avatar_frame, body.card_frame)):
        return await card_payload(request, member["id"], member)
    u, _, _ = await request.app.state.db.user_state(member["id"])
    return await character_payload(request, member["id"], u)


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
                "steady_available": state["steady_available"], "craft": char["stats"]["craft"], "focus": char["stats"]["focus"],
                "crit_pct": rpg.crit_chance(char["stats"]["focus"], None), "outfit": char["worn"]["art_id"], "style": char["style"]},
        "hits": state["right"], "hits_to_win": boss["hits_to_win"], "turn": state["i"] + 1, "total": total,
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
    char = await character_payload(request, member["id"], u)
    attempts = await db.quiz_attempts(member["id"], qid)
    rng = random.Random()
    boss = rpg.boss_for(q)
    state = {
        "orders": [rng.sample(range(len(it["choices"])), len(it["choices"])) for it in q.quiz],
        "i": 0, "right": 0, "wounds": 0, "debuff": None, "log": [], "first_try": len(attempts) == 0,
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
    u, _, _ = await db.user_state(member["id"])
    char = await character_payload(request, member["id"], u)
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
    u, _, _ = await db.user_state(member["id"])
    char = await character_payload(request, member["id"], u)
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
    state["debuff"] = None
    if right:
        state["right"] += 1
        crit_pct = rpg.crit_chance(char["stats"]["focus"], body.seconds)
        crit = rng.randint(1, 100) <= crit_pct
        dmg = 10 + 2 * char["stats"]["craft"]
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
        if state["steady_available"]:
            state["steady_available"] = False
            state["wounds"] += 0.5
            events.append({"kind": "steady", "text": rpg.boss_line(boss, "steady", rng),
                           "explain": item.get("explain", ""), "correct": order.index(item["answer_index"])})
        else:
            state["wounds"] += 1
            events.append({"kind": "wound", "text": rpg.boss_line(boss, "wound", rng),
                           "explain": item.get("explain", ""), "correct": order.index(item["answer_index"])})
        if (state["i"] + 1 - state["right"]) <= boss["wounds_allowed"] and i + 1 < len(q.quiz):
            state["debuff"] = rpg.debuff_for(None, rng)
            d = rpg.DEBUFFS[state["debuff"]]
            events.append({"kind": "debuff", "text": f"{d['name']}: {d['text']}", "debuff": state["debuff"]})
    state["answers"].append({"i": i, "chosen": chosen, "right": right})
    state["log"] += events
    state["i"] = i + 1

    total = len(q.quiz)
    # A "steady" half-wound is visual only: the miss still counts, so Resolve never changes the outcome.
    score = state["right"]
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
    else:
        loot = await new_outfits(request, uid)
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
    loot = await new_outfits(request, uid)
    await rdb.emit("quest_completed", uid, {"quest": q.id, "xp": xp, "outfit": loot["name"] if loot else None})
    return xp, loot


async def new_outfits(request: Request, uid: int) -> dict | None:
    """Grants any outfit the member just earned and returns the first new one (for the reward screen)."""
    u, _, _ = await request.app.state.db.user_state(uid)
    char = await character_payload(request, uid, u)
    if not char["new_outfits"]:
        return None
    st = next(o for o in char["outfits"] if o["id"] == char["new_outfits"][0])
    return {"name": st["name"], "flavour": st["flavour"], "tier": st["tier"], "color": st["color"], "id": st["id"]}


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
