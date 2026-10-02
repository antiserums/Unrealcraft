"""Reword what a quest page says (the intro, the steps, the "done when" line, the quiz text) without touching
anything else in the curriculum.

Run it with the API's Python, which has PyYAML:

  api/.venv/Scripts/python.exe tools/quest_wording.py status        how many quests have new wording, per file
  api/.venv/Scripts/python.exe tools/quest_wording.py next 15       the next 15 quests still to do, as JSON
  api/.venv/Scripts/python.exe tools/quest_wording.py show SQ1 SQ2  everything the curriculum holds for these quests
  api/.venv/Scripts/python.exe tools/quest_wording.py tell          questions whose right answer stands out by its length
  api/.venv/Scripts/python.exe tools/quest_wording.py tell SQ1 SQ2  those quests' quizzes, compact
  api/.venv/Scripts/python.exe tools/quest_wording.py noquiz        quests that have no quiz yet
  api/.venv/Scripts/python.exe tools/quest_wording.py refs          quests whose text leans on another quest
  api/.venv/Scripts/python.exe tools/quest_wording.py apply         put every file in tools/quest_wording/ into the curriculum

Wording files are read in name order and a later file wins, so a correction goes in a file that sorts last
(update-0001.json).

A wording file (tools/quest_wording/*.json) maps a quest id to the new text. Every key is optional:

  { "SQ1": { "brief": "Two to four sentences that explain the topic before the steps.",
             "checklist": ["Step one, reworded.", "Step two, reworded."],
             "done_when": "What the member sends as proof, reworded.",
             "title": "A new title", "official_url": "https://...",   (only for a quest rewritten around another topic)
             "quiz_choices": { "3": ["a", "b", "c", "d"] },          (new choices for question 3 only, same order)
             "new_quiz": [ {"q": "...", "choices": ["a", "b", "c", "d"], "answer_index": 2, "explain": "..."} ],
                                                                      (only for a quest that has no quiz yet)
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
            if key in ("quiz", "flavors", "verify_type"):
                cur["k_" + key] = n                               # where a new quiz can go
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
    if w.get("new_quiz") is not None and not at["quiz"]:
        # a quiz for a quest that has none: the whole block is written, answers included
        items = w["new_quiz"]
        ok = 1 <= len(items) <= 12 and all(
            isinstance(x.get("q"), str) and x["q"].strip() and isinstance(x.get("explain"), str) and x["explain"].strip()
            and isinstance(x.get("choices"), list) and len(x["choices"]) == 4 and len(set(x["choices"])) == 4
            and all(isinstance(c, str) and c.strip() for c in x["choices"])
            and isinstance(x.get("answer_index"), int) and 0 <= x["answer_index"] < 4 for x in items)
        if not ok:
            return None
        block = ["    quiz:"]
        for x in items:
            block += [f"      - q: {s(x['q'].strip())}", f"        choices: [{', '.join(s(c.strip()) for c in x['choices'])}]",
                      f"        answer_index: {x['answer_index']}", f"        explain: {s(x['explain'].strip())}"]
        if "k_quiz" in at:                                        # `quiz: []` or an empty `quiz:`
            repl[at["k_quiz"]] = "\n".join(block)
        elif "k_flavors" in at and (at["k_flavors"] - 1) not in ins:
            ins[at["k_flavors"] - 1] = "\n".join(block)           # just above the flavors
        elif "k_verify_type" in at and at["k_verify_type"] not in ins:
            ins[at["k_verify_type"]] = "\n".join(block)
        else:
            return None
    elif w.get("new_quiz") is not None and len(w["new_quiz"]) != len(at["quiz"]):
        return None                                               # the quest already has another quiz
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
    if w.get("quiz_choices") is not None:
        # new choices for single questions, by question number (1 is the first): {"3": ["a", "b", "c", "d"]}.
        # Done after "quiz", so these choices win over a full rewording of the same quiz.
        for num, choices in w["quiz_choices"].items():
            i = int(num) - 1
            if not 0 <= i < len(at["quiz"]) or "choices" not in at["quiz"][i]:
                return None
            n = at["quiz"][i]["choices"]
            try:
                old = yaml.safe_load(lines[n])["choices"]
            except (yaml.YAMLError, TypeError, KeyError):
                return None
            if not isinstance(choices, list) or len(choices) != len(old) or len(set(choices)) != len(choices) or not all(isinstance(c, str) and c.strip() for c in choices):
                return None
            ind = FIELD_RE.match(lines[n]).group(1)
            repl[n] = f"{ind}choices: [{', '.join(s(c.strip()) for c in choices)}]"
    return repl, ins


def skeleton(q: dict, new_quiz: bool = False) -> dict:
    """A quest with its rewordable text blanked, to prove that nothing else changed. `new_quiz`: this quest had no
    quiz and is getting one, so its quiz is left out of the comparison."""
    q = copy.deepcopy(q)
    if new_quiz:
        q.pop("quiz", None)
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
        fresh = wording[qid].get("new_quiz") is not None and not before[qid].get("quiz")
        if after.keys() != before.keys() or any(skeleton(after[k], fresh and k == qid) != skeleton(before[k], fresh and k == qid) for k in before):
            skipped.append(qid)
            continue
        lines, done, before = trial, done + 1, after          # the next quest is compared with this result
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


def telling(x: dict) -> bool:
    """The right answer gives itself away by its length. Either it is the longest choice and clearly longer than the
    rest, or the choices fall into a long pair and a short pair with the right answer in the long pair."""
    lens = [len(c) for c in x["choices"]]
    r = lens[x["answer_index"]]
    others = sorted((n for i, n in enumerate(lens) if i != x["answer_index"]), reverse=True)
    if r > others[0] and r >= 1.2 * (sum(others) / len(others)) and r - others[0] >= 4:
        return True
    third = sorted(lens, reverse=True)[2]                     # the third longest of the four
    return r > third and third < 0.7 * r and r - third >= 8


def tell(ids: list[str]) -> None:
    """How often the right answer is the longest choice. With quest ids: the quizzes of those quests, compact, with
    the right choice marked `*` and a `!` on questions where its length gives it away."""
    quests = all_quests()
    if ids:
        want = set(ids)
        for _, q in quests:
            if q["id"] in want:
                print(f"## {q['id']}  {q.get('title')}")
                for n, x in enumerate(q.get("quiz") or [], 1):
                    print(f"{'!' if telling(x) else ' '}{n}. {x['q']}")
                    for i, c in enumerate(x["choices"]):
                        print(f"     {'*' if i == x['answer_index'] else '-'} {c}")
        return
    total = longest = top2 = flagged = 0
    todo = []
    for _, q in quests:
        nums = []
        for n, x in enumerate(q.get("quiz") or [], 1):
            lens = [len(c) for c in x["choices"]]
            total += 1
            longest += lens[x["answer_index"]] > max(l for i, l in enumerate(lens) if i != x["answer_index"])
            top2 += lens[x["answer_index"]] >= sorted(lens, reverse=True)[1]
            if telling(x):
                flagged += 1
                nums.append(n)
        if nums:
            todo.append(f"{q['id']}: {','.join(map(str, nums))}")
    for line in todo:
        print(line)
    print(f"{total} questions | right answer is the longest choice in {100 * longest / total:.0f}% (chance 25%), one of the two "
          f"longest in {100 * top2 / total:.0f}% (chance 50%) | {flagged} questions in {len(todo)} quests give the answer away by length")


QUIZ_LEN = {"novice": 5, "apprentice": 6, "adept": 8, "expert": 10, "master": 12}      # TIERS in bot/registrar/curriculum.py


def noquiz() -> None:
    """Quests that have no quiz, with the number of questions their difficulty calls for."""
    n = 0
    for fname, q in all_quests():
        if not q.get("quiz"):
            n += 1
            print(f"{q['id']:8} {QUIZ_LEN.get(q.get('difficulty'), 5):2} questions  {q.get('difficulty'):10} {q.get('verify_type'):10} {fname:32} {q.get('title')}")
    print(f"{n} quests have no quiz")


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
    elif cmd == "noquiz":
        noquiz()
    elif cmd == "tell":
        tell(sys.argv[2:])
    elif cmd == "next":
        next_batch(int(sys.argv[2]) if len(sys.argv) > 2 else 15)
    else:
        status()


if __name__ == "__main__":
    main()
