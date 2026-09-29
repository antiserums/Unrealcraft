"""/major, /minor, /path, /profile. Handles respec."""
from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands

MAJOR_CHOICES = [
    ("Level Design", "level_design"), ("Environment Art", "lookdev"), ("Tech Art", "tech_art"),
    ("Gameplay Design", "gameplay_design"), ("Animation", "animation"), ("Programming", "programming"),
    ("Cinematics", "cinematics"), ("Undecided", "undecided"),
]
RESPEC_QUESTS_AFTER_R3 = 4


class Majors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def cat(self):
        return self.bot.catalog

    @app_commands.command(name="major", description="Declare or change your major.")
    @app_commands.choices(major=[app_commands.Choice(name=n, value=v) for n, v in MAJOR_CHOICES])
    async def major(self, itx: discord.Interaction, major: app_commands.Choice[str]):
        await itx.response.send_message(await self.set_major(itx, major.value), ephemeral=True)

    async def set_major(self, itx: discord.Interaction, new: str) -> str:
        """Shared by /major and the Orientation dropdown. Returns the reply text."""
        db, unl = self.bot.db, self.bot.unlocks
        name = self.cat.majors.get(new, {}).get("title", new)
        u = await db.user(itx.user.id)
        old = u["major"]
        if new == old and await db.kv_get(itx.user.id, "major_set"):
            return f"You're already {name}."
        if new == "undecided" and u["rank"] >= 2:
            return "Undecided ends at Rank 2. Pick a major."

        first_pick = old == "undecided" and not await db.kv_get(itx.user.id, "major_set")
        note = ""
        if first_pick or u["rank"] < 0:
            await db.set_user(itx.user.id, major=new)
        elif u["rank"] < 3:
            if u["respec_used"] and old != "undecided":
                return "Your free respec is used. After Rank 3 a change costs 4 quests. Ask a Mod if something went wrong."
            injected = self._missing_tasters(new, u["rank"], await db.done_set(itx.user.id))
            await db.set_user(itx.user.id, major=new, respec_used=1 if old != "undecided" else u["respec_used"],
                              tasters_json=json.dumps(injected))
            note = f"Free respec used. {len(injected)} missing taster(s) added to /quest." if old != "undecided" else ""
        else:
            await db.set_user(itx.user.id, respec_target=new)
            note = (f"Respec started. Finish {RESPEC_QUESTS_AFTER_R3} required {name} quests at Rank "
                    f"{u['rank']} to move your Specialty. Your current Specialty becomes a medal when it does.")

        member = itx.guild.get_member(itx.user.id)
        old_r, new_r = itx.guild.get_role(unl.role("major", old)), itx.guild.get_role(unl.role("major", new))
        try:
            if old_r and old_r in member.roles and old != new:
                await member.remove_roles(old_r)
            if new_r and u["rank"] < 3:
                await member.add_roles(new_r)
        except discord.Forbidden:
            pass
        await db.kv_set(itx.user.id, "major_set", "1")
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.major")
        blurb = self.cat.majors.get(new, {}).get("blurb", "")
        return f"**Major · {name}.** {blurb}\n{note}".strip()

    def _missing_tasters(self, major: str, rank: int, done: set[str]) -> list[str]:
        out = []
        for r in range(1, rank + 1):
            for g in self.cat.taster_groups(major, r):
                if not any(x in done for x in g):
                    out.append(g[0])
        return out

    @app_commands.command(name="minor", description="Optional second focus (Rank 3+). Earns a medal.")
    @app_commands.choices(major=[app_commands.Choice(name=n, value=v) for n, v in MAJOR_CHOICES[:-1]])
    async def minor(self, itx: discord.Interaction, major: app_commands.Choice[str]):
        u = await self.bot.db.user(itx.user.id)
        if u["rank"] < 3:
            await itx.response.send_message("Minors open at Rank 3.", ephemeral=True)
            return
        if major.value == u["major"]:
            await itx.response.send_message("That's your major.", ephemeral=True)
            return
        await self.bot.db.set_user(itx.user.id, minor=major.value)
        await itx.response.send_message(f"Minor · {major.name}. Its quests now show on /path as optional.",
                                        ephemeral=True)

    @app_commands.command(name="path", description="Your personal tree: done / now / locked / optional shelf.")
    async def path(self, itx: discord.Interaction):
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.path")
        await itx.response.send_message(await self.path_text(itx.user.id), ephemeral=True)

    async def path_text(self, uid: int) -> str:
        st = await self.bot.get_cog("Ranks").state(uid)
        text = "\n".join(self.cat.path_lines(st))
        if len(text) > 1900:
            text = text[:1900] + "\n…"
        return f"```\n{text}\n```"

    @app_commands.command(name="profile", description="Show or set your profile.")
    async def profile(self, itx: discord.Interaction, ue_version: str | None = None):
        db = self.bot.db
        if ue_version:
            await db.set_user(itx.user.id, ue_version=ue_version.strip()[:12])
            await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.profile_version")
        u = await db.user(itx.user.id)
        await itx.response.send_message(
            f"Major: {u['major']} · Minor: {u['minor'] or '—'} · Engine: {u['ue_version'] or 'not set'}",
            ephemeral=True)


async def setup(bot):
    await bot.add_cog(Majors(bot))
