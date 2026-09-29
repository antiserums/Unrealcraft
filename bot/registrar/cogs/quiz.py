"""/quiz: ephemeral, one question per step, buttons. Pass = 80%."""
from __future__ import annotations

import asyncio
import json
import random

import discord
from discord import app_commands
from discord.ext import commands

from .. import profile
from ..curriculum import QUIZ_PASS_RATIO


class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def quest_autocomplete(self, itx: discord.Interaction, current: str):
        u = await self.bot.db.user(itx.user.id)
        qs = [q for q in self.bot.catalog.quests.values() if q.quiz and q.rank <= max(u["rank"], 0)]
        cur = current.lower()
        return [app_commands.Choice(name=f"{q.id} · {q.raw['title']}"[:100], value=q.id)
                for q in qs if cur in q.id.lower() or cur in q.raw["title"].lower()][:25]

    @app_commands.command(name="quiz", description="Take a quest's quiz.")
    @app_commands.autocomplete(quest=quest_autocomplete)
    async def quiz(self, itx: discord.Interaction, quest: str):
        await self.start(itx, quest)

    async def start(self, itx: discord.Interaction, quest: str) -> None:
        """Shared by /quiz and the Rules quiz button."""
        q = self.bot.catalog.quests.get(quest.upper())
        if not q or not q.quiz:
            await itx.response.send_message("That quest has no quiz. `/submit` it directly.", ephemeral=True)
            return
        u = await self.bot.db.user(itx.user.id)
        if not await self.bot.get_cog("Quests").quest_board_only(itx, q):
            return
        if q.rank > max(u["rank"], 0) and q.rank >= 0:
            await itx.response.send_message("That quiz unlocks at a higher rank.", ephemeral=True)
            return
        first_try = await self.bot.db.quiz_attempts(itx.user.id, q.id) == 0
        view = QuizView(self, q, itx.user.id, first_try)
        await itx.response.send_message(**view.render(), view=view, ephemeral=True)

    async def finish(self, itx: discord.Interaction, q, score: int, first_try: bool):
        """Returns (message, view). The view always has a button to the next thing."""
        from ..embeds import guide_view, reading_links
        from .quests import NextQuestButton, SendWorkButton
        from .onboarding import NextStepsButton
        view = discord.ui.View(timeout=None)
        db = self.bot.db
        total = len(q.quiz)
        passed = score / total >= QUIZ_PASS_RATIO
        await db.log_quiz(itx.user.id, q.id, score, total, passed)
        if not passed:
            view.add_item(QuizButton(q.id, label="Try again"))
            guide_view(q, view)
            return (f"You need {int(QUIZ_PASS_RATIO * total)} right.\n"
                    + ("Read the guide again, then press **Try again**." if reading_links(q)
                       else "Read #welcome again, then press **Try again**.")), view
        await db.set_progress(itx.user.id, q.id, "quiz_passed", quiz_passed=True)
        msg = ""
        if first_try:
            bonus = round(q.xp * self.bot.catalog.xp_rules.get("quiz_first_try_bonus_pct", 20) / 100)
            await db.add_xp(itx.user.id, bonus, f"quiz_bonus:{q.id}")
            msg += f"⭐ First-try bonus: +{bonus} XP.\n"
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, f"quiz.{q.id}")   # action quests (O1) finish via their checklist
        prof = json.loads(await db.kv_get(itx.user.id, "profile") or "{}")
        test_out = q.spine and first_try and profile.can_test_out(prof)
        if q.raw.get("verify_type") == "quiz" or test_out:
            await self.bot.get_cog("Quests").complete(itx.guild, itx.user.id, q.id)
            msg += "Tested out: quest complete, no turn-in needed." if test_out and q.raw.get("verify_type") != "quiz" \
                else "✅ Quest complete."
            view.add_item(NextStepsButton() if q.rank < 0 else NextQuestButton())
        elif q.raw.get("verify_type") == "action":
            msg += "✅ That step is ticked."
            view.add_item(NextStepsButton())
        else:
            msg += "Next: press **Send my work**."
            view.add_item(SendWorkButton(q.id))
        return msg, view


