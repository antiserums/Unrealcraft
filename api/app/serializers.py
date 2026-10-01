"""Turn curriculum objects into JSON. Quiz answers never leave the API."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from registrar import checks  # noqa: E402
from registrar.curriculum import TIERS, Catalog, Quest, UserState  # noqa: E402

from .config import settings


_titles: tuple[float, dict[str, str]] = (0.0, {})
_SMALL = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def link_titles() -> dict[str, str]:
    """Page titles by URL, fetched by tools/link_titles.py into curriculum/link_titles.json. Read again when the file changes."""
    global _titles
    f = Path(settings.curriculum_dir) / "link_titles.json"
    try:
        mtime = f.stat().st_mtime
        if mtime != _titles[0]:
            _titles = (mtime, json.loads(f.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return _titles[1]


def link_label(url: str) -> str:
    """What a reading link is called: the page's own title, or, for a link not fetched yet, a title made from its address."""
    if (t := link_titles().get(url)):
        return t
    parts = urlparse(url)
    slug = parts.path.rstrip("/").rsplit("/", 1)[-1]
    words = [w for w in re.split(r"[-_]+", slug) if w]
    if not words or "youtu" in parts.netloc or len(slug) < 4:
        return parts.netloc.removeprefix("www.")
    return " ".join(w if i and w in _SMALL else w.capitalize() for i, w in enumerate(words))


def reading_links(q: Quest) -> list[dict]:
    """Every link names itself by its page title; `kind` says where it comes from (official, extra, community, backup)."""
    r, out = q.raw, []
    if (u := r.get("official_url")) and u.startswith("http"):
        out.append({"label": link_label(u), "url": u, "kind": "official"})
    for u in r.get("extra_urls") or []:
        if u.startswith("http"):
            out.append({"label": link_label(u), "url": u, "kind": "extra"})
    for c in r.get("community_urls") or []:
        u, t = (c.get("url", ""), c.get("title")) if isinstance(c, dict) else (c, None)
        if u.startswith("http"):
            out.append({"label": t or link_label(u), "url": u, "kind": "community"})
    if (u := r.get("backup_url")) and u.startswith("http"):
        out.append({"label": link_label(u), "url": u, "kind": "backup"})
    seen: set[str] = set()                                   # the same page listed twice shows once
    return [x for x in out if not (x["url"] in seen or seen.add(x["url"]))]


def checklist(q: Quest, facts: set[str], community_ready: bool) -> list[dict]:
    out = []
    for it in checks.items(q):
        if it.needs_others and not community_ready:
            state = "optional"
        elif it.kind == "fact":
            state = "done" if it.fact_ok(facts) else "todo"
        elif it.kind == "submit":
            state = "on_submit"
        else:
            state = "honor"
        out.append({"text": it.text, "state": state})
    return out


def _who(who: UserState | str | None) -> tuple[str | None, list[str]]:
    """The viewer's primary specialization and extras, from a UserState or a bare key."""
    if isinstance(who, UserState):
        return who.major, who.extras
    return who, []


def quest_summary(cat: Catalog, q: Quest, who: UserState | str | None = None) -> dict:
    r = q.raw
    major, extras = _who(who)
    return {
        "id": q.id, "title": r["title"], "rank": q.rank, "difficulty": q.difficulty,
        "tier": {"name": q.tier["name"], "emoji": q.tier["emoji"], "color": q.tier["color"]},
        "specializations": q.specializations, "required": q.required, "taster_for": q.taster_for,
        "subjects": r.get("subjects") or [], "xp": q.xp, "time_min": r.get("time_min"),
        "kind": "capstone" if q.capstone else ("required" if q.required else "elective"),
        "spine": q.spine, "first_steps": q.first_steps, "verify_type": r.get("verify_type"), "has_quiz": bool(q.quiz), "quiz_len": len(q.quiz),
        "owner": cat.owner_label(q),
        "affinity": cat.affinity(q, major, extras) if major else None,
    }


def quest_full(cat: Catalog, q: Quest, who: UserState | str | None, facts: set[str]) -> dict:
    r = q.raw
    d = quest_summary(cat, q, who)
    major, _ = _who(who)
    fl = q.flavor(major or "undecided")
    d.update({
        "why": fl.get("why"), "do": fl.get("do"),
        "reading": reading_links(q),
        "checklist": checklist(q, facts, cat.community_ready),
        "done_when": r.get("done_when_solo") if (not cat.community_ready and r.get("done_when_solo")) else r.get("done_when"),
        "step": r.get("step"),
        "quiz": [{"q": item["q"], "choices": item["choices"]} for item in q.quiz],   # no answer_index, no explain
        "file": r.get("_file"),
    })
    return d


def specializations_meta(cat: Catalog) -> dict:
    return {
        "tiers": TIERS,
        "ranks": [{k: v for k, v in r.items()} for r in cat.meta.get("ranks", [])],
        "specializations": {k: {"key": k, "title": v.get("title", k), "prefix": v.get("prefix"), "blurb": v.get("blurb"),
                                "capstones": v.get("capstones") or {}} for k, v in cat.specializations.items()},
        "xp_rules": cat.xp_rules,
        "quest_count": len(cat.quests),
    }
