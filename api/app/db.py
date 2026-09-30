"""Read access to the shared SQLite file (the bot still writes it until phase 2)."""
from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from registrar.curriculum import UserState  # noqa: E402  (bot package, see config.py)


class DB:
    def __init__(self, path: Path):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode = WAL")

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def user(self, uid: int) -> dict | None:
        cur = await self.conn.execute("SELECT * FROM users WHERE discord_id = ?", (uid,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def progress(self, uid: int) -> dict[str, dict]:
        cur = await self.conn.execute(
            "SELECT quest_id, status, quiz_passed, completed_at FROM quest_progress WHERE user_id=?", (uid,))
        return {r["quest_id"]: dict(r) for r in await cur.fetchall()}

    async def kv_get(self, uid: int, k: str) -> str | None:
        cur = await self.conn.execute("SELECT v FROM kv WHERE user_id=? AND k=?", (uid, k))
        row = await cur.fetchone()
        return row["v"] if row else None

    async def facts(self, uid: int) -> set[str]:
        cur = await self.conn.execute("SELECT k FROM kv WHERE user_id=? AND k LIKE 'fact:%'", (uid,))
        return {r["k"][5:] for r in await cur.fetchall()}

    async def medals(self, uid: int) -> list[dict]:
        cur = await self.conn.execute("SELECT medal_key, earned_at FROM medals WHERE user_id=? ORDER BY earned_at", (uid,))
        return [dict(r) for r in await cur.fetchall()]

    async def xp_recent(self, uid: int, limit: int = 20) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT amount, reason, created_at FROM xp_log WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
        return [dict(r) for r in await cur.fetchall()]

    async def quiz_attempts(self, uid: int, qid: str) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT score, total, passed, created_at FROM quiz_attempts WHERE user_id=? AND quest_id=? ORDER BY id",
            (uid, qid))
        return [dict(r) for r in await cur.fetchall()]

    async def submissions(self, uid: int, qid: str | None = None) -> list[dict]:
        sql = "SELECT id, quest_id, payload, status, route, notes, created_at, decided_at FROM submissions WHERE user_id=?"
        args: list = [uid]
        if qid:
            sql += " AND quest_id=?"
            args.append(qid)
        cur = await self.conn.execute(sql + " ORDER BY id DESC", args)
        out = []
        for r in await cur.fetchall():
            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload"] or "{}")
            except ValueError:
                d["payload"] = {"text": d["payload"]}
            out.append(d)
        return out

    async def leaderboard(self, days: int | None, limit: int = 50) -> list[dict]:
        if days:
            cur = await self.conn.execute(
                "SELECT u.discord_id, u.major, u.rank, COALESCE(SUM(x.amount),0) xp "
                "FROM users u JOIN xp_log x ON x.user_id=u.discord_id "
                "WHERE x.created_at >= datetime('now', ?) GROUP BY u.discord_id ORDER BY xp DESC LIMIT ?",
                (f"-{days} days", limit))
        else:
            cur = await self.conn.execute(
                "SELECT discord_id, major, rank, xp FROM users ORDER BY xp DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]

    async def user_state(self, uid: int) -> tuple[dict, UserState, dict[str, dict]]:
        """(users row or a blank one, UserState for the rules engine, progress rows)."""
        u = await self.user(uid) or {"discord_id": uid, "major": "undecided", "rank": -1, "xp": 0,
                                     "streak_days": 0, "ue_version": None, "tasters_json": "[]", "minor": None,
                                     "rank_since": None, "created_at": None}
        prog = await self.progress(uid)
        prof = json.loads(await self.kv_get(uid, "profile") or "{}")
        try:                                             # extra specializations chosen on the site (the primary is users.major)
            extras = [s for s in json.loads(await self.kv_get(uid, "web.specializations") or "[]") if isinstance(s, str)]
        except ValueError:
            extras = []
        state = UserState(u["major"], u["rank"],
                          {q for q, p in prog.items() if p["status"] == "done"},
                          {q for q, p in prog.items() if p["status"] == "skipped"},
                          json.loads(u.get("tasters_json") or "[]"), prof, extras=[e for e in extras if e != u["major"]])
        return u, state, prog