class QuizView(discord.ui.View):
    def __init__(self, cog: Quiz, q, uid: int, first_try: bool):
        super().__init__(timeout=900)
        self.cog, self.q, self.uid, self.first_try = cog, q, uid, first_try
        self.guild = cog.bot.get_guild(cog.bot.settings.guild_id or 0)
        self.i = 0
        self.score = 0
        self.feedback: tuple[bool, str] | None = None
        # Shuffle choice order per attempt so letter positions can't be memorized.
        self.orders = [random.sample(range(len(it["choices"])), len(it["choices"])) for it in q.quiz]
        self._build()

    def _build(self):
        self.clear_items()
        for pos, idx in enumerate(self.orders[self.i]):
            b = discord.ui.Button(label=f"{'ABCD'[pos]}", style=discord.ButtonStyle.secondary)
            b.callback = self._answer(idx)
            self.add_item(b)
        from ..embeds import guide_view
        guide_view(self.q, self)                      # 📖 Open the guide, on every question

    def _letter(self, idx: int) -> str:
        return "ABCD"[self.orders[self.i].index(idx)]

    def _card(self, title: str, text: str, color: str) -> discord.Embed:
        from ..embeds import linkify
        return discord.Embed(title=title, description=linkify(text, self.guild), color=discord.Color.from_str(color))

    def _feedback_card(self) -> list[discord.Embed]:
        if not self.feedback:
            return []
        right, text = self.feedback
        return [self._card("✅ Correct" if right else "❌ Not quite", text, "#3BA55C" if right else "#D9534F")]

    def render(self) -> dict:
        item = self.q.quiz[self.i]
        n = len(self.q.quiz)
        cards = self._feedback_card()
        if self.i == 0:
            from ..embeds import reading_links
            text = f"**{self.q.tier_label}** · {n} questions. You need {int(QUIZ_PASS_RATIO * n)} right."
            if reading_links(self.q):
                text += "\n📖 Not sure? Press **Open the guide**. It stays here on every question."
            cards.append(self._card(f"📝 {self.q.id} · {self.q.raw['title']}", text, "#3D7DD8"))
        body = "\n".join(f"**{'ABCD'[pos]}.** {item['choices'][idx]}" for pos, idx in enumerate(self.orders[self.i]))
        cards.append(self._card(f"❓ Question {self.i + 1} of {n}", f"{item['q']}\n\n{body}", "#8E6CCF"))
        return {"content": None, "embeds": cards}

    def _answer(self, idx: int):
        async def cb(itx: discord.Interaction):
            if itx.user.id != self.uid:
                return
            item = self.q.quiz[self.i]
            right = idx == item["answer_index"]
            self.score += right
            self.feedback = (right, ("" if right else f"The answer was **{self._letter(item['answer_index'])}**. ")
                             + item.get("explain", ""))
            self.i += 1
            if self.i >= len(self.q.quiz):
                result, view = await self.cog.finish(itx, self.q, self.score, self.first_try)
                n = len(self.q.quiz)
                passed = self.score / n >= QUIZ_PASS_RATIO
                card = self._card(f"🏆 Quiz passed · {self.score}/{n}" if passed else f"📝 Not yet · {self.score}/{n}",
                                  result.strip(), "#D4AF37" if passed else "#D9824A")
                await itx.response.edit_message(content=None, embeds=[*self._feedback_card(), card], view=view)
                self.stop()
                return
            self._build()
            await itx.response.edit_message(**self.render(), view=self)
        return cb


class QuizButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:quiz:(?P<q>[A-Za-z0-9-]+)"):
    """Opens a quest's quiz without typing (used for the O1 rules quiz)."""

    def __init__(self, qid: str, label: str = "Rules quiz"):
        super().__init__(discord.ui.Button(label=label, emoji="📝", style=discord.ButtonStyle.primary,
                                           custom_id=f"uc:quiz:{qid}"))
        self.qid = qid

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls(match["q"])

    async def callback(self, itx: discord.Interaction):
        await itx.client.get_cog("Quiz").start(itx, self.qid)


async def setup(bot):
    bot.add_dynamic_items(QuizButton)
    await bot.add_cog(Quiz(bot))
