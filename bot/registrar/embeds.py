"""Embed builders. Dark UI with the rank color as the accent."""
from __future__ import annotations

import re

import discord

from . import checks
from .curriculum import Catalog, Quest

DARK = discord.Color.from_str("#1E1F22")
GOLD = discord.Color.from_str("#D4AF37")


def rank_color(cat: Catalog, rank: int) -> discord.Color:
    c = cat.ranks.get(rank, {}).get("color")
    return discord.Color.from_str(c) if c else DARK


def nameplate(cat: Catalog, rank: int, major: str) -> str:
    """Rank title; from Expert up the major is the specialty and joins the plate: 'Expert · Level Design'."""
    if rank < 0:
        return "Orientation"
    title = cat.ranks[rank]["title"]
    if 3 <= rank < 6 and major and major != "undecided":
        return f"{title} · {cat.majors.get(major, {}).get('title', major)}"
    return title


_CHANNEL_REF = re.compile(r"(?<![<\w])#([a-z0-9][a-z0-9-]*)")


def linkify(text: str | None, guild: discord.Guild | None) -> str | None:
    """'#welcome' -> '<#id>' (a clickable channel link) for channels that exist on the server."""
    if not text or guild is None:
        return text

    def repl(m: re.Match) -> str:
        ch = discord.utils.get(guild.channels, name=m.group(1))
        return ch.mention if ch else m.group(0)
    return _CHANNEL_REF.sub(repl, text)


def reading_links(q: Quest) -> list[tuple[str, str]]:
    """(label, url) for a quest's learning material: the Epic page first, then extras, community guides,
    then a backup video. `community_urls` items are a URL or {title, url}."""
    r, out = q.raw, []
    if (u := r.get("official_url")) and u.startswith("http"):
        out.append(("Official Epic guide", u))
    for i, u in enumerate(r.get("extra_urls") or [], 1):
        if u.startswith("http"):
            out.append((f"Extra reading {i}", u))
    for i, c in enumerate(r.get("community_urls") or [], 1):
        u, t = (c.get("url", ""), c.get("title")) if isinstance(c, dict) else (c, None)
        if u.startswith("http"):
            out.append((t or f"Community guide {i}", u))
    if (u := r.get("backup_url")) and u.startswith("http"):
        out.append(("Backup video", u))
    return out


def guide_view(q: Quest, view: discord.ui.View | None = None) -> discord.ui.View | None:
    """Link buttons to the material (Discord opens them in the browser)."""
    links = reading_links(q)
    if not links:
        return view
    view = view or discord.ui.View(timeout=None)
    label, url = links[0]
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Open the guide", emoji="📖", url=url))
    return view


def quest_embed(cat: Catalog, q: Quest, major: str, reason: str | None = None,
                facts: set[str] | None = None, guild: discord.Guild | None = None) -> discord.Embed:
    e = _quest_embed(cat, q, major, reason, facts)
    for i, f in enumerate(e.fields):
        e.set_field_at(i, name=f.name, value=linkify(f.value, guild), inline=f.inline)
    if e.description:
        e.description = linkify(e.description, guild)
    return e


def _quest_embed(cat: Catalog, q: Quest, major: str, reason: str | None = None,
                 facts: set[str] | None = None) -> discord.Embed:
    r = q.raw
    fl = q.flavor(major)
    kind = "capstone" if q.capstone else ("elective" if q.elective else "required")
    rank_label = "Orientation" if q.rank < 0 else f"Rank {q.rank}"
    e = discord.Embed(
        title=f"{q.id} · {r['title']}",
        description=(f"*{fl['why']}*" if fl.get("why") else None),
        color=discord.Color.from_str(q.tier["color"]),
    )
    e.add_field(name="Info", value=f"**{q.tier_label}** · {rank_label} · {kind} · ~{r.get('time_min', '?')} min · "
                                   f"**{q.xp} XP**",
                inline=False)
    if fl.get("do"):
        e.add_field(name="Your version", value=fl["do"], inline=False)
    links = reading_links(q)
    has_quiz = bool(q.quiz)
    step = 1
    if links:
        e.add_field(name=f"📖 Step {step}: Read this first", inline=False, value=(
            "\n".join(f"• [{label}]({url})" for label, url in links)
            + ("\nThe quiz asks about this page." if has_quiz else ""))[:1024])
        step += 1
    checklist = checks.status_lines(q, facts or set(), cat.community_ready)
    if checklist:
        title = "🛠️ Step {}: Do this{}".format(step, " in Unreal" if q.rank >= 0 else "")
        e.add_field(name=title, value="\n".join(checklist)[:1024], inline=False)
        step += 1
    done_when = r.get("done_when_solo") if (not cat.community_ready and r.get("done_when_solo")) else r.get("done_when")
    e.add_field(name="Done when", value=(done_when or "—")[:1024], inline=False)
    vt = r.get("verify_type")
    if vt == "quiz":
        how = f"Pass `/quiz {q.id}`. That's all."
    elif vt == "action":
        how = "Nothing to send. The bot ticks it when it sees you do it."
    else:
        how = (f"`/quiz {q.id}` then " if q.quiz else "") + f"`/submit {q.id}`"
    e.add_field(name=f"✅ Step {step}: How to finish", value=how, inline=False)
    if reason:
        e.set_footer(text=f"Why this one: {reason}")
    return e


def rank_card(cat: Catalog, member: discord.abc.User, u, medals: list[str], next_line: str) -> discord.Embed:
    rank, major = u["rank"], u["major"]
    e = discord.Embed(title=nameplate(cat, rank, major), color=rank_color(cat, max(rank, 0)))
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
