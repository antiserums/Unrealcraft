"""Tables the API owns (characters, gear, fights, events) plus the quest-completion path the fight needs."""
from __future__ import annotations

import datetime as dt
import json

import aiosqlite

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
CREATE TABLE IF NOT EXISTS admin_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id    INTEGER NOT NULL,
    action      TEXT NOT NULL,                 -- grant_quest | clear_quest | set_rank | add_xp | medal | reset ...
    target_id   INTEGER,
    detail      TEXT NOT NULL DEFAULT '{}',    -- json
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
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
CREATE TABLE IF NOT EXISTS entitlements (          -- admin-added or admin-edited unlockables; see entitlements.py
    kind        TEXT NOT NULL,                     -- outfit | nameplate | avatar_frame | card_frame | title | achievement
    id          TEXT NOT NULL,
    name        TEXT NOT NULL,
    desc        TEXT NOT NULL DEFAULT '',
    data        TEXT NOT NULL DEFAULT '{}',        -- json, kind-specific (colour value, art id, achievement condition)
    unlock      TEXT NOT NULL DEFAULT '{"type":"starter"}',
    sort        INTEGER NOT NULL DEFAULT 100,
    enabled     INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (kind, id)
);
CREATE TABLE IF NOT EXISTS entitlement_grants (    -- one member handed one entitlement by staff
    member_id   INTEGER NOT NULL,
    kind        TEXT NOT NULL,
    id          TEXT NOT NULL,
    granted_by  INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (member_id, kind, id)
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

    # ---------- small per-member values (the bot's kv table) ----------
    async def kv_set(self, uid: int, k: str, v: str) -> None:
        await self.conn.execute("INSERT OR REPLACE INTO kv(user_id, k, v) VALUES (?,?,?)", (uid, k, v))
        await self.conn.commit()

    async def kv_get(self, uid: int, k: str) -> str | None:
        cur = await self.conn.execute("SELECT v FROM kv WHERE user_id=? AND k=?", (uid, k))
        row = await cur.fetchone()
        return row["v"] if row else None

    # ---------- reviews (the bot's submissions / review_actions tables) ----------
    async def submission(self, sid: int) -> dict | None:
        cur = await self.conn.execute("SELECT * FROM submissions WHERE id=?", (sid,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def pending_submissions(self, limit: int = 100) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT s.*, u.rank AS member_rank, u.major AS member_major FROM submissions s "
            "LEFT JOIN users u ON u.discord_id = s.user_id WHERE s.status='pending' ORDER BY s.id LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]

    async def decided_submissions(self, limit: int = 50) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT s.*, u.rank AS member_rank, u.major AS member_major FROM submissions s "
            "LEFT JOIN users u ON u.discord_id = s.user_id WHERE s.status!='pending' ORDER BY s.decided_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]

    async def review_actions(self, sid: int) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT reviewer_id, verdict, is_peer, notes, created_at FROM review_actions WHERE submission_id=? ORDER BY id", (sid,))
        return [dict(r) for r in await cur.fetchall()]

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

    async def decide(self, sid: int, status: str, reviewer_id: int | None, notes: str | None) -> None:
        await self.conn.execute(
            "UPDATE submissions SET status=?, reviewer_id=?, notes=?, decided_at=datetime('now') WHERE id=?",
            (status, reviewer_id, notes, sid))
        await self.conn.commit()

    async def xp_count_today(self, uid: int, reason_prefix: str) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) c FROM xp_log WHERE user_id=? AND reason LIKE ? AND date(created_at)=date('now')",
            (uid, reason_prefix + "%"))
        return (await cur.fetchone())["c"]

    # ---------- admin panel ----------
    async def admin_log(self, admin_id: int, action: str, target_id: int | None, detail: dict) -> None:
        await self.conn.execute("INSERT INTO admin_log(admin_id, action, target_id, detail) VALUES (?,?,?,?)",
                                (admin_id, action, target_id, json.dumps(detail)))
        await self.conn.commit()

    async def admin_log_tail(self, limit: int = 50) -> list[dict]:
        cur = await self.conn.execute("SELECT * FROM admin_log ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]

    async def search_members(self, q: str, limit: int = 40) -> list[dict]:
        """Members by id prefix or by the display name saved at login. Empty query -> most recently created."""
        sql = ("SELECT u.discord_id, u.major, u.rank, u.xp, u.streak_days, u.created_at, u.rank_since, "
               "(SELECT v FROM kv k WHERE k.user_id=u.discord_id AND k.k='web.name') AS name, "
               "(SELECT v FROM kv k WHERE k.user_id=u.discord_id AND k.k='web.avatar') AS avatar, "
               "(SELECT COUNT(*) FROM quest_progress p WHERE p.user_id=u.discord_id AND p.status='done') AS done "
               "FROM users u ")
        args: list = []
        if q.strip():
            sql += "WHERE CAST(u.discord_id AS TEXT) LIKE ? OR name LIKE ? "
            args += [q.strip() + "%", "%" + q.strip() + "%"]
        cur = await self.conn.execute(sql + "ORDER BY u.created_at DESC LIMIT ?", (*args, limit))
        return [dict(r) for r in await cur.fetchall()]

    async def progress_rows(self, uid: int) -> list[dict]:
        cur = await self.conn.execute("SELECT quest_id, status, quiz_passed, completed_at FROM quest_progress WHERE user_id=? ORDER BY completed_at DESC, quest_id", (uid,))
        return [dict(r) for r in await cur.fetchall()]

    async def clear_progress(self, uid: int, qid: str) -> None:
        await self.conn.execute("DELETE FROM quest_progress WHERE user_id=? AND quest_id=?", (uid, qid))
        await self.conn.commit()

    async def set_user(self, uid: int, **fields) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        await self.conn.execute(f"UPDATE users SET {cols} WHERE discord_id = ?", (*fields.values(), uid))
        await self.conn.commit()

    async def remove_medal(self, uid: int, key: str) -> None:
        await self.conn.execute("DELETE FROM medals WHERE user_id=? AND medal_key=?", (uid, key))
        await self.conn.commit()

    async def reset_member(self, uid: int, keep_user: bool = True) -> dict:
        """Wipe everything a member did. With keep_user the users row stays (rank -1, 0 XP) so the bot's roles still map."""
        counts = {}
        for table, col in (("quest_progress", "user_id"), ("quiz_attempts", "user_id"), ("xp_log", "user_id"), ("medals", "user_id"),
                           ("submissions", "user_id"), ("outfits", "member_id"), ("fights", "member_id"), ("characters", "member_id"),
                           ("events", "member_id"), ("kv", "user_id"), ("entitlement_grants", "member_id")):
            cur = await self.conn.execute(f"DELETE FROM {table} WHERE {col}=?", (uid,))
            counts[table] = cur.rowcount
        await self.conn.execute("DELETE FROM review_actions WHERE reviewer_id=? OR submission_id NOT IN (SELECT id FROM submissions)", (uid,))
        if keep_user:
            await self.conn.execute("UPDATE users SET xp=0, rank=-1, current_quest_id=NULL, spine_done=0, streak_days=0, "
                                    "last_active_day=NULL, rank_since=datetime('now') WHERE discord_id=?", (uid,))
        else:
            cur = await self.conn.execute("DELETE FROM users WHERE discord_id=?", (uid,))
            counts["users"] = cur.rowcount
        await self.conn.commit()
        return counts

    # ---------- entitlements (admin catalog + direct grants) ----------
    async def entitlement_rows(self) -> list[dict]:
        cur = await self.conn.execute("SELECT * FROM entitlements ORDER BY kind, sort, id")
        return [dict(r) for r in await cur.fetchall()]

    async def entitlement_save(self, kind: str, eid: str, name: str, desc: str, data: dict, unlock: dict, sort: int, enabled: bool) -> None:
        await self.conn.execute(
            "INSERT INTO entitlements(kind, id, name, desc, data, unlock, sort, enabled, updated_at) VALUES (?,?,?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(kind, id) DO UPDATE SET name=excluded.name, desc=excluded.desc, data=excluded.data, unlock=excluded.unlock, "
            "sort=excluded.sort, enabled=excluded.enabled, updated_at=datetime('now')",
            (kind, eid, name, desc, json.dumps(data), json.dumps(unlock), sort, int(enabled)))
        await self.conn.commit()

    async def entitlement_delete(self, kind: str, eid: str) -> int:
        cur = await self.conn.execute("DELETE FROM entitlements WHERE kind=? AND id=?", (kind, eid))
        await self.conn.commit()
        return cur.rowcount

    async def grants(self, uid: int) -> dict[tuple[str, str], dict]:
        cur = await self.conn.execute("SELECT kind, id, granted_by, created_at FROM entitlement_grants WHERE member_id=?", (uid,))
        return {(r["kind"], r["id"]): dict(r) for r in await cur.fetchall()}

    async def grant(self, uid: int, kind: str, eid: str, by: int | None) -> bool:
        cur = await self.conn.execute("INSERT OR IGNORE INTO entitlement_grants(member_id, kind, id, granted_by) VALUES (?,?,?,?)", (uid, kind, eid, by))
        await self.conn.commit()
        return cur.rowcount > 0

    async def revoke(self, uid: int, kind: str, eid: str) -> int:
        cur = await self.conn.execute("DELETE FROM entitlement_grants WHERE member_id=? AND kind=? AND id=?", (uid, kind, eid))
        await self.conn.commit()
        return cur.rowcount

    async def events_tail(self, limit: int = 50) -> list[dict]:
        cur = await self.conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]

    async def stats(self) -> dict:
        async def one(sql):
            cur = await self.conn.execute(sql)
            return (await cur.fetchone())[0]
        return {
            "members": await one("SELECT COUNT(*) FROM users"),
            "members_logged_in": await one("SELECT COUNT(*) FROM kv WHERE k='web.name'"),
            "quests_done": await one("SELECT COUNT(*) FROM quest_progress WHERE status='done'"),
            "pending_reviews": await one("SELECT COUNT(*) FROM submissions WHERE status='pending'"),
            "fights_today": await one("SELECT COUNT(*) FROM fights WHERE date(started_at)=date('now')"),
            "fights_total": await one("SELECT COUNT(*) FROM fights"),
            "events_undelivered": await one("SELECT COUNT(*) FROM events WHERE delivered=0"),
            "xp_total": await one("SELECT COALESCE(SUM(amount),0) FROM xp_log"),
        }

    # ---------- home page statistics ----------
    async def member_stats(self, uid: int) -> dict:
        async def one(sql, *a):
            cur = await self.conn.execute(sql, a)
            return (await cur.fetchone())[0] or 0
        return {
            "fights": await one("SELECT COUNT(*) FROM fights WHERE member_id=? AND result IS NOT NULL", uid),
            "fights_won": await one("SELECT COUNT(*) FROM fights WHERE member_id=? AND result='win'", uid),
            "bosses_first_try": await one(
                "SELECT COUNT(*) FROM quiz_attempts a WHERE user_id=? AND passed=1 AND NOT EXISTS "
                "(SELECT 1 FROM quiz_attempts b WHERE b.user_id=a.user_id AND b.quest_id=a.quest_id AND b.id<a.id)", uid),
            "crit_xp": await one("SELECT SUM(amount) FROM xp_log WHERE user_id=? AND reason LIKE 'crit:%'", uid),
            "xp_week": max(0, await one("SELECT SUM(amount) FROM xp_log WHERE user_id=? AND created_at >= datetime('now','-7 days')", uid)),
            "reads": await one("SELECT COUNT(*) FROM kv WHERE user_id=? AND k LIKE 'read:%'", uid),
            "turnins": await one("SELECT COUNT(*) FROM submissions WHERE user_id=?", uid),
            "turnins_passed": await one("SELECT COUNT(*) FROM submissions WHERE user_id=? AND status='pass'", uid),
            "turnins_pending": await one("SELECT COUNT(*) FROM submissions WHERE user_id=? AND status='pending'", uid),
        }

    async def guild_stats(self) -> dict:
        async def one(sql):
            cur = await self.conn.execute(sql)
            return (await cur.fetchone())[0] or 0
        return {
            "members": await one("SELECT COUNT(*) FROM users"),
            "quests_done": await one("SELECT COUNT(*) FROM quest_progress WHERE status='done'"),
            "quests_done_week": await one("SELECT COUNT(*) FROM quest_progress WHERE status='done' AND completed_at >= datetime('now','-7 days')"),
            "fights_week": await one("SELECT COUNT(*) FROM fights WHERE started_at >= datetime('now','-7 days')"),
            "xp_week": max(0, await one("SELECT SUM(amount) FROM xp_log WHERE created_at >= datetime('now','-7 days')")),
            "masters": await one("SELECT COUNT(*) FROM users WHERE rank >= 4"),
        }
