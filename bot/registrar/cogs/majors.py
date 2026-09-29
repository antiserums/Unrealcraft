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
        db, unl = self.bot.db, self.bot.unlocks
        u = await db.user(itx.user.id)
        new, old = major.value, u["major"]
        if new == old:
            await itx.response.send_message(f"You're already {major.name}.", ephemeral=True)
            return
        if new == "undecided" and u["rank"] >= 2:
            await itx.response.send_message("Undecided ends at Rank 2. Pick a major.", ephemeral=True)
            return

        first_pick = old == "undecided" and not await db.kv_get(itx.user.id, "major_set")
        note = ""
        if first_pick or u["rank"] < 0:
            await db.set_user(itx.user.id, major=new)
        elif u["rank"] < 3:
            if u["respec_used"] and old != "undecided":
                await itx.response.send_message("Your free respec is used. After Rank 3 a change costs 4 quests. "
                                                "Ask a Mod if something went wrong.", ephemeral=True)
                return
            injected = self._missing_tasters(new, u["rank"], await db.done_set(itx.user.id))
            await db.set_user(itx.user.id, major=new, respec_used=1 if old != "undecided" else u["respec_used"],
                              tasters_json=json.dumps(injected))
            note = f"Free respec used. {len(injected)} missing taster(s) added to /quest." if old != "undecided" else ""
        else:
            await db.set_user(itx.user.id, respec_target=new)
            note = (f"Respec started. Finish {RESPEC_QUESTS_AFTER_R3} required {major.name} quests at Rank "
                    f"{u['rank']} to move your Specialty. Your current Specialty becomes a medal when it does.")

        # swap major role
        member = itx.guild.get_member(itx.user.id)
        old_r, new_r = itx.guild.get_role(unl.role("major", old)), itx.guild.get_role(unl.role("major", new))
        try:
            if old_r and old_r in member.roles:
                await member.remove_roles(old_r)
            if new_r and u["rank"] < 3:
                await member.add_roles(new_r)
        except discord.Forbidden:
            pass
        await db.kv_set(itx.user.id, "major_set", "1")
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.major")
        blurb = self.cat.majors.get(new, {}).get("blurb", "")
        await itx.response.send_message(f"**Major · {major.name}.** {blurb}\n{note}".strip(), ephemeral=True)

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
        st = await self.bot.get_cog("Ranks").state(itx.user.id)
        lines = self.cat.path_lines(st)
        text = "\n".join(lines)
        if len(text) > 1900:
            text = text[:1900] + "\n…"
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.path")
        await itx.response.send_message(f"```\n{text}\n```", ephemeral=True)

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
