"""Progress rules the site owns: facts, quests that finish themselves, and promotions.

The Discord bot used to do all three. It no longer runs the game: the site decides, then writes an `events` row
(`rank_up`) so the bot can swap Discord roles and announce it.

Facts are small records of something the member did on the site (kv key `fact:<name>`). A quest whose checklist
is made only of fact checks (`verify_type: action`) completes itself the moment its last fact is recorded.
Fact names written by the site:
  quiz.<QID>          a boss was beaten
  submit.O5           the practice turn-in was sent
  spec.chosen         a primary specialization was chosen (Undecided counts)
  site.card           opened the player card page
  site.path           opened My path on the quest board
  site.achievements   opened the achievements page
  card.motto          saved a motto on the player card
"""
from __future__ import annotations

from fastapi import Request

from registrar import checks  # noqa: E402

JUMP_MEDAL = "jump_{}_{}"
TOP_RANK = 6


async def add_fact(request: Request, uid: int, name: str) -> bool:
    """Record a fact. Returns True if it was new; a new fact may finish a quest and earn a promotion."""
    rdb = request.app.state.rpg
    cur = await rdb.conn.execute("INSERT OR IGNORE INTO kv(user_id, k, v) VALUES (?,?,datetime('now'))", (uid, f"fact:{name}"))
    await rdb.conn.commit()
    if cur.rowcount > 0:
        await auto_complete(request, uid)
        return True
    return False


async def auto_complete(request: Request, uid: int) -> list[str]:
    """Finish every open quest whose checklist is fully verified by facts. Returns the quest ids it completed."""
    from .routers.rpg import complete_quest
    cat, db = request.app.state.catalog, request.app.state.db
    u, state, _ = await db.user_state(uid)
    facts = await db.facts(uid)
    done = []
    for q in cat.sorted(cat.quests.values()):
        if q.id in state.done or q.raw.get("verify_type") != "action" or not checks.fully_auto(q):
            continue
        if q.rank > max(state.rank, 0) or checks.facts_missing(q, facts):
            continue
        await complete_quest(request, uid, q, u)
        done.append(q.id)
    return done


async def check_promotion(request: Request, uid: int) -> list[int]:
    """Promote while the member meets the next rank's XP and requirements. Staff-approved ranks are never automatic.
    Returns the ranks reached."""
    cat, db, rdb = request.app.state.catalog, request.app.state.db, request.app.state.rpg
    reached: list[int] = []
    for _ in range(TOP_RANK + 2):
        u, state, _ = await db.user_state(uid)
        target = u["rank"] + 1
        if target > TOP_RANK or (target not in cat.ranks and target != 0):
            break
        if cat.ranks.get(target, {}).get("human_review"):
            break
        ok, _missing = cat.rank_requirements_met(state, target)
        if not ok or u["xp"] < cat.xp_needed(target):
            break
        await promote(request, uid, u["rank"], target)
        reached.append(target)
    return reached


async def promote(request: Request, uid: int, old: int, new: int, by_admin: bool = False) -> None:
    """Set the rank, stamp the date, grant the rank-up medal, and tell the bot."""
    rdb = request.app.state.rpg
    await rdb.conn.execute("UPDATE users SET rank=?, rank_since=datetime('now') WHERE discord_id=?", (new, uid))
    await rdb.conn.commit()
    if new > old:
        await rdb.grant_medal(uid, JUMP_MEDAL.format(old, new))
    await rdb.emit("rank_up" if new > old and not by_admin else "rank_set", uid, {"old": old, "rank": new, "admin": by_admin})
    if new > old:
        title = request.app.state.catalog.ranks.get(new, {}).get("title", f"rank {new}")
        await rdb.send_letter(uid, "rank", f"You reached {title}", "A new tier of dungeons is open, and a new set is waiting in your wardrobe.", "/me/wardrobe", None)
