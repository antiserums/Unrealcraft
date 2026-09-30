"""Tables the API owns (characters, gear, fights, events) plus the quest-completion path the fight needs."""
from __future__ import annotations

import datetime as dt
import json

from .db import DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    member_id   INTEGER PRIMARY KEY,
    cosmetics   TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS outfits (
    member_id   INTEGER NOT NULL,
    set_id      TEXT NOT NULL,                 -- see rpg.build_sets
    source      TEXT,                          -- quest id, rank:n, achievement key, starter
    earned_at   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (member_id, set_id)
);
CREATE TABLE IF NOT EXISTS fights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id   INTEGER NOT NULL,
    quest_id    TEXT NOT NULL,
    state       TEXT NOT NULL,                 -- json: order, i, right, wounds, dodges, debuff, log, boss, first_try
    result      TEXT,                          -- win | lose | retreat
    started_at  TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_fights_member ON fights(member_id, quest_id);
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,                 -- quest_completed | quiz_passed | loot
    member_id   INTEGER NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    delivered   INTEGER NOT NULL DEFAULT 0
);
"""


class RpgDB:
    def __init__(self, db: DB):
        self.db = db

    @property
    def conn(self):
        return self.db.conn

    async def migrate(self) -> None:
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    # ---------- character / gear ----------
    async def ensure_character(self, uid: int) -> bool:
        """Creates the users row (the bot's table) and the character if missing. True if it was new."""
        await self.conn.execute("INSERT OR IGNORE INTO users(discord_id) VALUES (?)", (uid,))
        cur = await self.conn.execute("INSERT OR IGNORE INTO characters(member_id) VALUES (?)", (uid,))
        await self.conn.commit()
        return cur.rowcount > 0

    async def cosmetics(self, uid: int) -> dict:
        cur = await self.conn.execute("SELECT cosmetics FROM characters WHERE member_id=?", (uid,))
        row = await cur.fetchone()
        return json.loads(row["cosmetics"] or "{}") if row else {}

    async def set_cosmetics(self, uid: int, data: dict) -> None:
        await self.conn.execute("UPDATE characters SET cosmetics=? WHERE member_id=?", (json.dumps(data), uid))
        await self.conn.commit()

    async def outfits(self, uid: int) -> dict[str, dict]:
        cur = await self.conn.execute("SELECT set_id, source, earned_at FROM outfits WHERE member_id=? ORDER BY earned_at", (uid,))
        return {r["set_id"]: dict(r) for r in await cur.fetchall()}

    async def grant_outfit(self, uid: int, set_id: str, source: str) -> bool:
        cur = await self.conn.execute("INSERT OR IGNORE INTO outfits(member_id, set_id, source) VALUES (?,?,?)", (uid, set_id, source))
        await self.conn.commit()
        return cur.rowcount > 0

    # ---------- stat inputs ----------
    async def stat_inputs(self, uid: int) -> dict:
        async def one(sql, *a):
            cur = await self.conn.execute(sql, a)
            return (await cur.fetchone())[0]
        done = await one("SELECT COUNT(*) FROM quest_progress WHERE user_id=? AND status='done'", uid)
        first = await one(
            "SELECT COUNT(*) FROM quiz_attempts a WHERE user_id=? AND passed=1 AND NOT EXISTS "
            "(SELECT 1 FROM quiz_attempts b WHERE b.user_id=a.user_id AND b.quest_id=a.quest_id AND b.id<a.id)", uid)
        approved = await one("SELECT COUNT(*) FROM submissions WHERE user_id=? AND status='pass' AND route IN ('mentor','peer','human')", uid)
        reads = await one("SELECT COUNT(*) FROM kv WHERE user_id=? AND k LIKE 'read:%'", uid)
        cur = await self.conn.execute("SELECT streak_days FROM users WHERE discord_id=?", (uid,))
        row = await cur.fetchone()
        cur = await self.conn.execute("SELECT medal_key FROM medals WHERE user_id=?", (uid,))
        medals = {r["medal_key"] for r in await cur.fetchall()}
        return {"done": done, "first": first, "approved": approved, "reads": reads,
                "streak": row["streak_days"] if row else 0, "medals": medals}

    async def mark_read(self, uid: int, qid: str) -> bool:
        await self.ensure_character(uid)
        cur = await self.conn.execute("INSERT OR IGNORE INTO kv(user_id,k,v) VALUES (?,?,datetime('now'))", (uid, f"read:{qid}"))
        await self.conn.commit()
        return cur.rowcount > 0

    async def crit_xp_today(self, uid: int) -> int:
        cur = await self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM xp_log WHERE user_id=? AND reason LIKE 'crit:%' AND date(created_at)=date('now')", (uid,))
        return (await cur.fetchone())[0]

    # ---------- fights ----------
    async def open_fight(self, uid: int, qid: str) -> dict | None:
        cur = await self.conn.execute(
            "SELECT * FROM fights WHERE member_id=? AND quest_id=? AND result IS NULL ORDER BY id DESC LIMIT 1", (uid, qid))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def fight(self, fid: int) -> dict | None:
        cur = await self.conn.execute("SELECT * FROM fights WHERE id=?", (fid,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def create_fight(self, uid: int, qid: str, state: dict) -> int:
        await self.conn.execute("UPDATE fights SET result='retreat', finished_at=datetime('now') WHERE member_id=? AND quest_id=? AND result IS NULL", (uid, qid))
        cur = await self.conn.execute("INSERT INTO fights(member_id, quest_id, state) VALUES (?,?,?)", (uid, qid, json.dumps(state)))
        await self.conn.commit()
        return cur.lastrowid

    async def save_fight(self, fid: int, state: dict, result: str | None = None) -> None:
        if result:
            await self.conn.execute("UPDATE fights SET state=?, result=?, finished_at=datetime('now') WHERE id=?",
                                    (json.dumps(state), result, fid))
        else:
            await self.conn.execute("UPDATE fights SET state=? WHERE id=?", (json.dumps(state), fid))
        await self.conn.commit()

    async def last_lost_fight_at(self, uid: int, qid: str) -> dt.datetime | None:
        cur = await self.conn.execute(
            "SELECT finished_at FROM fights WHERE member_id=? AND quest_id=? AND result='lose' ORDER BY id DESC LIMIT 1", (uid, qid))
        row = await cur.fetchone()
        return dt.datetime.fromisoformat(row["finished_at"]) if row and row["finished_at"] else None

    # ---------- writes shared with the bot's tables ----------
    async def log_quiz(self, uid: int, qid: str, score: int, total: int, passed: bool) -> None:
        await self.conn.execute("INSERT INTO quiz_attempts(user_id, quest_id, score, total, passed) VALUES (?,?,?,?,?)",
                                (uid, qid, score, total, int(passed)))
        await self.conn.commit()

    async def set_progress(self, uid: int, qid: str, status: str, quiz_passed: bool | None = None) -> None:
        now = dt.datetime.utcnow().isoformat(timespec="seconds") if status == "done" else None
        await self.conn.execute(
            """INSERT INTO quest_progress(user_id, quest_id, status, quiz_passed, completed_at) VALUES (?,?,?,?,?)
               ON CONFLICT(user_id, quest_id) DO UPDATE SET
                 status = CASE WHEN quest_progress.status = 'done' THEN 'done' ELSE excluded.status END,
                 quiz_passed = MAX(quest_progress.quiz_passed, excluded.quiz_passed),
                 completed_at = COALESCE(quest_progress.completed_at, excluded.completed_at)""",
            (uid, qid, status, int(bool(quiz_passed)), now))
        await self.conn.commit()

    async def add_xp(self, uid: int, amount: int, reason: str) -> int:
        await self.conn.execute("INSERT INTO xp_log(user_id, amount, reason) VALUES (?,?,?)", (uid, amount, reason))
        await self.conn.execute("UPDATE users SET xp = xp + ? WHERE discord_id = ?", (amount, uid))
        await self.conn.commit()
        cur = await self.conn.execute("SELECT xp FROM users WHERE discord_id = ?", (uid,))
        return (await cur.fetchone())["xp"]

    async def add_fact(self, uid: int, name: str) -> None:
        await self.conn.execute("INSERT OR IGNORE INTO kv(user_id, k, v) VALUES (?,?,datetime('now'))", (uid, f"fact:{name}"))
        await self.conn.commit()

    async def grant_medal(self, uid: int, key: str) -> bool:
        cur = await self.conn.execute("INSERT OR IGNORE INTO medals(user_id, medal_key) VALUES (?,?)", (uid, key))
        await self.conn.commit()
        return cur.rowcount > 0

    async def touch_streak(self, uid: int) -> int:
        cur = await self.conn.execute("SELECT streak_days, last_active_day, on_leave FROM users WHERE discord_id=?", (uid,))
        u = await cur.fetchone()
        today = dt.date.today()
        last = dt.date.fromisoformat(u["last_active_day"]) if u["last_active_day"] else None
        if last == today:
            return u["streak_days"]
        streak = u["streak_days"] + 1 if (last == today - dt.timedelta(days=1) or u["on_leave"]) else 1
        await self.conn.execute("UPDATE users SET streak_days=?, last_active_day=? WHERE discord_id=?", (streak, today.isoformat(), uid))
        await self.conn.commit()
        return streak

    async def emit(self, type_: str, uid: int, payload: dict) -> None:
        await self.conn.execute("INSERT INTO events(type, member_id, payload) VALUES (?,?,?)", (type_, uid, json.dumps(payload)))
        await self.conn.commit()
