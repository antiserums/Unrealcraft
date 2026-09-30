"""One-off: majors become specializations, tracks go away.

Rewrites curriculum/*.yaml line by line (comments and order kept):
  track: x                      -> specializations: [..]   (required_for_majors + taster_for_majors, else the old track mapped)
  required_for_majors / taster_for_majors / adjacent_for   -> removed
  elective: true|false          -> required: false|true    (+ `taster: true`, or `taster_for: [..]` when it tastes for
                                                            specializations other than the ones it lives in)
and majors.yaml -> specializations.yaml with the `majors:` key renamed.
Run once from the repo root: py -3 tools/migrate_specializations.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "curriculum"
TRACK_TO_SPEC = {
    "level-design": ["level_design"], "environment-art": ["lookdev"], "programming": ["programming"], "animation": ["animation"],
    "cinematics": ["cinematics"], "gameplay-design": ["gameplay_design"], "tech-art": ["tech_art"],
    "starter-quests": ["all"], "orientation": ["all"], "tasters": ["all"],
    "characters-anim": ["animation"], "bay-design": ["level_design"], "bay-lookdev": ["lookdev"], "bay-code": ["programming"],
    "materials": ["lookdev"], "world-lighting": ["level_design", "lookdev"], "blueprint": ["level_design", "gameplay_design", "programming"],
}
LIST_RE = re.compile(r"^(\s*)(track|required_for_majors|taster_for_majors|adjacent_for|elective):\s*(.*?)\s*$")
COMMENT_WORDS = [(r"\bmajors\.yaml\b", "specializations.yaml"), (r"\bMajors\b", "Specializations"), (r"\bmajors\b", "specializations"),
                 (r"\bMajor\b", "Specialization"), (r"\bmajor\b", "specialization")]


def flow(v: str) -> list[str]:
    v = v.strip()
    if not v.startswith("["):
        return [v] if v and v != "null" else []
    return [s.strip().strip("'\"") for s in v[1:-1].split(",") if s.strip()]


def shared_owner_map(files: list[Path]) -> dict[tuple[str, str], set[str]]:
    """(file, old track) -> every specialization a required quest with that track in that file was required for."""
    out: dict[tuple[str, str], set[str]] = {}
    for f in files:
        for q in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("quests") or []:
            req = [m for m in (q.get("required_for_majors") or []) if m != "all"]
            if req and not q.get("elective"):
                out.setdefault((f.name, q.get("track", "")), set()).update(req)
    return out


def specs_for(q: dict, fname: str, shared: dict) -> list[str]:
    """Where the quest lives: what it was required for, else (a pure taster) what it tasted, else its old track."""
    req, tas = q.get("required_for_majors") or [], q.get("taster_for_majors") or []
    if "all" in req:
        return ["all"]
    if req:
        return list(req)
    if tas:
        return list(tas)
    track = q.get("track", "")
    owners = shared.get((fname, track))
    if owners and track in ("world-lighting", "blueprint", "materials", "characters-anim", "bay-design", "bay-lookdev", "bay-code"):
        return sorted(owners)
    return TRACK_TO_SPEC.get(track, [track.replace("-", "_")])


def rewrite_quests(path: Path, shared: dict) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    by_id = {q["id"]: q for q in doc.get("quests") or []}
    out, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\s*)- id:\s*(\S+)", line)
        if m:
            cur = by_id[m.group(2).strip("'\"")]
        lm = LIST_RE.match(line)
        if lm and cur is not None:
            indent, key, val = lm.groups()
            if key == "track":
                out.append(f"{indent}specializations: [{', '.join(specs_for(cur, path.name, shared))}]")
            elif key == "elective":
                elective = val.strip().lower() == "true"
                # "required" means required within its specializations, so a quest nobody required (a pure taster,
                # or an unowned non-elective) is not required; tasters are owed through required_tasters instead.
                out.append(f"{indent}required: {'false' if (elective or not cur.get('required_for_majors')) else 'true'}")
                tas = cur.get("taster_for_majors") or []
                if tas and set(tas) == set(specs_for(cur, path.name, shared)):
                    out.append(f"{indent}taster: true")                       # a taster for the specializations it lives in
                elif tas:
                    out.append(f"{indent}taster_for: [{', '.join(tas)}]")      # lives in some, is a taster for others
            continue                                   # required_for_majors / taster_for_majors / adjacent_for are dropped
        if line.lstrip().startswith("#"):
            for pat, rep in COMMENT_WORDS:
                line = re.sub(pat, rep, line)
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def rewrite_meta(src: Path, dst: Path) -> None:
    out = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.startswith("majors:"):
            line = "specializations:"
        line = line.replace("in_major_multiplier_rank3plus", "in_specialization_multiplier_rank3plus")
        if line.lstrip().startswith("#") or ":" in line and line.split(":")[0].strip() in ("opens", "blurb", "brief"):
            for pat, rep in COMMENT_WORDS:
                line = re.sub(pat, rep, line)
        out.append(line)
    dst.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    if src != dst:
        src.unlink()


def main() -> None:
    files = [f for f in sorted(ROOT.glob("*.yaml")) if f.name not in ("majors.yaml", "specializations.yaml")]
    shared = shared_owner_map(files)
    for f in files:
        rewrite_quests(f, shared)
        print("rewrote", f.name)
    if (ROOT / "majors.yaml").exists():
        rewrite_meta(ROOT / "majors.yaml", ROOT / "specializations.yaml")
        print("majors.yaml -> specializations.yaml")


if __name__ == "__main__":
    main()
