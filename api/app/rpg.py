"""The RPG layer: stats, gear, bosses and fight rules.

The fight is how a quiz looks. Pass rules are unchanged (see QUIZ_PASS_RATIO): the boss is beaten when you have enough
right answers; you are knocked down one wrong answer past what the pass mark allows. Outfits are cosmetic only:
nothing but the answers changes the outcome.
"""
from __future__ import annotations

import hashlib
import math
import random

from registrar.curriculum import QUIZ_PASS_RATIO, TIERS, Quest  # noqa: E402

TIER_ORDER = ["novice", "apprentice", "adept", "expert", "master"]
RARITY = {"novice": "common", "apprentice": "uncommon", "adept": "rare", "expert": "epic", "master": "legendary"}
RARITY_COLOR = {"common": TIERS["novice"]["color"], "uncommon": TIERS["apprentice"]["color"],
                "rare": TIERS["adept"]["color"], "epic": TIERS["expert"]["color"], "legendary": TIERS["master"]["color"]}
RARITY_RANK = {r: i for i, r in enumerate(["common", "uncommon", "rare", "epic", "legendary"])}
SLOTS = ["head", "chest", "hands", "legs", "feet", "weapon", "offhand", "cape", "shoulders"]   # = UCSourceArt slots
CRIT_XP_DAILY_CAP = 25
SPEED_BONUS_SECONDS = 20          # answer within this many seconds for the full speed crit bonus


# ------------------------------------------------------------------ quiz math
def pass_mark(total: int) -> int:
    return math.ceil(QUIZ_PASS_RATIO * total - 1e-9)


def wounds_allowed(total: int) -> int:
    return total - pass_mark(total)


# ------------------------------------------------------------------ stats (computed, never stored)
def stats_from(done_count: int, first_try_passes: int, approved: int, reads: int, streak: int) -> dict:
    return {
        "vitality": 3 + done_count // 3,
        "focus": first_try_passes,
        "craft": approved,
        "lore": reads,
        "resolve": streak,
    }


STAT_BLURB = {
    "vitality": "Max health. Grows with every quest you finish.",
    "focus": "Crit chance. Grows with every quiz passed on the first try.",
    "craft": "Damage per hit. Grows with every piece of work a reviewer accepts.",
    "lore": "Reveals the boss's next move. Grows when you open the reading before a fight.",
    "resolve": "Steadiness. Your streak. At 7+ days, one wound per fight is halved.",
}


# ------------------------------------------------------------------ outfits (cosmetic only)
# Gear is a visual reward. A set is a whole outfit unlocked by a rank or an achievement. Members wear one set at a
# time, switch between the ones they own, and choose sword-and-shield or staff-and-orb. No stats, ever.
# The eight sets are the ones the art pack (UCSourceArt/pixel-v3) ships; ids match its metadata/pack.json.
SLOTS = ["head", "chest", "legs", "feet", "hands", "shoulders", "back", "weapon", "offhand"]   # = pack slots
STYLES = ["melee", "caster"]                                       # sword+shield | staff+orb
TIER_OF_RANK = {0: "novice", 1: "apprentice", 2: "adept", 3: "expert", 4: "master"}
RANK_FLAVOUR = {
    0: "Hood, tunic and a wooden shield. Everyone starts here.",
    1: "Leather and brass. You have cleared the first tier.",
    2: "Blued steel and rune-etched cloth. The middle of the road.",
    3: "Crimson plate and gold filigree. Few get this far.",
    4: "Ivory and gold, set with emerald. Worn by masters of the guild.",
}
REWARD_SETS = [
    # id (pack), name (pack), flavour, tier colour, unlock (achievement key from ACHIEVEMENTS)
    ("warrior", "Ironwarden", "Dark iron and a tower shield. Your first capstone dungeon, cleared.", "adept",
     {"type": "achievement", "key": "capstone_1", "hint": "Clear a capstone dungeon"}),
    ("ranger", "Thornwatch", "Green leather and a long cloak. Fifty dungeons behind you.", "expert",
     {"type": "achievement", "key": "rooms_50", "hint": "Finish fifty quests"}),
    ("spellcaster", "Runekeeper", "Violet silk and a rune-bound staff. Ten bosses beaten without a scratch.", "expert",
     {"type": "achievement", "key": "focus_10", "hint": "Beat ten bosses on the first try"}),
]
# Exclusive sets: never earned by playing; they belong to a staff role (the art pack's "exclusive" kind).
EXCLUSIVE_SETS = [
    ("developer", "Sourceforged Sovereign", "Circuit-blue plate forged from the source itself. Worn by those who build the guild.", "master",
     {"type": "staff", "role": "developer", "hint": "Developers only"}),
    ("admin", "Sunforged Arbiter", "Gold-chased plate that catches the light of judgement. Worn by those who keep the guild.", "master",
     {"type": "staff", "role": "admin", "hint": "Admins only"}),
    ("mentor", "Astral Guide", "Star-green robes for those who walk beside the newcomer. Worn by those who teach the guild.", "master",
     {"type": "staff", "role": "mentor", "hint": "Mentors only"}),
    # The thank-you set for anyone who donates on /support. Never required for anything; staff grant the
    # `supporter` medal after a donation and the whole set (outfit, avatar frame, card frame) opens at once.
    ("supporter", "Patron's Regalia", "Deep wine and gold, with the guild's mark on the shoulder. Worn by those who keep the lights on.", "master",
     {"type": "medal", "key": "supporter", "hint": "Support Unrealcraft"}),
]


