"""/rank, promotion ceremony, /grant-xp, perms sync."""
from __future__ import annotations

import json
import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..config import SIGNOFF
from ..curriculum import UserState
from ..embeds import nameplate, rank_card, rank_color

log = logging.getLogger("registrar.ranks")

JUMP_MEDAL = "jump_{}_{}"


class Ranks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def cat(self):
        return self.bot.catalog

    async def state(self, uid: int) -> UserState:
        u = await self.bot.db.user(uid)
        prof = json.loads(await self.bot.db.kv_get(uid, "profile") or "{}")
        return UserState(u["major"], u["rank"], await self.bot.db.done_set(uid),
                         await self.bot.db.skipped_set(uid), json.loads(u["tasters_json"] or "[]"), prof)

    # ------------------------------------------------------------------ /rank
    @app_commands.command(name="rank", description="Your rank card: XP, streak, next unlock, medals.")
    async def rank(self, itx: discord.Interaction, member: discord.Member | None = None):
        member = member or itx.user
        if member.id == itx.user.id:
            await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, "cmd.rank")
        await itx.response.send_message(embed=await self.card(member))

    async def card(self, member) -> discord.Embed:
        db = self.bot.db
        u = await db.user(member.id)
        st = await self.state(member.id)
        target = u["rank"] + 1
        ok, missing = self.cat.rank_requirements_met(st, target)
        if target in self.cat.ranks or target == 0:
            need = self.cat.xp_needed(target)
            next_line = (f"{self.cat.ranks.get(target, {}).get('title', 'Greenlit')}: "
                         f"{max(0, need - u['xp'])} XP to go · "
                         + ("all required quests done" if ok else f"{len(missing)} required left"))
        else:
            next_line = "Top of the ladder. The Optimization shelf is open."
        return rank_card(self.cat, member, u, await db.medals(member.id), next_line)

    # ------------------------------------------------------------- promotion
    async def check_promotion(self, guild: discord.Guild, uid: int) -> bool:
        """Called after any quest completes. Promotes at most one rank per call."""
        u = await self.bot.db.user(uid)
        target = u["rank"] + 1
        if target > 6:
            return False
        rank_cfg = self.cat.ranks.get(target, {})
        if rank_cfg.get("human_review"):
            return False  # R5/R6 are promoted by staff via /mentor-review on the capstone + vouchers (Phase 5)
        st = await self.state(uid)
        ok, _ = self.cat.rank_requirements_met(st, target)
        if not ok or u["xp"] < self.cat.xp_needed(target):
            return False
        if target == 3 and not u["seal"]:
            await self._ask_seal(guild, uid)
            return False  # the Specialty picker calls promote() when a Specialty is chosen
        await self.promote(guild, uid, target)
        return True

    async def promote(self, guild: discord.Guild, uid: int, new_rank: int, seal: str | None = None) -> None:
        db, unl = self.bot.db, self.bot.unlocks
        u = await db.user(uid)
        old_rank = u["rank"]
        seal = seal or u["seal"]
        member = guild.get_member(uid) or await guild.fetch_member(uid)

        # 1. swap visible rank role (never stack)
        remove = [guild.get_role(r) for r in unl.all_rank_roles()]
        if new_rank == 0:
            remove.append(guild.get_role(unl.role("recruit")))
        remove = [r for r in remove if r and r in member.roles]
        add = []
        new_role = guild.get_role(unl.rank_role(new_rank, seal))
        if new_role:
            add.append(new_role)
        if new_rank == 0 and (o := guild.get_role(unl.role("oriented"))):
            add.append(o)
        if new_rank == 3 and seal and (s := guild.get_role(unl.role("seal", seal))):
            add.append(s)  # permission twin, kept for life
        try:
            if remove:
                await member.remove_roles(*remove, reason=f"Promotion to rank {new_rank}")
            if add:
                await member.add_roles(*add, reason=f"Promotion to rank {new_rank}")
        except discord.Forbidden:
            log.error("Missing permissions to edit roles. Is the Quartermaster role above all rank roles?")

        # 2. category unlocks are role-based (overwrites set by /admin sync-perms), so nothing per-member here
        await db.set_user(uid, rank=new_rank, seal=seal, rank_since=discord.utils.utcnow().isoformat())

        # 5. jump medal (granted before the card so the card can show it)
        medal = JUMP_MEDAL.format(old_rank, new_rank)
        await db.grant_medal(uid, medal)

        # 3. DM briefing
        try:
            await member.send(await self.briefing(uid, new_rank))
        except discord.Forbidden:
            pass

        # 4. #rank-ups card
        ch = guild.get_channel(unl.channel("rank_ups"))
        if ch and new_rank >= 1:
            old_t = nameplate(self.cat, old_rank, u["seal"], u["major"])
            new_t = nameplate(self.cat, new_rank, seal, u["major"])
            e = discord.Embed(description=f"~~{old_t}~~ → **{new_t}**", color=rank_color(self.cat, new_rank, seal))
            e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            e.add_field(name="Major", value=self.cat.majors.get(u["major"], {}).get("title", u["major"]))
            cap = self.cat.capstone(u["major"], old_rank)
            if cap:
                e.add_field(name="Capstone", value=cap["title"])
                thumb = await self._capstone_thumb(uid, cap["id"])
                if thumb:
                    e.set_thumbnail(url=thumb)
            e.add_field(name="Medal", value=f"🎖 {medal}", inline=False)
            await ch.send(embed=e)

    async def briefing(self, uid: int, rank: int) -> str:
        """6-line DM. Templates live in docs/02-promotion-dms.md; keep them in sync."""
        u = await self.bot.db.user(uid)
        st = await self.state(uid)
        pick = self.cat.pick(st)
        nq = pick.main
        nxt = f"{nq.id} · {nq.raw['title']}" if nq else "run /quest"
        cap = self.cat.capstone(u["major"], rank) or {}
        seal_t = self.cat.seals.get(u["seal"] or "", {}).get("title", "")
        lines = {
            0: ["You're Greenlit. You have a desk but no badge yet.",
                "You owe the Starter Quests: 11 short quests, each one sitting.",
                f"Next: {nxt}. From now on, quests only work in #quest-board: press Continue your quest there.",
                "Stuck? #help-desk with the template. Mentors answer formatted posts first.",
                "New power: #foundations is open. Post WIP and questions there."],
            1: ["Blockout Artist. You can build a space and light it without getting lost.",
                f"You owe the Rank 1 path, ending in: {cap.get('title', '—')}.",
                f"Next: {nxt}. /path shows the whole rank.",
                "Ask in #world-lighting when a blockout feels wrong and you can't say why.",
                "New power: World & Lighting track, the Blockout showcase tag, and a voice seat on Studio Floor."],
            2: ["Gameplay Prototyper. You make things play.",
                f"You owe your side of Rank 2 + tasters, ending in: {cap.get('title', '—')}.",
                f"Next: {nxt}.",
                "Find a partner in Pair Program voice. Post graphs in #blueprint for reviews.",
                "New power: you can peer-approve Rank 0–1 turn-ins (3 a day) for +15 XP each."],
            3: [f"Specialist · {seal_t}. People can @ you for {seal_t} work now.",
                f"You owe your {seal_t} Specialty quests + shared character basics, ending in: {cap.get('title', '—')}.",
                f"Next: {nxt}.",
                "#characters-anim is open. For feedback, post in #showcase with the Critique-wanted tag.",
                f"New power: 1.25× XP on {seal_t} quests, /critique, and you can apply for Mentor-in-Training."],
            4: [f"Engineer · {seal_t}. You own a system now, not just a scene.",
                f"You owe one capstone: {cap.get('title', '—')}. {cap.get('brief', '')}",
                f"Next: {nxt}. Your 30-day workshop thread opens in your bay.",
                "Your mentor from here on is whoever reviewed your R3 capstone. Ping them there.",
                "New power: your systems track opens, you can review Rank 2 turn-ins, and your name is hoisted."],
        }.get(rank, [f"Rank {rank}.", "", f"Next: {nxt}.", "", ""])
        return "\n".join(lines + [SIGNOFF])

    async def _capstone_thumb(self, uid: int, qid: str) -> str | None:
        cur = await self.bot.db.conn.execute(
            "SELECT payload FROM submissions WHERE user_id=? AND quest_id=? AND status='pass' ORDER BY id DESC LIMIT 1",
            (uid, qid))
        row = await cur.fetchone()
        if not row:
            return None
        atts = json.loads(row["payload"]).get("attachments") or []
        return atts[0] if atts else None

    async def _ask_seal(self, guild: discord.Guild, uid: int) -> None:
        u = await self.bot.db.user(uid)
        allowed = self.cat.majors.get(u["major"], {}).get("seals") or list(self.cat.seals)
        member = guild.get_member(uid)
        if not member:
            return
        view = SealPicker(self, guild, uid, allowed)
        try:
            await member.send("Rank 3 is ready. Pick your Specialty. It becomes your job title.", view=view)
        except discord.Forbidden:
            pass

    # --------------------------------------------------------------- staff
    @app_commands.command(name="grant-xp", description="[Mod] Grant or remove XP. Logged.")
    @app_commands.default_permissions(moderate_members=True)
    async def grant_xp(self, itx: discord.Interaction, member: discord.Member, amount: int, reason: str):
        total = await self.bot.db.add_xp(member.id, amount, f"grant:{itx.user.id}:{reason}")
        await itx.response.send_message(f"{member.mention} {amount:+} XP → {total}. Reason: {reason}", ephemeral=True)
        log_ch = itx.guild.get_channel(self.bot.unlocks.channel("mod_log"))
        if log_ch:
            await log_ch.send(f"/grant-xp by {itx.user.mention}: {member.mention} {amount:+} ({reason})")
        await self.check_promotion(itx.guild, member.id)

    admin = app_commands.Group(name="admin", description="Owner setup helpers",
                               default_permissions=discord.Permissions(administrator=True))

    @admin.command(name="sync-perms", description="Apply cumulative category overwrites from unlocks.yaml.")
    async def sync_perms(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True)
        unl, g = self.bot.unlocks, itx.guild
        changed = 0
        for rank in range(0, 7):
            roles_at_or_above = [g.get_role(unl.rank_role(r, None)) for r in range(rank, 7) if r != 3]
            roles_at_or_above += [g.get_role(unl.role("specialist", s)) for s in self.cat.seals] if rank <= 3 else []
            roles_at_or_above = [r for r in roles_at_or_above if r]
            for cat_id in unl.categories_for_rank(rank):
                cat = g.get_channel(cat_id)
                if not cat:
                    continue
                ow = dict(cat.overwrites)
                ow[g.default_role] = discord.PermissionOverwrite(view_channel=False)
                for r in roles_at_or_above:
                    ow[r] = discord.PermissionOverwrite(view_channel=True)
                await cat.edit(overwrites=ow, reason="Quartermaster sync-perms")
                changed += 1
        await itx.followup.send(f"Synced {changed} categories. Workshop forums get their rank locks from bootstrap.",
                                ephemeral=True)

    @admin.command(name="reload-curriculum", description="Reload YAML from disk.")
    async def reload_curriculum(self, itx: discord.Interaction):
        from ..curriculum import Catalog
        new = Catalog.load(self.bot.settings.curriculum_dir)
        errs, warns = new.validate()
        if errs:
            await itx.response.send_message("Not reloaded:\n" + "\n".join(errs[:20]), ephemeral=True)
            return
        self.bot.catalog = new
        await itx.response.send_message(f"Reloaded {len(new.quests)} quests ({len(warns)} warnings).", ephemeral=True)


class SealPicker(discord.ui.View):
    def __init__(self, cog: Ranks, guild: discord.Guild, uid: int, allowed: list[str]):
        super().__init__(timeout=None)
        self.cog, self.guild, self.uid = cog, guild, uid
        for s in allowed:
            b = discord.ui.Button(label=cog.cat.seals[s]["title"], style=discord.ButtonStyle.secondary)
            b.callback = self._make(s)
            self.add_item(b)

    def _make(self, seal: str):
        async def cb(itx: discord.Interaction):
            await self.cog.promote(self.guild, self.uid, 3, seal=seal)
            await itx.response.edit_message(content=f"Specialty chosen: {self.cog.cat.seals[seal]['title']}.", view=None)
        return cb


async def setup(bot):
    await bot.add_cog(Ranks(bot))
