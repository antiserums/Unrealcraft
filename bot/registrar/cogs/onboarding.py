"""Orientation (O1–O8), /start, /help-server, /where, first-week DMs."""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import checks, profile
from ..config import SIGNOFF

log = logging.getLogger("registrar.onboarding")

VOICE_SECONDS = 60
HELP_FIELDS = ("Engine version", "Major", "What I tried", "Screenshot of graph or Details", "Expected vs actual")

WHERE = {
    "submit": ("/submit", "Pick the quest id, paste your proof, attach a screenshot. Pass the quiz first if it has one."),
    "ask for help": ("#help-desk", "Press **Unreal help** on the pin. The form fills in the template for you."),
    "see my rank": ("/rank", "Your card: XP bar, streak, next unlock, medals. /path shows the whole tree."),
    "find C++": ("/path", "C++ is a Rank 4 track for code-leaning majors. Everyone gets S11 and a taster. It's on the ◇ optional shelf."),
    "showcase": ("#showcase", "Your own map, WIP welcome. Use a tag. 5×🔥 gets +25 XP once a week."),
    "change major": ("/major", "One free change before Rank 3. After that it costs 4 quests at your rank."),
    "report a bug": ("#help-desk", "Press **Server / bot problem** on the pin. Staff get notified."),
    "what changed": ("#patch-notes", "Every server, bot and quest update is written up there."),
}