def _outfit_rows() -> list[dict]:
    """The built-in outfit entitlements (rank sets, reward sets, staff exclusives)."""
    rows = []
    for n, tier in TIER_OF_RANK.items():
        name = TIERS[tier]["name"]
        unlock = {"type": "starter"} if n == 0 else {"type": "rank", "n": n, "hint": f"Reach {name}"}
        rows.append(_row("outfit", tier, f"{name}'s Set", RANK_FLAVOUR[n], unlock, {"tier": tier, "art_id": tier, "set_kind": "rank"}, n))
    for i, (sid, name, flavour, tier, unlock) in enumerate(REWARD_SETS):
        rows.append(_row("outfit", sid, name, flavour, unlock, {"tier": tier, "art_id": sid, "set_kind": "reward"}, 10 + i))
    for i, (sid, name, flavour, tier, unlock) in enumerate(EXCLUSIVE_SETS):
        rows.append(_row("outfit", sid, name, flavour, unlock, {"tier": tier, "art_id": sid, "set_kind": "exclusive"}, 20 + i))
    return rows


def _row(kind: str, eid: str, name: str, desc: str, unlock: dict, data: dict, sort: int) -> dict:
    return {"kind": kind, "id": eid, "name": name, "desc": desc, "unlock": unlock, "data": data, "sort": sort, "builtin": True, "enabled": True}


def build_sets(ents) -> list[dict]:
    """The outfit catalog in the shape the wardrobe uses, from the entitlement store."""
    out = []
    for r in ents.of("outfit"):
        d = r["data"]
        tier = d.get("tier") if d.get("tier") in TIERS else "novice"
        out.append({"id": r["id"], "name": r["name"], "flavour": r["desc"], "kind": d.get("set_kind", "reward"),
                    "tier": tier, "color": TIERS[tier]["color"], "art_id": d.get("art_id") or r["id"], "unlock": r["unlock"]})
    return out


STARTER_SET = "novice"


def unlocked_now(sets: list[dict], *, rank: int, earned: set[str], role: str | None = None,
                 medals: set[str] | None = None, grants: set[tuple[str, str]] | None = None) -> list[dict]:
    """Which sets this member owns right now: by rule, or handed over by staff. Idempotent, so it runs on every visit."""
    from .entitlements import owned
    return [st for st in sets
            if owned(st["unlock"], rank=rank, earned=earned, medals=medals or set(), role=role) or ("outfit", st["id"]) in (grants or set())]


# ------------------------------------------------------------------ bosses
EPITHET = {"novice": "Sentry", "apprentice": "Warden", "adept": "Keeper", "expert": "Tyrant", "master": "Sovereign"}
NAMES = ["Vaelith", "Orrun", "Sisk", "Maelor", "Tharn", "Ilvess", "Korrigan", "Brann", "Ysolde", "Ferrox", "Nimue",
         "Draeg", "Ophane", "Ruk", "Selwyn", "Ashka", "Morrow", "Tindral", "Quell", "Harrowen", "Lisbet", "Vorn",
         "Emberlyn", "Gadrik", "Solenne", "Kestrel", "Umbra", "Peregrin", "Cindra", "Halvard"]
