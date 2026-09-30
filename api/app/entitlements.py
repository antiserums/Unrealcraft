"""Entitlements: every unlock an account can hold.

Kinds: outfit, nameplate (colour), avatar_frame, card_frame, title ("Name, the Learner") and achievement.
The built-in catalog is seeded from `rpg.py` (it mirrors the art pack). Admins add, edit or disable rows in the
`entitlements` table; a row with the same (kind, id) as a built-in overrides it. A member can also be handed one
directly (`entitlement_grants`), which counts as owned whatever the unlock rule says.

Unlock rules (`unlock` json):
  {"type": "starter"}                       everyone
  {"type": "rank", "n": 2}                  reach guild rank n
  {"type": "achievement", "key": "rooms_10"} earn that achievement
  {"type": "medal", "key": "some_medal"}    hold that medal (staff grant medals on Discord or in the admin panel)
  {"type": "staff", "role": "mentor"}       staff role (admins and developers own everything anyway)
  {"type": "granted"}                       only by a direct grant from the admin panel
Achievements use `data` for their condition instead: {"of": counter, "need": n, "icon": "…", "badge": n}.
"""
from __future__ import annotations

import json
import re

KINDS = ["outfit", "nameplate", "avatar_frame", "card_frame", "title", "achievement"]
KIND_LABEL = {"outfit": "Outfit", "nameplate": "Nameplate colour", "avatar_frame": "Avatar frame", "card_frame": "Player card frame",
              "title": "Title", "achievement": "Achievement"}
UNLOCK_TYPES = ["starter", "rank", "achievement", "medal", "staff", "granted"]
COUNTERS = ["done", "first", "approved", "reads", "streak", "capstones", "medal"]     # what an achievement counts
COUNTER_LABEL = {"done": "quests finished", "first": "bosses beaten first try", "approved": "work accepted by a reviewer",
                 "reads": "readings opened", "streak": "day streak", "capstones": "capstone dungeons cleared", "medal": "a medal with this key"}
ID_RE = re.compile(r"^[a-z0-9_]{2,40}$")


def owned(unlock: dict, *, rank: int, earned: set[str], medals: set[str], role: str | None) -> bool:
    """Does the rule alone make this owned? Direct grants are checked by the caller."""
    t = unlock.get("type")
    if t == "starter":
        return True
    if t == "rank":
        return rank >= int(unlock.get("n", 99))
    if t == "achievement":
        return unlock.get("key") in earned
    if t == "medal":
        return unlock.get("key") in medals
    if t == "staff":
        return role == unlock.get("role")
    return False


def hint_for(unlock: dict, ranks: dict | None = None) -> str | None:
    """A short sentence for a locked item. Custom rows may carry their own `hint`."""
    if unlock.get("hint"):
        return unlock["hint"]
    t = unlock.get("type")
    if t == "rank":
        n = int(unlock.get("n", 0))
        title = (ranks or {}).get(n, {}).get("title") or f"rank {n}"
        return f"Reach {title}"
    if t == "achievement":
        return f"Earn the achievement {unlock.get('key')}"
    if t == "medal":
        return f"Hold the medal {unlock.get('key')}"
    if t == "staff":
        return f"{str(unlock.get('role', '')).title()}s only"
    if t == "granted":
        return "Granted by staff"
    return None


class Entitlements:
    """The merged catalog: built-ins from rpg.py plus the admin table. Reloaded after every admin change."""

    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by_key = {(r["kind"], r["id"]): r for r in rows}

    def of(self, kind: str, include_disabled: bool = False) -> list[dict]:
        return [r for r in self.rows if r["kind"] == kind and (include_disabled or r["enabled"])]

    def get(self, kind: str, eid: str) -> dict | None:
        return self.by_key.get((kind, eid))

    @classmethod
    async def load(cls, rdb) -> "Entitlements":
        from . import rpg
        rows = {(r["kind"], r["id"]): r for r in rpg.default_entitlements()}
        for r in await rdb.entitlement_rows():
            key = (r["kind"], r["id"])
            base = rows.get(key, {"kind": r["kind"], "id": r["id"], "builtin": False, "data": {}})
            rows[key] = {**base, "name": r["name"], "desc": r["desc"] or "", "data": {**base.get("data", {}), **json.loads(r["data"] or "{}")},
                         "unlock": json.loads(r["unlock"] or '{"type":"starter"}'), "sort": r["sort"], "enabled": bool(r["enabled"]),
                         "custom": True, "updated_at": r["updated_at"]}
        out = sorted(rows.values(), key=lambda r: (KINDS.index(r["kind"]), r.get("sort", 0), r["id"]))
        for r in out:
            r.setdefault("custom", False)
            r.setdefault("enabled", True)
            r.setdefault("builtin", True)
        return cls(out)


def validate_row(kind: str, eid: str, name: str, unlock: dict, data: dict) -> list[str]:
    errs = []
    if kind not in KINDS:
        errs.append("Unknown kind.")
    if not ID_RE.match(eid or ""):
        errs.append("Id: 2 to 40 lower-case letters, digits or underscores.")
    if not (name or "").strip():
        errs.append("Name is required.")
    if kind == "achievement":
        if data.get("of") not in COUNTERS:
            errs.append("Achievement: pick what it counts.")
        if not isinstance(data.get("need"), int) or data.get("need", 0) < 1:
            errs.append("Achievement: need must be a whole number of at least 1.")
    else:
        t = unlock.get("type")
        if t not in UNLOCK_TYPES:
            errs.append("Unlock: pick a rule.")
        if t == "rank" and not isinstance(unlock.get("n"), int):
            errs.append("Unlock: rank needs a number.")
        if t in ("achievement", "medal") and not str(unlock.get("key", "")).strip():
            errs.append("Unlock: that rule needs a key.")
        if t == "staff" and unlock.get("role") not in ("admin", "developer", "mentor"):
            errs.append("Unlock: staff role must be admin, developer or mentor.")
    if kind == "nameplate" and not re.match(r"^#[0-9A-Fa-f]{6}$", str(data.get("value", ""))):
        errs.append("Nameplate: value must be a hex colour like #4AA3B5.")
    if kind == "outfit":
        if not data.get("art_id"):
            errs.append("Outfit: art id (a set in the art pack) is required.")
        if data.get("tier") not in ("novice", "apprentice", "adept", "expert", "master"):
            errs.append("Outfit: tier must be novice, apprentice, adept, expert or master.")
    if kind in ("avatar_frame", "card_frame") and eid != "none" and not data.get("art"):
        errs.append("Frame: art id (a decoration in the art pack) is required.")
    return errs
