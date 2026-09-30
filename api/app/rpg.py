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
# Gear is a visual reward. A set is a whole outfit (every slot at once) unlocked by a quest, a rank or an
# achievement. Members wear one set at a time and can switch between the ones they own. No stats, ever.
SLOTS = ["head", "chest", "hands", "legs", "feet", "weapon", "offhand", "cape", "shoulders"]   # = UCSourceArt slots
MAJOR_TITLE = {"level_design": "Level Design", "programming": "Programming", "lookdev": "Environment Art",
               "tech_art": "Tech Art", "gameplay_design": "Gameplay Design", "animation": "Animation",
               "cinematics": "Cinematics", "undecided": "Undecided"}

# Per major: the four rank outfits (Apprentice, Adept, Expert, Master) and four capstone regalia (rank 1-4).
RANK_SETS = {
    "level_design":    ["Surveyor's Garb", "Architect's Vestments", "Warden of Halls", "Worldshaper's Regalia"],
    "programming":     ["Scribe's Garb", "Compiler's Vestments", "Warden of Systems", "Kernelbinder's Regalia"],
    "lookdev":         ["Painter's Garb", "Lightweaver's Vestments", "Warden of Surfaces", "Sunforger's Regalia"],
    "tech_art":        ["Tinker's Garb", "Nodewright's Vestments", "Warden of Sparks", "Machinist's Regalia"],
    "gameplay_design": ["Playtester's Garb", "Rulewright's Vestments", "Warden of Loops", "Gamemaster's Regalia"],
    "animation":       ["Puppeteer's Garb", "Rigwright's Vestments", "Warden of Motion", "Lifegiver's Regalia"],
    "cinematics":      ["Framer's Garb", "Director's Vestments", "Warden of Light", "Showrunner's Regalia"],
}
CAPSTONE_SETS = {
    "level_design":    ["Courtyard Pilgrim", "Beatkeeper", "Encounter Marshal", "Kitsmith of the Modular Hall"],
    "programming":     ["Debug Room Squire", "Loopbinder", "Bridgewright of Two Languages", "Portmaster"],
    "lookdev":         ["Diorama Keeper", "Walker of the Lit Path", "Reference Bearer", "Librarian of Functions"],
    "tech_art":        ["Test Bed Warden", "Masterweaver", "Toolsmith", "Pipeline Marshal"],
    "gameplay_design": ["Toybox Keeper", "Loopmaster", "Systems Marshal", "Feature Marshal"],
    "animation":       ["First Mover", "Statekeeper", "Retarget Marshal", "Rigmaster"],
    "cinematics":      ["Shotkeeper", "Sequence Marshal", "Render Marshal", "Cutmaster"],
}
TIER_OF_RANK = {1: "apprentice", 2: "adept", 3: "expert", 4: "master"}


def _set(sid: str, name: str, flavour: str, major: str, tier: str, unlock: dict) -> dict:
    return {"id": sid, "name": name, "flavour": flavour, "major": major, "tier": tier, "color": TIERS[tier]["color"],
            "art_id": f"set_{sid}", "unlock": unlock}


def build_sets(cat) -> list[dict]:
    """The full outfit catalog. Unlock rules: starter | rank(n, major) | quest(id) | achievement(key)."""
    out = [_set("wayfarer", "Wayfarer's Set", "Teal cloth and brown leather. Everyone starts here.", "undecided", "novice", {"type": "starter"}),
           _set("first_blood", "First Blood Tabard", "You finished your first quest in the engine.", "undecided", "novice",
                {"type": "achievement", "key": "first_blood", "hint": "Finish your first Unreal quest"}),
           _set("flawless_10", "Flawless Mantle", "Ten bosses beaten on the first try. Nothing wasted.", "undecided", "adept",
                {"type": "achievement", "key": "focus_10", "hint": "Beat 10 bosses on the first try"}),
           _set("streak_30", "Ember of Thirty Days", "A month of showing up.", "undecided", "expert",
                {"type": "achievement", "key": "streak_30", "hint": "Reach a 30-day streak"}),
           _set("reader_50", "Loremaster's Robe", "Fifty guides opened before the fight.", "undecided", "expert",
                {"type": "achievement", "key": "lore_50", "hint": "Open the reading on 50 quests"})]
    for major, names in RANK_SETS.items():
        for i, name in enumerate(names, start=1):
            out.append(_set(f"{major}_r{i}", name, f"Worn by every {TIERS[TIER_OF_RANK[i]]['name']} of {MAJOR_TITLE[major]}.",
                            major, TIER_OF_RANK[i], {"type": "rank", "n": i, "major": major,
                                                     "hint": f"Reach {TIERS[TIER_OF_RANK[i]]['name']} in {MAJOR_TITLE[major]}"}))
    for major, names in CAPSTONE_SETS.items():
        caps = (cat.majors.get(major, {}).get("capstones") or {}) if cat else {}
        for i, name in enumerate(names, start=1):
            cap = caps.get(i) or {}
            out.append(_set(f"{major}_cap{i}", name, cap.get("brief") or f"The rank {i} capstone of {MAJOR_TITLE[major]}.",
                            major, TIER_OF_RANK[i], {"type": "quest", "id": cap.get("id"), "hint": f"Clear the {MAJOR_TITLE[major]} rank {i} capstone: {cap.get('title', '')}".strip()}))
    return out


def unlocked_now(sets: list[dict], *, rank: int, major: str, done: set[str], medals: set[str], stats: dict) -> list[dict]:
    """Which sets this member has earned, from facts we already store. Idempotent, so it can run on every visit."""
    won = []
    for st in sets:
        u = st["unlock"]
        if u["type"] == "starter":
            ok = True
        elif u["type"] == "rank":
            ok = major == u["major"] and rank >= u["n"]
        elif u["type"] == "quest":
            ok = bool(u.get("id")) and u["id"] in done
        else:
            key = u["key"]
            ok = (key in medals) or (key == "focus_10" and stats["focus"] >= 10) or \
                 (key == "streak_30" and stats["resolve"] >= 30) or (key == "lore_50" and stats["lore"] >= 50)
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
    ("knight", {"discord", "meta", "orientation", "viewport", "screenshots", "metrics", "foundations"}),
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


# UCSourceArt creature ids. Ordinary rooms use the six enemies; capstones use the three bosses.
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
        "crit": [f"A perfect strike. {n} howls.", "Critical hit. The room shakes.", f"{n} did not see that coming."],
        "wound": [f"{n} {boss['verb']}. You take the hit.", "It got through.", f"{n} finds the gap."],
        "steady": ["You brace. Half the blow lands.", "Resolve holds. It only grazes you."],
        "win": [f"{n} falls. The room goes quiet.", f"{n} is beaten. The way forward is open."],
        "lose": [f"{n} stands over you. Regroup and return.", "You are knocked down. The boss room closes for now."],
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