DOMAIN = {
    "lumen": "Bounced Light", "lighting": "Cast Shadow", "exposure": "the Blinding Sun", "post-process": "the Graded Veil",
    "world-lighting": "Cast Shadow", "fog": "the Low Mist", "sky": "the Painted Sky",
    "blueprint": "Wired Logic", "bp": "Wired Logic", "interaction": "the Pressed Switch", "components": "Bolted Parts",
    "cpp": "Iron Syntax", "code": "Iron Syntax", "networking": "the Split Mirror", "debugging": "the Hidden Fault",
    "profiling": "the Stolen Millisecond", "performance": "the Stolen Millisecond", "optimization": "the Stolen Millisecond",
    "materials": "Woven Surfaces", "material": "Woven Surfaces", "textures": "the Painted Skin", "decals": "the Stamped Mark",
    "sequencer": "Frozen Time", "cine-camera": "the Glass Eye", "movie-render-queue": "the Final Frame",
    "camera-shake": "the Trembling Frame", "virtual-camera": "the Borrowed Eye", "take-recorder": "the Caught Moment",
    "niagara": "Burning Motes", "vfx": "Burning Motes",
    "ai": "Hollow Minds", "navigation": "the Unseen Path", "smart-objects": "the Waiting Chair",
    "animation": "Bone Puppets", "animation-blueprint": "the Blended Pose", "control-rig": "the Pulled String",
    "retargeting": "the Borrowed Skeleton", "ik": "the Planted Foot", "montage": "the Cut Motion", "groom": "the Wild Hair",
    "physics-asset": "the Ragdoll", "skeletal-mesh": "the Bare Skeleton",
    "landscape": "the Sculpted Earth", "foliage": "the Green Tide", "pcg": "the Endless Scatter", "water": "the Still River",
    "world-partition": "the Streamed World", "data-layers": "the Layered World", "hlod": "the Far Horizon",
    "level-instancing": "the Repeated Room", "modeling-mode": "the Cut Stone", "geometry-script": "the Living Mesh",
    "nanite": "the Million Triangles", "static-mesh": "the Cold Stone", "merge-actors": "the Fused Kit",
    "editor": "the Toolbox", "editor-utility-widget": "the Toolbox", "editor-utility": "the Toolbox", "python": "the Scripted Hand",
    "tools": "the Toolbox", "umg": "the Painted Glass", "audio": "the Echo", "discord": "the Guild Hall", "meta": "the Guild Hall",
    "viewport": "the First Window", "screenshots": "the Captured View", "metrics": "the Measured Step", "capstone": "the Whole Work",
    "testing": "the Proving Ground", "actors": "the Placed Thing", "path-tracer": "the Slow Truth",
    "install": "the First Launch", "project": "the Empty Project", "content-browser": "the Asset Vault",
    "outliner": "the Long List", "graybox": "the Grey Room", "pawn": "the First Body", "gas": "the Granted Power",
    "rules": "the Guild Hall",
}
LOOK = [  # (look key, subjects/tracks that pick it)
    ("wisp", {"lumen", "lighting", "exposure", "post-process", "world-lighting", "fog", "sky", "path-tracer"}),
    ("golem", {"materials", "material", "textures", "decals", "static-mesh", "nanite", "merge-actors"}),
    ("serpent", {"blueprint", "bp", "interaction", "components", "cpp", "code", "networking", "debugging", "programming"}),
    ("spectre", {"sequencer", "cine-camera", "movie-render-queue", "camera-shake", "virtual-camera", "take-recorder", "cinematics"}),
    ("beast", {"animation", "animation-blueprint", "control-rig", "retargeting", "ik", "montage", "groom", "physics-asset", "skeletal-mesh", "characters-anim"}),
    ("swarm", {"niagara", "vfx"}),
    ("sentinel", {"ai", "navigation", "smart-objects"}),
    ("treant", {"landscape", "foliage", "pcg", "water", "world-partition", "data-layers", "hlod", "level-instancing", "level-design"}),
    ("construct", {"editor", "editor-utility-widget", "editor-utility", "python", "tools", "umg", "modeling-mode", "geometry-script", "tech-art"}),
    ("wraith", {"profiling", "performance", "optimization", "testing"}),
    ("knight", {"discord", "meta", "orientation", "viewport", "screenshots", "metrics", "starter-quests"}),
    ("drake", {"capstone"}),
]
MOVES = {
    "wisp": ("flares", "The light bends toward you."), "golem": ("swings", "Stone grinds on stone."),
    "serpent": ("coils", "It winds through the graph."), "spectre": ("cuts", "The frame skips."),
    "beast": ("lunges", "Every bone moves at once."), "swarm": ("scatters", "A thousand sparks turn."),
    "sentinel": ("scans", "It has already found the path to you."), "treant": ("roots", "The ground shifts."),
    "construct": ("clicks", "Gears you did not build turn."), "wraith": ("drains", "A frame goes missing."),
    "knight": ("advances", "It has read the rules."), "drake": ("rises", "The whole work stands before you."),
}


