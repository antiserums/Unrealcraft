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


def _set(sid: str, name: str, flavour: str, kind: str, tier: str, unlock: dict) -> dict:
    return {"id": sid, "name": name, "flavour": flavour, "kind": kind, "major": "undecided", "tier": tier,
            "color": TIERS[tier]["color"], "art_id": sid, "unlock": unlock}


def build_sets(cat=None) -> list[dict]:
    """The full outfit catalog. Unlock rules: starter | rank(n) | achievement(key)."""
    out = []
    for n, tier in TIER_OF_RANK.items():
        name = TIERS[tier]["name"]
        unlock = {"type": "starter"} if n == 0 else {"type": "rank", "n": n, "hint": f"Reach {name}"}
        out.append(_set(tier, f"{name}'s Set", RANK_FLAVOUR[n], "rank", tier, unlock))
    for sid, name, flavour, tier, unlock in REWARD_SETS:
        out.append(_set(sid, name, flavour, "reward", tier, unlock))
    return out


STARTER_SET = "novice"


def unlocked_now(sets: list[dict], *, rank: int, earned: set[str]) -> list[dict]:
    """Which sets this member has earned. Idempotent, so it can run on every visit."""
    won = []
    for st in sets:
        u = st["unlock"]
        ok = u["type"] == "starter" or (u["type"] == "rank" and rank >= u["n"]) or \
             (u["type"] == "achievement" and u["key"] in earned)
        if ok:
            won.append(st)
    return won


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
]
RANK_UP_NAMES = {1: "Apprentice", 2: "Adept", 3: "Expert", 4: "Master"}


def achievements_for(cat, inputs: dict, done: set[str], medals: list[dict]) -> list[dict]:
    """Every achievement with progress, earned flag and the outfit it unlocks (if any). Rank-ups come from medals."""
    earned_at = {m["medal_key"]: m["earned_at"] for m in medals}
    caps = sum(1 for qid in done if (q := cat.quests.get(qid)) and q.capstone) if cat else 0
    have = {"done": inputs["done"], "first": inputs["first"], "approved": inputs["approved"], "reads": inputs["reads"],
            "streak": inputs["streak"], "capstones": caps}
    out = []
    for a in ACHIEVEMENTS:
        n = 1 if (a["of"] == "medal" and a["key"] in earned_at) else (0 if a["of"] == "medal" else have[a["of"]])
        ok = n >= a["need"]
        out.append({**a, "have": min(n, a["need"]), "earned": ok, "earned_at": earned_at.get(a["key"]) if ok else None})
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
]
AVATAR_FRAMES = [(i, n, u) for i, n, _d, u in DECORATIONS]
CARD_FRAMES = [(i, n, u) for i, n, _d, u in DECORATIONS]
DECO_DESC = {i: d for i, _n, d, _u in DECORATIONS}


def _owned(unlock: dict, rank: int, earned: set[str]) -> bool:
    return unlock["type"] == "starter" or (unlock["type"] == "rank" and rank >= unlock["n"]) or \
        (unlock["type"] == "achievement" and unlock["key"] in earned)


def cosmetic_catalog(rank: int, earned: set[str], unlock_all: bool = False) -> dict:
    """Every card cosmetic with its owned flag and unlock hint, grouped by kind. Admins testing get everything."""
    own = (lambda u: True) if unlock_all else (lambda u: _owned(u, rank, earned))
    return {
        "nameplate": [{"id": i, "value": v, "name": n, "owned": own(u), "hint": u.get("hint")} for i, v, n, u in NAMEPLATES],
        "avatar_frame": [{"id": i, "name": n, "desc": DECO_DESC[i], "owned": own(u), "hint": u.get("hint")} for i, n, u in AVATAR_FRAMES],
        "card_frame": [{"id": i, "name": n, "desc": DECO_DESC[i], "owned": own(u), "hint": u.get("hint")} for i, n, u in CARD_FRAMES],
    }


def pick_owned(catalog: list[dict], chosen: str | None) -> dict:
    """The chosen cosmetic if it is owned (by id or value), else the first starter."""
    for c in catalog:
        if chosen and chosen in (c["id"], c.get("value")) and c["owned"]:
            return c
    return next(c for c in catalog if c["owned"])
