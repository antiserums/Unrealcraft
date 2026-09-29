"""Curriculum loader, quest picker and /path builder.

YAML in /curriculum is the source of truth. This module has no Discord or DB imports, so it can be unit-tested
and run by tools/validate_curriculum.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import profile as prof_mod

ALL = "all"
ORIENTATION_RANK = -1
VERIFY_TYPES = {"action", "quiz", "screenshot", "writeup", "package", "mentor"}
QUIZ_PASS_RATIO = 0.8          # 4/5
REQUIRED_QUIZ_LEN = 5


def natural_key(qid: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", qid)]


@dataclass
class Quest:
    raw: dict[str, Any]

    @property
    def id(self) -> str: return self.raw["id"]
    @property
    def rank(self) -> int: return int(self.raw["rank"])
    @property
    def track(self) -> str: return self.raw.get("track", "")
    @property
    def elective(self) -> bool: return bool(self.raw.get("elective"))
    @property
    def capstone(self) -> bool: return bool(self.raw.get("capstone"))
    @property
    def spine(self) -> bool: return bool(self.raw.get("required_spine"))
    @property
    def xp(self) -> int: return int(self.raw.get("xp", 0))
    @property
    def quiz(self) -> list[dict]: return self.raw.get("quiz") or []
    @property
    def required_for(self) -> list[str]: return self.raw.get("required_for_majors") or []
    @property
    def taster_for(self) -> list[str]: return self.raw.get("taster_for_majors") or []
    @property
    def adjacent_for(self) -> list[str]: return self.raw.get("adjacent_for") or []

    def required_for_major(self, major: str) -> bool:
        return not self.elective and (ALL in self.required_for or major in self.required_for)

    def flavor(self, major: str) -> dict:
        fl = self.raw.get("flavors") or {}
        return fl.get(major) or fl.get("_default") or {}


@dataclass
class UserState:
    major: str
    rank: int
    done: set[str] = field(default_factory=set)
    skipped: set[str] = field(default_factory=set)
    injected_tasters: list[str] = field(default_factory=list)
    profile: dict = field(default_factory=dict)      # from onboarding answers (see profile.py)


@dataclass
class Pick:
    main: Quest | None
    reason: str
    electives: list[Quest] = field(default_factory=list)
    adjacent: Quest | None = None


class Catalog:
    def __init__(self, quests: dict[str, Quest], meta: dict):
        self.quests = quests
        self.meta = meta
        self.ranks = {r["n"]: r for r in meta.get("ranks", [])}
        self.majors = meta.get("majors", {})
        self.seals = meta.get("seals", {})
        self.xp_rules = meta.get("xp_rules", {})

    # ---------------- loading ----------------
    @classmethod
    def load(cls, directory: Path) -> "Catalog":
        meta = yaml.safe_load((directory / "majors.yaml").read_text(encoding="utf-8"))
        quests: dict[str, Quest] = {}
        for f in sorted(directory.glob("*.yaml")):
            if f.name == "majors.yaml":
                continue
            doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for q in doc.get("quests", []) or []:
                q["_file"] = f.name
                if q["id"] in quests:
                    raise ValueError(f"Duplicate quest id {q['id']} in {f.name} and {quests[q['id']].raw['_file']}")
                quests[q["id"]] = Quest(q)
        return cls(quests, meta)

    def validate(self) -> tuple[list[str], list[str]]:
        """Returns (errors, warnings). Errors block loading; warnings are TODOs."""
        errs: list[str] = []
        warns: list[str] = []
        for q in self.quests.values():
            r = q.raw
            where = f"{q.id} ({r.get('_file')})"
            for k in ("id", "rank", "track", "title", "xp", "verify_type", "done_when"):
                if r.get(k) in (None, ""):
                    errs.append(f"{where}: missing {k}")
            if r.get("verify_type") not in VERIFY_TYPES:
                errs.append(f"{where}: bad verify_type {r.get('verify_type')!r}")
            required_somewhere = not q.elective and q.rank >= 0 and bool(q.required_for)
            if required_somewhere and q.quiz and len(q.quiz) != REQUIRED_QUIZ_LEN:
                warns.append(f"{where}: required quest has {len(q.quiz)} quiz questions (want {REQUIRED_QUIZ_LEN})")
            if required_somewhere and not q.quiz and r.get("verify_type") != "action":
                warns.append(f"{where}: required quest has no quiz yet")
            if r.get("official_url") == "TODO_URL":
                warns.append(f"{where}: official_url TODO_URL")
            for i, item in enumerate(q.quiz):
                ch = item.get("choices") or []
                ai = item.get("answer_index")
                if not isinstance(ai, int) or not (0 <= ai < len(ch)):
                    errs.append(f"{where}: quiz[{i}] answer_index out of range")
            url = r.get("official_url") or ""
            if url and not (url.startswith("https://") or url.startswith("discord://") or url == "TODO_URL"):
                errs.append(f"{where}: official_url must be https://, discord:// or TODO_URL")
        for major, cfg in self.majors.items():
            for rank, groups in (cfg.get("required_tasters") or {}).items():
                for g in groups or []:
                    for qid in g:
                        if qid not in self.quests:
                            errs.append(f"majors.{major}.required_tasters[{rank}]: unknown quest {qid}")
            for rank, cap in (cfg.get("capstones") or {}).items():
                if int(rank) <= 3 and major in ("level_design", "programming", "lookdev") and cap["id"] not in self.quests:
                    errs.append(f"majors.{major}.capstones[{rank}]: {cap['id']} not defined in any quest file")
        return errs, warns

    # ---------------- queries ----------------
    def sorted(self, qs) -> list[Quest]:
        return sorted(qs, key=lambda q: (q.rank, q.capstone, natural_key(q.id)))

    def orientation(self) -> list[Quest]:
        return self.sorted(q for q in self.quests.values() if q.rank == ORIENTATION_RANK and not q.elective)

    def spine(self) -> list[Quest]:
        return self.sorted(q for q in self.quests.values() if q.spine)

    def required(self, major: str, rank: int) -> list[Quest]:
        """Major-required quests at exactly this rank (excluding spine and orientation)."""
        return self.sorted(q for q in self.quests.values()
                           if q.rank == rank and q.rank >= 1 and q.required_for_major(major))

    def taster_groups(self, major: str, rank: int) -> list[list[str]]:
        cfg = self.majors.get(major, {})
        return [list(g) for g in (cfg.get("required_tasters") or {}).get(rank, []) or []]

    def capstone(self, major: str, rank: int) -> dict | None:
        return (self.majors.get(major, {}).get("capstones") or {}).get(rank)

    def home_tracks(self, major: str) -> set[str]:
        return {q.track for q in self.quests.values() if q.rank >= 1 and major in q.required_for}

    def affinity(self, q: Quest, major: str) -> str:
        """major: the member's own path (or an elective in a home track). adjacent: flagged adjacent,
        a taster, or it has a flavor written for this major. other: everything else."""
        shared_tracks = {"foundations", "orientation"}          # meta electives are for everyone
        if major in q.required_for or ALL in q.required_for or \
                (q.elective and (q.track in self.home_tracks(major) or q.track in shared_tracks)):
            return "major"
        if major in q.adjacent_for or major in q.taster_for or major in (q.raw.get("flavors") or {}):
            return "adjacent"
        return "other"

    def owner_label(self, q: Quest) -> str:
        owners = [m for m in q.required_for if m != ALL]
        if owners:
            return self.majors.get(owners[0], {}).get("title", owners[0])
        return "Tasters" if (q.track == "tasters" or q.taster_for) else q.track

    # ---------------- picker ----------------
    def pick(self, u: UserState) -> Pick:
        todo = lambda q: q.id not in u.done and q.id not in u.skipped

        # 1. Orientation
        for q in self.orientation():
            if todo(q):
                return Pick(q, "Orientation")
        # 2. Starter Quests
        for q in self.spine():
            if q.id not in u.done:
                return Pick(q, "Starter Quests")
        # 3. Missing required taster for this rank (+ respec-injected tasters)
        for group in self.taster_groups(u.major, u.rank):
            if not any(g in u.done for g in group):
                group = self.order_group(group, u.profile)
                return Pick(self.quests[group[0]], "Required taster" + (" (any one of " + ", ".join(group) + ")" if len(group) > 1 else ""))
        for qid in u.injected_tasters:
            if qid in self.quests and qid not in u.done:
                return Pick(self.quests[qid], "Taster added by respec")
        # 4. Major-required at this rank (capstone sorts last)
        req = [q for q in self.required(u.major, u.rank) if q.id not in u.done]
        main = req[0] if req else None
        cap = self.capstone(u.major, u.rank) if u.rank >= 1 else None
        if main is None and cap and cap["id"] in self.quests and cap["id"] not in u.done:
            main = self.quests[cap["id"]]      # e.g. Undecided borrows the LD capstone
        reason = ("Capstone" if main and main.capstone else "Major required") if main else "Rank complete. Electives only."
        # 5. Offer 2 major electives + 1 adjacent
        pool = [q for q in self.sorted(self.quests.values())
                if q.elective and 0 <= q.rank <= u.rank and todo(q)]
        score = lambda q: -prof_mod.elective_score(q, u.profile)      # stable sort keeps catalog order on ties
        majors = sorted([q for q in pool if self.affinity(q, u.major) == "major"], key=score)[:2]
        adj_pool = [q for q in self.sorted(self.quests.values())
                    if 1 <= q.rank <= u.rank and todo(q) and q not in majors
                    and self.affinity(q, u.major) == "adjacent" and not q.required_for_major(u.major)
                    and not (q.taster_for and u.major not in q.taster_for)]   # other majors' tasters aren't for you
        if not adj_pool and u.profile.get("curious"):   # nothing flagged adjacent: fall back to a curiosity match
            adj_pool = [q for q in pool if q not in majors and prof_mod.quest_matches_curious(q, u.profile)]
        adj = min(adj_pool, key=score) if adj_pool else None
        return Pick(main, reason, majors, adj)

    def order_group(self, group: list[str], profile: dict) -> list[str]:
        """Any-one-of taster groups: non-coders get the non-C++ option first, coders the C++ one."""
        codes = profile.get("code")
        if not codes:
            return group
        is_cpp = lambda qid: "cpp" in {s.lower() for s in (self.quests[qid].raw.get("subjects") or [])} or "CPP" in qid
        want_cpp = codes in ("some", "cpp")
        return sorted(group, key=lambda qid: 0 if is_cpp(qid) == want_cpp else 1)

    def remaining_minutes(self, u: UserState) -> int:
        """Minutes of required work left before the next promotion (spine, required, tasters, capstone)."""
        target = max(u.rank, -1) + 1
        _, missing = self.rank_requirements_met(u, target)
        total = 0
        for m in missing:
            qid = m.split("/")[0]
            if qid in self.quests:
                total += int(self.quests[qid].raw.get("time_min") or 30)
        return total

    def rank_requirements_met(self, u: UserState, target_rank: int) -> tuple[bool, list[str]]:
        """What's missing to be promoted INTO target_rank (from target_rank-1)."""
        cur = target_rank - 1
        missing: list[str] = []
        if cur == ORIENTATION_RANK:
            missing = [q.id for q in self.orientation() if q.id not in u.done]
        elif cur == 0:
            missing = [q.id for q in self.spine() if q.id not in u.done]
        else:
            missing = [q.id for q in self.required(u.major, cur) if q.id not in u.done]
            for g in self.taster_groups(u.major, cur):
                if not any(x in u.done for x in g):
                    missing.append("/".join(g))
            cap = self.capstone(u.major, cur)
            if cap and cap["id"] not in u.done and cap["id"] not in missing:
                missing.append(cap["id"])
        return (not missing, missing)

    def xp_needed(self, target_rank: int) -> int:
        return int(self.ranks.get(target_rank, {}).get("xp", 0)) if target_rank >= 0 else 0

    # ---------------- /path ----------------
    def path_lines(self, u: UserState, max_optional: int = 6) -> list[str]:
        """Personal tree: ✔ done / ▶ now / 🔒 locked-for-rank / ◇ optional shelf."""
        pick = self.pick(u)
        now_id = pick.main.id if pick.main else None
        lines: list[str] = []
        mt = self.majors.get(u.major, {}).get("title", u.major)

        def row(q: Quest, extra: str = "") -> str:
            mark = "✔" if q.id in u.done else ("▶" if q.id == now_id else "·")
            cap = " ★" if q.capstone else ""
            return f"  {mark} {q.id:<10} {q.raw['title']}{cap}{extra}"

        if u.rank == ORIENTATION_RANK or any(q.id not in u.done for q in self.orientation()):
            lines.append("ORIENTATION")
            lines += [row(q) for q in self.orientation()]
        lines.append("STARTER QUESTS (everyone)")
        lines += [row(q) for q in self.spine()]

        for r in range(1, max(u.rank, 0) + 1):
            title = self.ranks.get(r, {}).get("title", f"Rank {r}")
            lines.append(f"RANK {r} · {title.upper()} · {mt}")
            lines += [row(q) for q in self.required(u.major, r)]
            for g in self.taster_groups(u.major, r):
                qs = [self.quests[x] for x in g if x in self.quests]
                if qs:
                    tag = "  (taster" + (": pick one" if len(qs) > 1 else "") + ")"
                    lines += [row(q, tag) for q in qs]

        nxt = max(u.rank, 0) + 1
        if nxt in self.ranks:
            title = self.ranks[nxt]["title"]
            gate = "Starter Quests" if nxt == 1 else f"Rank {nxt - 1} path"
            lines.append(f"🔒 RANK {nxt} · {title.upper()} · {mt}: needs {self.ranks[nxt]['xp']} XP + {gate}")
            if self.ranks[nxt].get("opens"):
                lines.append(f"  🔓 opens: {self.ranks[nxt]['opens']}")
            req = self.required(u.major, nxt)
            plain = [q for q in req if not q.capstone]
            lines += [f"  🔒 {q.id:<10} {q.raw['title']}" for q in plain[:4]]
            if len(plain) > 4:
                lines.append(f"  🔒 … {len(plain) - 4} more")
            for g in self.taster_groups(u.major, nxt):
                names = " or ".join(f"{x} {self.quests[x].raw['title']}" for x in g if x in self.quests)
                lines.append(f"  🔒 taster: {names}")
            cap = self.capstone(u.major, nxt)
            if cap:
                lines.append(f"  ★ capstone: {cap['title']}")

        taster_ids = {x for r in range(1, nxt + 3) for g in self.taster_groups(u.major, r) for x in g}
        shelf = [q for q in self.sorted(self.quests.values())
                 if 1 <= q.rank <= nxt + 2 and not q.elective and not q.required_for_major(u.major)
                 and q.id not in taster_ids]
        if shelf:
            lines.append("◇ OPTIONAL SHELF: other majors' work. Nothing here gates you. It opens by rank.")
            groups: dict[str, list[int]] = {}
            hits: dict[str, int] = {}
            for q in shelf:
                label = self.owner_label(q)
                groups.setdefault(label, []).append(q.rank)
                hits[label] = hits.get(label, 0) + prof_mod.quest_matches_curious(q, u.profile)
            ordered = sorted(groups.items(), key=lambda kv: -hits.get(kv[0], 0))
            for label, ranks in ordered[:max_optional]:
                lo, hi = min(ranks), max(ranks)
                span = f"R{lo}" if lo == hi else f"R{lo}–{hi}"
                lines.append(f"  ◇ {label:<26} {span:<6} {len(ranks)} quests")
        return lines
