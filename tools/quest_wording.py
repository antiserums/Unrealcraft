"""Reword what a quest page says (the intro, the steps, the "done when" line, the quiz text) without touching
anything else in the curriculum.

Run it with the API's Python, which has PyYAML:

  api/.venv/Scripts/python.exe tools/quest_wording.py status        how many quests have new wording, per file
  api/.venv/Scripts/python.exe tools/quest_wording.py next 15       the next 15 quests still to do, as JSON
  api/.venv/Scripts/python.exe tools/quest_wording.py show SQ1 SQ2  everything the curriculum holds for these quests
  api/.venv/Scripts/python.exe tools/quest_wording.py refs          quests whose text leans on another quest
  api/.venv/Scripts/python.exe tools/quest_wording.py apply         put every file in tools/quest_wording/ into the curriculum

Wording files are read in name order and a later file wins, so a correction goes in a file that sorts last
(update-0001.json).

A wording file (tools/quest_wording/*.json) maps a quest id to the new text. Every key is optional:

  { "SQ1": { "brief": "Two to four sentences that explain the topic before the steps.",
             "checklist": ["Step one, reworded.", "Step two, reworded."],
             "done_when": "What the member sends as proof, reworded.",
             "title": "A new title", "official_url": "https://...",   (only for a quest rewritten around another topic)
             "quiz": [ {"q": "...", "choices": ["...", "..."], "explain": "..."} ] } }

Only text changes. A checklist written on one line (`checklist: ["a", "b"]`) is handled too. Steps that carry a `check:` keep their number and order (a checklist of plain text lines may get a different
number of steps, 1 to 12), the quiz keeps its answers
and the order of its choices. `apply` parses the result and compares it with the original: if anything other than
that text differs, or a list has a different length, the quest is left as it was and reported.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum"
WORDING = ROOT / "tools" / "quest_wording"
META = {"specializations.yaml", "majors.yaml"}

ID_RE = re.compile(r"^  - id:\s*[\"']?([A-Za-z0-9_]+)")
KEY_RE = re.compile(r"^    ([a-z_]+):")
ITEM_RE = re.compile(r"^      - ")
Q_RE = re.compile(r"^(\s+)- q: ")
FIELD_RE = re.compile(r"^(\s+)(choices|answer_index|explain): ")
STR = r'"(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\''


def s(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)          # a JSON string is a valid YAML double-quoted string


def files() -> list[Path]:
    return [f for f in sorted(CURRICULUM.glob("*.yaml")) if f.name not in META]


def load_wording() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted(WORDING.glob("*.json")):
        for qid, w in json.loads(f.read_text(encoding="utf-8")).items():
            out.setdefault(qid, {}).update({"quiz": w} if isinstance(w, list) else w)
    return out


def item_text(raw) -> str:
    return raw.get("text", "") if isinstance(raw, dict) else str(raw)


# ---------------------------------------------------------------- apply
def index(lines: list[str]) -> dict[str, dict]:
    """Where each quest's rewordable lines are."""
    quests: dict[str, dict] = {}
    cur, key = None, None
    for n, line in enumerate(lines):
        if (m := ID_RE.match(line)):
            cur = quests.setdefault(m.group(1), {"id_line": n, "items": [], "quiz": []})
            key = None
            continue
        if cur is None:
            continue
        if (m := KEY_RE.match(line)):
            key = m.group(1)
            if key in ("title", "brief", "done_when", "official_url"):
                cur[key] = n
            elif key == "checklist" and line.rstrip().endswith("]"):
                cur["inline"] = n                                 # the whole list on one line: checklist: ["a", "b"]
        elif key == "checklist" and ITEM_RE.match(line):
            cur["items"].append(n)
        elif key == "quiz" and Q_RE.match(line):
            cur["quiz"].append({"q": n})
        elif key == "quiz" and cur["quiz"] and (m := FIELD_RE.match(line)) and m.group(2) not in cur["quiz"][-1]:
            cur["quiz"][-1][m.group(2)] = n
    return quests


def reword_item(line: str, text: str) -> str | None:
    """A checklist line with its text swapped: `- "text"`, `- text: "text"` or `- {text: "text", ...}`."""
    for pat in (rf'^(      - )({STR})(\s*)$', rf'^(      - text: )({STR})(\s*)$', rf'^(      - \{{\s*text: )({STR})(.*)$'):
        if (m := re.match(pat, line)):
            return m.group(1) + s(text) + m.group(3)
    return None