# UCSourceArt creature ids. Ordinary dungeons use the six enemies; capstones use the three bosses.
ENEMY_FOR_LOOK = {"wisp": "enemy_rune_wisp", "golem": "enemy_broken_construct", "serpent": "enemy_crystal_crawler",
                  "spectre": "enemy_rune_wisp", "beast": "enemy_moss_imp", "swarm": "enemy_crystal_slime",
                  "sentinel": "enemy_thorn_sentinel", "treant": "enemy_thorn_sentinel", "construct": "enemy_broken_construct",
                  "wraith": "enemy_rune_wisp", "knight": "enemy_crystal_slime", "drake": "boss_blueprint_hydra"}
BOSS_TITLE = {"boss_compiler_golem": "The Compiler Golem", "boss_blueprint_hydra": "The Blueprint Hydra",
              "boss_optimization_wyrm": "The Optimization Wyrm"}


def capstone_creature(q: Quest) -> str:
    owners = [m for m in q.required_for if m != "all"]
    major = owners[0] if owners else ""
    if q.difficulty in ("expert", "master"):
        return "boss_optimization_wyrm"
    return "boss_compiler_golem" if major in ("programming", "tech_art") else "boss_blueprint_hydra"


def boss_for(q: Quest) -> dict:
    subjects = [s.lower() for s in (q.raw.get("subjects") or [])]
    h = int(hashlib.sha1(q.id.encode()).hexdigest(), 16)
    name = NAMES[h % len(NAMES)]
    domain = next((DOMAIN[s] for s in subjects if s in DOMAIN), None) or (subjects[0].replace("-", " ").title() if subjects else "the Unknown")
    look = "drake" if q.capstone else next((k for k, keys in LOOK if (set(subjects) & keys) or q.track in keys), "knight")
    epithet = "Dragon" if q.capstone else EPITHET.get(q.difficulty, "Keeper")
    total = len(q.quiz)
    verb, line = MOVES[look]
    creature = capstone_creature(q) if q.capstone else ENEMY_FOR_LOOK.get(look, "enemy_crystal_slime")
    full_name = f"{BOSS_TITLE[creature]} of {domain}" if q.capstone else f"{name}, {epithet} of {domain}"
    return {
        "name": full_name, "short": BOSS_TITLE[creature].removeprefix("The ") if q.capstone else name,
        "epithet": epithet, "domain": domain, "look": look, "creature": creature, "kind": "boss" if q.capstone else "enemy",
        "tier": q.difficulty, "color": q.tier["color"], "hits_to_win": pass_mark(total) if total else 0,
        "questions": total, "wounds_allowed": wounds_allowed(total) if total else 0, "verb": verb, "intro": line,
        "hint_topics": subjects[:3],
    }


def boss_line(boss: dict, kind: str, rng: random.Random) -> str:
    n = boss["short"]
    lines = {
        "hit": [f"{n} staggers.", f"Your strike lands. {n} reels.", f"{n} loses its footing.", "A clean hit."],
        "crit": [f"A perfect strike. {n} howls.", "Critical hit. The dungeon shakes.", f"{n} did not see that coming."],
        "wound": [f"{n} {boss['verb']}. You take the hit.", "It got through.", f"{n} finds the gap."],
        "steady": ["You brace. Half the blow lands.", "Resolve holds. It only grazes you."],
        "win": [f"{n} falls. The dungeon goes quiet.", f"{n} is beaten. The way forward is open."],
        "lose": [f"{n} stands over you. Regroup and return.", "You are knocked down. The dungeon closes for now."],
    }
    return rng.choice(lines[kind])


