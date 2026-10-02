from __future__ import annotations

import subprocess
import time

from fastapi import APIRouter

from registrar import release  # noqa: E402

from ..config import settings

router = APIRouter(tags=["changelog"])
_rev: tuple[float, int | None] = (0.0, None)


def running_rev() -> int | None:
    """The revision this server runs: the number of commits in its checkout, the same count a release takes as its
    build number. None when git cannot be asked. Looked up at most once a minute."""
    global _rev
    if time.time() - _rev[0] > 60:
        try:
            out = subprocess.run(["git", "-C", str(settings.changelog_path.parent), "rev-list", "--count", "HEAD"],
                                 capture_output=True, text=True, timeout=10)
            _rev = (time.time(), int(out.stdout) if out.returncode == 0 else None)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            _rev = (time.time(), None)
    return _rev[1]


@router.get("/changelog")
async def changelog():
    """Every release, newest first. `rev` on an entry is its build number (the fourth number of its version)."""
    es = release.entries(settings.changelog_path)
    for e in es:
        e["rev"] = release.build_of(e["version"])
    return {"current": es[0]["version"] if es else None, "rev": running_rev(), "entries": es}