def edits_for(lines: list[str], at: dict, w: dict) -> tuple[dict[int, str], dict[int, str]] | None:
    """(replacements by line, insertions after a line) for one quest, or None when the wording does not fit."""
    repl: dict[int, str | None] = {}                      # None removes the line
    ins: dict[int, str] = {}
    for key in ("title", "official_url"):                     # a quest rewritten around another topic or docs page
        if isinstance(w.get(key), str) and w[key].strip():
            if key not in at:
                return None
            repl[at[key]] = f"    {key}: {s(w[key].strip())}"
    if isinstance(w.get("brief"), str) and w["brief"].strip():
        if "brief" in at:
            repl[at["brief"]] = f"    brief: {s(w['brief'].strip())}"
        elif "title" in at:
            ins[at["title"]] = f"    brief: {s(w['brief'].strip())}"
        else:
            return None
    if isinstance(w.get("done_when"), str) and w["done_when"].strip():
        if "done_when" not in at:
            return None
        repl[at["done_when"]] = f"    done_when: {s(w['done_when'].strip())}"
    if w.get("checklist") is not None and "inline" in at:
        try:
            old = yaml.safe_load(lines[at["inline"]])["checklist"]
        except (yaml.YAMLError, TypeError, KeyError):
            return None
        if not all(isinstance(it, str) for it in old) or not 1 <= len(w["checklist"]) <= 12:
            return None
        repl[at["inline"]] = f"    checklist: [{', '.join(s(str(t).strip()) for t in w['checklist'])}]"
    elif w.get("checklist") is not None and len(w["checklist"]) != len(at["items"]):
        # a different number of steps: only when every step is a plain line of text (none carries a `check:`)
        plain = all(re.match(rf'^      - ({STR})\s*$', lines[n]) for n in at["items"])
        last = at["items"][-1] if at["items"] else -1
        solid = at["items"] == list(range(at["items"][0], last + 1)) if at["items"] else False
        if not (plain and solid and 1 <= len(w["checklist"]) <= 12):
            return None
        for n in at["items"]:
            repl[n] = None
        repl[at["items"][0]] = "\n".join(f"      - {s(str(t).strip())}" for t in w["checklist"])
    elif w.get("checklist") is not None:
        for n, text in zip(at["items"], w["checklist"]):
            new = reword_item(lines[n], str(text).strip())
            if new is None:
                return None
            repl[n] = new
    if w.get("quiz") is not None:
        if len(w["quiz"]) != len(at["quiz"]):
            return None
        for x, q in zip(w["quiz"], at["quiz"]):
            if not {"choices", "explain"} <= q.keys():
                return None
            ind = Q_RE.match(lines[q["q"]]).group(1)
            repl[q["q"]] = f"{ind}- q: {s(x['q'])}"
            repl[q["choices"]] = f"{ind}  choices: [{', '.join(s(c) for c in x['choices'])}]"
            repl[q["explain"]] = f"{ind}  explain: {s(x['explain'])}"
    return repl, ins


def skeleton(q: dict) -> dict:
    """A quest with its rewordable text blanked, to prove that nothing else changed."""
    q = copy.deepcopy(q)
    q.pop("brief", None)
    for key in ("done_when", "title", "official_url"):
        if key in q:
            q[key] = ""
    items = q.get("checklist") or []
    # plain steps may change in number; steps that carry a check keep their place and their check
    q["checklist"] = "plain steps" if all(isinstance(it, str) for it in items) else [dict(it, text="") if isinstance(it, dict) else "" for it in items]
    for x in q.get("quiz") or []:
        x["q"], x["explain"], x["choices"] = "", "", len(x.get("choices") or [])
    return q


def apply_file(path: Path, wording: dict[str, dict]) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    quests = index(lines)
    before = {q["id"]: q for q in (yaml.safe_load(text) or {}).get("quests") or []}
    done, skipped = 0, []
    for qid in [q for q in quests if q in wording]:
        e = edits_for(lines, quests[qid], wording[qid])
        if e is None:
            skipped.append(qid)
            continue
        repl, ins = e
        trial: list[str] = []
        for n, line in enumerate(lines):
            new = repl.get(n, line)
            if new is not None:
                trial.extend(new.split("\n"))
            if n in ins:
                trial.append(ins[n])
        if trial == lines:
            continue                                          # already has this wording
        try:
            after = {q["id"]: q for q in (yaml.safe_load("\n".join(trial)) or {}).get("quests") or []}
        except yaml.YAMLError:
            skipped.append(qid)
            continue
        if after.keys() != before.keys() or any(skeleton(after[k]) != skeleton(before[k]) for k in before):
            skipped.append(qid)
            continue
        lines, done = trial, done + 1
        quests = index(lines)                                 # an inserted line moves everything after it
    if done:
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return done, skipped