# ------------------------------------------------------------------ debuffs
DEBUFFS = {
    "dazed": {"name": "Dazed", "text": "The choices shuffle next turn."},
    "weakened": {"name": "Weakened", "text": "Your next hit does half damage."},
    "blinded": {"name": "Blinded", "text": "No hint next turn."},
}


def debuff_for(subject: str | None, rng: random.Random) -> str:
    return rng.choice(list(DEBUFFS))


def crit_chance(focus: int, seconds: float | None) -> int:
    speed = 0
    if seconds is not None and seconds <= SPEED_BONUS_SECONDS:
        speed = round(15 * (1 - seconds / SPEED_BONUS_SECONDS))
    return min(40, 5 + focus + speed)


# ------------------------------------------------------------------ achievements
# Facts we already store decide these; nothing is written when one is earned except the medals the bot grants.
# Keys named in REWARD_SETS (capstone_1, rooms_50, focus_10) unlock outfits; `badge` is the pack's ui/badges index.
ACHIEVEMENTS = [
    {"key": "first_blood", "name": "First Blood", "desc": "Finish your first quest in the engine.", "icon": "⚔️", "need": 1, "of": "medal", "badge": 1},
    {"key": "rooms_10", "name": "Ten Dungeons Cleared", "desc": "Finish ten quests.", "icon": "🚪", "need": 10, "of": "done", "badge": 3},
    {"key": "rooms_50", "name": "Fifty Dungeons Cleared", "desc": "Finish fifty quests.", "icon": "🏰", "need": 50, "of": "done", "outfit": "ranger", "badge": 3},
    {"key": "rooms_150", "name": "Dungeon Delver", "desc": "Finish one hundred and fifty quests.", "icon": "🗝️", "need": 150, "of": "done", "badge": 8},
    {"key": "focus_10", "name": "Flawless", "desc": "Beat ten bosses on the first try.", "icon": "🎯", "need": 10, "of": "first", "outfit": "spellcaster", "badge": 6},
    {"key": "focus_50", "name": "Unerring", "desc": "Beat fifty bosses on the first try.", "icon": "💎", "need": 50, "of": "first", "badge": 6},
    {"key": "craft_1", "name": "Reviewed", "desc": "Have a piece of your work accepted by a reviewer.", "icon": "🛠️", "need": 1, "of": "approved", "badge": 4},
    {"key": "craft_10", "name": "Journeyman's Hands", "desc": "Have ten pieces of work accepted.", "icon": "🔨", "need": 10, "of": "approved", "badge": 4},
    {"key": "lore_10", "name": "Well Read", "desc": "Open the reading on ten quests before the fight.", "icon": "📖", "need": 10, "of": "reads", "badge": 7},
    {"key": "lore_50", "name": "Loremaster", "desc": "Open the reading on fifty quests before the fight.", "icon": "📚", "need": 50, "of": "reads", "badge": 7},
    {"key": "streak_7", "name": "A Week of Showing Up", "desc": "Keep a seven-day streak.", "icon": "🔥", "need": 7, "of": "streak", "badge": 5},
    {"key": "streak_30", "name": "Ember of Thirty Days", "desc": "Keep a thirty-day streak.", "icon": "🌋", "need": 30, "of": "streak", "badge": 5},
    {"key": "capstone_1", "name": "Capstone Bearer", "desc": "Clear a capstone dungeon.", "icon": "🐉", "need": 1, "of": "capstones", "outfit": "warrior", "badge": 6},
    {"key": "capstone_4", "name": "Dragonslayer", "desc": "Clear four capstone dungeons.", "icon": "👑", "need": 4, "of": "capstones", "badge": 8},
    {"key": "specs_3", "name": "Many Trades", "desc": "Finish a quest in three different specializations.", "icon": "🧭", "need": 3, "of": "specs", "badge": 3},
    {"key": "specs_7", "name": "Guild of One", "desc": "Finish a quest in every specialization.", "icon": "🌐", "need": 7, "of": "specs", "badge": 8},
    {"key": "cross_25", "name": "Far Traveller", "desc": "Finish twenty-five quests outside your primary specialization.", "icon": "🧳", "need": 25, "of": "cross", "badge": 3},
]
RANK_UP_NAMES = {1: "Apprentice", 2: "Adept", 3: "Expert", 4: "Master"}