class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._voice_tasks: dict[int, asyncio.Task] = {}
        self.first_week.start()

    def cog_unload(self):
        self.first_week.cancel()

    @property
    def cat(self):
        return self.bot.catalog

    # ------------------------------------------------------------ helpers
    async def mark(self, guild: discord.Guild | None, uid: int, qid: str) -> None:
        """Complete an action-verified Orientation quest (idempotent)."""
        if qid not in self.cat.quests:
            return
        if qid in await self.bot.db.done_set(uid):
            return
        await self.bot.get_cog("Quests").complete(guild, uid, qid)

    async def fact(self, guild: discord.Guild | None, uid: int, name: str) -> None:
        """Record something the bot saw, then (in the background, so interactions stay under 3s) complete any
        quest whose checklist is now fully verified."""
        if await self.bot.db.add_fact(uid, name):
            asyncio.create_task(self._auto_complete(guild, uid))

    async def _auto_complete(self, guild: discord.Guild | None, uid: int) -> None:
        facts = await self.bot.db.facts(uid)
        u = await self.bot.db.user(uid)
        done = await self.bot.db.done_set(uid)
        for q in self.cat.quests.values():
            if q.id in done or q.rank > max(u["rank"], 0) or q.raw.get("verify_type") != "action":
                continue
            if checks.fully_auto(q) and not checks.facts_missing(q, facts):
                await self.mark(guild, uid, q.id)

    async def rules_ok(self, member: discord.Member | None) -> bool:
        """Rules Screening: a pending member hasn't clicked 'I've read and agree' yet."""
        return bool(member) and not member.pending

    async def maybe_finish_orientation(self, guild: discord.Guild | None, uid: int) -> None:
        u = await self.bot.db.user(uid)
        if u["rank"] >= 0:
            return
        done = await self.bot.db.done_set(uid)
        if all(q.id in done for q in self.cat.orientation()):
            guild = guild or self.bot.get_guild(self.bot.settings.guild_id or 0)
            if guild:
                await self.bot.get_cog("Ranks").promote(guild, uid, 0)   # Oriented + Greenlit + S1 in DM

    def orientation_embed(self, done: set[str], facts: set[str]) -> discord.Embed:
        """Simple-English checklist: progress bar, one 'Next' line, one short line per step."""
        steps = self.cat.orientation()
        n_done = sum(q.id in done for q in steps)
        bar = "🟩" * n_done + "⬜" * (len(steps) - n_done)
        nxt = next((q for q in steps if q.id not in done), None)
        lines = []
        for i, q in enumerate(steps, 1):
            its = checks.items(q)
            part = ""
            if q.id not in done and len(its) > 1:            # e.g. O3: 1/3 commands used
                ok = sum(it.kind == "fact" and it.fact_ok(facts) for it in its)
                part = f" ({ok}/{len(its)})"
            mark = "✅" if q.id in done else ("👉" if q is nxt else "⬜")
            text = q.raw["title"] if q.id in done else f"**{q.raw['title']}**{part}: {q.raw.get('step', '')}"
            lines.append(f"{mark} {i}. {text}")
        desc = f"{bar}  **{n_done} of {len(steps)} done**\n\n" + "\n".join(lines)
        if nxt:
            desc += "\n\nThe bot checks each step for you. Come back and press **Start Orientation** to see this again."
        else:
            desc += "\n\n🎉 **All done!** Type `/quest` to get your first Unreal quest."
        return discord.Embed(title="🧭 Orientation: 8 small steps", description=desc,
                             color=discord.Color.from_str("#7A8C7E"))

    def orientation_view(self, done: set[str]) -> discord.ui.View | None:
        """Buttons for the steps that can be done with a click."""
        from .quiz import QuizButton
        v = discord.ui.View(timeout=None)
        if "O1" not in done:
            v.add_item(QuizButton("O1"))
        if "O7" not in done:
            v.add_item(SkipVoiceButton())
        return v if v.children else None

    # ------------------------------------------------------------ commands
    @app_commands.command(name="start", description="Begin Orientation.")
    async def start(self, itx: discord.Interaction):
        await self.begin(itx)

    async def begin(self, itx: discord.Interaction) -> None:
        """Shared by /start and the #welcome Start button. Recruit role = can see Hub + Training during Orientation."""
        u = await self.bot.db.user(itx.user.id)
        member = itx.guild.get_member(itx.user.id) if itx.guild else None
        if not await self.rules_ok(member):
            await itx.response.send_message(
                "First, accept the rules. Look at the bottom of the chat and press **Complete** / "
                "**I've read and agree**. Then press **Start Orientation** again.", ephemeral=True)
            return
        await self.bot.db.add_fact(itx.user.id, "rules.accepted")
        if member:
            await self.sync_profile(member)
        if u["rank"] < 0 and member:
            recruit = itx.guild.get_role(self.bot.unlocks.role("recruit"))
            if recruit and recruit not in member.roles:
                try:
                    await member.add_roles(recruit, reason="Started Orientation")
                except discord.Forbidden:
                    log.error("Can't add Recruit role; bot role too low?")
        done = await self.bot.db.done_set(itx.user.id)
        facts = await self.bot.db.facts(itx.user.id)
        kw = {"view": v} if (v := self.orientation_view(done)) else {}
        await itx.response.send_message(embed=self.orientation_embed(done, facts), ephemeral=True, **kw)

    @app_commands.command(name="help-server", description="How this server works in 30 seconds.")
    async def help_server(self, itx: discord.Interaction):
        await itx.response.send_message(
            "**The loop:** /quest → do it in-engine → /quiz → /submit → XP → rank-up → new rooms.\n"
            "**Five commands:** /quest · /quiz · /submit · /rank · /path\n"
            "**Stuck, or something broken?** #help-desk. **Lost?** /where. **What changed?** #patch-notes\n"
            "Chat doesn't earn XP. Finished work does.", ephemeral=True)

    async def _where_ac(self, itx: discord.Interaction, current: str):
        return [app_commands.Choice(name=k, value=k) for k in WHERE if current.lower() in k][:25]

    @app_commands.command(name="where", description="Where do I… ?")
    @app_commands.autocomplete(thing=_where_ac)
    async def where(self, itx: discord.Interaction, thing: str):
        target, line = WHERE.get(thing, ("/help-server", "Not sure. Start here."))
        await itx.response.send_message(f"**{target}**: {line}", ephemeral=True)

    @app_commands.command(name="skip-voice", description="Skip the voice step of Orientation (O7).")
    async def skip_voice(self, itx: discord.Interaction):
        await self.fact(itx.guild, itx.user.id, "cmd.skip_voice")
        await itx.response.send_message("Voice step skipped. You can join Studio Floor any time.", ephemeral=True)

    # ------------------------------------------------------------ listeners
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild.id != self.bot.settings.guild_id:
            return
        if before.pending and not after.pending:                # Rules Screening accepted
            await self.fact(after.guild, after.id, "rules.accepted")
            try:
                await after.send("Rules accepted. Welcome to Unrealcraft. Press **Start Orientation** in #welcome.\n"
                                 + SIGNOFF)
            except discord.HTTPException:
                pass
        if after.nick and after.nick != before.nick and "|" in after.nick:
            await self.fact(after.guild, after.id, "nick.major")
        if set(after.roles) != set(before.roles):
            await self.sync_profile(after)
        if after.flags.completed_onboarding and not before.flags.completed_onboarding:
            await self.send_path_dm(after)

    async def sync_profile(self, member: discord.Member) -> dict:
        """Onboarding answers arrive as hidden roles. Mirror them into the DB (kv 'profile').
        The major is only taken from roles while the member is new; after that /major is the only way."""
        prof = profile.profile_from_roles({r.name for r in member.roles})
        await self.bot.db.kv_set(member.id, "profile", json.dumps(prof))
        u = await self.bot.db.user(member.id)
        majors = prof.get("majors") or []
        if majors and u["rank"] <= 0 and not await self.bot.db.kv_get(member.id, "major_set"):
            if len(majors) == 1:
                await self.bot.db.set_user(member.id, major=majors[0])
                await self.bot.db.kv_set(member.id, "major_set", "1")
                await self.fact(member.guild, member.id, "cmd.major")
            else:
                await self.ask_primary_major(member, majors)
        return prof

    async def ask_primary_major(self, member: discord.Member, majors: list[str]) -> None:
        """Several 'what do you want to learn' answers: ask once which one is the main path."""
        if await self.bot.db.kv_get(member.id, "primary_asked") == ",".join(sorted(majors)):
            return
        await self.bot.db.kv_set(member.id, "primary_asked", ",".join(sorted(majors)))
        titles = [self.cat.majors.get(m, {}).get("title", m) for m in majors]
        v = discord.ui.View(timeout=None)
        for m in majors[:5]:
            v.add_item(PrimaryMajorButton(m, self.cat.majors.get(m, {}).get("title", m)))
        try:
            await member.send(
                f"You picked **{', '.join(titles)}**. Which one is your **main path**? That becomes your major "
                "(~70% of your quests after the Starter Quests). The others stay as interests: their quests get "
                "suggested first. You can change your major once for free with `/major`.", view=v)
        except discord.HTTPException:
            pass

    async def send_path_dm(self, member: discord.Member) -> None:
        """One DM after Discord onboarding: what the bot did with their answers."""
        if await self.bot.db.kv_get(member.id, "path_dm_sent"):
            return
        prof = await self.sync_profile(member)
        await self.bot.db.kv_set(member.id, "path_dm_sent", "1")
        cat = self.cat
        lines = ["**Your Unrealcraft path**"]
        majors = prof.get("majors") or ["undecided"]
        major = majors[0] if len(majors) == 1 else (await self.bot.db.user(member.id))["major"]
        if len(majors) > 1 and not await self.bot.db.kv_get(member.id, "major_set"):
            names = ", ".join(cat.majors.get(m, {}).get("title", m) for m in majors)
            lines.append(f"• You want to learn **{names}**. Pick your **main path** with the buttons I sent; "
                         "the others stay as interests.")
        else:
            lines.append(f"• Major: **{cat.majors.get(major, {}).get('title', major)}**. "
                         "~70% of your quests after the Starter Quests are for this. Change it once for free with /major.")
        if major == "undecided" and (sug := profile.suggested_major(prof)):
            lines.append(f"• Your curiosities point at **{cat.majors[sug]['title']}**. Try it with `/major`.")
        if profile.can_test_out(prof):
            lines.append("• You've used Unreal before, so you can **test out** of Starter Quests: "
                         "pass the quiz on the first try and the quest completes without a turn-in.")
        if prof.get("code") in ("none", "blueprint"):
            lines.append("• Code stays optional: your one code taster will be the GAS read-through, not C++.")
        elif prof.get("code") in ("some", "cpp"):
            lines.append("• You code, so your taster will be Hello, C++, and C++ electives get suggested first.")
        if prof.get("curious"):
            lines.append("• Curious about " + ", ".join(prof["curious"]) + ": those electives show up first "
                         "in /quest and on your /path shelf.")
        if prof.get("pace"):
            lines.append(f"• Pace: ~{profile.PACE_HOURS[prof['pace']]:g} h/week. /quest will estimate "
                         "how far your next rank is at that pace.")
        lines.append("Next: press **Start Orientation** in #welcome.")
        try:
            await member.send("\n".join(lines) + "\n" + SIGNOFF)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        """Only author + channel are used (no Message Content intent)."""
        if m.author.bot or not m.guild or m.guild.id != self.bot.settings.guild_id:
            return
        if m.channel.id == self.bot.unlocks.channel("welcome") and m.type == discord.MessageType.default:
            # commands-only channel: slash commands aren't messages, so anything posted here is plain chat
            try:
                await m.delete()
                await m.channel.send(f"{m.author.mention} #welcome is for commands like `/start` and `/quiz O1`. "
                                     "Chat in #general!", delete_after=8,
                                     allowed_mentions=discord.AllowedMentions(users=True))
            except discord.HTTPException:
                pass
            return
        key = self._channel_key(m.channel.id) or self._channel_key(getattr(m.channel, "parent_id", 0) or 0)
        if key:
            await self.fact(m.guild, m.author.id, f"msg.{key}")

    def _channel_key(self, cid: int) -> str | None:
        if not cid:
            return None
        for k, v in (self.bot.unlocks.data.get("channels") or {}).items():
            if v == cid:
                return k
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        floor = self.bot.unlocks.channel("studio_floor_voice")
        if after.channel and after.channel.id == floor and member.id not in self._voice_tasks:
            async def wait():
                await asyncio.sleep(VOICE_SECONDS)
                if member.voice and member.voice.channel and member.voice.channel.id == floor:
                    await self.fact(member.guild, member.id, "voice.studio_floor")
                self._voice_tasks.pop(member.id, None)
            self._voice_tasks[member.id] = asyncio.create_task(wait())
        elif (not after.channel or after.channel.id != floor) and member.id in self._voice_tasks:
            self._voice_tasks.pop(member.id).cancel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, p: discord.RawReactionActionEvent):
        showcase = self.bot.unlocks.channel("showcase")
        guild = self.bot.get_guild(p.guild_id) if p.guild_id else None
        if not guild or p.user_id == self.bot.user.id:
            return
        ch = guild.get_channel_or_thread(p.channel_id)
        in_showcase = ch and (ch.id == showcase or getattr(ch, "parent_id", None) == showcase)
        if not in_showcase:
            return
        author = p.message_author_id or getattr(ch, "owner_id", None)
        if author and author not in (p.user_id, self.bot.user.id):
            await self.fact(guild, p.user_id, "react.showcase")
        # Phase 3: count 🔥 toward the showcase bonus (5 reactions, +25, 1/week) for ch.owner_id

    # ------------------------------------------------------------ first week DMs
    @tasks.loop(hours=6)
    async def first_week(self):
        """Day 0 map (sent by promote to Greenlit), day 1 nudge, day 3 sample submit. Stops after S1."""
        db = self.bot.db
        cur = await db.conn.execute(
            "SELECT discord_id, onboarding_day, created_at, on_leave FROM users WHERE rank <= 0 AND onboarding_day < 3")
        for row in await cur.fetchall():
            if row["on_leave"] or "S1" in await db.done_set(row["discord_id"]):
                continue
            age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(row["created_at"])).days
            step = 3 if age >= 3 else (1 if age >= 1 else 0)
            if step <= row["onboarding_day"]:
                continue
            prof = json.loads(await db.kv_get(row["discord_id"], "profile") or "{}")
            # Fewer nudges for people who said they're light on time or already know Unreal.
            if step == 1 and (prof.get("pace") == "light" or profile.can_test_out(prof)):
                await db.set_user(row["discord_id"], onboarding_day=1)
                continue
            msg = {
                1: "Day 1 check-in: run `/quest` and it gives you one 5–10 minute step. That's all for today.",
                3: "Day 3: here's what a turn-in looks like.\n`/submit quest:S6 proof:\"Doorway 140 wide, ceiling 300\"` "
                   "+ one screenshot. Honor system at this rank.",
            }[step]
            try:
                user = await self.bot.fetch_user(row["discord_id"])
                await user.send(f"{msg}\n{SIGNOFF}")
            except discord.HTTPException:
                pass
            await db.set_user(row["discord_id"], onboarding_day=step)

    @first_week.before_loop
    async def _wait_ready(self):
        await self.bot.wait_until_ready()


