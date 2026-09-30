"""/setup bootstrap, sync-pins, sync-roles, patch-notes, reload-curriculum. Builds the guild hall.

The website is where Unrealcraft is played. The Discord server is a guild hall: a place to talk, ask for help and
show progress. So the server is small and open: everyone who accepted the rules can read and post everywhere
except the staff category. Roles show rank and specializations and are handed out by cogs/roles.py.

Idempotent: roles, categories and channels are matched by name and reused if they already exist. It migrates a
server built by the older "Discord is the game" bootstrap: it renames what carries over and removes only its own
leftovers (the quest log, the mentor queue, the gate roles), and only when no member ever posted there.
"""
from __future__ import annotations

import logging
import re

import discord
import yaml
from discord import app_commands
from discord.ext import commands

from .. import profile

log = logging.getLogger("quartermaster.setup")

C = discord.Color.from_str
P = discord.PermissionOverwrite

RANK_ROLES = [(6, "Lead", "#D4AF37", True), (5, "Senior", "#8E6CCF", True), (4, "Master", "#8A9BA8", True),
              (3, "Expert", "#D9824A", False), (2, "Adept", "#3D7DD8", False), (1, "Apprentice", "#B5714B", False),
              (0, "Novice", "#7A8C7E", False)]
MOD_PERMS = discord.Permissions(kick_members=True, moderate_members=True, manage_messages=True,
                                manage_threads=True, view_audit_log=True, manage_nicknames=True)
# Roles from the older design that gated channels or tagged onboarding answers. Nothing uses them any more.
LEGACY_ROLES = ["Recruit", "Oriented", "Major · Undecided", "Mentor-in-Training", "Ping · Raid"]

SHOWCASE_TAGS = ["WIP", "Blockout", "Lit", "Playable", "Critique-wanted", "Shipped"]
HELP_TAGS = ["Site / Bot issue", "Blueprint", "C++", "Materials", "Animation", "Lighting", "Level Design", "Packaging"]
SPEC_TAGS = ["WIP", "Question", "Tip", "Done"]

CAT_GATE, CAT_HALL, CAT_SPEC, CAT_VOICE, CAT_STAFF = ("00 · GATE", "01 · GUILD HALL", "02 · SPECIALIZATIONS",
                                                      "03 · TOWN HALL", "04 · STAFF")


def spec_slug(cat, key: str) -> str:
    """Forum name for a specialization: its title, lower-case with dashes (level-design, environment-art)."""
    return re.sub(r"[^a-z0-9]+", "-", cat.title_of(key).lower()).strip("-")


def _set(d: dict, path: tuple, value: int) -> None:
    for k in path[:-1]:
        d = d.setdefault(k, {})
    d[path[-1]] = value


class SetupServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_specs(self) -> list[tuple]:
        """(name, color or None, hoist, mentionable, unlocks key path, older name or None), highest first."""
        cat = self.bot.catalog
        specs = [("Mod", "#E0E0E0", True, True, ("staff", "mod"), None),
                 ("Mentor", "#6FB3A0", False, True, ("staff", "mentor"), None)]
        specs += [(name, color, hoist, n >= 3, ("rank", n), None) for n, name, color, hoist in RANK_ROLES]
        for key in cat.specializations:
            if key != "undecided":
                title = cat.title_of(key)
                old = "Major · Lookdev" if key == "lookdev" else f"Major · {title}"
                specs.append((title, None, False, True, ("specialization", key), old))
        specs += [("Ping · Showcase", None, False, True, ("ping", "showcase"), None),
                  ("Ping · Patch Notes", None, False, True, ("ping", "patch_notes"), None)]
        return specs

    # ------------------------------------------------------------------ helpers
    async def _role(self, g: discord.Guild, name, color, hoist, mention, perms=None, old=None) -> discord.Role:
        r = discord.utils.get(g.roles, name=name)
        if r:
            return r
        for old_name in ([old] if old else []) + ([f"Major · {name}"]):
            if (r := discord.utils.get(g.roles, name=old_name)):
                await r.edit(name=name, mentionable=mention, reason="Unrealcraft: renamed")
                return r
        return await g.create_role(name=name, color=C(color) if color else discord.Color.default(), hoist=hoist,
                                   mentionable=mention, permissions=perms or discord.Permissions.none(),
                                   reason="Unrealcraft bootstrap")

    async def _category(self, g, name, overwrites, old_names=()) -> discord.CategoryChannel:
        c = discord.utils.get(g.categories, name=name)
        if not c:
            for old in old_names:
                if (c := discord.utils.get(g.categories, name=old)):
                    await c.edit(name=name, reason="Unrealcraft: renamed")
                    break
        if c:
            await c.edit(overwrites=overwrites)
            return c
        return await g.create_category(name, overwrites=overwrites, reason="Unrealcraft bootstrap")

    async def _text(self, g, cat, name, topic=None, news=False, old_names=()):
        """Find a text channel anywhere by name (or an old name) and move it into `cat`; else create it.
        Its permissions always follow the category."""
        ch = next((c for n in (name, *old_names) for c in g.text_channels if c.name == n), None)
        if ch:
            await ch.edit(name=name, category=cat, topic=topic or ch.topic, overwrites=cat.overwrites, reason="Unrealcraft: layout")
            return ch
        kw = dict(category=cat, topic=topic, reason="Unrealcraft bootstrap")
        if news and "COMMUNITY" in g.features:
            kw["news"] = True
        return await g.create_text_channel(name, **kw)

    async def _is_empty(self, ch: discord.TextChannel) -> bool:
        """True if nobody but bots ever posted there."""
        async for m in ch.history(limit=200):
            if not m.author.bot:
                return False
        return True

    async def _forum(self, g, cat, name, tags, topic=None, require_tag=False, reaction=None, report=None):
        """A forum (or a text channel while Community is off) inside `cat`, with the category's permissions."""
        ch = discord.utils.get(g.channels, name=name)
        community = "COMMUNITY" in g.features
        if ch and community and isinstance(ch, discord.TextChannel):
            # Community was switched on after the first bootstrap: swap the text channel for a forum.
            if await self._is_empty(ch):
                await ch.delete(reason="Unrealcraft: replaced by a forum (Community on)")
                report is not None and report.append(f"#{name}: text → forum")
            else:
                await ch.edit(name=f"{name}-archive", reason="Unrealcraft: kept (had member posts)")
                report is not None and report.append(f"#{name}: had member posts, renamed to #{name}-archive")
            ch = None
        if ch:
            await ch.edit(category=cat, topic=topic, overwrites=cat.overwrites, reason="Unrealcraft: layout")
            if isinstance(ch, discord.ForumChannel):
                have = {t.name for t in ch.available_tags}
                missing = [discord.ForumTag(name=t) for t in tags if t not in have]
                if missing:
                    await ch.edit(available_tags=list(ch.available_tags) + missing)
            return ch
        if community:
            extra = {"default_reaction_emoji": reaction} if reaction else {}
            forum = await g.create_forum(name, category=cat, topic=topic,
                                         available_tags=[discord.ForumTag(name=t) for t in tags],
                                         default_sort_order=discord.ForumOrderType.latest_activity,
                                         reason="Unrealcraft bootstrap", **extra)
            if require_tag:
                await forum.edit(require_tag=True)
            return forum
        return await g.create_text_channel(name, category=cat, topic=topic, reason="Unrealcraft bootstrap")

    async def _retire(self, g, names) -> list[str]:
        """Delete our own obsolete channels by name, only if no member ever posted in them."""
        out = []
        for name in names:
            for ch in [c for c in g.channels if c.name == name]:
                if isinstance(ch, discord.TextChannel) and not await self._is_empty(ch):
                    await ch.edit(name=f"{name}-archive", reason="Unrealcraft: no longer used (kept: has member messages)")
                    out.append(f"#{name}: had member messages, renamed to #{name}-archive")
                    continue
                if isinstance(ch, discord.ForumChannel):
                    threads = list(ch.threads) + [t async for t in ch.archived_threads(limit=50)]
                    if any(t.owner_id != g.me.id for t in threads):
                        await ch.edit(name=f"{name}-archive", reason="Unrealcraft: no longer used (kept: has member posts)")
                        out.append(f"#{name}: had member posts, renamed to #{name}-archive")
                        continue
                await ch.delete(reason="Unrealcraft: the site replaced this channel")
                out.append(f"removed #{name}")
        return out

    async def _voice(self, g, cat, name):
        ch = discord.utils.get(g.voice_channels, name=name)
        if ch:
            await ch.edit(category=cat, overwrites=cat.overwrites, reason="Unrealcraft: layout")
            return ch
        return await g.create_voice_channel(name, category=cat, reason="Unrealcraft bootstrap")

    # ------------------------------------------------------------------ bootstrap
    async def bootstrap(self, g: discord.Guild) -> list[str]:
        report: list[str] = []
        unl, cat, me = self.bot.unlocks, self.bot.catalog, g.me
        data = unl.data

        # roles ------------------------------------------------------------
        specs = self.role_specs()
        data["roles"] = {k: v for k, v in (data.get("roles") or {}).items() if k in ("staff", "rank", "ping")}
        roles: dict[str, discord.Role] = {}
        for name, color, hoist, mention, key, old in specs:
            r = await self._role(g, name, color, hoist, mention, MOD_PERMS if name == "Mod" else None, old)
            roles[name] = r
            _set(data["roles"], key, r.id)
        top = me.top_role.position
        try:                                      # first in the list = highest, all below the bot's own role
            await g.edit_role_positions({roles[s[0]]: max(1, top - 1 - i) for i, s in enumerate(specs)},
                                        reason="Unrealcraft bootstrap")
        except discord.HTTPException as e:
            report.append(f"⚠ could not order roles ({e}). Drag the Quartermaster role to the top.")
        report.append(f"roles: {len(specs)} ready")
        # the old gate and onboarding-answer roles: nothing reads them any more
        legacy = set(LEGACY_ROLES) | {name for name, _q, _v in profile.all_role_names()}
        for r in [r for r in g.roles if r.name in legacy or r.name.startswith(("Specialty · ", "Seal · "))]:
            try:
                await r.delete(reason="Unrealcraft: the site replaced this role")
                report.append(f"removed role {r.name}")
            except discord.HTTPException as e:
                report.append(f"⚠ could not remove role {r.name}: {e}")

        everyone, staff = g.default_role, [roles["Mod"], roles["Mentor"]]
        bot_ow = P(view_channel=True, send_messages=True, manage_messages=True, manage_threads=True, manage_channels=True,
                   embed_links=True, attach_files=True, read_message_history=True, connect=True, move_members=True)
        read_ow = P(view_channel=True, send_messages=False, add_reactions=True, create_public_threads=False,
                    read_message_history=True, use_application_commands=True)
        member_ow = P(view_channel=True, send_messages=True, send_messages_in_threads=True, create_public_threads=True,
                      attach_files=True, embed_links=True, add_reactions=True, read_message_history=True,
                      use_application_commands=True, connect=True, speak=True)
        chans = data.setdefault("channels", {})
        for stale in ("quest_board", "mentor_queue", "tracks", "curriculum_wip", "roles_info", "how_this_place_works", "bays"):
            chans.pop(stale, None)

        # 00 GATE: read-only essentials -------------------------------------------------
        gate = await self._category(g, CAT_GATE, {everyone: read_ow, me: bot_ow})
        welcome = await self._text(g, gate, "welcome", topic="Start here: what Unrealcraft is, the rules, and the way to the site.")
        ann = await self._text(g, gate, "announcements", news=True, topic="Events and big news.")
        notes = await self._text(g, gate, "patch-notes", news=True,
                                 topic="What changed on the site and in the curriculum. Posted on every release.")
        rankups = await self._text(g, gate, "rank-ups", topic="Promotions earned on the site. Posted by the Quartermaster.")
        resources = await self._text(g, gate, "epic-games-resources", old_names=("resources",),
                                     topic="Epic Games docs and free courses. Quests link to these too.")
        chans.update(welcome=welcome.id, announcements=ann.id, patch_notes=notes.id, rank_ups=rankups.id, resources=resources.id)

        # 01 GUILD HALL: open to everyone who accepted the rules ------------------------
        hall = await self._category(g, CAT_HALL, {everyone: member_ow, me: bot_ow}, old_names=("01 · GUILD HUB", "01 · HUB"))
        general = await self._text(g, hall, "general", topic="Talk about anything Unreal.")
        intros = await self._text(g, hall, "introductions", topic="Say hi: what you want to learn and one thing you want to build.")
        showcase = await self._forum(g, hall, "showcase", SHOWCASE_TAGS, reaction="🔥", report=report,
                                     topic="Your own map or scene. Work in progress is welcome. Pick a tag.")
        helpdesk = await self._forum(g, hall, "help-desk", HELP_TAGS, require_tag=True, report=report,
                                     topic="Stuck in Unreal, on a quest, or something broken on the site? Say your engine "
                                           "version, what you tried, and what happened.")
        suggestions = await self._forum(g, hall, "suggestions", ["Site", "Server", "Quests", "Other"], report=report,
                                        topic="Ideas for the site, the server or the quests. One idea per post.")
        chans.update(general=general.id, introductions=intros.id, showcase=showcase.id, help_desk=helpdesk.id,
                     suggestions=suggestions.id)

        # 02 SPECIALIZATIONS: one discussion forum each, open to everyone ---------------
        spec_cat = await self._category(g, CAT_SPEC, {everyone: member_ow, me: bot_ow},
                                        old_names=("02 · QUEST BOARD", "03 · WORKSHOP"))
        chans["specializations"] = {}
        for key, cfg in cat.specializations.items():
            if key == "undecided":
                continue
            slug = spec_slug(cat, key)
            forum = await self._forum(g, spec_cat, slug, SPEC_TAGS, report=report,
                                      topic=f"{cfg['title']}: questions, tips and work in progress. {cfg.get('blurb', '')}".strip())
            chans["specializations"][key] = forum.id
        report += await self._retire(g, ["quest-log", "starter-quests", "foundations", "mentor-queue"])

        # 03 TOWN HALL: join-to-create voice ---------------------------------------------
        from .voice import HUBS
        town = await self._category(g, CAT_VOICE, {everyone: member_ow, me: bot_ow},
                                    old_names=("02 · TOWN HALL", "02 · VOICE ROOMS", "02 · TRAINING GROUNDS"))
        floor = await self._voice(g, town, HUBS["studio_floor_voice"][0])
        chans.update(studio_floor_voice=floor.id)

        # 04 STAFF -----------------------------------------------------------------------
        st = await self._category(g, CAT_STAFF, {everyone: P(view_channel=False), me: bot_ow,
                                                 **{r: P(view_channel=True) for r in staff}})
        modlog = await self._text(g, st, "mod-log", topic="AutoMod alerts and Discord's own notices.")
        chans.update(mod_log=modlog.id)

        data["categories"] = {"hall": hall.id, "specializations": spec_cat.id, "town_hall": town.id}
        data.pop("unlock_at_rank", None)
        unl.path.write_text("# Written by /setup bootstrap. Safe to edit; bootstrap re-matches by name.\n"
                            + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

        if "COMMUNITY" in g.features:
            report += await self._community(g, welcome, modlog)
            report += await self.onboarding(g)
            if isinstance(ann, discord.TextChannel) and not ann.is_news():
                try:
                    await ann.edit(type=discord.ChannelType.news)
                    report.append("#announcements → announcement channel")
                except discord.HTTPException as e:
                    report.append(f"⚠ #announcements conversion: {e}")
        else:
            report.append("Community is off: showcase, help-desk and the specialization forums are plain text channels. "
                          "Turn on Community in Server Settings and run bootstrap again.")
        report += await self._remove_defaults(g)
        report += await self.order(g)
        report.append("categories + channels ready; IDs written to config/unlocks.yaml")
        return report

    # ------------------------------------------------------------------ community extras
    async def _community(self, g, welcome, modlog) -> list[str]:
        out = []
        try:
            await g.edit(community=True, rules_channel=welcome, public_updates_channel=modlog, safety_alerts_channel=modlog,
                         system_channel=None, reason="Unrealcraft bootstrap")
            out.append("rules channel = #welcome, Discord community updates → #mod-log, join spam off")
        except discord.HTTPException as e:
            out.append(f"⚠ guild settings: {e}")
        try:
            await g.edit_welcome_screen(
                enabled=True,
                description="The guild hall of Unrealcraft, an RPG for learning Unreal Engine 5. The game is on the site; "
                            "this is where we talk and show our work.",
                welcome_channels=[
                    discord.WelcomeChannel(channel=welcome, description="Start here: the rules and the way to the site",
                                           emoji=discord.PartialEmoji(name="🚪")),
                    discord.WelcomeChannel(channel=g.get_channel(self.bot.unlocks.channel("general")),
                                           description="Say hello", emoji=discord.PartialEmoji(name="👋")),
                ])
            out.append("welcome screen set")
        except discord.HTTPException as e:
            out.append(f"⚠ welcome screen: {e}")
        # Rules Screening: members must accept these before they can talk. Only created if none exists,
        # so edits made later in Server Settings are never overwritten.
        try:
            route = discord.http.Route("GET", "/guilds/{guild_id}/member-verification", guild_id=g.id)
            try:
                await self.bot.http.request(route)
                out.append("rules screening already set (left as is)")
            except discord.NotFound:
                rules = self.rules()
                await self.bot.http.request(
                    discord.http.Route("PATCH", "/guilds/{guild_id}/member-verification", guild_id=g.id),
                    json={"enabled": True,
                          "description": "Unrealcraft is an RPG for learning Unreal Engine 5. Read the rules, then follow "
                                         "the link in #welcome to the site.",
                          "form_fields": [{"field_type": "TERMS", "label": "Read and agree to the server rules",
                                           "values": rules, "required": True}]},
                    reason="Unrealcraft rules screening")
                out.append(f"rules screening on ({len(rules)} rules)")
        except discord.HTTPException as e:
            out.append(f"⚠ rules screening: {e}")
        # AutoMod: presets only, alerts to #mod-log. Existing rules with the same name are left alone.
        try:
            existing = {r.name for r in await g.fetch_automod_rules()}
            alert = discord.AutoModRuleAction(channel_id=modlog.id)
            block = discord.AutoModRuleAction(custom_message="Blocked by Unrealcraft AutoMod.")
            if "UC · mention spam" not in existing:
                await g.create_automod_rule(
                    name="UC · mention spam", event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.mention_spam, mention_limit=6),
                    actions=[block, alert], enabled=True, reason="Unrealcraft bootstrap")
            if "UC · flagged words" not in existing:
                await g.create_automod_rule(
                    name="UC · flagged words", event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword_preset,
                                                   presets=discord.AutoModPresets.all()),
                    actions=[block, alert], enabled=True, reason="Unrealcraft bootstrap")
            if "UC · spam" not in existing:
                await g.create_automod_rule(
                    name="UC · spam", event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.spam),
                    actions=[block], enabled=True, reason="Unrealcraft bootstrap")
            out.append("AutoMod: mention spam, flagged words, spam → alerts in #mod-log")
        except discord.HTTPException as e:
            out.append(f"⚠ AutoMod: {e}")
        return out

    def rules(self) -> list[str]:
        text = (Path_root() / "docs" / "06-community-rules.md").read_text(encoding="utf-8")
        return [ln.split(". ", 1)[1].replace("**", "") for ln in text.splitlines() if ln[:2].rstrip(".").isdigit()]

    async def onboarding(self, g: discord.Guild) -> list[str]:
        """Discord Onboarding: no questions about what to learn (that is chosen on the site), only opt-in pings."""
        unl = self.bot.unlocks
        E = discord.PartialEmoji
        pings = discord.OnboardingPrompt(
            type=discord.OnboardingPromptType.multiple_choice, title="What should we ping you for?",
            single_select=False, required=False, in_onboarding=False,
            options=[
                discord.OnboardingPromptOption(title="Showcase spotlights", description="Great work from members",
                                               emoji=E(name="🔥"), roles=[unl.role("ping", "showcase")]),
                discord.OnboardingPromptOption(title="Patch notes", description="New quests and site changes",
                                               emoji=E(name="📦"), roles=[unl.role("ping", "patch_notes")]),
            ])
        defaults = [c for name in (CAT_GATE, CAT_HALL) if (cat := discord.utils.get(g.categories, name=name))
                    for c in cat.channels if isinstance(c, (discord.TextChannel, discord.ForumChannel))]
        try:
            await g.edit_onboarding(prompts=[pings], default_channels=defaults, enabled=True,
                                    mode=discord.OnboardingMode.advanced, reason="Unrealcraft onboarding")
            return [f"onboarding on: 1 question (pings), {len(defaults)} default channels"]
        except discord.HTTPException as e:
            return [f"⚠ onboarding: {e}"]

    CATEGORY_ORDER = [CAT_GATE, CAT_HALL, CAT_SPEC, CAT_VOICE, CAT_STAFF]
    CHANNEL_ORDER = {
        CAT_GATE: ["welcome", "announcements", "patch-notes", "rank-ups", "epic-games-resources"],
        CAT_HALL: ["general", "introductions", "showcase", "help-desk", "suggestions"],
    }

    async def order(self, g: discord.Guild) -> list[str]:
        """Put categories and their text/forum channels in reading order."""
        moved = 0
        for i, name in enumerate(self.CATEGORY_ORDER):
            c = discord.utils.get(g.categories, name=name)
            if c and c.position != i:
                await c.edit(position=i, reason="Unrealcraft: order")
                moved += 1
        for cat_name, names in self.CHANNEL_ORDER.items():
            c = discord.utils.get(g.categories, name=cat_name)
            if not c:
                continue
            present = [ch for n in names if (ch := discord.utils.get(c.channels, name=n))]
            if present and sorted(present, key=lambda ch: ch.position) != present:
                base = min(ch.position for ch in present)
                for i, ch in enumerate(present):
                    await ch.edit(position=base + i, reason="Unrealcraft: order")
                    moved += 1
        return [f"ordered {moved} categories/channels"] if moved else []

    async def _remove_defaults(self, g: discord.Guild) -> list[str]:
        """Delete Discord's starter 'Text Channels/#general' and 'Voice Channels/General' if nobody used them."""
        out = []
        for cat_name in ("Text Channels", "Voice Channels"):
            cat = discord.utils.get(g.categories, name=cat_name)
            if not cat:
                continue
            for ch in list(cat.channels):
                if isinstance(ch, discord.TextChannel) and not await self._is_empty(ch):
                    out.append(f"kept #{ch.name} in {cat_name} (has member messages)")
                    continue
                if isinstance(ch, discord.VoiceChannel) and ch.members:
                    out.append(f"kept {ch.name} voice (people in it)")
                    continue
                await ch.delete(reason="Unrealcraft: default starter channel")
                out.append(f"removed default {cat_name}/{ch.name}")
            if not cat.channels:
                await cat.delete(reason="Unrealcraft: default starter category")
        return out

    # ------------------------------------------------------------------ pinned messages
    # One pinned bot message per purpose. Updates EDIT that message in place (never re-post), so channels stay clean.
    # kv(user 0) "pin:<key>" = "<channel_id>:<message_id>:<content hash>"
    def pin_specs(self, g: discord.Guild) -> list[dict]:
        unl, cat, site = self.bot.unlocks, self.bot.catalog, self.bot.settings.site_url
        ch = lambda *k: g.get_channel(unl.channel(*k))
        E = lambda title, text, color="#7A8C7E": discord.Embed(title=title, description=text, color=C(color))

        def link(label: str, url: str) -> discord.ui.View:
            v = discord.ui.View(timeout=None)
            v.add_item(discord.ui.Button(label=label, url=url))
            return v

        rule_lines = "\n".join(f"{i}. {r}" for i, r in enumerate(self.rules(), 1))
        rank_lines = "\n".join(f"**{r['title']}**" + (f": {r['xp']} XP" if r.get("xp") else "") for r in cat.meta["ranks"] if r["n"] <= 4)
        specs = [
            dict(key="welcome", channel=ch("welcome"), view=link("Open Unrealcraft", site), embeds=[
                E("👋 Welcome to Unrealcraft",
                  "Learn **Unreal Engine 5** the way you would play it.\n"
                  "Read the guides, build it in Unreal, beat the bosses, claim your rewards."),
                E("🗺️ The game is on the site",
                  "Quests, boss fights, turn-ins and reviews all happen on the website. "
                  "Press the button below and log in with Discord.\n"
                  "Your rank and specializations show up here as roles once you play.", "#3D7DD8"),
                E("🏛️ This server is the guild hall",
                  "**#general** and **#introductions**: talk and say hi.\n"
                  "**#showcase**: show what you are building, finished or not.\n"
                  "**#help-desk**: stuck in Unreal or on a quest.\n"
                  "**Specialization forums**: questions and tips for each field.\n"
                  "**#rank-ups**: promotions earned on the site.", "#8E6CCF"),
                E("🎖️ Ranks", "Ranks come only from quests. Chatting gives no XP.\n" + rank_lines, "#B5714B"),
                E("📜 Rules", rule_lines, "#D4AF37"),
            ]),
            dict(key="how-to-ask", channel=ch("help_desk"), title="How to get help", tag=HELP_TAGS[0], embeds=[
                E("🆘 Need help?", "Make a post and pick a tag. One problem per post."),
                E("✍️ A good question", "Say your **engine version**, what you **tried**, and what you **expected** "
                  "against what **happened**. Add a screenshot.\n\n"
                  "❌ \"lighting broken help\"\n"
                  "✅ \"5.8 · Level Design · Tried raising Sky Light intensity · [screenshot] · "
                  "Expected a lit interior, got black walls\"", "#3D7DD8"),
                E("🐞 Something wrong on the site?", "Use the **Site / Bot issue** tag. Say what you did, what happened "
                  "and when. Staff check #patch-notes and answer there.", "#D9824A"),
            ]),
            dict(key="wip-feedback", channel=ch("showcase"), title="How to give feedback", tag="WIP", embeds=[
                E("🔥 Showcase", "Share what you are building. Finished or not. Only your own work."),
                E("💬 Giving feedback", "One thing that works.\nOne specific issue.\nOne next step.", "#3D7DD8"),
                E("⭐ Want critique?", "Tag your post **Critique-wanted**.", "#D4AF37"),
            ]),
            dict(key="resources", channel=ch("resources"), embeds=[
                E("📚 Epic Games resources", "Epic's own docs and free courses. "
                  "Quests link these, plus hand-picked guides from the community.\n\n"
                  "• [Get Started](https://dev.epicgames.com/documentation/en-us/unreal-engine/get-started)\n"
                  "• [Your First Hour](https://dev.epicgames.com/documentation/en-us/unreal-engine/first-hour-in-unreal-engine)\n"
                  "• [Level Designer Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/level-designer-quick-start-in-unreal-engine)\n"
                  "• [Programming Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-cpp-quick-start)\n"
                  "• [Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-materials)\n"
                  "• [Blueprints](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine)",
                  "#3D7DD8"),
            ]),
        ]
        for key, cfg in cat.specializations.items():
            if key == "undecided":
                continue
            slug = spec_slug(cat, key)
            specs.append(dict(key=f"about-{slug}", channel=ch("specializations", key), title=f"About #{slug}", tag="Tip",
                              view=link(f"{cfg['title']} quests", f"{site}/quests?specialization={key}"), embeds=[
                E(f"🛠️ {cfg['title']}", f"{cfg.get('blurb', '')}\nAnyone can post here, whatever their specialization."),
                E("📝 Post here", "One thread per thing you are building (tag WIP), or a question (tag Question).\n"
                  "Quests for this specialization are on the site.", "#3D7DD8"),
            ]))
        return [s for s in specs if s["channel"]]

    @staticmethod
    def _fingerprint(spec: dict) -> str:
        import hashlib
        raw = (spec.get("content") or "") + "".join(str(e.to_dict()) for e in spec.get("embeds") or [])
        items = spec["view"].children if spec.get("view") else []
        raw += "".join((getattr(i, "label", None) or "") + str(getattr(i, "url", "") or "") for i in items)
        return hashlib.sha1(raw.encode()).hexdigest()[:12]

    async def _fetch_pin(self, g: discord.Guild, rec: str | None) -> discord.Message | None:
        if not rec:
            return None
        try:
            cid, mid, _ = rec.split(":")
            ch = g.get_channel_or_thread(int(cid)) or await g.fetch_channel(int(cid))
            if isinstance(ch, discord.ForumChannel):
                th = g.get_thread(int(mid)) or await g.fetch_channel(int(mid))
                return await th.fetch_message(th.id)
            return await ch.fetch_message(int(mid))
        except (discord.HTTPException, ValueError):
            return None

    async def sync_pins(self, g: discord.Guild) -> list[str]:
        """Create each pinned message once; afterwards only edit it when its text changes."""
        out = []
        for spec in self.pin_specs(g):
            key, chan = spec["key"], spec["channel"]
            fp = self._fingerprint(spec)
            rec = await self.bot.db.kv_get(0, f"pin:{key}")
            msg = await self._fetch_pin(g, rec)
            if msg and (msg.channel.id == chan.id or getattr(msg.channel, "parent_id", None) == chan.id):
                if rec.split(":")[2] != fp:
                    await msg.edit(content=spec.get("content"), embeds=spec.get("embeds") or [], view=spec.get("view"))
                    out.append(f"edited {key}")
                mid = msg.id
            else:
                kw = {"view": spec["view"]} if spec.get("view") else {}
                if isinstance(chan, discord.ForumChannel):
                    tag = discord.utils.get(chan.available_tags, name=spec.get("tag", "")) or \
                        (chan.available_tags[:1] or [None])[0]
                    # Forums allow ONE pinned post: unpin old bot posts first (cleanup_bot_posts deletes them).
                    for t in chan.threads:
                        if t.flags.pinned and t.owner_id == g.me.id:
                            await t.edit(pinned=False)
                    created = await chan.create_thread(name=spec.get("title", key), content=spec.get("content"),
                                                       embeds=spec.get("embeds") or [],
                                                       applied_tags=[tag] if tag else [], **kw)
                    await created.thread.edit(pinned=True)
                    mid = created.thread.id
                else:
                    m = await chan.send(content=spec.get("content"), embeds=spec.get("embeds") or [], **kw)
                    await m.pin()
                    mid = m.id
                out.append(f"posted {key}")
            await self.bot.db.kv_set(0, f"pin:{key}", f"{chan.id}:{mid}:{fp}")
        return out

    async def cleanup_bot_posts(self, g: discord.Guild) -> list[str]:
        """Delete every message/thread the bot posted except the tracked pins, anything that mentions a member
        (old turn-in posts made for members), #rank-ups cards, patch notes and the staff channels."""
        cur = await self.bot.db.conn.execute("SELECT k, v FROM kv WHERE user_id=0 AND k LIKE 'pin:%'")
        current = {f"pin:{spec['key']}" for spec in self.pin_specs(g)}
        keep = set()
        for row in await cur.fetchall():
            parts = (row["v"] or "").split(":")
            if row["k"] not in current or len(parts) != 3:     # a pin we no longer use: forget it
                await self.bot.db.conn.execute("DELETE FROM kv WHERE user_id=0 AND k=?", (row["k"],))
                continue
            keep.add(int(parts[1]))
        await self.bot.db.conn.commit()
        unl = self.bot.unlocks
        skip = {unl.channel(k) for k in ("rank_ups", "mod_log", "patch_notes", "announcements")}
        removed = 0
        for chan in g.channels:
            if chan.id in skip:
                continue
            if isinstance(chan, discord.TextChannel):
                async for m in chan.history(limit=200):
                    if m.author.id == g.me.id and m.id not in keep and "<@" not in m.content:
                        await m.delete()
                        removed += 1
            elif isinstance(chan, discord.ForumChannel):
                threads = list(chan.threads)
                async for t in chan.archived_threads(limit=100):
                    threads.append(t)
                for t in threads:
                    if t.owner_id != g.me.id or t.id in keep:
                        continue
                    try:
                        starter = await t.fetch_message(t.id)
                        if "<@" in starter.content:
                            continue                # a member's post made through the old bot
                    except discord.HTTPException:
                        pass
                    await t.delete()
                    removed += 1
        return [f"cleaned up {removed} old bot posts"]

    # ------------------------------------------------------------------ patch notes
    @staticmethod
    def patch_embed(rel: dict) -> discord.Embed:
        """One embed per version: the summary line as description, each '### Section' as a field."""
        parts = re.split(r"\n(?=### )", rel["body"])
        intro = parts[0].strip() if not parts[0].startswith("### ") else ""
        sections = [p for p in parts if p.startswith("### ")]
        e = discord.Embed(title=rel["version"], color=C("#D4AF37"),
                          description=(intro or ("" if sections else rel["body"]))[:4000] or None)
        for sec in sections[:25]:
            head, _, body = sec.partition("\n")
            e.add_field(name=head[4:].strip()[:256], value=body.strip()[:1024] or "—", inline=False)
        e.set_footer(text=rel["date"])
        return e

    async def post_patch_notes(self, g: discord.Guild, force_latest: bool = False) -> list[str]:
        """#patch-notes is a full history: one message per released version, oldest first.
        A version counts as released once its tag (e.g. v0.2.0) is on GitHub. If a released entry's text is
        corrected later, its existing message is edited; nothing is re-posted."""
        import hashlib
        from .. import release
        from ..config import BOT_ROOT
        ch = g.get_channel(self.bot.unlocks.channel("patch_notes"))
        if not ch:
            return []
        repo = BOT_ROOT.parent
        tags = await release.pushed_tags(repo)
        if tags is None:
            log.warning("patch notes: couldn't reach the git remote; nothing posted")
            return []
        done = []
        es = [e for e in release.entries(repo / "CHANGELOG.md") if e["version"] in tags]
        for rel in reversed(es):                                   # oldest first
            key = f"patchnotes:{rel['version']}"
            fp = hashlib.sha1((rel["title"] + rel["body"]).encode()).hexdigest()[:12]
            rec = await self.bot.db.kv_get(0, key)
            mid, _, old_fp = (rec or "").partition(":")
            embed = self.patch_embed(rel)
            if mid and not (force_latest and rel is es[0]):
                if old_fp != fp:                                   # corrected entry: edit, don't re-post
                    try:
                        msg = await ch.fetch_message(int(mid))
                        await msg.edit(embed=embed)
                        await self.bot.db.kv_set(0, key, f"{mid}:{fp}")
                        done.append(f"{rel['version']} (edited)")
                    except discord.HTTPException as ex:
                        log.warning("patch notes: couldn't edit %s: %s", rel["version"], ex)
                continue
            msg = await ch.send(embed=embed)
            if ch.is_news():
                try:
                    await msg.publish()                            # reach servers that follow #patch-notes
                except discord.HTTPException:
                    pass
            await self.bot.db.kv_set(0, key, f"{msg.id}:{fp}")
            done.append(rel["version"])
        return done

    # ------------------------------------------------------------------ commands
    admin = app_commands.Group(name="setup", description="Owner: build and maintain the server",
                               default_permissions=discord.Permissions(administrator=True))

    @admin.command(name="bootstrap", description="Create or repair roles, channels and pins. Only removes the bot's own leftovers.")
    async def bootstrap_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        rep = await self.bootstrap(itx.guild)
        rep += await self.sync_pins(itx.guild) + await self.cleanup_bot_posts(itx.guild)
        rep.append(f"roles synced for {await self.bot.get_cog('Roles').sync_all(itx.guild)} members")
        await itx.followup.send("\n".join(rep)[:1900], ephemeral=True)

    @admin.command(name="sync-pins", description="Update pinned messages in place and remove stray bot posts.")
    async def sync_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        rep = await self.sync_pins(itx.guild) + await self.cleanup_bot_posts(itx.guild)
        await itx.followup.send("\n".join(rep) or "Everything up to date.", ephemeral=True)

    @admin.command(name="sync-roles", description="Make every member's rank and specialization roles match the site.")
    async def sync_roles_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        n = await self.bot.get_cog("Roles").sync_all(itx.guild)
        await itx.followup.send(f"Roles updated for {n} members.", ephemeral=True)

    @admin.command(name="patch-notes", description="Post pushed versions missing from #patch-notes (re-posts the latest).")
    async def patch_notes_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        v = await self.post_patch_notes(itx.guild, force_latest=True)
        await itx.followup.send(f"Posted {', '.join(v)}." if v else "Nothing to post: no version tag pushed to GitHub yet, or #patch-notes is missing.",
                                ephemeral=True)

    @admin.command(name="reload-curriculum", description="Reload ranks and specializations from the curriculum files.")
    async def reload_curriculum(self, itx: discord.Interaction):
        from ..curriculum import Catalog
        new = Catalog.load(self.bot.settings.curriculum_dir)
        errs, warns = new.validate()
        if errs:
            await itx.response.send_message("Not reloaded:\n" + "\n".join(errs[:20]), ephemeral=True)
            return
        self.bot.catalog = new
        await itx.response.send_message(f"Reloaded {len(new.quests)} quests ({len(warns)} warnings).", ephemeral=True)


def Path_root():
    from ..config import BOT_ROOT
    return BOT_ROOT.parent


async def setup(bot):
    await bot.add_cog(SetupServer(bot))
