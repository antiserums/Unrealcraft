"""Discord roles follow the website.

The site is where the game is played: quests, boss fights, turn-ins, reviews, ranks. This cog only mirrors the
result into Discord so the guild hall shows who is who:
  - one rank role (Novice … Lead), swapped, never stacked
  - one role per chosen specialization (the primary and every extra)
  - a card in #rank-ups when the site promotes someone
It reads the shared SQLite file and the `events` rows the API writes. It never grants XP, ranks or quests.
"""
from __future__ import annotations

import json
import logging

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

log = logging.getLogger("quartermaster.roles")

EVENTS_SQL = """CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, member_id INTEGER NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT (datetime('now')), delivered INTEGER NOT NULL DEFAULT 0)"""
LEGACY_ROLE_KEYS = [("oriented",), ("recruit",), ("major", "undecided")]     # gates from when Discord was the game


def nameplate(cat, rank: int, primary: str) -> str:
    """Rank title; from Expert up the primary specialization joins it: 'Expert · Level Design'."""
    title = cat.ranks.get(max(rank, 0), {}).get("title", f"Rank {rank}")
    if 3 <= rank < 6 and primary and primary != "undecided":
        return f"{title} · {cat.title_of(primary)}"
    return title


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll.start()

    def cog_unload(self):
        self.poll.cancel()

    # ------------------------------------------------------------------ state from the site's database
    async def member_state(self, uid: int) -> dict | None:
        """What the site knows about a member, or None if they never logged in there. Never creates a row."""
        conn = self.bot.db.conn
        cur = await conn.execute("SELECT rank, major, xp FROM users WHERE discord_id=?", (uid,))
        row = await cur.fetchone()
        if not row:
            return None
        try:
            extras = [e for e in json.loads(await self.bot.db.kv_get(uid, "web.specializations") or "[]") if isinstance(e, str)]
        except ValueError:
            extras = []
        cur = await conn.execute("SELECT COUNT(*) FROM quest_progress WHERE user_id=? AND status='done'", (uid,))
        done = (await cur.fetchone())[0]
        primary = row["major"] or "undecided"
        specs = ([primary] if primary != "undecided" else []) + [e for e in extras if e != primary]
        return {"rank": row["rank"], "primary": primary, "specializations": specs, "xp": row["xp"], "done": done}

    # ------------------------------------------------------------------ roles
    def _role(self, guild: discord.Guild, *keys) -> discord.Role | None:
        rid = self.bot.unlocks.role(*keys)
        return guild.get_role(rid) if rid else None

    def managed(self, guild: discord.Guild) -> set[discord.Role]:
        """Every role this cog owns: rank roles, specialization roles, and the old gate roles it now removes."""
        unl = self.bot.unlocks
        ids = set(unl.all_rank_roles())
        ids |= {int(v or 0) for v in (unl.data.get("roles", {}).get("specialization") or {}).values()}
        ids |= {unl.role(*k) for k in LEGACY_ROLE_KEYS}
        return {r for i in ids if i and (r := guild.get_role(i))}

    def desired(self, guild: discord.Guild, st: dict) -> set[discord.Role]:
        want = set()
        if st["rank"] >= 0 and (r := self._role(guild, "rank", st["rank"])):
            want.add(r)
        for key in st["specializations"]:
            if (r := self._role(guild, "specialization", key)):
                want.add(r)
        return want

    async def apply(self, guild: discord.Guild, uid: int) -> bool:
        """Make the member's Discord roles match the site. True if anything changed."""
        st = await self.member_state(uid)
        if not st:
            return False
        member = guild.get_member(uid)
        if not member:
            try:
                member = await guild.fetch_member(uid)
            except discord.HTTPException:
                return False                          # logged in on the site but not (or no longer) on the server
        want, mine = self.desired(guild, st), self.managed(guild)
        add = [r for r in want if r not in member.roles]
        remove = [r for r in member.roles if r in mine and r not in want]
        try:
            if remove:
                await member.remove_roles(*remove, reason="Unrealcraft: roles follow the site")
            if add:
                await member.add_roles(*add, reason="Unrealcraft: roles follow the site")
        except discord.Forbidden:
            log.error("Missing permissions to edit roles. Drag the Quartermaster role above the rank and specialization roles.")
            return False
        return bool(add or remove)

    async def sync_all(self, guild: discord.Guild) -> int:
        cur = await self.bot.db.conn.execute("SELECT discord_id FROM users")
        changed = 0
        for row in await cur.fetchall():
            if guild.get_member(row["discord_id"]) and await self.apply(guild, row["discord_id"]):
                changed += 1
        return changed

    # ------------------------------------------------------------------ rank-up announcement
    async def announce(self, guild: discord.Guild, uid: int, old: int, new: int) -> None:
        ch = guild.get_channel(self.bot.unlocks.channel("rank_ups"))
        member = guild.get_member(uid)
        st = await self.member_state(uid)
        if not ch or not member or not st or new < 1:        # everyone starts as Novice; only real rank-ups are announced
            return
        cat = self.bot.catalog
        color = discord.Color.from_str(cat.ranks.get(new, {}).get("color") or "#7A8C7E")
        e = discord.Embed(description=f"~~{nameplate(cat, old, st['primary'])}~~ → **{nameplate(cat, new, st['primary'])}**", color=color)
        e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        if st["specializations"]:
            e.add_field(name="Specializations", value=" · ".join(cat.title_of(s) for s in st["specializations"]))
        e.add_field(name="Quests done", value=str(st["done"]))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Player card", url=f"{self.bot.settings.site_url}/members/{uid}"))
        await ch.send(embed=e, view=view)

    # ------------------------------------------------------------------ events from the site
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
        if not guild:
            return                                     # keep the events until the bot is in the server
        for r in rows:
            try:
                await self.handle(guild, r["type"], r["member_id"], json.loads(r["payload"] or "{}"))
            except Exception:                          # one bad event must not stop the rest
                log.exception("event %s failed", r["id"])
            await conn.execute("UPDATE events SET delivered=1 WHERE id=?", (r["id"],))
        if rows:
            await conn.commit()

    async def handle(self, guild: discord.Guild, type_: str, uid: int, payload: dict) -> None:
        """Only rank and specialization changes matter here. Everything else the site does stays on the site."""
        if type_ == "rank_up":
            await self.apply(guild, uid)
            await self.announce(guild, uid, int(payload.get("old", -1)), int(payload["rank"]))
        elif type_ in ("rank_set", "specialization_set"):
            await self.apply(guild, uid)
        else:
            return
        log.info("site event %s for %s: %s", type_, uid, payload)

    @poll.before_loop
    async def _wait(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id == self.bot.settings.guild_id:
            await self.apply(member.guild, member.id)      # someone who played before and came back

    # ------------------------------------------------------------------ commands
    @app_commands.command(name="site", description="Where the game is played: quests, boss fights, your player card.")
    async def site(self, itx: discord.Interaction):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open Unrealcraft", url=self.bot.settings.site_url))
        await itx.response.send_message("Quests, boss fights, turn-ins and reviews all happen on the site. "
                                        "This server is for talking and showing your progress.", view=view, ephemeral=True)

    @app_commands.command(name="card", description="A member's rank and specializations, with a link to their player card.")
    async def card(self, itx: discord.Interaction, member: discord.Member | None = None):
        member = member or itx.user
        st = await self.member_state(member.id)
        if not st:
            await itx.response.send_message(f"{member.display_name} has not logged in on the site yet.", ephemeral=True)
            return
        cat = self.bot.catalog
        e = discord.Embed(title=nameplate(cat, st["rank"], st["primary"]),
                          color=discord.Color.from_str(cat.ranks.get(max(st["rank"], 0), {}).get("color") or "#7A8C7E"))
        e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        e.add_field(name="Specializations", value=" · ".join(cat.title_of(s) for s in st["specializations"]) or "Undecided", inline=False)
        e.add_field(name="XP", value=str(st["xp"]))
        e.add_field(name="Quests done", value=str(st["done"]))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Player card", url=f"{self.bot.settings.site_url}/members/{member.id}"))
        await itx.response.send_message(embed=e, view=view)


async def setup(bot):
    await bot.add_cog(Roles(bot))
