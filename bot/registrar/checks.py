"""Checklist verification.

A checklist item in YAML is either a plain string (honor) or a mapping:

    - text: "React to someone else's showcase post."
      check: {fact: site.card}                 # the site saw it happen
    - text: "Open your path, or your achievements."
      check: {any: [site.path, site.achievements]}
    - text: "Post one screenshot of the graph."
      check: {attachment: image}               # validated on /submit
    - text: "Link your review comment."
      check: {link: showcase, author: self, on: others}   # validated on /submit
    - text: "Explain what you changed."
      check: {min_length: 120}

Facts are small timestamped records the site writes when a member does something (kv key "fact:<name>").
The fact names in use are listed in api/app/progress.py. The website validates the submit-side checks
(attachment, min_length, link) in api/app/routers/submit.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

LINK_RE = re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)")

SUBMIT_DEFAULTS = {             # applied when a quest's checklist has no submit-side checks of its own
    "screenshot": {"attachment": "image"},
    "writeup": {"min_length": 80},
}


@dataclass
class Item:
    text: str
    check: dict | None
    needs_others: bool = False

    @property
    def kind(self) -> str:
        if not self.check:
            return "honor"
        if "fact" in self.check or "any" in self.check:
            return "fact"
        return "submit"

    def fact_ok(self, facts: set[str]) -> bool:
        if "fact" in self.check:
            return self.check["fact"] in facts
        return any(f in facts for f in self.check["any"])


def items(q) -> list[Item]:
    out = []
    for raw in q.raw.get("checklist") or []:
        if isinstance(raw, dict):
            out.append(Item(raw.get("text", ""), raw.get("check"), bool(raw.get("needs_others"))))
        else:
            out.append(Item(str(raw), None))
    return out


def status_lines(q, facts: set[str], community_ready: bool = True) -> list[str]:
    """✅ seen by the site · ☐ not yet · 📎 checked when you submit · ▫ on your honor."""
    lines = []
    for it in items(q):
        if it.needs_others and not community_ready:
            lines.append("⏳ (optional for now: needs more members) " + it.text)
        elif it.kind == "fact":
            lines.append(("✅ " if it.fact_ok(facts) else "☐ ") + it.text)
        elif it.kind == "submit":
            lines.append("📎 " + it.text)
        else:
            lines.append("▫ " + it.text)
    return lines


def facts_missing(q, facts: set[str]) -> list[str]:
    return [it.text for it in items(q) if it.kind == "fact" and not it.fact_ok(facts)]


def fully_auto(q) -> bool:
    """True if every item is verifiable from facts. Such quests complete themselves."""
    its = items(q)
    return bool(its) and all(it.kind == "fact" for it in its)
