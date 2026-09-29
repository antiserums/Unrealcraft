"""Checklist verification.

A checklist item in YAML is either a plain string (honor) or a mapping:

    - text: "React to someone else's showcase post."
      check: {fact: react.showcase}            # the bot saw it happen
    - text: "Join Studio Floor for 60s, or /skip-voice."
      check: {any: [voice.studio_floor, cmd.skip_voice]}
    - text: "Post one screenshot of the graph."
      check: {attachment: image}               # validated on /submit
    - text: "Link your review comment."
      check: {link: showcase, author: self, on: others}   # validated on /submit
    - text: "Explain what you changed."
      check: {min_length: 120}

Facts are small timestamped records the bot writes when it sees something happen (kv key "fact:<name>").
Fact names in use:
  rules.accepted            Rules Screening accepted (or the member was never gated)
  cmd.<name>                a slash command was used: rank, quest, path, major, skip_voice, profile_version
  btn.<key>                 a pinned button was pressed: clockin
  quiz.<QID>                a quiz was passed
  submit.<QID>              a dry-run submit (O5)
  msg.<channel_key>         posted at least one message in that channel
  react.<channel_key>       reacted to someone else's post there
  voice.<channel_key>       60s in that voice channel
  thread.<channel_key>      opened a post there through the bot's form
  nick.major                server nickname looks like "Name | Major"
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
            out.append(Item(raw.get("text", ""), raw.get("check")))
        else:
            out.append(Item(str(raw), None))
    return out


def status_lines(q, facts: set[str]) -> list[str]:
    """✅ seen by the bot · ☐ not yet · 📎 checked when you submit · ▫ on your honor."""
    lines = []
    for it in items(q):
        if it.kind == "fact":
            lines.append(("✅ " if it.fact_ok(facts) else "☐ ") + it.text)
        elif it.kind == "submit":
            lines.append("📎 " + it.text)
        else:
            lines.append("▫ " + it.text)
    return lines


def facts_missing(q, facts: set[str]) -> list[str]:
    return [it.text for it in items(q) if it.kind == "fact" and not it.fact_ok(facts)]


def fully_auto(q) -> bool:
    """True if every item is bot-verifiable from facts. Such quests complete themselves."""
    its = items(q)
    return bool(its) and all(it.kind == "fact" for it in its)


async def validate_submit(bot, q, uid: int, proof: str, attachment) -> list[str]:
    """Returns human-readable problems; empty = OK."""
    problems: list[str] = []
    checks = [it.check for it in items(q) if it.kind == "submit"]
    if not checks and q.raw.get("verify_type") in SUBMIT_DEFAULTS:
        checks = [SUBMIT_DEFAULTS[q.raw["verify_type"]]]
    for c in checks:
        if "attachment" in c:
            want = c["attachment"]
            ctype = (attachment.content_type or "") if attachment else ""
            if not attachment or (want in ("image", "video") and not ctype.startswith(want + "/")):
                problems.append(f"Attach a {want} (as a file on /submit, not a link).")
        if "min_length" in c and len(proof.strip()) < c["min_length"]:
            problems.append(f"Write at least {c['min_length']} characters (you wrote {len(proof.strip())}).")
        if "link" in c:
            problems += await _check_link(bot, c, uid, proof)
    return problems


async def _check_link(bot, c: dict, uid: int, proof: str) -> list[str]:
    m = LINK_RE.search(proof)
    if not m:
        return ["Paste a message link (right-click the message → Copy Message Link)."]
    gid, cid, mid = map(int, m.groups())
    guild = bot.get_guild(gid)
    if not guild or gid != bot.settings.guild_id:
        return ["That link isn't from this server."]
    ch = guild.get_channel_or_thread(cid)
    if ch is None:
        try:
            ch = await guild.fetch_channel(cid)
        except Exception:
            return ["I can't open that channel."]
    want_parent = bot.unlocks.channel(c["link"])
    parent_id = getattr(ch, "parent_id", None)
    if want_parent and want_parent not in (ch.id, parent_id):
        return [f"That link must point into #{c['link'].replace('_', '-')}."]
    try:
        msg = await ch.fetch_message(mid)
    except Exception:
        return ["I can't find that message. Was it deleted?"]
    if c.get("author", "self") == "self" and msg.author.id != uid:
        return ["That message isn't yours."]
    owner = getattr(ch, "owner_id", None)
    if c.get("on") == "others" and owner == uid:
        return ["Link a comment on someone else's post, not your own."]
    if c.get("on") == "own" and owner != uid:
        return ["Link a reply inside your own post."]
    return []
