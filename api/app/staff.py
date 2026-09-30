"""Staff roles for the website: admin, developer, mentor.

  admin      ADMIN_IDS in api/.env. Everything unlocked for testing, the admin panel, the review inbox.
  developer  DEVELOPER_IDS, plus the local dev login. Same powers as admin; a different nameplate.
  mentor     MENTOR_IDS, or the Discord staff mentor role / rank 6 on the session. The review inbox only:
             no unlocks, no admin panel. Their nameplate reads Mentor.

The nameplate replaces the player rank title on the site (top bar, player cards, leaderboard); XP and rank
underneath are untouched."""
from __future__ import annotations

from pathlib import Path

import yaml

from .config import settings

TITLES = {"admin": ("Admin", "#D4AF37"), "developer": ("Developer", "#3FB6B0"), "mentor": ("Mentor", "#6FB3A0")}


def _discord_staff_roles() -> set[int]:
    """Role ids the bot treats as mentors (from its unlocks.yaml). Missing file or ids -> empty."""
    try:
        data = yaml.safe_load(Path(settings.unlocks_path).read_text(encoding="utf-8")) or {}
    except OSError:
        return set()
    roles = data.get("roles") or {}
    ids = {int(((roles.get("staff") or {}).get("mentor")) or 0), int(((roles.get("rank") or {}).get(6)) or 0)}
    return {i for i in ids if i}


def role_of_id(uid: int) -> str | None:
    """Staff role by Discord id alone (for other members' cards and the leaderboard)."""
    uid = int(uid)
    if uid in settings.admin_ids:
        return "admin"
    if uid in settings.developer_ids:
        return "developer"
    if uid in settings.mentor_ids:
        return "mentor"
    return None


def role_of(member: dict | None) -> str | None:
    """Staff role for a logged-in session: the id lists first, then the dev login, then Discord roles."""
    if not member:
        return None
    r = role_of_id(member["id"])
    if r:
        return r
    if member.get("dev"):
        return "developer"
    session_roles = {int(x) for x in member.get("roles", []) if str(x).isdigit()}
    if session_roles & _discord_staff_roles():
        return "mentor"
    return None


def is_admin(member: dict | None) -> bool:
    """Admin panel and unlock-all: admins and developers."""
    return role_of(member) in ("admin", "developer")


def can_review(member: dict | None) -> bool:
    return role_of(member) is not None


def unlock_all(member: dict | None) -> bool:
    return is_admin(member)


def nameplate_for(role: str | None) -> tuple[str, str] | None:
    return TITLES.get(role or "")
