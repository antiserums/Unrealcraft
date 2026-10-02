"""Reads CHANGELOG.md (repo root) so the bot knows its version and can post patch notes.

Versions are written vMAJOR.MINOR.PATCH.BUILD, the way Unreal Engine builds carry a changelist number:
  MAJOR  breaking change for members: progress reset, ranks/XP rebalanced, commands removed or renamed
  MINOR  new things, backwards compatible: new quests, channels, commands, features
  PATCH  fixes only: typos, broken links, bug fixes, wording
  BUILD  the number of commits in the repo at that release (`tools/version.py next` works it out). It only goes up,
         so two builds can always be told apart, even of the same release.
Unrealcraft is pre-release: every release so far is v0.1.0 with its own build number (its "rev"), and the first three
numbers only move on a milestone the owner decides on.
The first 15 releases were first published under other numbers (v0.2.0 … v0.10.1), see FIRST_NAMES.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

# vMAJOR.MINOR.PATCH.BUILD; the build is missing on old releases. A pre-release suffix (v1.2.0.700-beta.1) is allowed.
SEMVER = r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:-([0-9A-Za-z.-]+))?"
# "## v1.2.3.700 · 2026-10-01" (an old-style " · Title" suffix is still accepted and ignored)
HEADER = re.compile(rf"^## ({SEMVER})\s*·\s*(\d{{4}}-\d{{2}}-\d{{2}})(?:\s*·\s*(.+))?$")
LOOSE_HEADER = re.compile(r"^## ")


def version_key(v: str) -> tuple:
    m = re.fullmatch(SEMVER, v)
    major, minor, patch, build, pre = int(m[1]), int(m[2]), int(m[3]), int(m[4] or 0), m[5]
    return (major, minor, patch, 0 if pre else 1, pre or "", build)   # a pre-release sorts before its release


# The first 15 releases, by build number: the version each one was first published (and tagged, and posted) under.
FIRST_NAMES = {1: "v0.1.0", 3: "v0.2.0", 6: "v0.3.0", 9: "v0.3.1", 11: "v0.3.2", 14: "v0.4.0", 18: "v0.5.0", 20: "v0.6.0",
               22: "v0.6.1", 28: "v0.7.0", 31: "v0.8.0", 33: "v0.9.0", 35: "v0.9.1", 39: "v0.10.0", 41: "v0.10.1"}


def build_of(v: str) -> int | None:
    """The build number of a version, or None for a release from before builds were numbered."""
    m = re.fullmatch(SEMVER, v)
    return int(m[4]) if m and m[4] is not None else None


def entries(changelog: Path) -> list[dict]:
    """Every entry, newest first: [{"version", "date", "title", "body"}, ...]."""
    if not changelog.exists():
        return []
    out: list[dict] = []
    for line in changelog.read_text(encoding="utf-8").splitlines():
        m = HEADER.match(line.strip())
        if m:
            out.append({"version": m.group(1), "date": m.group(7), "title": (m.group(8) or "").strip(), "lines": []})
        elif out:
            out[-1]["lines"].append(line)
    for e in out:
        e["body"] = "\n".join(e.pop("lines")).strip()
    return out


def validate(changelog: Path) -> list[str]:
    """Problems with the changelog: bad headers, duplicate versions, or versions that don't go down newest→oldest."""
    errs = []
    if not changelog.exists():
        return ["CHANGELOG.md is missing"]
    for n, line in enumerate(changelog.read_text(encoding="utf-8").splitlines(), 1):
        if LOOSE_HEADER.match(line) and not HEADER.match(line.strip()):
            errs.append(f"line {n}: header must look like '## v1.2.3.700 · 2026-10-01' (got {line.strip()!r})")
    es = entries(changelog)
    seen = set()
    for newer, older in zip(es, es[1:]):
        if version_key(newer["version"]) <= version_key(older["version"]):
            errs.append(f"{newer['version']} is listed above {older['version']} but isn't a higher version")
        nb, ob = build_of(newer["version"]), build_of(older["version"])
        if ob is not None and (nb is None or nb <= ob):
            errs.append(f"{newer['version']} must have a higher build number than {older['version']}")
    for e in es:
        if e["version"] in seen:
            errs.append(f"{e['version']} appears twice")
        seen.add(e["version"])
    return errs


def latest(changelog: Path) -> dict:
    """The top entry (the bot's current version), or {}."""
    es = entries(changelog)
    return es[0] if es else {}


async def pushed_tags(repo: Path, remote: str = "origin") -> set[str] | None:
    """Version tags that exist on the remote (i.e. were pushed to GitHub). None if git/remote is unreachable.
    Patch notes are only posted for versions in this set."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "-C", str(repo), "ls-remote", "--tags", remote,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
    except (OSError, asyncio.TimeoutError):
        return None
    if proc.returncode != 0:
        return None
    tags = set()
    for line in out.decode().splitlines():
        ref = line.split("\t")[-1]
        if ref.startswith("refs/tags/"):
            tags.add(ref[len("refs/tags/"):].removesuffix("^{}"))
    return tags
