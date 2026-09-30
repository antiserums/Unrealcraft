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
META_FILES = {"specializations.yaml", "majors.yaml"}
VERIFY_TYPES = {"action", "quiz", "screenshot", "writeup", "package", "mentor"}
QUIZ_PASS_RATIO = 0.8          # 4/5

# Quest difficulty. Every quest has one (`difficulty:` in YAML); each guild rank opens the next tier
# (majors.yaml ranks[].tier). Harder tiers have longer quizzes.
TIERS = {
    "novice":     {"name": "Novice",     "emoji": "🟢", "color": "#4FA36C", "quiz_len": 5},
    "apprentice": {"name": "Apprentice", "emoji": "🔵", "color": "#3D7DD8", "quiz_len": 6},
    "adept":      {"name": "Adept",      "emoji": "🟣", "color": "#8E6CCF", "quiz_len": 8},
    "expert":     {"name": "Expert",     "emoji": "🟠", "color": "#D9824A", "quiz_len": 10},
    "master":     {"name": "Master",     "emoji": "🔴", "color": "#D9534F", "quiz_len": 12},
}
TIER_BY_RANK = {-1: "novice", 0: "novice", 1: "apprentice", 2: "adept", 3: "expert"}   # default; 4+ = master


def natural_key(qid: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", qid)]


@dataclass
class Quest:
    raw: dict[str, Any]

    @property
    def id(self) -> str: return self.raw["id"]
    @property
    def rank(self) -> int: return int(self.raw["rank"])
    # A quest belongs to one or more specializations (`all` = everyone). `required` means required within them;
    # otherwise it is an elective on their shelf. `taster` marks a short look into a specialization for newcomers.
    @property
    def specializations(self) -> list[str]: return list(self.raw.get("specializations") or [])
    @property
    def required(self) -> bool: return bool(self.raw.get("required", not self.raw.get("elective", False)))
    @property
    def taster(self) -> bool: return bool(self.raw.get("taster") or self.raw.get("taster_for"))

    def in_specialization(self, key: str) -> bool:
        return ALL in self.specializations or key in self.specializations

    # ---- older names, kept so the bot's cogs read the same data until its Discord pass ----
    @property
    def track(self) -> str: return self.specializations[0] if self.specializations else ""
    @property
    def elective(self) -> bool: return not self.required
    @property
    def capstone(self) -> bool: return bool(self.raw.get("capstone"))
    @property
    def spine(self) -> bool: return bool(self.raw.get("required_spine"))
    @property
    def first_steps(self) -> bool: return bool(self.raw.get("first_steps"))
    @property
    def xp(self) -> int: return int(self.raw.get("xp", 0))
    @property
    def difficulty(self) -> str: return self.raw.get("difficulty") or TIER_BY_RANK.get(self.rank, "master")
    @property
    def tier(self) -> dict: return TIERS.get(self.difficulty, TIERS["novice"])
    @property
    def tier_label(self) -> str: return f"{self.tier['emoji']} {self.tier['name']}"
    @property
    def quiz(self) -> list[dict]: return self.raw.get("quiz") or []
    @property
    def required_for(self) -> list[str]: return self.specializations if self.required else []
    @property
    def taster_for(self) -> list[str]:
        """Specializations this quest is a taster for: `taster_for` when listed, else its own when `taster: true`."""
        if self.raw.get("taster_for"):
            return list(self.raw["taster_for"])
        return [s for s in self.specializations if s != ALL] if self.raw.get("taster") else []
    @property
    def adjacent_for(self) -> list[str]: return []

    def required_for_major(self, major: str) -> bool:
        return self.required and self.in_specialization(major)

    def flavor(self, major: str) -> dict:
        fl = self.raw.get("flavors") or {}
        return fl.get(major) or fl.get("_default") or {}


@dataclass
class UserState:
    major: str                                       # the primary specialization (ranks, nameplate, next quest)
    rank: int
    done: set[str] = field(default_factory=set)
    skipped: set[str] = field(default_factory=set)
    injected_tasters: list[str] = field(default_factory=list)
    profile: dict = field(default_factory=dict)      # from onboarding answers (see profile.py)
    extras: list[str] = field(default_factory=list)  # further specializations the member chose; their quests count as "yours"

    @property
    def specializations(self) -> list[str]:
        return [self.major] + [e for e in self.extras if e != self.major] if self.major != "undecided" else list(self.extras)


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
        self.specializations: dict = meta.get("specializations") or meta.get("majors") or {}
        self.majors = self.specializations                  # older name, same dict
        self.xp_rules = meta.get("xp_rules", {})
        self.min_members = int((meta.get("community") or {}).get("min_members", 20))
        self.community_ready = True        # set by the bot from the live member count

    def available(self, q: "Quest") -> bool:
        """Quests that need other members are hidden while the server is too small."""
        return self.community_ready or not q.raw.get("needs_others")

    # ---------------- loading ----------------
    @classmethod
    def load(cls, directory: Path) -> "Catalog":
        meta_file = directory / "specializations.yaml"
        if not meta_file.exists():
            meta_file = directory / "majors.yaml"           # the file's older name
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        quests: dict[str, Quest] = {}
        for f in sorted(directory.glob("*.yaml")):
            if f.name in META_FILES:
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
            for k in ("id", "rank", "title", "xp", "verify_type", "done_when"):
                if r.get(k) in (None, ""):
                    errs.append(f"{where}: missing {k}")
            if not q.specializations:
                errs.append(f"{where}: missing specializations")
            for s in q.specializations:
                if s != ALL and s not in self.specializations:
                    errs.append(f"{where}: unknown specialization {s!r}")
            if r.get("verify_type") not in VERIFY_TYPES:
                errs.append(f"{where}: bad verify_type {r.get('verify_type')!r}")
            required_somewhere = not q.elective and bool(q.required_for)
            if r.get("difficulty") not in TIERS:
                errs.append(f"{where}: difficulty must be one of {', '.join(TIERS)} (got {r.get('difficulty')!r})")
            want = q.tier["quiz_len"]
            if required_somewhere and q.quiz and len(q.quiz) < want:
                warns.append(f"{where}: {q.difficulty} quiz has {len(q.quiz)} questions (want {want})")
            if required_somewhere and not q.quiz and r.get("verify_type") not in ("action", "mentor") and not q.capstone:
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
            for c in r.get("community_urls") or []:
                u = c.get("url", "") if isinstance(c, dict) else c
                if not str(u).startswith("https://"):
                    errs.append(f"{where}: community_urls entries must be https:// (got {u!r})")
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

    def first_steps(self) -> list[Quest]:
        """The five site steps every Novice does first (curriculum/orientation.yaml)."""
        return self.sorted(q for q in self.quests.values() if q.first_steps and not q.elective)

    def spine(self) -> list[Quest]:
        return self.sorted(q for q in self.quests.values() if q.spine)

    def required(self, major: str, rank: int) -> list[Quest]:
        """Major-required quests at exactly this rank (excluding spine and first steps)."""
        return self.sorted(q for q in self.quests.values()
                           if q.rank == rank and q.rank >= 1 and q.required_for_major(major) and self.available(q))

    def taster_groups(self, major: str, rank: int) -> list[list[str]]:
        cfg = self.majors.get(major, {})
        return [list(g) for g in (cfg.get("required_tasters") or {}).get(rank, []) or []]

    def capstone(self, major: str, rank: int) -> dict | None:
        return (self.majors.get(major, {}).get("capstones") or {}).get(rank)

    def affinity(self, q: Quest, major: str, extras: list[str] | tuple[str, ...] = ()) -> str:
        """major: in one of the member's specializations (primary or extra), or for everyone. adjacent: a taster
        for one of them, or it has a flavor written for one. other: everything else."""
        mine = {major, *extras} - {"undecided"}
        if ALL in q.specializations or mine & set(q.specializations):
            return "major"
        if mine & set(q.taster_for) or mine & set(q.raw.get("flavors") or {}):
            return "adjacent"
        return "other"

    def title_of(self, key: str) -> str:
        return self.specializations.get(key, {}).get("title", key)

    def owner_label(self, q: Quest) -> str:
        """Who a quest belongs to, for grouping: its specializations' titles, 'Everyone' or 'Tasters'."""
        owners = [s for s in q.specializations if s != ALL]
        if q.taster and not q.required:
            return "Tasters"
        if not owners:
            return "Everyone"
        return " · ".join(self.title_of(s) for s in owners[:2]) + (" …" if len(owners) > 2 else "")

    # ---------------- picker ----------------
    def pick(self, u: UserState) -> Pick:
        todo = lambda q: q.id not in u.done and q.id not in u.skipped

        # 1. First steps
        for q in self.first_steps():
            if todo(q):
                return Pick(q, "First steps")
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
        if main is None and u.rank >= 1:
            done_n, need_n, _, tier = self.tier_progress(u, u.rank)
            if done_n < need_n:
                reason = f"Core path done. {done_n}/{need_n} {TIERS[tier]['emoji']} {TIERS[tier]['name']} quests toward the next rank. Pick any."
        # 5. Offer 2 major electives + 1 adjacent
        pool = [q for q in self.sorted(self.quests.values())
                if q.elective and 0 <= q.rank <= u.rank and todo(q) and self.available(q)]
        score = lambda q: -prof_mod.elective_score(q, u.profile, u.major)      # stable sort keeps catalog order on ties
        majors = sorted([q for q in pool if self.affinity(q, u.major, u.extras) == "major"], key=score)[:2]
        adj_pool = [q for q in self.sorted(self.quests.values())
                    if 1 <= q.rank <= u.rank and todo(q) and q not in majors
                    and self.affinity(q, u.major, u.extras) == "adjacent" and not q.required_for_major(u.major)
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
        target = max(u.rank, 0) + 1
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
        if cur <= 0:                          # Novice: the first steps and the Starter Quests
            missing = [q.id for q in self.first_steps() + self.spine() if q.id not in u.done]
        else:
            missing = [q.id for q in self.required(u.major, cur) if q.id not in u.done]
            for g in self.taster_groups(u.major, cur):
                if not any(x in u.done for x in g):
                    missing.append("/".join(g))
            cap = self.capstone(u.major, cur)
            if cap and cap["id"] not in u.done and cap["id"] not in missing:
                missing.append(cap["id"])
            done, need, _, tier = self.tier_progress(u, cur)
            if done < need:                      # tier count: any quests of this tier in the major, member's choice
                missing.append(f"tier:{tier}:{need - done}")
        return (not missing, missing)

    # ---------------- tier counts ----------------
    def counts_for(self, q: Quest, major: str) -> bool:
        """A quest counts toward a specialization's tier total if it belongs to it (or to everyone)."""
        prefix = self.specializations.get(major, {}).get("prefix")
        return bool(prefix and q.id.startswith(prefix)) or q.in_specialization(major)

    def tier_progress(self, u: UserState, rank: int) -> tuple[int, int, int, str]:
        """(done, needed, available, tier) for leaving `rank`. `needed` is capped at what exists so far."""
        cfg = self.ranks.get(rank, {})
        tier = cfg.get("tier", TIER_BY_RANK.get(rank, "master"))
        pool = [q for q in self.quests.values() if q.difficulty == tier and not q.first_steps and self.counts_for(q, u.major)
                and self.available(q)]
        done = sum(q.id in u.done for q in pool)
        need = min(int(cfg.get("quests_to_leave") or 0), len(pool))
        return done, need, len(pool), tier

    def xp_needed(self, target_rank: int) -> int:
        return int(self.ranks.get(target_rank, {}).get("xp", 0))

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
            return f"  {mark} {q.tier['emoji']} {q.id:<7} {q.raw['title']}{cap}{extra}"

        if any(q.id not in u.done for q in self.first_steps()):
            lines.append("FIRST STEPS")
            lines += [row(q) for q in self.first_steps()]
        lines.append("STARTER QUESTS (everyone)")
        lines += [row(q) for q in self.spine()]

        for r in range(1, max(u.rank, 0) + 1):
            title = self.ranks.get(r, {}).get("title", f"Rank {r}")
            lines.append(f"RANK {r} · {title.upper()} · {mt}")
            lines += [row(q) for q in self.required(u.major, r)]
            done_n, need_n, avail, tier = self.tier_progress(u, r)
            if need_n:
                lines.append(f"  {TIERS[tier]['emoji']} {TIERS[tier]['name']} quests: {done_n}/{need_n} done"
                             f" (any {TIERS[tier]['name']} quest in {mt} counts; {avail} exist so far)")
            for g in self.taster_groups(u.major, r):
                qs = [self.quests[x] for x in g if x in self.quests]
                if qs:
                    tag = "  (taster" + (": pick one" if len(qs) > 1 else "") + ")"
                    lines += [row(q, tag) for q in qs]

        nxt = max(u.rank, 0) + 1
        if nxt in self.ranks:
            title = self.ranks[nxt]["title"]
            gate = "Starter Quests" if nxt == 1 else f"Rank {nxt - 1} path"
            if nxt >= 2:
                _, need_n, _, tier = self.tier_progress(u, nxt - 1)
                if need_n:
                    gate += f" + {need_n} {TIERS[tier]['name']} quests"
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
            lines.append("◇ OPTIONAL SHELF: other specializations' work. Nothing here gates you. It opens by rank.")
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
