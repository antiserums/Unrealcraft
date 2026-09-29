"""/quest, /submit, /tree, /skip-elective, mentor queue + /mentor-review."""
from __future__ import annotations

import datetime as dt
import json
import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import checks, profile
from ..embeds import guide_view, quest_embed

log = logging.getLogger("registrar.quests")


def route_for(quest_rank: int, verify_type: str) -> str:
    """Where a submission goes. See docs/03-commands.md → Routing a /submit."""
    if quest_rank < 0 or verify_type == "action":
        return "auto"
    if quest_rank <= 1:
        return "auto" if verify_type == "quiz" else "honor"
    if quest_rank == 2:
        return "peer"          # peer (R2+, capped) or mentor, whichever gets there first
    if quest_rank <= 4:
        return "mentor"        # mentor, or 2 peer approves
    return "human"


class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def cat(self):
        return self.bot.catalog

    async def _autocomplete(self, itx: discord.Interaction, current: str):
        u = await self.bot.db.user(itx.user.id)
        cur = current.lower()
        qs = [q for q in self.cat.sorted(self.cat.quests.values()) if q.rank <= max(u["rank"], 0)]
        return [app_commands.Choice(name=f"{q.id} · {q.raw['title']}"[:100], value=q.id)
                for q in qs if cur in q.id.lower() or cur in q.raw["title"].lower()][:25]

    # ------------------------------------------------------------ /quest
    @app_commands.command(name="quest", description="Your next quest, or a specific one by id.")
    @app_commands.autocomplete(id=_autocomplete)
    async def quest(self, itx: discord.Interaction, id: str | None = None):
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.quest")
        if id:
            q = self.cat.quests.get(id.upper())
            if not q:
                await itx.response.send_message("No quest with that id. Try `/path`.", ephemeral=True)
                return
            if not await self.quest_board_only(itx, q):
                return
            u = await self.bot.db.user(itx.user.id)
            facts = await self.bot.db.facts(itx.user.id)
            await itx.response.send_message(embed=quest_embed(self.cat, q, u["major"], facts=facts, guild=itx.guild),
                                            ephemeral=True,
                                            view=await self.card_view(q, itx.user.id))
            return
        await self.send_next(itx)

    async def quest_board_only(self, itx: discord.Interaction, q=None) -> bool:
        """After Orientation, quests live in #quest-board. Returns True if this interaction may continue;
        otherwise replies with a Go-to-#quest-board button. Orientation quests (rank < 0) work anywhere."""
        if q is not None and q.rank < 0:
            return True
        board = self.bot.unlocks.channel("quest_board")
        if not board or itx.channel_id == board:
            return True
        v = discord.ui.View(timeout=None)
        v.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Go to #quest-board", emoji="🗺️",
                                     url=f"https://discord.com/channels/{self.bot.settings.guild_id}/{board}"))
        await itx.response.send_message("Quests only work in **#quest-board**. Go there and press **Continue your quest**.", view=v, ephemeral=True)
        return False

    async def card_view(self, q, uid: int) -> discord.ui.View:
        """Every quest card has a button to the next thing: guide → quiz → send work → next quest."""
        from .quiz import QuizButton
        db = self.bot.db
        v = discord.ui.View(timeout=None)
        done = q.id in await db.done_set(uid)
        needs_submit = q.raw.get("verify_type") not in ("quiz", "action")
        if done:
            v.add_item(NextQuestButton())
        elif q.quiz and not await db.quiz_passed(uid, q.id):
            v.add_item(QuizButton(q.id, label="Start quiz"))
        elif needs_submit:
            v.add_item(SendWorkButton(q.id))
        elif q.rank < 0:
            from .onboarding import NextStepsButton
            v.add_item(NextStepsButton())
        guide_view(q, v)
        return v

    async def send_next(self, itx: discord.Interaction) -> None:
        """Show the member's next quest (used by /quest and every 'Next' button)."""
        db = self.bot.db
        u = await db.user(itx.user.id)
        facts = await db.facts(itx.user.id)
        st = await self.bot.get_cog("Ranks").state(itx.user.id)
        pick = self.cat.pick(st)
        if not await self.quest_board_only(itx, pick.main):
            return
        embeds = []
        if pick.main:
            await db.set_user(itx.user.id, current_quest_id=pick.main.id)
            embeds.append(quest_embed(self.cat, pick.main, u["major"], pick.reason, facts=facts, guild=itx.guild))
        extras = [f"• `{q.id}` {q.raw['title']} ({q.xp} XP)" for q in pick.electives]
        if pick.adjacent:
            extras.append(f"• `{pick.adjacent.id}` {pick.adjacent.raw['title']} (adjacent, {pick.adjacent.xp} XP)")
        content = ("**Also on offer:**\n" + "\n".join(extras)) if extras else None
        notes = []
        if pick.main and pick.main.spine and profile.can_test_out(st.profile):
            notes.append(f"⚡ You can test out: pass the quiz on the first try and it's done.")
        if st.profile.get("pace"):
            mins = self.cat.remaining_minutes(st)
            hours = profile.PACE_HOURS[st.profile["pace"]]
            if mins:
                weeks = max(1, round(mins / 60 / hours))
                nxt = self.cat.ranks.get(max(st.rank, -1) + 1, {}).get("title", "your next rank")
                notes.append(f"⏱ ~{mins / 60:.0f} h of required work to **{nxt}**, about "
                             f"{weeks} week{'s' if weeks != 1 else ''} at your pace.")
        if st.major == "undecided" and (sug := profile.suggested_major(st.profile)):
            notes.append(f"🧭 Your curiosities point at **{self.cat.majors[sug]['title']}**. `/major` when you're ready.")
        if notes:
            content = "\n".join(notes) + ("\n\n" + content if content else "")
        if not embeds and not content:
            content = "Nothing open right now. You're at the edge of the catalog. Check `/path` for the optional shelf."
        kw = {"view": await self.card_view(pick.main, itx.user.id)} if pick.main else {}
        await itx.response.send_message(content=content, embeds=embeds, ephemeral=True, **kw)

    # ------------------------------------------------------------ /tree
    @app_commands.command(name="tree", description="The whole catalog by rank and track (the same for everyone).")
    async def tree(self, itx: discord.Interaction):
        rows: dict[tuple[int, str], int] = {}
        for q in self.cat.quests.values():
            rows[(q.rank, q.track)] = rows.get((q.rank, q.track), 0) + 1
        lines = [f"R{r:>2} · {t:<16} {n}" for (r, t), n in sorted(rows.items())]
        await itx.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)

    @app_commands.command(name="skip-elective", description="Hide an elective from /quest suggestions.")
    @app_commands.autocomplete(id=_autocomplete)
    async def skip_elective(self, itx: discord.Interaction, id: str):
        q = self.cat.quests.get(id.upper())
        if not q or not q.elective:
            await itx.response.send_message("Only electives can be skipped.", ephemeral=True)
            return
        await self.bot.db.set_progress(itx.user.id, q.id, "skipped")
        await itx.response.send_message(f"Skipped {q.id}. It's still on /path if you change your mind.", ephemeral=True)

    # ------------------------------------------------------------ /submit
    @app_commands.command(name="submit", description="Turn in proof for a quest.")
    @app_commands.autocomplete(quest=_autocomplete)
    async def submit(self, itx: discord.Interaction, quest: str, proof: str,
                     attachment: discord.Attachment | None = None):
        await self.do_submit(itx, quest, proof, attachment)

    async def do_submit(self, itx: discord.Interaction, quest: str, proof: str,
                        attachment: discord.Attachment | None = None) -> None:
        """Shared by /submit and the Send-my-work form."""
        db = self.bot.db
        q = self.cat.quests.get(quest.upper())
        if not q:
            await itx.response.send_message("Unknown quest id.", ephemeral=True)
            return
        if not await self.quest_board_only(itx, q):
            return
        u = await db.user(itx.user.id)
        if q.rank > max(u["rank"], 0):
            await itx.response.send_message("That quest is above your rank.", ephemeral=True)
            return
        if q.id in await db.done_set(itx.user.id):
            await itx.response.send_message("Already done.", ephemeral=True)
            return
        last_fail = await db.last_fail_at(itx.user.id, q.id)
        cooldown = self.cat.xp_rules.get("submit_cooldown_after_fail_min", 120)
        if last_fail and dt.datetime.utcnow() - last_fail < dt.timedelta(minutes=cooldown):
            await itx.response.send_message(f"Cooldown: {cooldown} min after a Fail. Use the time to fix it.",
                                            ephemeral=True)
            return
        if q.quiz and not await db.quiz_passed(itx.user.id, q.id):
            await itx.response.send_message(f"Pass `/quiz {q.id}` first.", ephemeral=True)
            return

        # Orientation dry-run submit: records a fact, O5's checklist does the rest
        if q.id == "O5":
            if proof.strip().upper() != "READY":
                await itx.response.send_message("For O5, the proof is literally `READY`.", ephemeral=True)
                return
            await itx.response.send_message(
                "✅ Practice done! A real turn-in works the same way.", ephemeral=True, view=_next_steps_view())
            await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "submit.O5")
            return
        if q.raw.get("verify_type") == "action":
            await itx.response.send_message("This one completes itself when the Quartermaster sees you do it. "
                                            f"Check `/quest {q.id}` for what's still ☐.", ephemeral=True)
            return

        # Checklist: everything the bot can see must already be ✅; attachments/links/length are checked now
        missing = checks.facts_missing(q, await db.facts(itx.user.id))
        problems = [f"☐ {m}" for m in missing] + await checks.validate_submit(self.bot, q, itx.user.id, proof, attachment)
        if problems:
            await itx.response.send_message("Not yet:\n" + "\n".join(problems), ephemeral=True)
            return

        payload = {"text": proof, "attachments": [attachment.url] if attachment else [],
                   "ue_version": u["ue_version"]}
        route = route_for(q.rank, q.raw.get("verify_type", "screenshot"))
        sid = await db.create_submission(itx.user.id, q.id, payload, route)
        await db.set_progress(itx.user.id, q.id, "submitted")

        if route in ("auto", "honor"):
            await db.decide(sid, "pass", None, route)
            await itx.response.send_message(f"✅ {q.id} accepted. +{q.xp} XP.", ephemeral=True, view=_next_view())
            await self.post_turnin(itx.guild, itx.user, q, payload, route)
            await self.complete(itx.guild, itx.user.id, q.id)
            return
        await self.post_to_queue(itx.guild, sid)
        who = {"peer": "a peer (Rank 2+) or a mentor",
               "mentor": "a mentor or two peers",
               "human": "a human mentor"}[route]
        await itx.response.send_message(f"📥 Submitted #{sid}. Waiting on {who}. Target turnaround is under 48h.",
                                        ephemeral=True, view=_next_view())
        await self.post_turnin(itx.guild, itx.user, q, payload, route)

    # --------------------------------------------------------- completion
    async def complete(self, guild: discord.Guild, uid: int, qid: str) -> None:
        """Single path for a quest becoming done: XP, streak, medals, promotion check."""
        db = self.bot.db
        if qid in await db.done_set(uid):
            return
        guild = guild or self.bot.get_guild(self.bot.settings.guild_id or 0)
        q = self.cat.quests[qid]
        u = await db.user(uid)
        xp = q.xp
        if u["rank"] >= 3 and u["seal"] and q.raw.get("seal") == u["seal"]:
            xp = round(xp * self.cat.xp_rules.get("in_seal_multiplier_rank3plus", 1.25))
        await db.set_progress(uid, qid, "done")
        await db.add_xp(uid, xp, f"quest:{qid}")
        await db.touch_streak(uid)
        if q.rank >= 0:
            await db.grant_medal(uid, "first_blood")     # idempotent: first Unreal quest done
        done = await db.done_set(uid)
        if all(s.id in done for s in self.cat.spine()):
            await db.set_user(uid, spine_done=1)
        onboarding = self.bot.get_cog("Onboarding")
        if q.rank < 0 and onboarding:
            await onboarding.maybe_finish_orientation(guild, uid)
            await onboarding.refresh_page(uid)
        if guild:
            await self.bot.get_cog("Ranks").check_promotion(guild, uid)

    # ------------------------------------------------------ public turn-in post
    async def post_turnin(self, guild: discord.Guild, member: discord.abc.User, q, payload: dict, route: str) -> None:
        """Mirror a /submit into its Workshop forum so people can see and cheer it."""
        unl = self.bot.unlocks
        # Starter Quests → #starter-quests; everything else → the member's major forum.
        from .workshop import STARTER, major_slug
        if q.rank < 0:
            return
        u = await self.bot.db.user(member.id)
        slug = STARTER if (q.spine or q.rank == 0 or u["major"] == "undecided") else major_slug(self.cat, u["major"])
        ch = guild.get_channel(unl.channel("tracks", slug))
        if not ch:
            return                                   # orientation/tasters: no public post
        status = {"auto": "✅ accepted", "honor": "✅ accepted", "peer": "📥 waiting on a peer or mentor",
                  "mentor": "📥 waiting on a mentor or two peers", "human": "📥 waiting on a mentor"}[route]
        body = (f"{member.mention} turned in **{q.id} · {q.raw['title']}** · {status}\n"
                f"Engine: {payload.get('ue_version') or 'not stated'}\n\n{payload['text'][:1500]}")
        embed = None
        if payload["attachments"]:
            embed = discord.Embed(color=discord.Color.from_str("#3D7DD8"))
            embed.set_image(url=payload["attachments"][0])
        try:
            if isinstance(ch, discord.ForumChannel):
                tag = discord.utils.get(ch.available_tags, name="Turn-in")
                await ch.create_thread(name=f"{q.id} · {member.display_name}"[:100], content=body, embed=embed,
                                       applied_tags=[tag] if tag else [],
                                       allowed_mentions=discord.AllowedMentions.none())
            else:
                await ch.send(body, embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as e:
            log.warning("turn-in post failed for %s: %s", q.id, e)

    # ------------------------------------------------------ mentor queue
    async def post_to_queue(self, guild: discord.Guild, sid: int) -> None:
        ch = guild.get_channel(self.bot.unlocks.channel("mentor_queue"))
        s = await self.bot.db.submission(sid)
        if not ch or not s:
            log.warning("mentor_queue channel not configured; submission %s is only in the DB", sid)
            return
        q = self.cat.quests[s["quest_id"]]
        p = json.loads(s["payload"])
        e = discord.Embed(title=f"#{sid} · {q.id} · {q.raw['title']}", description=p["text"][:2000],
                          color=discord.Color.from_str("#3D7DD8"))
        e.add_field(name="From", value=f"<@{s['user_id']}>")
        e.add_field(name="Route", value=s["route"])
        e.add_field(name="Engine", value=p.get("ue_version") or "not stated ⚠")
        e.add_field(name="Done when", value=q.raw.get("done_when", "")[:1024], inline=False)
        if p["attachments"]:
            e.set_image(url=p["attachments"][0])
        msg = await ch.send(embed=e, view=ReviewView(sid))
        await self.bot.db.set_queue_message(sid, msg.id)

    async def review(self, itx: discord.Interaction, sid: int, verdict: str, notes: str | None) -> str:
        """Shared by buttons and /mentor-review. Enforces reviewer eligibility and peer caps."""
        db, unl = self.bot.db, self.bot.unlocks
        s = await db.submission(sid)
        if not s or s["status"] != "pending":
            return "That submission is closed."
        if s["user_id"] == itx.user.id:
            return "You can't review your own work."
        q = self.cat.quests[s["quest_id"]]
        member = itx.guild.get_member(itx.user.id)
        is_mentor = member.guild_permissions.administrator or \
            any(r.id in (unl.role("staff", "mentor"), unl.role("rank", 6)) for r in member.roles)
        rv = await db.user(itx.user.id)
        # peer-approve ranges: R2 → 0–1, R3 → 0–2, R4 → 0–3, R5 → 0–4, R6 → all
        peer_ok = rv["rank"] >= 2 and q.rank <= rv["rank"] - 1
        if s["route"] == "human" and not is_mentor:
            return "Rank 5+ work needs a human mentor."
        if not is_mentor and not peer_ok:
            return "You can't review this rank yet."
        if not is_mentor:
            cap = self.cat.xp_rules.get("peer_review", {}).get("daily_cap", 3)
            if await db.xp_count_today(itx.user.id, "peer_review:") >= cap:
                return f"Peer review cap reached ({cap}/day)."
        is_peer = not is_mentor
        pv = "approve" if (is_peer and verdict == "pass") else verdict
        if not await db.add_review_action(sid, itx.user.id, pv, is_peer, notes):
            return "You already reviewed this one."
        if is_peer:
            await db.add_xp(itx.user.id, self.cat.xp_rules.get("peer_review", {}).get("xp", 15), f"peer_review:{sid}")

        final = None
        if is_mentor:
            final = verdict
        elif verdict in ("changes", "fail"):
            final = verdict                      # one peer can bounce, two needed to pass at R3+
        elif s["route"] == "peer":
            final = "pass"
        elif await db.peer_approvals(sid) >= 2:
            final = "pass"
        if final:
            await db.decide(sid, final, itx.user.id, notes)
            try:
                user = await self.bot.fetch_user(s["user_id"])
                await user.send(f"{q.id}: **{final.upper()}** from {itx.user.display_name}."
                                + (f"\n> {notes}" if notes else ""))
            except discord.HTTPException:
                pass
            if final == "pass":
                await self.complete(itx.guild, s["user_id"], q.id)
            return f"Recorded: {final}."
        return f"Approve recorded ({await db.peer_approvals(sid)}/2)."

    @app_commands.command(name="mentor-review", description="Pass / Changes / Fail a submission.")
    @app_commands.choices(verdict=[app_commands.Choice(name=n, value=n.lower()) for n in ("Pass", "Changes", "Fail")])
    async def mentor_review(self, itx: discord.Interaction, submission: int, verdict: app_commands.Choice[str],
                            notes: str | None = None):
        await itx.response.send_message(await self.review(itx, submission, verdict.value, notes), ephemeral=True)


def _next_view() -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    v.add_item(NextQuestButton())
    return v


def _next_steps_view() -> discord.ui.View:
    from .onboarding import NextStepsButton
    v = discord.ui.View(timeout=None)
    v.add_item(NextStepsButton())
    return v


class NextQuestButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:nextquest"):
    """'Next' everywhere after Orientation: shows the member's next quest card."""

    def __init__(self, label: str = "Next quest"):
        super().__init__(discord.ui.Button(label=label, emoji="👉", style=discord.ButtonStyle.success,
                                           custom_id="uc:nextquest"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Quests").send_next(itx)


class SendWorkButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:send:(?P<q>[A-Za-z0-9-]+)"):
    """Opens a form instead of typing /submit."""

    def __init__(self, qid: str):
        super().__init__(discord.ui.Button(label="Send my work", emoji="📤", style=discord.ButtonStyle.success,
                                           custom_id=f"uc:send:{qid}"))
        self.qid = qid

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(match["q"])

    async def callback(self, itx: discord.Interaction):
        q = itx.client.catalog.quests.get(self.qid)
        if not q:
            await itx.response.send_message("That quest doesn't exist anymore.", ephemeral=True)
            return
        if not await itx.client.get_cog("Quests").quest_board_only(itx, q):
            return
        await itx.response.send_modal(SendWorkModal(q))


class SendWorkModal(discord.ui.Modal):
    def __init__(self, q):
        super().__init__(title=f"Send your work: {q.id}"[:45])
        self.q = q
        self.proof = discord.ui.TextInput(style=discord.TextStyle.paragraph, max_length=1500,
                                          placeholder=(q.raw.get("done_when") or "Describe what you did.")[:100])
        self.add_item(discord.ui.Label(text="What did you do?", description="Include your Unreal version",
                                       component=self.proof))
        self.file = discord.ui.FileUpload(required=False, max_values=1)
        self.add_item(discord.ui.Label(text="Screenshot or clip", description="Needed for screenshot quests",
                                       component=self.file))

    async def on_submit(self, itx: discord.Interaction):
        att = (self.file.values or [None])[0]
        await itx.client.get_cog("Quests").do_submit(itx, self.q.id, str(self.proof.value), att)


class ReviewView(discord.ui.View):
    """Persistent buttons; custom_id encodes the submission id."""

    def __init__(self, sid: int):
        super().__init__(timeout=None)
        for label, verdict, style in (("Pass", "pass", discord.ButtonStyle.success),
                                      ("Changes", "changes", discord.ButtonStyle.secondary),
                                      ("Fail", "fail", discord.ButtonStyle.danger)):
            self.add_item(ReviewButton(sid, label, verdict, style))


class ReviewButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uu:review:(?P<sid>\d+):(?P<v>\w+)"):
    def __init__(self, sid: int, label: str = "", verdict: str = "pass",
                 style: discord.ButtonStyle = discord.ButtonStyle.secondary):
        super().__init__(discord.ui.Button(label=label, style=style, custom_id=f"uu:review:{sid}:{verdict}"))
        self.sid, self.verdict = sid, verdict

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(int(match["sid"]), verdict=match["v"])

    async def callback(self, itx: discord.Interaction):
        if self.verdict == "pass":
            msg = await itx.client.get_cog("Quests").review(itx, self.sid, "pass", None)
            await itx.response.send_message(msg, ephemeral=True)
        else:
            await itx.response.send_modal(NotesModal(self.sid, self.verdict))


class NotesModal(discord.ui.Modal, title="Review notes"):
    notes = discord.ui.TextInput(label="What should they change? (be specific)", style=discord.TextStyle.paragraph,
                                 max_length=1000)

    def __init__(self, sid: int, verdict: str):
        super().__init__()
        self.sid, self.verdict = sid, verdict

    async def on_submit(self, itx: discord.Interaction):
        msg = await itx.client.get_cog("Quests").review(itx, self.sid, self.verdict, str(self.notes))
        await itx.response.send_message(msg, ephemeral=True)


async def setup(bot):
    bot.add_dynamic_items(ReviewButton, NextQuestButton, SendWorkButton)
    await bot.add_cog(Quests(bot))
