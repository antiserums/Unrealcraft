"""SQLite access. One connection, and every write goes through a helper here so XP is always logged."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import aiosqlite

from .config import BOT_ROOT

SCHEMA = BOT_ROOT / "db" / "schema.sql"


class DB:
    def __init__(self, path: Path):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        # small migrations for databases created before a column existed
        for table, col, kind in (("submissions", "public_channel_id", "INTEGER"),
                                 ("submissions", "public_message_id", "INTEGER")):
            try:
                await self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {kind}")
            except aiosqlite.OperationalError:
                pass                                  # already there
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    # ---------- users ----------
    async def user(self, uid: int) -> aiosqlite.Row:
        await self.conn.execute("INSERT OR IGNORE INTO users(discord_id) VALUES (?)", (uid,))
        await self.conn.commit()
        cur = await self.conn.execute("SELECT * FROM users WHERE discord_id = ?", (uid,))
        return await cur.fetchone()

    async def set_user(self, uid: int, **fields) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        await self.conn.execute(f"UPDATE users SET {cols} WHERE discord_id = ?", (*fields.values(), uid))
        await self.conn.commit()

    # ---------- xp ----------
    async def add_xp(self, uid: int, amount: int, reason: str) -> int:
        """The only way XP changes. Returns new total."""
        await self.conn.execute("INSERT INTO xp_log(user_id, amount, reason) VALUES (?,?,?)", (uid, amount, reason))
        await self.conn.execute("UPDATE users SET xp = xp + ? WHERE discord_id = ?", (amount, uid))
        await self.conn.commit()
        cur = await self.conn.execute("SELECT xp FROM users WHERE discord_id = ?", (uid,))
        return (await cur.fetchone())["xp"]

    async def xp_count_today(self, uid: int, reason_prefix: str) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) c FROM xp_log WHERE user_id=? AND reason LIKE ? AND date(created_at)=date('now')",
            (uid, reason_prefix + "%"),
        )
        return (await cur.fetchone())["c"]

    async def xp_count_since(self, uid: int, reason_prefix: str, days: int) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) c FROM xp_log WHERE user_id=? AND reason LIKE ? AND created_at >= datetime('now', ?)",
            (uid, reason_prefix + "%", f"-{days} days"),
        )
        return (await cur.fetchone())["c"]

    # ---------- progress ----------
    async def progress(self, uid: int) -> dict[str, str]:
        cur = await self.conn.execute("SELECT quest_id, status FROM quest_progress WHERE user_id=?", (uid,))
        return {r["quest_id"]: r["status"] for r in await cur.fetchall()}

    async def done_set(self, uid: int) -> set[str]:
        return {q for q, s in (await self.progress(uid)).items() if s == "done"}

    async def skipped_set(self, uid: int) -> set[str]:
        return {q for q, s in (await self.progress(uid)).items() if s == "skipped"}

    async def set_progress(self, uid: int, qid: str, status: str, quiz_passed: bool | None = None) -> None:
        now = dt.datetime.utcnow().isoformat(timespec="seconds") if status == "done" else None
        await self.conn.execute(
            """INSERT INTO quest_progress(user_id, quest_id, status, quiz_passed, completed_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(user_id, quest_id) DO UPDATE SET
                 status = CASE WHEN quest_progress.status = 'done' THEN 'done' ELSE excluded.status END,
                 quiz_passed = MAX(quest_progress.quiz_passed, excluded.quiz_passed),
                 completed_at = COALESCE(quest_progress.completed_at, excluded.completed_at)""",
            (uid, qid, status, int(bool(quiz_passed)), now),
        )
        await self.conn.commit()

    async def quiz_passed(self, uid: int, qid: str) -> bool:
        cur = await self.conn.execute(
            "SELECT quiz_passed FROM quest_progress WHERE user_id=? AND quest_id=?", (uid, qid))
        row = await cur.fetchone()
        return bool(row and row["quiz_passed"])

    async def quiz_attempts(self, uid: int, qid: str) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) c FROM quiz_attempts WHERE user_id=? AND quest_id=?", (uid, qid))
        return (await cur.fetchone())["c"]

    async def log_quiz(self, uid: int, qid: str, score: int, total: int, passed: bool) -> None:
        await self.conn.execute(
            "INSERT INTO quiz_attempts(user_id, quest_id, score, total, passed) VALUES (?,?,?,?,?)",
            (uid, qid, score, total, int(passed)))
        await self.conn.commit()

    # ---------- submissions ----------
    async def create_submission(self, uid: int, qid: str, payload: dict, route: str) -> int:
        cur = await self.conn.execute(
            "INSERT INTO submissions(user_id, quest_id, payload, route) VALUES (?,?,?,?)",
            (uid, qid, json.dumps(payload), route))
        await self.conn.commit()
        return cur.lastrowid

    async def submission(self, sid: int) -> aiosqlite.Row | None:
        cur = await self.conn.execute("SELECT * FROM submissions WHERE id=?", (sid,))
        return await cur.fetchone()

    async def last_fail_at(self, uid: int, qid: str) -> dt.datetime | None:
        cur = await self.conn.execute(
            "SELECT decided_at FROM submissions WHERE user_id=? AND quest_id=? AND status='fail' "
            "ORDER BY decided_at DESC LIMIT 1", (uid, qid))
        row = await cur.fetchone()
        return dt.datetime.fromisoformat(row["decided_at"]) if row and row["decided_at"] else None

    async def decide(self, sid: int, status: str, reviewer_id: int | None, notes: str | None) -> None:
        await self.conn.execute(
            "UPDATE submissions SET status=?, reviewer_id=?, notes=?, decided_at=datetime('now') WHERE id=?",
            (status, reviewer_id, notes, sid))
        await self.conn.commit()

    async def add_review_action(self, sid: int, reviewer: int, verdict: str, is_peer: bool, notes: str | None) -> bool:
        try:
            await self.conn.execute(
                "INSERT INTO review_actions(submission_id, reviewer_id, verdict, is_peer, notes) VALUES (?,?,?,?,?)",
                (sid, reviewer, verdict, int(is_peer), notes))
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def peer_approvals(self, sid: int) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) c FROM review_actions WHERE submission_id=? AND is_peer=1 AND verdict='approve'", (sid,))
        return (await cur.fetchone())["c"]

    async def set_public_post(self, sid: int, channel_id: int, message_id: int) -> None:
        await self.conn.execute("UPDATE submissions SET public_channel_id=?, public_message_id=? WHERE id=?",
                                (channel_id, message_id, sid))
        await self.conn.commit()

    async def set_queue_message(self, sid: int, message_id: int) -> None:
        await self.conn.execute("UPDATE submissions SET queue_message_id=? WHERE id=?", (message_id, sid))
        await self.conn.commit()

    # ---------- medals / kv ----------
    async def grant_medal(self, uid: int, key: str) -> bool:
        cur = await self.conn.execute("INSERT OR IGNORE INTO medals(user_id, medal_key) VALUES (?,?)", (uid, key))
        await self.conn.commit()
        return cur.rowcount > 0

    async def medals(self, uid: int) -> list[str]:
        cur = await self.conn.execute("SELECT medal_key FROM medals WHERE user_id=? ORDER BY earned_at", (uid,))
        return [r["medal_key"] for r in await cur.fetchall()]

    async def kv_get(self, uid: int, k: str) -> str | None:
        cur = await self.conn.execute("SELECT v FROM kv WHERE user_id=? AND k=?", (uid, k))
        row = await cur.fetchone()
        return row["v"] if row else None

    async def kv_set(self, uid: int, k: str, v: str) -> None:
        await self.conn.execute("INSERT OR REPLACE INTO kv(user_id, k, v) VALUES (?,?,?)", (uid, k, v))
        await self.conn.commit()

    async def add_fact(self, uid: int, name: str) -> bool:
        """Record something the bot saw. Returns True if it's new."""
        await self.user(uid)
        cur = await self.conn.execute("INSERT OR IGNORE INTO kv(user_id, k, v) VALUES (?,?,datetime('now'))",
                                      (uid, f"fact:{name}"))
        await self.conn.commit()
        return cur.rowcount > 0

    async def facts(self, uid: int) -> set[str]:
        cur = await self.conn.execute("SELECT k FROM kv WHERE user_id=? AND k LIKE 'fact:%'", (uid,))
        return {r["k"][5:] for r in await cur.fetchall()}

    async def touch_streak(self, uid: int) -> int:
        """Call on any quest completion. A day counts once and a gap of more than one day resets the streak."""
        u = await self.user(uid)
        today = dt.date.today()
        last = dt.date.fromisoformat(u["last_active_day"]) if u["last_active_day"] else None
        if last == today:
            return u["streak_days"]
        streak = u["streak_days"] + 1 if (last == today - dt.timedelta(days=1) or u["on_leave"]) else 1
        await self.set_user(uid, streak_days=streak, last_active_day=today.isoformat())
        return streak