def _achievement_rows() -> list[dict]:
    return [_row("achievement", a["key"], a["name"], a["desc"], {"type": "starter"},
                 {k: v for k, v in a.items() if k in ("icon", "need", "of", "badge", "outfit")}, i) for i, a in enumerate(ACHIEVEMENTS)]


def achievements_for(ents, cat, inputs: dict, done: set[str], medals: list[dict], grants: set[tuple[str, str]] | None = None,
                     primary: str | None = None) -> list[dict]:
    """Every achievement with progress, earned flag and the outfit it unlocks (if any). Rank-ups come from medals.
    An achievement counting `medal` is earned when the member holds a medal with the achievement's key; a direct
    grant from the admin panel earns any of them. `specs` counts the specializations the member finished a quest
    in; `cross` counts finished quests outside the primary specialization (both ignore quests for everyone)."""
    earned_at = {m["medal_key"]: m["earned_at"] for m in medals}
    done_q = [q for qid in done if cat and (q := cat.quests.get(qid))]
    caps = sum(1 for q in done_q if q.capstone)
    owned_specs = {s for q in done_q for s in q.specializations if s != "all"}
    cross = sum(1 for q in done_q if q.specializations and "all" not in q.specializations and primary not in q.specializations)
    have = {"done": inputs["done"], "first": inputs["first"], "approved": inputs["approved"], "reads": inputs["reads"],
            "streak": inputs["streak"], "capstones": caps, "specs": len(owned_specs), "cross": cross}
    out = []
    for r in ents.of("achievement"):
        d = r["data"]
        a = {"key": r["id"], "name": r["name"], "desc": r["desc"], "icon": d.get("icon") or "🏅", "need": int(d.get("need", 1)),
             "of": d.get("of", "medal"), "badge": d.get("badge", 2), **({"outfit": d["outfit"]} if d.get("outfit") else {})}
        n = 1 if (a["of"] == "medal" and a["key"] in earned_at) else (0 if a["of"] == "medal" else have.get(a["of"], 0))
        ok = n >= a["need"] or ("achievement", a["key"]) in (grants or set())
        out.append({**a, "have": a["need"] if ok else min(n, a["need"]), "earned": ok, "earned_at": earned_at.get(a["key"]) if ok else None})
    for key, at in earned_at.items():
        if key.startswith("jump_"):
            to = int(key.split("_")[-1])
            out.append({"key": key, "name": f"Rose to {RANK_UP_NAMES.get(to, f'rank {to}')}", "desc": "Promoted by the guild.",
                        "icon": "🏅", "need": 1, "of": "medal", "have": 1, "earned": True, "earned_at": at, "badge": 2})
    return out


