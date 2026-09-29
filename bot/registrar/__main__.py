"""Entry point: `python -m registrar` from the bot/ directory."""
from __future__ import annotations

import asyncio
import logging
import sys

import discord
from discord.ext import commands, tasks

from . import release
from .config import BOT_ROOT, Unlocks, load_settings
from .curriculum import Catalog
from .db import DB

COGS = [
    "registrar.cogs.onboarding",
    "registrar.cogs.majors",
    "registrar.cogs.quests",
    "registrar.cogs.quiz",
    "registrar.cogs.ranks",
    "registrar.cogs.setup_server",
    "registrar.cogs.workshop",
]

log = logging.getLogger("quartermaster")


class Quartermaster(commands.Bot):
    def __init__(self, settings):
        intents = discord.Intents.default()
        intents.members = True          # role swaps + first-week DMs (privileged; enable in Dev Portal)
        intents.voice_states = True     # O7
        intents.reactions = True        # O8, showcase 🔥
        # Message Content intent deliberately OFF. The help-desk template uses a modal instead (see onboarding cog).
        super().__init__(command_prefix=commands.when_mentioned, intents=intents,
                         allowed_mentions=discord.AllowedMentions(everyone=False, roles=False))
        self.settings = settings
        self.db = DB(settings.db_path)
        self.unlocks = Unlocks(settings.unlocks_path)
        self.catalog = Catalog.load(settings.curriculum_dir)
        self.release = release.latest(BOT_ROOT.parent / "CHANGELOG.md")
        self.changelog_errors = release.validate(BOT_ROOT.parent / "CHANGELOG.md")

    async def setup_hook(self) -> None:
        errs, warns = self.catalog.validate()
        for w in warns:
            log.debug("curriculum warning: %s", w)
        if errs:
            for e in errs:
                log.error("curriculum: %s", e)
            raise SystemExit("Curriculum invalid; fix the errors above.")
        log.info("Loaded %d quests (%d warnings)", len(self.catalog.quests), len(warns))
        await self.db.open()
        for ext in COGS:
            await self.load_extension(ext)
        if self.settings.guild_id:
            guild = discord.Object(id=self.settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            try:
                synced = await self.tree.sync(guild=guild)
                log.info("Synced %d slash commands to guild %s", len(synced), self.settings.guild_id)
            except discord.Forbidden:
                log.error("Bot is not in guild %s yet (or lacks applications.commands). Invite it; commands sync automatically on join.",
                          self.settings.guild_id)
        else:
            await self.tree.sync()

    async def on_guild_join(self, g: discord.Guild) -> None:
        log.info("Joined guild %s (%s)", g.name, g.id)
        if g.id == self.settings.guild_id:
            synced = await self.tree.sync(guild=g)
            log.info("Synced %d slash commands", len(synced))
            await self.on_ready()

    async def on_ready(self) -> None:
        log.info("Online as %s in %d guild(s) · %s", self.user, len(self.guilds),
                 self.release.get("version", "no CHANGELOG"))
        g = self.get_guild(self.settings.guild_id or 0)
        for err in self.changelog_errors:
            log.error("CHANGELOG: %s (patch notes not posted until fixed)", err)
        if not self.watch_releases.is_running():
            self.watch_releases.start()

    @tasks.loop(minutes=1)
    async def watch_releases(self) -> None:
        """Post patch notes for any version tag that has been pushed to GitHub since the last check."""
        g = self.get_guild(self.settings.guild_id or 0)
        self.changelog_errors = release.validate(BOT_ROOT.parent / "CHANGELOG.md")
        self.release = release.latest(BOT_ROOT.parent / "CHANGELOG.md") or self.release
        if not g or self.changelog_errors:
            return
        posted = await self.get_cog("SetupServer").post_patch_notes(g)
        if posted:
            log.info("patch notes posted: %s", ", ".join(posted))
        if self.run_bootstrap and not getattr(self, "_bootstrapped", False):
            g = self.get_guild(self.settings.guild_id or 0)
            if not g:
                log.warning("--bootstrap: waiting for the bot to be invited to guild %s", self.settings.guild_id)
                return
            self._bootstrapped = True
            cog = self.get_cog("SetupServer")
            for line in await cog.bootstrap(g):
                log.info("bootstrap: %s", line)
            log.info("bootstrap: pins %s", await cog.sync_pins(g))
            log.info("bootstrap: %s", await cog.cleanup_bot_posts(g))

    async def close(self) -> None:
        await self.db.close()
        await super().close()


def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not settings.token:
        raise SystemExit("DISCORD_TOKEN missing. Copy .env.example to .env.")
    bot = Quartermaster(settings)
    bot.run_bootstrap = "--bootstrap" in sys.argv
    asyncio.run(bot.start(settings.token))


if __name__ == "__main__":
    main()
