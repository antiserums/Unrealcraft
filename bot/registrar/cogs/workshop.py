"""Workshop forums: a 'New post' dialog (button on each forum's pinned intro, or /post)."""
from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("quartermaster.workshop")

TRACKS = ["foundations", "world-lighting", "materials", "blueprint", "characters-anim"]
TYPES = [("WIP", "Work in progress: show where you are", "🛠️"),
         ("Help", "Stuck: ask a specific question", "🆘"),
         ("Done", "Finished something: show it off", "✅")]


class Workshop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def forum(self, guild: discord.Guild, slug: str) -> discord.ForumChannel | None:
        ch = guild.get_channel(self.bot.unlocks.channel("tracks", slug))
        return ch if isinstance(ch, discord.ForumChannel) else None

    def open_tracks(self, member: discord.Member) -> list[str]:
        """Workshop forums this member can actually see (rank-gated by Discord permissions)."""
        return [s for s in TRACKS if (f := self.forum(member.guild, s)) and f.permissions_for(member).view_channel]

    async def open_dialog(self, itx: discord.Interaction, slug: str) -> None:
        member = itx.guild.get_member(itx.user.id)
        forum = self.forum(itx.guild, slug)
        if not forum or not member or not forum.permissions_for(member).view_channel:
            await itx.response.send_message(f"#{slug} isn't open for you yet. `/path` shows when it opens.",
                                            ephemeral=True)
            return
        u = await self.bot.db.user(itx.user.id)
        quests = [q for q in self.bot.catalog.sorted(self.bot.catalog.quests.values())
                  if q.track == slug and 0 <= q.rank <= max(u["rank"], 0)]
        await itx.response.send_modal(PostModal(self, slug, quests[:24], u["ue_version"]))

    async def publish(self, itx: discord.Interaction, slug: str, title: str, kind: str, qid: str | None,
                      details: str, files: list[discord.Attachment]) -> None:
        forum = self.forum(itx.guild, slug)
        tag = discord.utils.get(forum.available_tags, name=kind)
        q = self.bot.catalog.quests.get(qid) if qid else None
        name = (f"[{q.id}] " if q else "") + title
        head = f"**{kind}** by {itx.user.mention}" + (f" · quest **{q.id} · {q.raw['title']}**" if q else "")
        await itx.response.defer(ephemeral=True, thinking=True)
        uploads = []
        for a in files[:4]:
            try:
                uploads.append(await a.to_file())
            except discord.HTTPException:
                pass
        created = await forum.create_thread(name=name[:100], content=f"{head}\n\n{details}"[:2000], files=uploads,
                                            applied_tags=[tag] if tag else [],
                                            allowed_mentions=discord.AllowedMentions.none())
        try:
            await created.thread.add_user(itx.user)      # so they get reply notifications
        except discord.HTTPException:
            pass
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, f"post.{slug.replace('-', '_')}")
        await itx.followup.send(f"Posted: {created.thread.mention}", ephemeral=True)

    # ------------------------------------------------------------ /post
    async def _track_ac(self, itx: discord.Interaction, current: str):
        member = itx.guild.get_member(itx.user.id)
        return [app_commands.Choice(name=f"#{s}", value=s) for s in self.open_tracks(member)
                if current.lower() in s][:25]

    @app_commands.command(name="post", description="Start a post in a Workshop forum (WIP, help, or done).")
    @app_commands.autocomplete(forum=_track_ac)
    async def post(self, itx: discord.Interaction, forum: str | None = None):
        slug = forum
        if not slug:                                   # inside a workshop forum/thread → use that one
            parent = getattr(itx.channel, "parent_id", None) or getattr(itx.channel, "id", None)
            slug = next((s for s in TRACKS if self.bot.unlocks.channel("tracks", s) == parent), None)
        if not slug:
            member = itx.guild.get_member(itx.user.id)
            opened = self.open_tracks(member)
            slug = opened[-1] if opened else None      # default: the newest forum they've unlocked
        if not slug:
            await itx.response.send_message("No Workshop forum is open for you yet. Finish Orientation first.",
                                            ephemeral=True)
            return
        await self.open_dialog(itx, slug)


class PostModal(discord.ui.Modal):
    def __init__(self, cog: Workshop, slug: str, quests, ue_version: str | None):
        super().__init__(title=f"New post in #{slug}"[:45])
        self.cog, self.slug = cog, slug
        self.title_in = discord.ui.TextInput(max_length=90, placeholder="e.g. My courtyard's third route feels dead")
        self.add_item(discord.ui.Label(text="Title", component=self.title_in))
        self.kind = discord.ui.Select(options=[discord.SelectOption(label=l, description=d, emoji=e, default=(l == "WIP"))
                                               for l, d, e in TYPES], min_values=1, max_values=1)
        self.add_item(discord.ui.Label(text="Type", component=self.kind))
        self.quest = None
        if quests:
            opts = [discord.SelectOption(label="Not tied to a quest", value="-")]
            opts += [discord.SelectOption(label=f"{q.id} · {q.raw['title']}"[:100], value=q.id) for q in quests]
            self.quest = discord.ui.Select(options=opts, min_values=0, max_values=1, required=False)
            self.add_item(discord.ui.Label(text="Quest", description="Optional", component=self.quest))
        self.details = discord.ui.TextInput(
            style=discord.TextStyle.paragraph, max_length=1800,
            default=f"Engine: {ue_version or '5.'}\n\n",
            placeholder="What you're making, what you tried, what you want feedback on.")
        self.add_item(discord.ui.Label(text="Details", description="Keep the engine version line",
                                       component=self.details))
        self.upload = discord.ui.FileUpload(required=False, max_values=4)
        self.add_item(discord.ui.Label(text="Screenshot or clip", description="Optional, up to 4 files",
                                       component=self.upload))

    async def on_submit(self, itx: discord.Interaction):
        qid = (self.quest.values[0] if self.quest and self.quest.values else None)
        qid = None if qid in (None, "-") else qid
        await self.cog.publish(itx, self.slug, str(self.title_in.value), self.kind.values[0], qid,
                               str(self.details.value), list(self.upload.values or []))


class NewPostButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:newpost:(?P<slug>[\w-]+)"):
    """On each Workshop forum's pinned intro."""

    def __init__(self, slug: str):
        super().__init__(discord.ui.Button(label="New post", emoji="📝", style=discord.ButtonStyle.primary,
                                           custom_id=f"uc:newpost:{slug}"))
        self.slug = slug

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(match["slug"])

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Workshop").open_dialog(itx, self.slug)


async def setup(bot):
    bot.add_dynamic_items(NewPostButton)
    await bot.add_cog(Workshop(bot))
