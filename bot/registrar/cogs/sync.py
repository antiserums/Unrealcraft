"""Picks up things that happened on the website (the API writes an `events` row) and mirrors them into Discord:
promotion checks, orientation auto-completion and page refresh. Polls the shared SQLite file."""
from __future__ import annotations

import json
import logging

import aiosqlite
from discord.ext import commands, tasks

log = logging.getLogger("registrar.sync")

EVENTS_SQL = """CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, member_id INTEGER NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT (datetime('now')), delivered INTEGER NOT NULL DEFAULT 0)"""


class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll.start()

    def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(seconds=20)
    async def poll(self):
        conn = self.bot.db.conn
        try:
            await conn.execute(EVENTS_SQL)
            cur = await conn.execute("SELECT id, type, member_id, payload FROM events WHERE delivered=0 ORDER BY id LIMIT 50")
            rows = await cur.fetchall()
        except aiosqlite.Error as e:
            log.warning("events poll failed: %s", e)
            return
        guild = self.bot.get_guild(self.bot.settings.guild_id or 0)
        for r in rows:
            try:
                await self.handle(guild, r["type"], r["member_id"], json.loads(r["payload"] or "{}"))
            except Exception:                              # one bad event must not stop the rest
                log.exception("event %s failed", r["id"])
            await conn.execute("UPDATE events SET delivered=1 WHERE id=?", (r["id"],))
        if rows:
            await conn.commit()

    async def handle(self, guild, type_: str, uid: int, payload: dict) -> None:
        onboarding, ranks, quests = self.bot.get_cog("Onboarding"), self.bot.get_cog("Ranks"), self.bot.get_cog("Quests")
        if type_ == "quiz_passed":
            await onboarding._auto_complete(guild, uid)         # action quests whose checklist is now verified
        elif type_ == "quest_completed":
            await onboarding.maybe_finish_orientation(guild, uid)
            await onboarding.refresh_page(uid)
            if guild:
                await ranks.check_promotion(guild, uid)
        elif type_ in ("submission_created", "submission_accepted") and guild:
            # Mirror a website turn-in: public post in the major forum, and the review/spot-check card for mentors.
            s = await self.bot.db.submission(int(payload["submission"]))
            member = guild.get_member(uid) or await guild.fetch_member(uid)
            if s and member:
                q = self.bot.catalog.quests[s["quest_id"]]
                await quests.post_turnin(guild, member, q, json.loads(s["payload"]), s["route"], s["id"])
                if type_ == "submission_created":
                    await quests.post_to_queue(guild, s["id"])
                elif s["route"] == "honor" and await quests.spot_check_due():
                    await quests.post_to_queue(guild, s["id"], spot=True)
        log.info("website event %s for %s: %s", type_, uid, payload)

    @poll.before_loop
    async def _wait(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Sync(bot))
