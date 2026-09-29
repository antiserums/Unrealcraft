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
        from ..embeds import guide_view, reading_links
        links = reading_links(q)
        if links:                                   # read first: show the guide before any question
            intro = discord.ui.View(timeout=900)
            intro.add_item(StartQuizButton(self, q, itx.user.id, first_try))
            guide_view(q, intro)
            lines = "\n".join(f"• [{label}]({url})" for label, url in links)
            await itx.response.send_message(
                f"**{q.id} · {q.raw['title']}: quiz**\n"
                f"📖 The questions are about this material. Read it first:\n{lines}\n\n"
                f"{len(q.quiz)} questions. You need {int(QUIZ_PASS_RATIO * len(q.quiz))} right. "
                "Press **Start quiz** when you're ready.", view=intro, ephemeral=True, suppress_embeds=True)
            return
        view = QuizView(self, q, itx.user.id, first_try)
        await itx.response.send_message(**view.render(), view=view, ephemeral=True)

    async def finish(self, itx: discord.Interaction, q, score: int, first_try: bool):
        """Returns (message, view). The view always has a button to the next thing."""
        from ..embeds import guide_view
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
            return (f"**{score}/{total}**. You need {int(QUIZ_PASS_RATIO * total)}. "
                    + ("Read the guide again, then try again." if q.raw.get("official_url", "").startswith("http")
                       else "Read #welcome again, then try again.")), view
        await db.set_progress(itx.user.id, q.id, "quiz_passed", quiz_passed=True)
        msg = f"**{score}/{total}**. Passed."
        if first_try:
            bonus = round(q.xp * self.bot.catalog.xp_rules.get("quiz_first_try_bonus_pct", 20) / 100)
            await db.add_xp(itx.user.id, bonus, f"quiz_bonus:{q.id}")
            msg += f" First-try bonus +{bonus} XP."
        await self.bot.get_cog("Onboarding").fact(itx.guild, itx.user.id, f"quiz.{q.id}")   # action quests (O1) finish via their checklist
        prof = json.loads(await db.kv_get(itx.user.id, "profile") or "{}")
        test_out = q.spine and first_try and profile.can_test_out(prof)
        if q.raw.get("verify_type") == "quiz" or test_out:
            await self.bot.get_cog("Quests").complete(itx.guild, itx.user.id, q.id)
            msg += " Tested out: quest complete, no turn-in needed." if test_out and q.raw.get("verify_type") != "quiz" \
                else " Quest complete."
            view.add_item(NextStepsButton() if q.rank < 0 else NextQuestButton())
        elif q.raw.get("verify_type") == "action":
            msg += " That step is ticked."
            view.add_item(NextStepsButton())
        else:
            msg += " Now send your work."
            view.add_item(SendWorkButton(q.id))
        return msg, view


class StartQuizButton(discord.ui.Button):
    def __init__(self, cog: "Quiz", q, uid: int, first_try: bool):
        super().__init__(label="Start quiz", emoji="📝", style=discord.ButtonStyle.success)
        self.cog, self.q, self.uid, self.first_try = cog, q, uid, first_try

    async def callback(self, itx: discord.Interaction):
        if itx.user.id != self.uid:
            return
        view = QuizView(self.cog, self.q, self.uid, self.first_try)
        await itx.response.edit_message(**view.render(), view=view)


class QuizView(discord.ui.View):
    def __init__(self, cog: Quiz, q, uid: int, first_try: bool):
        super().__init__(timeout=900)
        self.cog, self.q, self.uid, self.first_try = cog, q, uid, first_try
        self.i = 0
        self.score = 0
        self.feedback = ""
        # Shuffle choice order per attempt so letter positions can't be memorized.
        self.orders = [random.sample(range(len(it["choices"])), len(it["choices"])) for it in q.quiz]
        self._build()

    def _build(self):
        self.clear_items()
        for pos, idx in enumerate(self.orders[self.i]):
            b = discord.ui.Button(label=f"{'ABCD'[pos]}", style=discord.ButtonStyle.secondary)
            b.callback = self._answer(idx)
            self.add_item(b)

    def _letter(self, idx: int) -> str:
        return "ABCD"[self.orders[self.i].index(idx)]

    def render(self) -> dict:
        item = self.q.quiz[self.i]
        body = "\n".join(f"**{'ABCD'[pos]}.** {item['choices'][idx]}" for pos, idx in enumerate(self.orders[self.i]))
        head = f"{self.feedback}\n\n" if self.feedback else ""
        return {"content": f"{head}**{self.q.id} · Q{self.i + 1}/{len(self.q.quiz)}**\n{item['q']}\n\n{body}"}

    def _answer(self, idx: int):
        async def cb(itx: discord.Interaction):
            if itx.user.id != self.uid:
                return
            item = self.q.quiz[self.i]
            right = idx == item["answer_index"]
            self.score += right
            self.feedback = ("✅ " if right else f"❌ Answer: {self._letter(item['answer_index'])}. ") + item.get("explain", "")
            self.i += 1
            if self.i >= len(self.q.quiz):
                result, view = await self.cog.finish(itx, self.q, self.score, self.first_try)
                await itx.response.edit_message(content=f"{self.feedback}\n\n{result}", view=view)
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