# ---------------------------------------------------------------- persistent views
class ClockInButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uu:clockin"):
    """Posted once on the #quest-board pin by the owner (Phase 2 /admin post-pins)."""

    def __init__(self):
        super().__init__(discord.ui.Button(label="I found it", emoji="✅", style=discord.ButtonStyle.success,
                                           custom_id="uu:clockin"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Onboarding").fact(itx.guild, itx.user.id, "btn.clockin")
        await itx.response.send_message("✅ Step done! New quests and weekly events are posted here.", ephemeral=True)


class HelpPostButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uu:helppost"):
    """Pinned in #help-desk. Opens a modal that creates a forum post with the template filled in.
    This handles O6 without the Message Content intent."""

    def __init__(self):
        super().__init__(discord.ui.Button(label="Unreal help", emoji="🛠️", style=discord.ButtonStyle.primary,
                                           custom_id="uu:helppost"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.response.send_modal(HelpModal())


TAG_WORDS = {
    "Blueprint": ("blueprint", "bp_", "node", "graph", "cast"), "C++": ("c++", "cpp", "uclass", "compile", "visual studio"),
    "Materials": ("material", "shader", "texture"), "Animation": ("anim", "montage", "skeleton", "retarget"),
    "Lighting": ("light", "lumen", "shadow", "exposure", "dark"), "Level Design": ("level", "blockout", "layout", "nav"),
    "Packaging": ("package", "build", "cook", "shipping"),
}


def _guess_tag(forum: discord.ForumChannel, text: str, orienting: bool):
    """Pick a forum tag from keywords (Discord-help while in Orientation). The poster can change it."""
    name = "Discord-help"
    if not orienting:
        low = text.lower()
        name = next((t for t, words in TAG_WORDS.items() if any(w in low for w in words)), "Discord-help")
    return discord.utils.get(forum.available_tags, name=name)


class HelpModal(discord.ui.Modal, title="Help-desk post"):
    title_ = discord.ui.TextInput(label="Title (the problem in a few words)", max_length=90)
    version = discord.ui.TextInput(label="Engine version", placeholder="5.x", max_length=12)
    tried = discord.ui.TextInput(label="What I tried", style=discord.TextStyle.paragraph, max_length=800)
    expected = discord.ui.TextInput(label="Expected vs actual", style=discord.TextStyle.paragraph, max_length=600)
    shot = discord.ui.TextInput(label="Screenshot link (or attach in thread after)", required=False, max_length=300)

    async def on_submit(self, itx: discord.Interaction):
        bot = itx.client
        forum = itx.guild.get_channel(bot.unlocks.channel("help_desk"))
        u = await bot.db.user(itx.user.id)
        major = bot.catalog.majors.get(u["major"], {}).get("title", u["major"])
        body = (f"**Engine version:** {self.version}\n**Major:** {major}\n**What I tried:** {self.tried}\n"
                f"**Screenshot:** {self.shot or 'attached below'}\n**Expected vs actual:** {self.expected}\n"
                f"— posted by {itx.user.mention}")
        if isinstance(forum, discord.ForumChannel):
            tag = _guess_tag(forum, f"{self.title_} {self.tried} {self.expected}", u["rank"] < 0)
            thread = (await forum.create_thread(name=str(self.title_), content=body,
                                                applied_tags=[tag] if tag else [])).thread
        elif isinstance(forum, discord.TextChannel):          # Community off: message + thread
            msg = await forum.send(f"**{self.title_}**\n{body}")
            thread = await msg.create_thread(name=str(self.title_)[:90])
            await thread.add_user(itx.user)
        else:
            await itx.response.send_message("help-desk isn't set up yet.", ephemeral=True)
            return
        await bot.db.set_user(itx.user.id, ue_version=str(self.version))
        await bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "thread.help_desk")
        await itx.response.send_message(f"Posted: {thread.mention}. Add your screenshot there.", ephemeral=True)


class BugReportButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:bugreport"):
    """Pinned in #help-desk next to Unreal help: reports a server/bot problem (not an Unreal question)."""

    def __init__(self):
        super().__init__(discord.ui.Button(label="Server / bot problem", emoji="🐞",
                                           style=discord.ButtonStyle.secondary, custom_id="uc:bugreport"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.response.send_modal(BugModal())


class BugModal(discord.ui.Modal, title="Server / bot problem"):
    what = discord.ui.TextInput(label="What were you doing?", max_length=300,
                                placeholder="e.g. Ran /submit S6 with a screenshot")
    happened = discord.ui.TextInput(label="What happened instead?", style=discord.TextStyle.paragraph,
                                    max_length=800, placeholder="Exact error text or what looked wrong")
    expected = discord.ui.TextInput(label="What did you expect?", style=discord.TextStyle.paragraph,
                                    max_length=500)
    where = discord.ui.TextInput(label="Where and when?", max_length=200, required=False,
                                 placeholder="Channel, command, rough time (e.g. #foundations, 8pm)")

    async def on_submit(self, itx: discord.Interaction):
        bot = itx.client
        forum = itx.guild.get_channel(bot.unlocks.channel("help_desk"))
        version = bot.release.get("version", "unknown") if getattr(bot, "release", None) else "unknown"
        body = (f"🐞 **Server / bot problem** reported by {itx.user.mention}\n"
                f"**Doing:** {self.what}\n**Happened:** {self.happened}\n**Expected:** {self.expected}\n"
                f"**Where/when:** {self.where or 'not given'}\n**Bot version:** {version}")
        title = f"[Bug] {str(self.what)[:80]}"
        if isinstance(forum, discord.ForumChannel):
            tag = discord.utils.get(forum.available_tags, name="Server / Bot issue")
            thread = (await forum.create_thread(name=title, content=body, applied_tags=[tag] if tag else [],
                                                allowed_mentions=discord.AllowedMentions.none())).thread
            await thread.add_user(itx.user)
        else:
            await itx.response.send_message("help-desk isn't set up yet.", ephemeral=True)
            return
        log_ch = itx.guild.get_channel(bot.unlocks.channel("mod_log"))
        if log_ch:
            await log_ch.send(f"🐞 New server/bot report from {itx.user.mention}: {thread.mention}",
                              allowed_mentions=discord.AllowedMentions.none())
        await bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "thread.help_desk")
        await itx.response.send_message(f"Reported: {thread.mention}. Staff have been notified. Thanks!",
                                        ephemeral=True)


class PrimaryMajorButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:primary:(?P<m>[a-z_]+)"):
    """DM button: choose the main path when several 'what do you want to learn' answers were picked."""

    def __init__(self, major: str, label: str = ""):
        super().__init__(discord.ui.Button(label=(label or major)[:80], style=discord.ButtonStyle.primary,
                                           custom_id=f"uc:primary:{major}"))
        self.major = major

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(match["m"])

    async def callback(self, itx: discord.Interaction):
        bot = itx.client
        if await bot.db.kv_get(itx.user.id, "major_set"):
            await itx.response.send_message("Your main path is already set. Use `/major` in the server to change it.",
                                            ephemeral=True)
            return
        await bot.db.set_user(itx.user.id, major=self.major)
        await bot.db.kv_set(itx.user.id, "major_set", "1")
        guild = bot.get_guild(bot.settings.guild_id or 0)
        await bot.get_cog("Onboarding").fact(guild, itx.user.id, "cmd.major")
        title = bot.catalog.majors.get(self.major, {}).get("title", self.major)
        await itx.response.edit_message(content=f"Main path set: **{title}**. The other picks stay as interests. "
                                                "Next: press **Start Orientation** in #welcome.", view=None)


class SkipVoiceButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:skipvoice"):
    """Orientation step 7 without typing /skip-voice."""

    def __init__(self):
        super().__init__(discord.ui.Button(label="Skip voice", emoji="🔇", style=discord.ButtonStyle.secondary,
                                           custom_id="uc:skipvoice"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.skip_voice")
        await itx.response.send_message("✅ Voice step skipped. You can join Studio Floor any time.", ephemeral=True)


class StartButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uu:start"):
    """Pinned in #welcome."""

    def __init__(self):
        super().__init__(discord.ui.Button(label="Start Orientation", style=discord.ButtonStyle.success,
                                           custom_id="uu:start"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Onboarding").begin(itx)


class HonorButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uu:honor:(?P<qid>[\w-]+)"):
    """'Done' on honor-system Orientation electives (action_key: honor_button)."""

    def __init__(self, qid: str):
        super().__init__(discord.ui.Button(label="Done", style=discord.ButtonStyle.success,
                                           custom_id=f"uu:honor:{qid}"))
        self.qid = qid

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(match["qid"])

    async def callback(self, itx: discord.Interaction):
        q = itx.client.catalog.quests.get(self.qid)
        if not q or q.raw.get("action_key") != "honor_button":
            await itx.response.send_message("That button isn't valid anymore.", ephemeral=True)
            return
        await itx.client.get_cog("Onboarding").mark(itx.guild, itx.user.id, self.qid)
        await itx.response.send_message(f"{self.qid} done. +{q.xp} XP.", ephemeral=True)


async def setup(bot):
    bot.add_dynamic_items(ClockInButton, HelpPostButton, BugReportButton, StartButton, HonorButton,
                          PrimaryMajorButton, SkipVoiceButton)
    await bot.add_cog(Onboarding(bot))
