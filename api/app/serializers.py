"""Turn curriculum objects into JSON. Quiz answers never leave the API."""
from __future__ import annotations

from registrar import checks  # noqa: E402
from registrar.curriculum import TIERS, Catalog, Quest  # noqa: E402


def reading_links(q: Quest) -> list[dict]:
    r, out = q.raw, []
    if (u := r.get("official_url")) and u.startswith("http"):
        out.append({"label": "Official Epic guide", "url": u, "kind": "official"})
    for i, u in enumerate(r.get("extra_urls") or [], 1):
        if u.startswith("http"):
            out.append({"label": f"Extra reading {i}", "url": u, "kind": "extra"})
    for i, c in enumerate(r.get("community_urls") or [], 1):
        u, t = (c.get("url", ""), c.get("title")) if isinstance(c, dict) else (c, None)
        if u.startswith("http"):
            out.append({"label": t or f"Community guide {i}", "url": u, "kind": "community"})
    if (u := r.get("backup_url")) and u.startswith("http"):
        out.append({"label": "Backup video", "url": u, "kind": "backup"})
    return out


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


def quest_summary(cat: Catalog, q: Quest, major: str | None = None) -> dict:
    r = q.raw
    return {
        "id": q.id, "title": r["title"], "rank": q.rank, "difficulty": q.difficulty,
        "tier": {"name": q.tier["name"], "emoji": q.tier["emoji"], "color": q.tier["color"]},
        "track": q.track, "subjects": r.get("subjects") or [], "xp": q.xp, "time_min": r.get("time_min"),
        "kind": "capstone" if q.capstone else ("elective" if q.elective else "required"),
        "spine": q.spine, "verify_type": r.get("verify_type"), "has_quiz": bool(q.quiz), "quiz_len": len(q.quiz),
        "owner": cat.owner_label(q), "required_for": q.required_for, "adjacent_for": q.adjacent_for,
        "affinity": cat.affinity(q, major) if major else None,
    }


def quest_full(cat: Catalog, q: Quest, major: str, facts: set[str]) -> dict:
    r = q.raw
    d = quest_summary(cat, q, major)
    fl = q.flavor(major)
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


def majors_meta(cat: Catalog) -> dict:
    return {
        "tiers": TIERS,
        "ranks": [{k: v for k, v in r.items()} for r in cat.meta.get("ranks", [])],
        "majors": {k: {"key": k, "title": v.get("title", k), "prefix": v.get("prefix"),
                       "capstones": v.get("capstones") or {}} for k, v in cat.majors.items()},
        "xp_rules": cat.xp_rules,
        "quest_count": len(cat.quests),
    }
