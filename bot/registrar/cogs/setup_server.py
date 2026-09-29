"""/admin bootstrap + /admin post-pins. Builds the whole server from docs/01 and writes IDs to unlocks.yaml.

Idempotent: roles, categories and channels are matched by name and reused if they already exist.
Deletes only (a) Discord's default starter channels and (b) our own text channels being upgraded to forums,
and only when no member ever posted in them. Anything with member messages is kept/renamed.
"""
from __future__ import annotations

import logging

import discord
import yaml
from discord import app_commands
from discord.ext import commands

from .. import profile

log = logging.getLogger("quartermaster.setup")

C = discord.Color.from_str
P = discord.PermissionOverwrite

# (name, color or None, hoist, mentionable, unlocks key path)
ROLES = [
    ("Mod", "#E0E0E0", True, True, ("staff", "mod")),
    ("Curriculum", "#B0A48A", False, True, ("staff", "curriculum")),
    ("Mentor", "#6FB3A0", False, True, ("staff", "mentor")),
    ("Mentor-in-Training", "#8FC4B5", False, False, ("staff", "mentor_in_training")),
    ("Studio Lead", "#D4AF37", True, True, ("rank", 6)),
    ("Systems Architect", "#8E6CCF", True, True, ("rank", 5)),
    ("Engineer", "#8A9BA8", True, True, ("rank", 4)),
    ("Specialist · Environment Art", "#D9824A", False, True, ("specialist", "lookdev")),
    ("Specialist · Design", "#4FA36C", False, True, ("specialist", "design")),
    ("Specialist · Anim", "#C85C8E", False, True, ("specialist", "anim")),
    ("Specialist · Code", "#4AA3B5", False, True, ("specialist", "code")),
    ("Gameplay Prototyper", "#3D7DD8", False, False, ("rank", 2)),
    ("Blockout Artist", "#B5714B", False, False, ("rank", 1)),
    ("Greenlit", "#7A8C7E", False, False, ("rank", 0)),
    ("Oriented", None, False, False, ("oriented",)),
    ("Recruit", None, False, False, ("recruit",)),
    ("Major · Level Design", None, False, False, ("major", "level_design")),
    ("Major · Environment Art", None, False, False, ("major", "lookdev")),
    ("Major · Tech Art", None, False, False, ("major", "tech_art")),
    ("Major · Gameplay Design", None, False, False, ("major", "gameplay_design")),
    ("Major · Animation", None, False, False, ("major", "animation")),
    ("Major · Programming", None, False, False, ("major", "programming")),
    ("Major · Cinematics", None, False, False, ("major", "cinematics")),
    ("Major · Undecided", None, False, False, ("major", "undecided")),
    *[(name, None, False, False, ("profile", qkey, value)) for name, qkey, value in profile.all_role_names()],
    ("Ping · Raid", None, False, True, ("ping", "raid")),
    ("Ping · Showcase", None, False, True, ("ping", "showcase")),
    ("Ping · Patch Notes", None, False, True, ("ping", "patch_notes")),
    ("Alumni", "#A0A0A0", False, False, None),
    ("Visiting Mentor", "#A0A0A0", False, False, None),
    ("Founding Crew", "#A0A0A0", False, False, None),
    ("On Leave", "#555555", False, False, ("on_leave",)),
]

MOD_PERMS = discord.Permissions(kick_members=True, moderate_members=True, manage_messages=True,
                                manage_threads=True, view_audit_log=True, manage_nicknames=True)

SHOWCASE_TAGS = ["WIP", "Blockout", "Lit", "Playable", "Critique-wanted", "Shipped"]
HELP_TAGS = ["Server / Bot issue", "Blueprint", "C++", "Materials", "Animation", "Lighting", "Level Design",
             "Packaging", "Discord-help"]

# (category name, unlocks.categories key or None, min rank or special, channels)
# channel: (name, kind, unlocks.channels key path or None, flags)
TRACKS = [
    ("03 · FOUNDATIONS", "foundations", 0, "foundations"),
    ("03 · WORLD & LIGHTING", "world_lighting", 1, "world-lighting"),
    ("03 · MATERIALS", "materials", 2, "materials"),
    ("03 · BLUEPRINT", "blueprint", 2, "blueprint"),
    ("03 · CHARACTERS & ANIM", "characters_anim", 3, "characters-anim"),
]
SEALS = ["lookdev", "design", "anim", "code"]


def _set(d: dict, path: tuple, value: int) -> None:
    for k in path[:-1]:
        d = d.setdefault(k, {})
    d[path[-1]] = value


class SetupServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------ helpers
    RENAMED_ROLES: dict[str, str] = {}                   # new prefix -> old prefix (for future renames)
    RENAMED_EXACT = {"Specialist · Environment Art": "Specialist · Lookdev",   # new name -> old name
                     "Major · Environment Art": "Major · Lookdev"}

    async def _role(self, g: discord.Guild, name, color, hoist, mention, perms=None) -> discord.Role:
        r = discord.utils.get(g.roles, name=name)
        if r:
            return r
        old_exact = self.RENAMED_EXACT.get(name)
        if old_exact and (r := discord.utils.get(g.roles, name=old_exact)):
            await r.edit(name=name, reason="Unrealcraft: renamed")
            return r
        for new, old in self.RENAMED_ROLES.items():
            if name.startswith(new) and (r := discord.utils.get(g.roles, name=old + name[len(new):])):
                await r.edit(name=name, reason="Unrealcraft: renamed")
                return r
        return await g.create_role(name=name, color=C(color) if color else discord.Color.default(), hoist=hoist,
                                   mentionable=mention, permissions=perms or discord.Permissions.none(),
                                   reason="Unrealcraft bootstrap")

    async def _category(self, g, name, overwrites) -> discord.CategoryChannel:
        c = discord.utils.get(g.categories, name=name)
        if c:
            await c.edit(overwrites=overwrites)
            return c
        return await g.create_category(name, overwrites=overwrites, reason="Unrealcraft bootstrap")

    async def _text(self, g, cat, name, overwrites=None, topic=None, news=False):
        ch = discord.utils.get(cat.channels, name=name)
        if ch:
            return ch
        kw = dict(category=cat, topic=topic, reason="Unrealcraft bootstrap")
        if overwrites:
            kw["overwrites"] = {**cat.overwrites, **overwrites}
        if news and "COMMUNITY" in g.features:
            kw["news"] = True
        return await g.create_text_channel(name, **kw)

    async def _is_empty(self, ch: discord.TextChannel) -> bool:
        """True if nobody but bots ever posted there."""
        async for m in ch.history(limit=200):
            if not m.author.bot:
                return False
        return True

    async def _forum_or_text(self, g, cat, name, tags, overwrites=None, topic=None, require_tag=False,
                             reaction=None, report=None):
        ch = discord.utils.get(cat.channels, name=name)
        community = "COMMUNITY" in g.features
        if ch and community and isinstance(ch, discord.TextChannel):
            # Community was switched on after the first bootstrap: swap the text channel for a forum.
            if await self._is_empty(ch):
                await ch.delete(reason="Unrealcraft: replaced by a forum (Community on)")
                if report is not None:
                    report.append(f"#{name}: text → forum")
            else:
                await ch.edit(name=f"{name}-archive", reason="Unrealcraft: kept (had member posts)")
                if report is not None:
                    report.append(f"#{name}: had member posts, renamed to #{name}-archive")
            ch = None
        if ch:
            return ch
        ow = {**cat.overwrites, **(overwrites or {})}
        if community:
            extra = {"default_reaction_emoji": reaction} if reaction else {}
            forum = await g.create_forum(name, category=cat, topic=topic, overwrites=ow,
                                         available_tags=[discord.ForumTag(name=t) for t in tags],
                                         default_sort_order=discord.ForumOrderType.latest_activity,
                                         reason="Unrealcraft bootstrap", **extra)
            if require_tag:
                await forum.edit(require_tag=True)
            return forum
        return await g.create_text_channel(name, category=cat, topic=topic, overwrites=ow,
                                           reason="Unrealcraft bootstrap")

    async def _rename_category(self, g, old: str, new: str) -> None:
        c = discord.utils.get(g.categories, name=old)
        if c and not discord.utils.get(g.categories, name=new):
            await c.edit(name=new, reason="Unrealcraft: renamed")

    async def _move_or_text(self, g, cat, name, old_names=(), topic=None):
        """Find a text channel anywhere (by name or an old name), move/rename it into `cat`; else create it."""
        ch = next((c for n in (name, *old_names) for c in g.text_channels if c.name == n), None)
        if ch:
            if ch.category_id != cat.id or ch.name != name:
                await ch.edit(name=name, category=cat, topic=topic, reason="Unrealcraft: layout")
            return ch
        return await self._text(g, cat, name, topic=topic)

    async def _ensure_tags(self, forum, tags) -> None:
        if not isinstance(forum, discord.ForumChannel):
            return
        have = {t.name for t in forum.available_tags}
        missing = [discord.ForumTag(name=t) for t in tags if t not in have]
        if missing:
            await forum.edit(available_tags=list(forum.available_tags) + missing)

    async def _retire(self, g, cat, names, drop_category=False) -> list[str]:
        """Delete our own obsolete channels (names=None: all in the category), only if no member ever posted."""
        out = []
        if not cat:
            return out
        for ch in list(cat.channels):
            if names is not None and ch.name not in names:
                continue
            if isinstance(ch, discord.TextChannel) and not await self._is_empty(ch):
                out.append(f"kept #{ch.name} (has member messages)")
                continue
            if isinstance(ch, discord.ForumChannel) and ch.threads and any(
                    t.owner_id != g.me.id for t in ch.threads):
                out.append(f"kept #{ch.name} (has member posts)")
                continue
            await ch.delete(reason="Unrealcraft: channel layout simplified")
            out.append(f"removed #{ch.name}")
        if drop_category and not cat.channels:
            await cat.delete(reason="Unrealcraft: channel layout simplified")
        return out

    async def _voice(self, g, cat, name, overwrites=None):
        ch = discord.utils.get(cat.channels, name=name)
        if ch:
            return ch
        return await g.create_voice_channel(name, category=cat, overwrites={**cat.overwrites, **(overwrites or {})},
                                            reason="Unrealcraft bootstrap")

    # ------------------------------------------------------------------ bootstrap
    async def bootstrap(self, g: discord.Guild) -> list[str]:
        report: list[str] = []
        unl = self.bot.unlocks
        data = unl.data
        me = g.me

        # roles ------------------------------------------------------------
        roles: dict[str, discord.Role] = {}
        for name, color, hoist, mention, key in ROLES:
            perms = MOD_PERMS if name == "Mod" else None
            r = await self._role(g, name, color, hoist, mention, perms)
            roles[name] = r
            if key:
                _set(data.setdefault("roles", {}), key, r.id)
        # order: first in ROLES = highest, all below the bot's top role
        top = me.top_role.position
        positions = {}
        for i, (name, *_rest) in enumerate(ROLES):
            positions[roles[name]] = max(1, top - 1 - i)
        try:
            await g.edit_role_positions(positions, reason="Unrealcraft bootstrap")
        except discord.HTTPException as e:
            report.append(f"⚠ could not order roles ({e}). Drag the bot's role to the top.")
        report.append(f"roles: {len(ROLES)} ready")

        R = roles
        rank_roles = {n: R[x] for n, x in ((0, "Greenlit"), (1, "Blockout Artist"), (2, "Gameplay Prototyper"),
                                           (4, "Engineer"), (5, "Systems Architect"), (6, "Studio Lead"))}
        spec = [R[name] for name, *_rest, key in ROLES if key and key[0] == "specialist"]   # by key, not by name
        staff = [R["Mod"], R["Mentor"], R["Curriculum"]]
        everyone = g.default_role
        bot_ow = P(view_channel=True, send_messages=True, manage_messages=True, manage_threads=True,
                   embed_links=True, attach_files=True, read_message_history=True, connect=True)

        def allowed_from(rank: int) -> list[discord.Role]:
            rs = [r for n, r in rank_roles.items() if n >= rank]
            if rank <= 3:
                rs += spec
            return rs + staff

        def gated(rank: int, extra: dict | None = None) -> dict:
            ow = {everyone: P(view_channel=False), me: bot_ow}
            for r in allowed_from(rank):
                ow[r] = P(view_channel=True)
            ow.update(extra or {})
            return ow

        # 00 GATE: read-only essentials, visible to everyone ----------------------
        chans = data.setdefault("channels", {})
        cats = data.setdefault("categories", {})
        gate_ow = {everyone: P(view_channel=True, send_messages=False, add_reactions=True, create_public_threads=False,
                               read_message_history=True, use_application_commands=True),
                   me: bot_ow}
        gate = await self._category(g, "00 · GATE", gate_ow)
        welcome = await self._text(g, gate, "welcome",
                                   topic="Start here. Accept the rules, press Start your first quest (a short rules quiz). "
                                         "Commands only; chat in #general.")
        # Discord greys out the message box where you can't send, which also blocks slash commands. Allow sending
        # in #welcome so /start and /quiz work; plain messages are removed by the bot (commands-only channel).
        await welcome.edit(overwrites={**gate_ow, everyone: P(view_channel=True, send_messages=True,
                                                              add_reactions=True, create_public_threads=False,
                                                              read_message_history=True,
                                                              use_application_commands=True)})
        ann = await self._text(g, gate, "announcements", news=True,       # converted after _community() frees it
                               topic="Raids, events and big news.")
        notes = await self._text(g, gate, "patch-notes", news=True,
                                 topic="What changed on the server, the bot and the curriculum. Posted on every update.")
        resources = await self._move_or_text(g, gate, "epic-games-resources", old_names=("resources",),
                                             topic="Official Epic Games docs and free courses. Every quest's reading comes from here.")
        rankups = await self._move_or_text(g, gate, "rank-ups", topic="Promotions. Posted by the Quartermaster.")
        for c in (resources, rankups):
            await c.edit(overwrites=gate_ow)
        report += await self._retire(g, gate, ["roles", "how-this-place-works"])   # merged into #welcome
        chans.pop("roles_info", None)
        chans.pop("how_this_place_works", None)
        chans.update(welcome=welcome.id, announcements=ann.id, patch_notes=notes.id,
                     resources=resources.id, rank_ups=rankups.id)

        # 01 GUILD HUB: open to everyone who accepted the rules (Rules Screening gates talking).
        # Discord Onboarding needs >= 7 @everyone-visible default channels, 5 of them postable.
        member_ow = P(view_channel=True, send_messages=True, send_messages_in_threads=True,
                      create_public_threads=True, attach_files=True, embed_links=True, add_reactions=True,
                      read_message_history=True, use_application_commands=True, connect=True, speak=True)
        recruit_ow = P(view_channel=True, send_messages=False, send_messages_in_threads=True,
                       create_public_threads=False, add_reactions=True, read_message_history=True,
                       use_application_commands=True, connect=True, speak=True)
        hub_ow = {everyone: member_ow, me: bot_ow}
        await self._rename_category(g, "01 · HUB", "01 · GUILD HUB")
        hub = await self._category(g, "01 · GUILD HUB", hub_ow)
        cats["hub"] = hub.id
        general = await self._text(g, hub, "general")
        intros = await self._text(g, hub, "introductions",
                                  topic="Say hi: your major and one thing you want to build in 3 months.")
        showcase = await self._forum_or_text(
            g, hub, "showcase", SHOWCASE_TAGS, reaction="🔥", report=report,
            topic="Your own map or scene. WIP welcome. Pick a tag. One thing that works, one issue, one next step.")
        helpdesk = await self._forum_or_text(
            g, hub, "help-desk", HELP_TAGS, require_tag=True, report=report,
            topic="Stuck in Unreal, or something broken on the server or with the Quartermaster? Use the buttons "
                  "in the pinned post. Always say your engine version / what you did right before it broke.")
        await self._ensure_tags(helpdesk, HELP_TAGS)
        suggestions = await self._forum_or_text(
            g, hub, "suggestions", ["Server", "Bot", "Quests", "Other"], report=report,
            topic="Ideas for the server, the Quartermaster or the quests. One idea per post; upvote with 👍.")
        for c in (general, intros, showcase, helpdesk, suggestions):
            await c.edit(overwrites=hub_ow)
        chans.update(general=general.id, introductions=intros.id, showcase=showcase.id, help_desk=helpdesk.id,
                     suggestions=suggestions.id)

        # 02 VOICE ROOMS -------------------------------------------------------------
        await self._rename_category(g, "02 · TRAINING GROUNDS", "02 · VOICE ROOMS")
        training = await self._category(g, "02 · VOICE ROOMS", {everyone: P(view_channel=False),
                                                                R["Recruit"]: recruit_ow,
                                                                R["Oriented"]: member_ow, me: bot_ow})
        cats["training"] = training.id
        floor = await self._voice(g, training, "Studio Floor")
        no_connect = {R["Oriented"]: P(view_channel=True, connect=False), R["Recruit"]: P(view_channel=False)}
        await self._voice(g, training, "Pair Program",
                          {**no_connect, **{r: P(connect=True, speak=True) for r in allowed_from(2)}})
        await self._voice(g, training, "Critique Room",
                          {**no_connect, **{r: P(connect=True, speak=True) for r in allowed_from(3)}})
        chans.update(studio_floor_voice=floor.id)

        # 03 WORKSHOP: the quest board + one forum per track, each unlocking at its rank ----------
        # Quests start on the board; lessons arrive through /quest; /submit posts turn-ins into the track forums.
        workshop = await self._category(g, "03 · WORKSHOP", {everyone: P(view_channel=False), me: bot_ow})
        cats["workshop"] = workshop.id
        qb = await self._move_or_text(g, workshop, "quest-board", topic="How quests work and the weekly raid.")
        # send_messages on so slash commands work here; plain chat is removed by the bot (commands-only)
        board_ow = P(view_channel=True, send_messages=True, create_public_threads=False, add_reactions=True,
                     read_message_history=True, use_application_commands=True)
        await qb.edit(overwrites={**workshop.overwrites, R["Recruit"]: board_ow, R["Oriented"]: board_ow})
        chans.update(quest_board=qb.id)
        for old_cat, key, rank, slug in TRACKS:
            forum = await self._forum_or_text(
                g, workshop, slug, ["Turn-in", "WIP", "Help", "Done"], overwrites=gated(rank), report=report,
                topic=f"Rank {rank}+ · Work out loud, ask for help, and see everyone's turn-ins for this track. "
                      "Start a post per thing you're building. Say your engine version.")
            await forum.edit(overwrites={**workshop.overwrites, **gated(rank)})
            cats[key] = forum.id                         # rank-gated area = this forum
            chans.setdefault("tracks", {})[slug] = forum.id
            report += await self._retire(g, discord.utils.get(g.categories, name=old_cat), None, drop_category=True)

        # Specialist Halls were removed: retire the category, its channels and the Specialty permission roles.
        for old_cat in ("03 · SPECIALIST HALLS", "03 · BAYS"):
            report += await self._retire(g, discord.utils.get(g.categories, name=old_cat), None, drop_category=True)
        for r in [r for r in g.roles if r.name.startswith(("Specialty · ", "Seal · "))]:
            await r.delete(reason="Unrealcraft: Specialist Halls removed")
            report.append(f"removed role {r.name}")
        cats.pop("bays", None)
        chans.pop("bays", None)
        data.get("roles", {}).pop("seal", None)
        uar = data.get("unlock_at_rank") or {}
        uar[3] = [x for x in uar.get(3, []) if x != "bays"]

        # 04 STAFF ------------------------------------------------------------
        st = await self._category(g, "04 · STAFF", {everyone: P(view_channel=False), me: bot_ow,
                                                    **{r: P(view_channel=True) for r in staff}})
        modlog = await self._text(g, st, "mod-log")
        wip = await self._text(g, st, "curriculum-wip", overwrites={R["Studio Lead"]: P(view_channel=True)})
        mq = await self._text(g, st, "mentor-queue", overwrites={
            R["Mentor-in-Training"]: P(view_channel=True, send_messages=False),
            R["Systems Architect"]: P(view_channel=True, send_messages=False),
            R["Studio Lead"]: P(view_channel=True)})
        chans.update(mod_log=modlog.id, curriculum_wip=wip.id, mentor_queue=mq.id)

        if "COMMUNITY" in g.features:
            if not discord.utils.get(training.channels, name="Lecture Hall"):
                speakers = [rank_roles[5], rank_roles[6], R["Mentor"], R["Mod"]]
                await g.create_stage_channel("Lecture Hall", category=training, reason="Unrealcraft bootstrap",
                                             overwrites={**training.overwrites,
                                                         R["Recruit"]: P(view_channel=False),
                                                         **{r: P(request_to_speak=True, speak=True) for r in speakers}})
                report.append("Lecture Hall stage created (Architect+ speak)")
            report += await self._community(g, welcome, welcome, qb, helpdesk, showcase, modlog)
            report += await self.onboarding(g)
            # Discord's community-updates channel can't be an announcement channel; _community moved it to #mod-log.
            if isinstance(ann, discord.TextChannel) and not ann.is_news():
                try:
                    await ann.edit(type=discord.ChannelType.news)
                    report.append("#announcements → announcement channel")
                except discord.HTTPException as e:
                    report.append(f"⚠ #announcements conversion: {e}")
        else:
            report.append("Community is off: showcase, help-desk and turn-ins are text channels, and there's no stage.")
        report += await self._remove_defaults(g)
        report += await self.order(g)

        # persist ---------------------------------------------------------------
        data.setdefault("unlock_at_rank", {0: ["hub", "training", "foundations"], 1: ["world_lighting"],
                                           2: ["materials", "blueprint"], 3: ["characters_anim"],
                                           4: ["systems"], 5: ["net_shipping"], 6: []})
        unl.path.write_text("# Written by /admin bootstrap. Safe to edit; bootstrap re-matches by name.\n"
                            + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        report.append("categories + channels ready; IDs written to config/unlocks.yaml")
        return report

    # ------------------------------------------------------------------ community extras
    async def _community(self, g, welcome, manual, quest_board, helpdesk, showcase, modlog) -> list[str]:
        out = []
        try:
            await g.edit(community=True, rules_channel=welcome, public_updates_channel=modlog, safety_alerts_channel=modlog,
                         system_channel=None,
                         reason="Unrealcraft bootstrap")
            out.append("rules channel = #welcome, Discord community updates → #mod-log, join spam off")
        except discord.HTTPException as e:
            out.append(f"⚠ guild settings: {e}")
        try:
            await g.edit_welcome_screen(
                enabled=True,
                description="A Discord RPG for learning Unreal Engine 5. Quests, ranks, real work.",
                welcome_channels=[   # must be readable by @everyone, so GATE channels only
                    discord.WelcomeChannel(channel=welcome, description="Start here: press Start your first quest",
                                           emoji=discord.PartialEmoji(name="🚪")),
                    discord.WelcomeChannel(channel=g.get_channel(self.bot.unlocks.channel("announcements")),
                                           description="Raids, events, new quests",
                                           emoji=discord.PartialEmoji(name="📣")),
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
                rules = [l.split(". ", 1)[1].replace("**", "") for l in
                         (Path_root() / "docs" / "06-community-rules.md").read_text(encoding="utf-8").splitlines()
                         if l[:2].rstrip(".").isdigit()]
                await self.bot.http.request(
                    discord.http.Route("PATCH", "/guilds/{guild_id}/member-verification", guild_id=g.id),
                    json={"enabled": True,
                          "description": "Unrealcraft is a Discord RPG for learning Unreal Engine 5. Read the rules, "
                                         "then press Start your first quest in #welcome.",
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
                    trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.mention_spam,
                                                   mention_limit=6),
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

    async def onboarding(self, g: discord.Guild) -> list[str]:
        """Discord Onboarding (Questions + default channels) and the Server Guide (welcome, to-dos, resources)."""
        out, unl = [], self.bot.unlocks
        ch = lambda key: g.get_channel(unl.channel(key))
        recruit = unl.role("recruit")
        E = discord.PartialEmoji
        prompts = []
        for q in profile.QUESTIONS:
            opts = []
            for ans in q.answers:
                roles = [unl.role("major", ans.value), recruit] if q.key == "major"                     else [unl.role("profile", q.key, ans.value)]
                opts.append(discord.OnboardingPromptOption(title=ans.title, description=ans.description,
                                                           emoji=E(name=ans.emoji), roles=[r for r in roles if r]))
            prompts.append(discord.OnboardingPrompt(type=discord.OnboardingPromptType.multiple_choice,
                                                    title=q.title, single_select=q.single, required=q.required,
                                                    in_onboarding=q.pre_join, options=opts))
        pings = discord.OnboardingPrompt(
            type=discord.OnboardingPromptType.multiple_choice, title="What should we ping you for?",
            single_select=False, required=False, in_onboarding=False,
            options=[
                discord.OnboardingPromptOption(title="Weekly raid", description="One server-wide quest each week",
                                               emoji=E(name="⚔️"), roles=[unl.role("ping", "raid")]),
                discord.OnboardingPromptOption(title="Showcase spotlights", description="Great maps from members",
                                               emoji=E(name="🔥"), roles=[unl.role("ping", "showcase")]),
                discord.OnboardingPromptOption(title="Patch notes", description="New quests and bot changes",
                                               emoji=E(name="📦"), roles=[unl.role("ping", "patch_notes")]),
            ])
        # Default channels must be readable by @everyone: GATE + the open hub. Workshop forums stay rank-locked.
        gate = discord.utils.get(g.categories, name="00 · GATE")
        defaults = [c for c in (gate.channels if gate else []) if isinstance(c, discord.TextChannel)]
        defaults += [c for c in (ch("general"), ch("introductions"), ch("showcase"), ch("help_desk"),
                                 ch("suggestions")) if c]
        try:
            ob = await g.edit_onboarding(prompts=prompts + [pings], default_channels=defaults, enabled=True,
                                         mode=discord.OnboardingMode.advanced, reason="Unrealcraft onboarding")
            out.append(f"onboarding on: {len(prompts) + 1} questions, {len(defaults)} default channels")
        except discord.HTTPException as e:
            out.append(f"⚠ onboarding: {e}")

        # Server Guide (not in discord.py yet: raw route)
        def act(key, title, desc, emoji, chat=False):
            c = ch(key)
            return c and {"channel_id": str(c.id), "action_type": 1 if chat else 0, "title": title,
                          "description": desc, "emoji": {"name": emoji}}
        def res(key, title, desc, emoji):
            c = ch(key) if isinstance(key, str) and key in (unl.data.get("channels") or {}) else                 discord.utils.get(g.channels, name=key)
            return c and {"channel_id": str(c.id), "title": title, "description": desc, "emoji": {"name": emoji}}
        guide = {
            "enabled": True,
            "welcome_message": {
                "author_ids": [str(g.owner_id)],
                "message": "Welcome to Unrealcraft, where you level up by making things in Unreal Engine 5. "
                           "Every rank is earned with real work: quests, quizzes and turn-ins, never by chatting. "
                           "Start with Orientation and the Quartermaster will walk you through it.",
            },
            "new_member_actions": [a for a in (
                act("welcome", "Start your first quest", "Press the green button. It is a short rules quiz.", "🚪"),

                act("introductions", "Say hi with a goal", "Your major + one thing you want to build.", "👋", chat=True),
                act("quest_board", "Find the quest board", "Press Clocked in on the pinned post.", "🗺️"),
                act("help_desk", "Ask for help the right way", "Use the New help post button.", "🛠️"),
            ) if a],
            "resource_channels": [r for r in (
                res("welcome", "How Unrealcraft works", "Start here, commands, ranks and help", "🎖️"),
                res("resources", "Epic Games resources", "Where every quest's reading comes from", "📘"),
                res("announcements", "Announcements", "Raids, events, changes", "📣"),
            ) if r],
        }
        try:
            await self.bot.http.request(
                discord.http.Route("PUT", "/guilds/{guild_id}/new-member-welcome", guild_id=g.id),
                json=guide, reason="Unrealcraft server guide")
            out.append(f"server guide on: {len(guide['new_member_actions'])} to-dos, "
                       f"{len(guide['resource_channels'])} resources")
        except discord.HTTPException as e:
            out.append(f"⚠ server guide: {e}")
        return out

    CATEGORY_ORDER = ["00 · GATE", "01 · GUILD HUB", "02 · VOICE ROOMS", "03 · WORKSHOP",
                      "04 · STAFF"]
    CHANNEL_ORDER = {
        "00 · GATE": ["welcome", "announcements", "patch-notes", "epic-games-resources",
                      "rank-ups"],
        "01 · GUILD HUB": ["general", "introductions", "showcase", "help-desk", "suggestions"],
        "03 · WORKSHOP": ["quest-board", "foundations", "world-lighting", "materials", "blueprint", "characters-anim"],
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
            current = sorted(present, key=lambda ch: ch.position)
            if current != present:                       # only touch categories that are out of order
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

    # ------------------------------------------------------------------ pins
    # ------------------------------------------------------------------ pinned messages
    # One pinned bot message per purpose. Updates EDIT that message in place (never re-post), so channels stay clean.
    # kv(user 0) "pin:<key>" = "<channel_id>:<message_id>:<content hash>"

    TRACK_ABOUT = {
        "foundations": (0, "the Starter Quests: install, editor basics, your first room, light, material and Blueprint."),
        "world-lighting": (1, "blockouts, landscapes, foliage and lighting that makes spaces readable."),
        "materials": (2, "the Material Editor, instances, PBR, landscape materials and decals."),
        "blueprint": (2, "Actor Blueprints, triggers, timelines, interfaces: making things play."),
        "characters-anim": (3, "characters, Animation Blueprints, montages and retargeting."),
    }

    def pin_specs(self, g: discord.Guild) -> list[dict]:
        from .onboarding import BugReportButton, ClockInButton, HelpPostButton, StartButton
        from .quiz import QuizButton
        from .quests import NextQuestButton
        QuestBoardButton = lambda: NextQuestButton("Continue your quest")
        from .workshop import NewPostButton
        unl, cat = self.bot.unlocks, self.bot.catalog
        ch = lambda *k: g.get_channel(unl.channel(*k))

        def view(*items):
            v = discord.ui.View(timeout=None)
            for item in items:
                v.add_item(item)
            return v

        rules = (Path_root() / "docs" / "06-community-rules.md").read_text(encoding="utf-8").split("\n", 2)[2].strip()
        E = lambda title, text, color="#7A8C7E": discord.Embed(title=title, description=text, color=C(color))
        rank_lines = "\n".join(f"**{r['title']}** → {r.get('opens', '—')}" for r in cat.meta["ranks"])
        rule_lines = "\n".join(f"{i}. {r}" for i, r in enumerate(
            [ln.split(". ", 1)[1].replace("**", "") for ln in rules.splitlines() if ln[:2].rstrip(".").isdigit()], 1))
        welcome_page = [
            E("👋 Welcome to Unrealcraft",
              "Learn **Unreal Engine 5** by doing quests.\n"
              "Finish quests → get XP → rank up → new channels open.\n"
              "Chatting does **not** give XP. Only finished work does."),
            E("🚀 Start here: 3 steps",
              "**1.** Press the green button below. Your first quest is a short quiz about the rules.\n"
              "**2.** Then do the other small steps. There is always a button for the next one.\n"
              "**3.** When you finish, go to **#quest-board**. After Orientation, quests only work there.", "#3D7DD8"),
            E("⌨️ 5 commands",
              "`/quest` : your next task\n"
              "`/quiz` : answer questions about a quest\n"
              "`/submit` : send your finished work\n"
              "`/rank` : see your level and XP\n"
              "`/path` : see all your quests\n"
              "Lost? Type `/where`.", "#B5714B"),
            E("🗺️ What opens when",
              "You only see channels you have unlocked.\n"
              "**Everyone:** GATE and Guild Hub channels.\n"
              "**After your first quest:** #quest-board and Voice Rooms.\n" + rank_lines, "#8E6CCF"),
            E("🆘 Need help?",
              "Go to #help-desk.\n"
              "🛠️ **Unreal help**: a problem in Unreal or with a quest.\n"
              "🐞 **Server / bot problem**: something here is broken.", "#D9824A"),
            E("📜 Rules", rule_lines, "#D4AF37"),
        ]

        specs = [
            dict(key="welcome", channel=ch("welcome"), embeds=welcome_page,
                 view=view(StartButton())),
            dict(key="quest-board", channel=ch("quest_board"), view=view(QuestBoardButton(), ClockInButton()), content=(
                "**📋 Quest board**\n"
                "Type `/quest` to get your next task. Each quest has:\n"
                "• a link to the official Epic docs\n• a short checklist\n• a quiz\n• then `/submit` to send your work\n\n"
                "**This is your home for quests.** After Orientation, quests only work in this channel.\n"
                "Press **Continue your quest** any time to get your next task.\n"
                "New quests and weekly events are posted here.")),
            dict(key="how-to-ask", channel=ch("help_desk"), title="How to get help", tag="Discord-help",
                 view=view(HelpPostButton(), BugReportButton()), content=(
                     "**Two kinds of help, one desk**\n"
                     "🛠️ **Unreal help**: stuck on a quest or in the editor. The form asks for your engine version, "
                     "what you tried and expected vs actual.\n"
                     "🐞 **Server / bot problem**: a command failed, a channel or role looks wrong, a quest won't tick, "
                     "or something broke after an update. The form asks what you did, what happened and when. "
                     "Staff get notified and compare it with #patch-notes.\n\n"
                     "❌ \"lighting broken help\"\n✅ \"5.8 · Level Design · Tried raising Sky Light intensity · "
                     "[screenshot] · Expected a lit interior, got black walls\"")),
            dict(key="wip-feedback", channel=ch("showcase"), title="How to give WIP feedback", tag="WIP", content=(
                "**How to give WIP feedback**\nOne thing that works · one specific issue · one next step.\n"
                "Want critique? Tag your post **Critique-wanted**.\n"
                "React 🔥 👀 or 🧱 on anything you looked at. Five 🔥 on your post earns +25 XP (once a week).")),
            dict(key="resources", channel=ch("resources"), content=(
                "**Epic Games resources**: the official docs and free courses every quest links to.\n"
                "• Get Started: https://dev.epicgames.com/documentation/en-us/unreal-engine/get-started\n"
                "• Your First Hour: https://dev.epicgames.com/documentation/en-us/unreal-engine/first-hour-in-unreal-engine\n"
                "• Level Designer Quick Start: https://dev.epicgames.com/documentation/en-us/unreal-engine/level-designer-quick-start-in-unreal-engine\n"
                "• Programming Quick Start: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-cpp-quick-start\n"
                "• Materials: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-materials\n"
                "• Blueprints: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine")),
        ]
        for slug, (rank, what) in self.TRACK_ABOUT.items():
            title = cat.ranks.get(rank, {}).get("title", f"Rank {rank}")
            specs.append(dict(key=f"about-{slug}", channel=ch("tracks", slug), title=f"About #{slug}", tag="Help",
                              view=view(NewPostButton(slug)), content=(
                f"**#{slug}** opens at **{title}** (rank {rank}).\n"
                f"**What it covers:** {what}\n"
                "**Post here:** press **New post** below (or type `/post`): one thread per thing you're building "
                "(tag WIP), questions about these quests (tag Help).\n"
                "**Turn-ins:** when you `/submit` a quest from this track, the Quartermaster posts it here (tag "
                "Turn-in) so people can see it and cheer it on.")))
        return [s for s in specs if s["channel"]]

    @staticmethod
    def _fingerprint(spec: dict) -> str:
        import hashlib
        raw = (spec.get("content") or "") + "".join(str(e.to_dict()) for e in spec.get("embeds") or [])
        raw += "".join(i.custom_id or "" for i in (spec["view"].children if spec.get("view") else []))
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
                if isinstance(chan, discord.ForumChannel):
                    tag = discord.utils.get(chan.available_tags, name=spec.get("tag", "")) or \
                        (chan.available_tags[:1] or [None])[0]
                    # Forums allow ONE pinned post: unpin old bot posts first (cleanup_bot_posts deletes them).
                    for t in chan.threads:
                        if t.flags.pinned and t.owner_id == g.me.id:
                            await t.edit(pinned=False)
                    created = await chan.create_thread(name=spec.get("title", key), content=spec.get("content"),
                                                       embeds=spec.get("embeds") or [], view=spec.get("view"),
                                                       applied_tags=[tag] if tag else [])
                    await created.thread.edit(pinned=True)
                    mid = created.thread.id
                else:
                    m = await chan.send(content=spec.get("content"), embeds=spec.get("embeds") or [],
                                        view=spec.get("view"))
                    await m.pin()
                    mid = m.id
                out.append(f"posted {key}")
            await self.bot.db.kv_set(0, f"pin:{key}", f"{chan.id}:{mid}:{fp}")
        return out

    async def cleanup_bot_posts(self, g: discord.Guild) -> list[str]:
        """Delete every message/thread the bot posted except the tracked pins and real member activity
        (turn-ins, /post threads, help posts, #rank-ups cards, staff channels)."""
        cur = await self.bot.db.conn.execute("SELECT k, v FROM kv WHERE user_id=0 AND k LIKE 'pin:%'")
        keep = set()
        for row in await cur.fetchall():
            parts = (row["v"] or "").split(":")
            if len(parts) == 3:
                keep.add(int(parts[1]))
            else:                                   # old-style flag from before pins were tracked
                await self.bot.db.conn.execute("DELETE FROM kv WHERE user_id=0 AND k=?", (row["k"],))
        await self.bot.db.conn.commit()
        unl = self.bot.unlocks
        skip = {unl.channel(k) for k in ("rank_ups", "mentor_queue", "mod_log", "curriculum_wip", "patch_notes",
                                          "announcements")}
        member_markers = ("<@",)            # any bot thread that mentions a member is that member's post
        removed = 0
        for chan in g.channels:
            if chan.id in skip:
                continue
            if isinstance(chan, discord.TextChannel):
                async for m in chan.history(limit=200):
                    if m.author.id == g.me.id and m.id not in keep:
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
                        if any(mk in starter.content for mk in member_markers):
                            continue                # a member's post made through the bot
                    except discord.HTTPException:
                        pass
                    await t.delete()
                    removed += 1
        return [f"cleaned up {removed} old bot posts"]

    @staticmethod
    def patch_embed(rel: dict) -> discord.Embed:
        """One embed per version: the summary line as description, each '### Section' as a field."""
        import re
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
    admin = app_commands.Group(name="setup", description="Owner: build the server",
                               default_permissions=discord.Permissions(administrator=True))

    @admin.command(name="sync-pins", description="Update pinned messages in place and remove stray bot posts.")
    async def sync_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        rep = await self.sync_pins(itx.guild) + await self.cleanup_bot_posts(itx.guild)
        await itx.followup.send("\n".join(rep) or "Everything up to date.", ephemeral=True)

    @admin.command(name="patch-notes", description="Post pushed versions missing from #patch-notes (re-posts the latest).")
    async def patch_notes_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        v = await self.post_patch_notes(itx.guild, force_latest=True)
        await itx.followup.send(f"Posted {', '.join(v)}." if v else "Nothing to post: no version tag pushed to GitHub yet, or #patch-notes is missing.",
                                ephemeral=True)

    @admin.command(name="bootstrap", description="Create/repair roles, channels and pins. Only removes the bot's own leftovers.")
    async def bootstrap_cmd(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        rep = await self.bootstrap(itx.guild)
        rep += await self.sync_pins(itx.guild) + await self.cleanup_bot_posts(itx.guild)
        await itx.followup.send("\n".join(rep)[:1900], ephemeral=True)


def Path_root():
    from ..config import BOT_ROOT
    return BOT_ROOT.parent


async def setup(bot):
    await bot.add_cog(SetupServer(bot))
