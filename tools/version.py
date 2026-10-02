"""The next version number, the way Unreal Engine builds carry a changelist: vMAJOR.MINOR.PATCH.BUILD.

  py -3 tools/version.py               the released version, and the build this checkout would get
  py -3 tools/version.py next patch    the version to release next: fixes only
  py -3 tools/version.py next minor    new things that break nothing
  py -3 tools/version.py next major    breaking for members

BUILD is the number of commits in the repo at the release commit. `next` counts the commits there are now and adds
one for the release commit itself, so write the CHANGELOG entry and commit it as the next commit:

  ## v0.11.0.173 · 2026-10-02
  git commit -am "v0.11.0.173" && git tag -a v0.11.0.173 -m "v0.11.0.173"
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = re.compile(r"^## v(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?")


def commits() -> int:
    return int(subprocess.run(["git", "-C", str(ROOT), "rev-list", "--count", "HEAD"], capture_output=True, text=True, check=True).stdout)


def released() -> tuple[int, int, int, int | None]:
    for line in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        if (m := HEADER.match(line)):
            return int(m[1]), int(m[2]), int(m[3]), int(m[4]) if m[4] else None
    return 0, 0, 0, None


def main() -> None:
    major, minor, patch, build = released()
    now = commits()
    if len(sys.argv) >= 3 and sys.argv[1] == "next":
        step = sys.argv[2]
        if step == "major":
            major, minor, patch = major + 1, 0, 0
        elif step == "minor":
            minor, patch = minor + 1, 0
        elif step == "patch":
            patch += 1
        else:
            sys.exit("say: next patch, next minor or next major")
        print(f"v{major}.{minor}.{patch}.{now + 1}")
        return
    last = f"v{major}.{minor}.{patch}" + (f".{build}" if build is not None else "")
    print(f"released: {last}")
    print(f"this checkout: build {now}" + (f" ({now - build} commits since the release)" if build is not None else ""))


if __name__ == "__main__":
    main()