# ------------------------------------------------------------------ card cosmetics (nameplate colours, frames)
# Small unlockables in the spirit of Nitro perks, earned rather than bought: starter picks are free, the rest come
# from ranks and achievements. Values are ids; the site maps them to colours and CSS frames.
NAMEPLATES = [
    ("slate", "#7A8C7E", "Slate", {"type": "starter"}),
    ("teal", "#4AA3B5", "Teal", {"type": "starter"}),
    ("umber", "#B5714B", "Umber", {"type": "starter"}),
    ("cobalt", "#3D7DD8", "Cobalt", {"type": "rank", "n": 1, "hint": "Reach Apprentice"}),
    ("amethyst", "#8E6CCF", "Amethyst", {"type": "rank", "n": 2, "hint": "Reach Adept"}),
    ("ember", "#D9824A", "Ember", {"type": "rank", "n": 3, "hint": "Reach Expert"}),
    ("crimson", "#D9534F", "Crimson", {"type": "rank", "n": 4, "hint": "Reach Master"}),
    ("moss", "#4FA36C", "Moss", {"type": "achievement", "key": "rooms_10", "hint": "Finish ten quests"}),
    ("rose", "#C85C8E", "Rose", {"type": "achievement", "key": "streak_7", "hint": "Keep a seven-day streak"}),
    ("gold", "#D4AF37", "Gold", {"type": "achievement", "key": "capstone_1", "hint": "Clear a capstone dungeon"}),
]
# Ten decoration themes from the art pack (profile-decorations/): each has a matching avatar ring and card border.
# The same rule unlocks both, so a theme arrives as a pair.
DECORATIONS = [
    ("none", "None", "No decoration.", {"type": "starter"}),
    ("novice", "Novice", "Leather wraps and a bronze rim.", {"type": "starter"}),
    ("apprentice", "Apprentice", "Teal ribbons on bronze.", {"type": "rank", "n": 1, "hint": "Reach Apprentice"}),
    ("adept", "Adept", "Polished silver with blue crystal.", {"type": "rank", "n": 2, "hint": "Reach Adept"}),
    ("expert", "Expert", "Dark steel, violet runes.", {"type": "rank", "n": 3, "hint": "Reach Expert"}),
    ("master", "Master", "Ivory enamel, gold filigree, emerald.", {"type": "rank", "n": 4, "hint": "Reach Master"}),
    ("thornwood", "Thornwood", "Twisting vines and small leaves.", {"type": "achievement", "key": "rooms_10", "hint": "Finish ten quests"}),
    ("emberforge", "Emberforge", "Charcoal iron with ember cracks.", {"type": "achievement", "key": "streak_7", "hint": "Keep a seven-day streak"}),
    ("frostbound", "Frostbound", "Pale silver and ice crystals.", {"type": "achievement", "key": "focus_10", "hint": "Beat ten bosses on the first try"}),
    ("celestial", "Celestial", "Midnight blue, gold stars, a crescent moon.", {"type": "achievement", "key": "lore_10", "hint": "Open the reading on ten quests"}),
    ("dragonheart", "Dragonheart", "Crimson scales and dragon horns.", {"type": "achievement", "key": "capstone_1", "hint": "Clear a capstone dungeon"}),
    ("developer", "Developer", "Circuit-blue trim with a living pulse.", {"type": "staff", "role": "developer", "hint": "Developers only"}),
    ("admin", "Admin", "Sunforged gold with a steady shine.", {"type": "staff", "role": "admin", "hint": "Admins only"}),
    ("mentor", "Mentor", "Astral green with a quiet glow.", {"type": "staff", "role": "mentor", "hint": "Mentors only"}),
    ("supporter", "Patron", "Wine-red enamel and gold, with a small heart at the top.", {"type": "medal", "key": "supporter", "hint": "Support Unrealcraft"}),
]
# Titles, shown after the name like "Kai, the Learner". Earned, never bought; "none" hides it.
TITLES = [
    ("none", "No title", "Nothing after your name.", {"type": "starter"}),
    ("learner", "the Learner", "You finished your first quest.", {"type": "achievement", "key": "first_blood", "hint": "Finish your first quest"}),
    ("steadfast", "the Steadfast", "A seven-day streak.", {"type": "achievement", "key": "streak_7", "hint": "Keep a seven-day streak"}),
    ("well_read", "the Well-Read", "Ten readings opened before the fight.", {"type": "achievement", "key": "lore_10", "hint": "Open the reading on ten quests"}),
    ("flawless", "the Flawless", "Ten bosses beaten on the first try.", {"type": "achievement", "key": "focus_10", "hint": "Beat ten bosses on the first try"}),
    ("reviewed", "the Reviewed", "A reviewer accepted your work.", {"type": "achievement", "key": "craft_1", "hint": "Have a piece of work accepted"}),
    ("delver", "the Delver", "Fifty dungeons cleared.", {"type": "achievement", "key": "rooms_50", "hint": "Finish fifty quests"}),
    ("dragonslayer", "the Dragonslayer", "Four capstone dungeons cleared.", {"type": "achievement", "key": "capstone_4", "hint": "Clear four capstone dungeons"}),
    ("master", "the Master", "The top rank of the guild.", {"type": "rank", "n": 4, "hint": "Reach Master"}),
    ("versatile", "the Versatile", "A quest finished in three specializations.", {"type": "achievement", "key": "specs_3", "hint": "Finish a quest in three specializations"}),
    ("wayfarer", "the Wayfarer", "Twenty-five quests outside your primary specialization.", {"type": "achievement", "key": "cross_25", "hint": "Finish twenty-five quests outside your primary specialization"}),
    ("guide", "the Guide", "Walks beside the newcomer.", {"type": "staff", "role": "mentor", "hint": "Mentors only"}),
    ("keeper", "Keeper of the Guild", "Keeps the guild.", {"type": "staff", "role": "admin", "hint": "Admins only"}),
    ("sourceforged", "the Sourceforged", "Builds the guild.", {"type": "staff", "role": "developer", "hint": "Developers only"}),
]
DEFAULT_TITLE = "none"
# Home banners: the living scene behind the home page. The river town is everyone's; each rank opens a new place.
# Ids match the art pack (banners/rank-banners/<id>); "town" is the original living town.
HOME_BANNERS = [
    ("town", "Riverside Town", "The guild's town by the river, where everyone starts.", {"type": "starter"}),
    ("apprentice", "Mossgate Guild Outpost", "An ancient oak, a training yard, a forest stream and a watermill.", {"type": "rank", "n": 1, "hint": "Reach Apprentice"}),
    ("adept", "Moonmere Academy", "A lakeside observatory with a crystal telescope and an island shrine.", {"type": "rank", "n": 2, "hint": "Reach Adept"}),
    ("expert", "Emberfall Bastion", "A dragon-guarded mountain fortress, a causeway and a hydraulic forge.", {"type": "rank", "n": 3, "hint": "Reach Expert"}),
    ("master", "Crown of the Aether", "A floating celestial capital with garden canals and cascading islands.", {"type": "rank", "n": 4, "hint": "Reach Master"}),
]
DEFAULT_HOME_BANNER = "town"


