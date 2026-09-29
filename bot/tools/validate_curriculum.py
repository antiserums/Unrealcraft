"""Validate curriculum/*.yaml and print a per-major summary.

Usage (from bot/):  python tools/validate_curriculum.py [--warnings] [--path MAJOR]
Exit code 1 if there are errors.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from registrar.curriculum import Catalog, UserState  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parents[2] / "curriculum"))
    ap.add_argument("--warnings", action="store_true")
    ap.add_argument("--path", metavar="MAJOR", help="print a sample /path for a fresh Greenlit of this major")
    args = ap.parse_args()

    cat = Catalog.load(Path(args.dir))
    errs, warns = cat.validate()
    from registrar import release
    errs += [f"CHANGELOG: {e}" for e in release.validate(Path(args.dir).parent / "CHANGELOG.md")]
    print(f"{len(cat.quests)} quests loaded from {args.dir}")
    for e in errs:
        print("ERROR  ", e)
    if args.warnings:
        for w in warns:
            print("warn   ", w)
    else:
        print(f"{len(warns)} warnings (use --warnings)")

    print("\nRequired XP by major and rank (quests + tasters, first option of each group):")
    for major in ("level_design", "programming", "lookdev"):
        row = []
        for r in (1, 2, 3):
            xp = sum(q.xp for q in cat.required(major, r))
            xp += sum(cat.quests[g[0]].xp for g in cat.taster_groups(major, r) if g and g[0] in cat.quests)
            row.append(f"R{r}={xp}")
        print(f"  {major:<14}", "  ".join(row))

    if args.path:
        done = {q.id for q in cat.orientation()} | {f"S{i}" for i in range(1, 7)}
        print()
        print("\n".join(cat.path_lines(UserState(args.path, 0, done))))
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
