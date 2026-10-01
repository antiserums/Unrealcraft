"""Put reworded quiz text into the curriculum without touching anything else.

  py -3 tools/apply_quiz_wording.py wording.json [more.json ...]

Each JSON file maps a quest id to its questions, in the same order as the quest's quiz:
  { "SQ1": [ {"q": "...", "choices": ["...", "..."], "explain": "..."}, ... ] }

Only the `q`, `choices` and `explain` lines of those questions change. The answer (`answer_index`) and the order
of the choices stay as they are, so a rewrite must keep every choice in its place. A quest whose rewrite does not
match (a different number of questions or choices) is skipped and reported.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CURRICULUM = Path(__file__).resolve().parent.parent / "curriculum"
ID_RE = re.compile(r"^  - id:\s*[\"']?([A-Za-z0-9_]+)")
Q_RE = re.compile(r"^(\s+)- q: ")
FIELD_RE = re.compile(r"^(\s+)(choices|answer_index|explain): ")


def s(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)          # a JSON string is a valid YAML double-quoted string


def choices_on(line: str) -> int:
    try:
        return len(json.loads(line.split("choices: ", 1)[1]))
    except ValueError:
        return -1                                          # not a one-line JSON-style list: leave this quest alone


def apply(path: Path, wording: dict[str, list[dict]]) -> tuple[int, list[str]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    # first pass: where each quest's questions are, so a quest is changed whole or not at all
    quests: dict[str, list[dict]] = {}
    qid = None
    for n, line in enumerate(lines):
        if (m := ID_RE.match(line)):
            qid = m.group(1)
        elif qid and Q_RE.match(line):
            quests.setdefault(qid, []).append({"q": n})
        elif qid and qid in quests and (m := FIELD_RE.match(line)) and m.group(2) not in quests[qid][-1]:
            quests[qid][-1][m.group(2)] = n
    changed, skipped = 0, []
    for qid, items in quests.items():
        new = wording.get(qid)
        if new is None:
            continue
        ok = len(new) == len(items) and all(
            {"choices", "explain"} <= at.keys() and isinstance(x.get("q"), str) and isinstance(x.get("explain"), str)
            and isinstance(x.get("choices"), list) and len(x["choices"]) == choices_on(lines[at["choices"]])
            for x, at in zip(new, items))
        if not ok:
            skipped.append(qid)
            continue
        for x, at in zip(new, items):
            ind = Q_RE.match(lines[at["q"]]).group(1)
            lines[at["q"]] = f"{ind}- q: {s(x['q'])}"
            lines[at["choices"]] = f"{ind}  choices: [{', '.join(s(c) for c in x['choices'])}]"
            lines[at["explain"]] = f"{ind}  explain: {s(x['explain'])}"
            changed += 1
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed, skipped


def main() -> None:
    wording: dict[str, list[dict]] = {}
    for f in sys.argv[1:]:
        wording.update(json.loads(Path(f).read_text(encoding="utf-8")))
    total, skipped = 0, []
    for path in sorted(CURRICULUM.glob("*.yaml")):
        n, sk = apply(path, wording)
        total += n
        skipped += sk
        if n:
            print(f"{path.name}: {n} questions reworded")
    print(f"{total} questions reworded in all")
    if skipped:
        print("skipped (the rewrite does not match the quiz):", ", ".join(skipped))


if __name__ == "__main__":
    main()
