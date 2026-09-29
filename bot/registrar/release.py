"""Reads CHANGELOG.md (repo root) so the bot knows its version and can post patch notes.

Versions follow Semantic Versioning (https://semver.org): MAJOR.MINOR.PATCH, written with a leading "v".
  MAJOR  breaking change for members: progress reset, ranks/XP rebalanced, commands removed or renamed
  MINOR  new things, backwards compatible: new quests, channels, commands, features
  PATCH  fixes only: typos, broken links, bug fixes, wording
While MAJOR is 0 the server is still pre-release; anything may change between MINOR versions.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

# vMAJOR.MINOR.PATCH with an optional pre-release suffix (e.g. v1.2.0-beta.1), as in SemVer 2.0.0.
SEMVER = r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?"
HEADER = re.compile(rf"^## ({SEMVER})\s*·\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*·\s*(.+)$")
LOOSE_HEADER = re.compile(r"^## ")


def version_key(v: str) -> tuple:
    m = re.fullmatch(SEMVER, v)
    major, minor, patch, pre = int(m[1]), int(m[2]), int(m[3]), m[4]
    return (major, minor, patch, 0 if pre else 1, pre or "")      # a pre-release sorts before its release


def entries(changelog: Path) -> list[dict]:
    """Every entry, newest first: [{"version", "date", "title", "body"}, ...]."""
    if not changelog.exists():
        return []
    out: list[dict] = []
    for line in changelog.read_text(encoding="utf-8").splitlines():
        m = HEADER.match(line.strip())
        if m:
            out.append({"version": m.group(1), "date": m.group(6), "title": m.group(7).strip(), "lines": []})
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
            errs.append(f"line {n}: header must look like '## v1.2.3 · 2026-10-01 · Title' (got {line.strip()!r})")
    es = entries(changelog)
    seen = set()
    for newer, older in zip(es, es[1:]):
        if version_key(newer["version"]) <= version_key(older["version"]):
            errs.append(f"{newer['version']} is listed above {older['version']} but isn't a higher version")
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
