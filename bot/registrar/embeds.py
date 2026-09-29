"""Embed builders. Dark UI with the rank or Specialty color as the accent."""
from __future__ import annotations

import discord

from . import checks
from .curriculum import Catalog, Quest

DARK = discord.Color.from_str("#1E1F22")
GOLD = discord.Color.from_str("#D4AF37")


def rank_color(cat: Catalog, rank: int, seal: str | None) -> discord.Color:
    if rank == 3 and seal and seal in cat.seals:
        return discord.Color.from_str(cat.seals[seal]["color"])
    c = cat.ranks.get(rank, {}).get("color")
    return discord.Color.from_str(c) if c else DARK


def nameplate(cat: Catalog, rank: int, seal: str | None, major: str) -> str:
    if rank < 0:
        return "Orientation"
    title = cat.ranks[rank]["title"]
    if rank == 5:
        title = "Architect"
    if rank >= 3 and seal and rank < 6:
        return f"{title} · {cat.seals[seal]['title']}"
    if rank == 0 and major != "undecided":
        m = cat.majors.get(major, {})
        seal_hint = (m.get("seals") or [None])[0]
        if seal_hint:
            return f"{title} · {cat.seals[seal_hint]['title']}"
    return title


def quest_embed(cat: Catalog, q: Quest, major: str, reason: str | None = None,
                facts: set[str] | None = None) -> discord.Embed:
    r = q.raw
    fl = q.flavor(major)
    kind = "capstone" if q.capstone else ("elective" if q.elective else "required")
    rank_label = "Orientation" if q.rank < 0 else f"Rank {q.rank}"
    e = discord.Embed(
        title=f"{q.id} · {r['title']}",
        description=(f"*{fl['why']}*" if fl.get("why") else None),
        color=rank_color(cat, max(q.rank, 0), r.get("seal")),
    )
    e.add_field(name="Info", value=f"{rank_label} · {q.track} · {kind} · ~{r.get('time_min', '?')} min · **{q.xp} XP**",
                inline=False)
    if fl.get("do"):
        e.add_field(name="Your version", value=fl["do"], inline=False)
    links = []
    if r.get("official_url") and r["official_url"] != "TODO_URL":
        links.append(f"📘 [Official]({r['official_url']})" if r["official_url"].startswith("http") else f"📘 {r['official_url']}")
    if r.get("backup_url") and r["backup_url"] != "TODO_URL":
        links.append(f"🎞 [Backup video]({r['backup_url']})")
    if links:
        e.add_field(name="Sources", value=" · ".join(links), inline=False)
    checklist = checks.status_lines(q, facts or set(), cat.community_ready)
    if checklist:
        e.add_field(name="Checklist  (✅ seen by the bot · ☐ not yet · 📎 checked on submit · ▫ honor)",
                    value="\n".join(checklist)[:1024], inline=False)
    done_when = r.get("done_when_solo") if (not cat.community_ready and r.get("done_when_solo")) else r.get("done_when")
    e.add_field(name="Done when", value=(done_when or "—")[:1024], inline=False)
    vt = r.get("verify_type")
    if vt == "quiz":
        how = f"Pass `/quiz {q.id}`. That's all."
    elif vt == "action":
        how = "Nothing to send. The bot ticks it when it sees you do it."
    else:
        how = (f"`/quiz {q.id}` then " if q.quiz else "") + f"`/submit {q.id}`"
    e.add_field(name="How to finish", value=how, inline=False)
    if reason:
        e.set_footer(text=f"Why this one: {reason}")
    return e


def rank_card(cat: Catalog, member: discord.abc.User, u, medals: list[str], next_line: str) -> discord.Embed:
    rank, seal, major = u["rank"], u["seal"], u["major"]
    e = discord.Embed(title=nameplate(cat, rank, seal, major), color=rank_color(cat, max(rank, 0), seal))
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    nxt = cat.ranks.get(rank + 1)
    if nxt:
        lo = cat.ranks.get(rank, {}).get("xp", 0) if rank >= 0 else 0
        hi = nxt["xp"]
        frac = 0 if hi <= lo else min(1, max(0, (u["xp"] - lo) / (hi - lo)))
        bar = "█" * round(frac * 16) + "░" * (16 - round(frac * 16))
        e.add_field(name="XP", value=f"`{bar}` {u['xp']} / {hi}", inline=False)
    else:
        e.add_field(name="XP", value=str(u["xp"]), inline=False)
    e.add_field(name="Major", value=cat.majors.get(major, {}).get("title", major))
    e.add_field(name="Streak", value=f"{u['streak_days']} d")
    e.add_field(name="Engine", value=u["ue_version"] or "set with /profile")
    e.add_field(name="Next unlock", value=next_line, inline=False)
    e.add_field(name="Medals", value=" · ".join(medals) if medals else "—", inline=False)
    return e