def apply() -> None:
    wording = load_wording()
    total, skipped = 0, []
    for path in files():
        n, sk = apply_file(path, wording)
        total, skipped = total + n, skipped + sk
        if n:
            print(f"{path.name}: {n} quests changed")
    print(f"{total} quests changed in all")
    if skipped:
        print("NOT applied (the wording does not fit the quest, fix the JSON):", ", ".join(skipped))


# ---------------------------------------------------------------- next / status
def all_quests() -> list[tuple[str, dict]]:
    out = []
    for f in files():
        for q in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("quests") or []:
            out.append((f.name, q))
    return out


def page_done(w: dict | None) -> bool:
    return bool(w and w.get("brief"))


def status() -> None:
    wording = load_wording()
    per: dict[str, list[int]] = {}
    for fname, q in all_quests():
        c = per.setdefault(fname, [0, 0])
        c[0] += page_done(wording.get(q["id"]))
        c[1] += 1
    for fname, (d, n) in per.items():
        print(f"{fname:36} {d:4}/{n}")
    print(f"{'total':36} {sum(d for d, _ in per.values()):4}/{sum(n for _, n in per.values())}")


def next_batch(count: int) -> None:
    wording = load_wording()
    out = []
    for fname, q in all_quests():
        if page_done(wording.get(q["id"])):
            continue
        fl = (q.get("flavors") or {}).get("_default") or {}
        out.append({
            "id": q["id"], "file": fname, "title": q.get("title"), "difficulty": q.get("difficulty"), "subjects": q.get("subjects"),
            "why": fl.get("why"), "verify_type": q.get("verify_type"),
            "checklist": [item_text(it) for it in q.get("checklist") or []],
            "done_when": q.get("done_when"),
            # what the quiz teaches, as background for the intro (the quiz itself is not reworded)
            "quiz_facts": [x.get("explain") for x in q.get("quiz") or [] if x.get("explain")],
        })
        if len(out) >= count:
            break
    print(json.dumps(out, ensure_ascii=False, indent=1))


def show(ids: list[str]) -> None:
    """Everything the curriculum holds for these quests, as JSON (quiz answers included)."""
    want = set(ids)
    out = [dict({k: v for k, v in q.items()}, file=fname) for fname, q in all_quests() if q["id"] in want]
    print(json.dumps(out, ensure_ascii=False, indent=1))


OTHER_ID = re.compile(r"\b(?:SQ|LDQ|GDQ|EAQ|TAQ|AQ|CQ|PQ|O)\d+[A-Z]?\b")
LEAN_ON = re.compile(r"(?i)\b(earlier quests?|previous quests?|last quest|another quest|from (?:the|a|an|your) (?:earlier|previous|last)|you (?:made|built|created|set up) (?:in|earlier|before)|built earlier|made earlier|sandbox project|same project)\b")


def refs() -> None:
    """Quests whose page or quiz text leans on another quest: it names another quest id, or says "earlier quest" and
    the like. A quest should be doable on its own."""
    n = 0
    for fname, q in all_quests():
        texts = [("brief", q.get("brief") or ""), ("done_when", q.get("done_when") or "")]
        texts += [(f"step {i + 1}", item_text(it)) for i, it in enumerate(q.get("checklist") or [])]
        for i, x in enumerate(q.get("quiz") or []):
            texts.append((f"quiz {i + 1}", " | ".join([x.get("q", ""), *x.get("choices", []), x.get("explain") or ""])))
        for fl in (q.get("flavors") or {}).values():
            texts.append(("flavor (not editable here)", " | ".join(str(v) for v in fl.values()) if isinstance(fl, dict) else str(fl)))
        hits = []
        for where, t in texts:
            found = sorted({m.group(0) for m in OTHER_ID.finditer(t) if m.group(0) != q["id"]} | {m.group(0) for m in LEAN_ON.finditer(t)})
            if found:
                hits.append(f"   {where}: {', '.join(found)}")
        if hits:
            n += 1
            print(f"{q['id']}  ({fname})")
            print("\n".join(hits))
    print(f"{n} quests lean on another quest")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "apply":
        apply()
    elif cmd == "show":
        show(sys.argv[2:])
    elif cmd == "refs":
        refs()
    elif cmd == "next":
        next_batch(int(sys.argv[2]) if len(sys.argv) > 2 else 15)
    else:
        status()


if __name__ == "__main__":
    main()