def default_entitlements() -> list[dict]:
    """The built-in catalog, one flat list of entitlement rows. The admin table overrides or extends it."""
    rows = _outfit_rows()
    rows += [_row("nameplate", i, n, "", u, {"value": v}, k) for k, (i, v, n, u) in enumerate(NAMEPLATES)]
    for kind in ("avatar_frame", "card_frame"):
        rows += [_row(kind, i, n, d, u, {"art": None if i == "none" else i}, k) for k, (i, n, d, u) in enumerate(DECORATIONS)]
    rows += [_row("title", i, n, d, u, {}, k) for k, (i, n, d, u) in enumerate(TITLES)]
    rows += [_row("home_banner", i, n, d, u, {"art": None if i == DEFAULT_HOME_BANNER else i}, k) for k, (i, n, d, u) in enumerate(HOME_BANNERS)]
    rows += _achievement_rows()
    return rows


def entitlement_catalog(ents, *, rank: int, earned: set[str], medals: set[str], role: str | None,
                        grants: set[tuple[str, str]], unlock_all: bool = False, ranks: dict | None = None) -> dict:
    """Every card entitlement (colour, frames, title, home banner) with its owned flag and unlock hint, grouped by kind.
    Admins and developers testing get everything."""
    from .entitlements import hint_for, owned
    out: dict[str, list[dict]] = {}
    for kind in ("nameplate", "avatar_frame", "card_frame", "title", "home_banner"):
        items = []
        for r in ents.of(kind):
            granted = (kind, r["id"]) in grants
            own = unlock_all or granted or owned(r["unlock"], rank=rank, earned=earned, medals=medals, role=role)
            item = {"id": r["id"], "name": r["name"], "desc": r["desc"], "owned": own, "hint": hint_for(r["unlock"], ranks), "granted": granted}
            if kind == "nameplate":
                item["value"] = r["data"].get("value")
            if kind in ("avatar_frame", "card_frame", "home_banner"):
                item["art"] = r["data"].get("art")
            items.append(item)
        out[kind] = items
    return out


def pick_owned(catalog: list[dict], chosen: str | None) -> dict:
    """The chosen entitlement if it is owned (by id or value), else the first owned one."""
    for c in catalog:
        if chosen and chosen in (c["id"], c.get("value")) and c["owned"]:
            return c
    return next(c for c in catalog if c["owned"])
