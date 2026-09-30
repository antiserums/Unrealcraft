"""The RPG layer: stats, gear, bosses and fight rules.

The fight is how a quiz looks. Pass rules are unchanged (see QUIZ_PASS_RATIO): the boss is beaten when you have enough
right answers; you are knocked down one wrong answer past what the pass mark allows. Gear may afford ONE dodge per
fight (a wrong answer that does not count) and can cleanse a debuff; nothing else changes the outcome.
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
SLOTS = ["head", "body", "hands", "feet", "main", "trinket"]
MAX_DODGE_PCT = 25
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


# ------------------------------------------------------------------ gear
# Per major: the six slots with a base name and a flavour line. Rarity adjectives wrap the base name.
GEAR = {
    "level_design": {
        "head": ("Surveyor's Hood", "Stitched from blockout tarps. Sees the flow of a room before it is built."),
        "body": ("Greybox Mantle", "Plain armor of unlit cubes. Nothing fancy ever reached the player; this did."),
        "hands": ("Metric Gauntlets", "Every finger knows the jump height. 180 units, always."),
        "feet": ("Pathfinder Treads", "They only walk where the NavMesh is green."),
        "main": ("Measuring Staff", "A staff marked in Unreal units. Struck once, it tells you what is too tall."),
        "trinket": ("Compass of Sightlines", "It points at the thing the player should see next."),
    },
    "programming": {
        "head": ("Debugger's Visor", "Shows every value at the moment it went wrong."),
        "body": ("Header Plate", "Declared once, included everywhere."),
        "hands": ("Pointer Gloves", "They never touch anything null."),
        "feet": ("Tick Boots", "Each step arrives exactly one frame later."),
        "main": ("Compiler Blade", "It cuts the code that does not build. Clean edge, no warnings."),
        "trinket": ("Breakpoint Charm", "Time stops when you hold it."),
    },
    "lookdev": {
        "head": ("Lumen Crown", "Bounced light gathers in it and stays."),
        "body": ("Master Material Cloak", "One cloak, a hundred instances."),
        "hands": ("Painter's Wraps", "Vertex colors soak into the cloth."),
        "feet": ("Landscape Walkers", "Grass grows back behind them."),
        "main": ("Palette Shield", "Every surface it touches finds its roughness."),
        "trinket": ("Reflection Sphere", "A small captured sky."),
    },
    "tech_art": {
        "head": ("Node Circlet", "Wires run where the hair should be."),
        "body": ("Shader Harness", "Written once, compiled a thousand times."),
        "hands": ("Niagara Gloves", "Sparks leave the fingertips on their own."),
        "feet": ("Profiler's Soles", "They know how many milliseconds a step costs."),
        "main": ("Node Wand", "Points at a graph and the graph explains itself."),
        "trinket": ("Scratch Pad Rune", "A module that exists nowhere else."),
    },
    "gameplay_design": {
        "head": ("Playtester's Cap", "It has seen the game break in every way."),
        "body": ("Tuning Vest", "Pockets full of variables, all exposed."),
        "hands": ("Feel Gloves", "They know when a jump is 80 milliseconds late."),
        "feet": ("Loop Runners", "Start, play, win, lose, again."),
        "main": ("Dice Mace", "Rolls a number nobody expected. Balanced, somehow."),
        "trinket": ("Data Table Token", "One row changes the whole game."),
    },
    "animation": {
        "head": ("Keyframe Helm", "Poses hold still under it."),
        "body": ("Rigger's Coat", "Every joint has a control."),
        "hands": ("Blend Gloves", "Two motions become one between the fingers."),
        "feet": ("Root Motion Boots", "The capsule follows the feet, not the other way."),
        "main": ("Rig Hook", "Pulls a bone into place from across the graph."),
        "trinket": ("Retarget Chain", "Fits any skeleton that has a spine."),
    },
    "cinematics": {
        "head": ("Director's Cowl", "Sees the frame before the camera does."),
        "body": ("Sequencer Robe", "Tracks stitched in rows down the front."),
        "hands": ("Focus Puller's Gloves", "Depth of field obeys them."),
        "feet": ("Dolly Shoes", "They move on rails only."),
        "main": ("The Slate", "Clapped once, the take begins."),
        "trinket": ("Render Lens", "A whole shot fits inside it."),
    },
}
GEAR["undecided"] = {
    "head": ("Wayfarer's Hood", "For those still choosing a road."),
    "body": ("Traveler's Mantle", "Warm enough for any major."),
    "hands": ("Curious Gloves", "They have tried a bit of everything."),
    "feet": ("Crossroad Boots", "Seven roads, one pair of boots."),
    "main": ("Walking Staff", "Plain wood. It will become something."),
    "trinket": ("Unset Compass", "It spins until you decide."),
}
RARITY_ADJ = {"common": "Worn", "uncommon": "Tempered", "rare": "Runed", "epic": "Sunforged", "legendary": "Mythic"}
# What each slot does, by rarity index 0..4
SLOT_EFFECT = {
    "head":    ("lore",    [1, 1, 2, 2, 3]),
    "body":    ("dodge",   [3, 5, 8, 12, 15]),      # percent chance to dodge one attack per fight
    "hands":   ("craft",   [1, 1, 2, 2, 3]),
    "feet":    ("dodge",   [2, 3, 4, 6, 8]),
    "main":    ("craft",   [1, 2, 3, 4, 5]),
    "trinket": ("cleanse", [0, 0, 1, 1, 1]),        # 1 = removes a debuff at the start of your next turn
}
CAPSTONE_GEAR = {   # unique set pieces: (slot, name, flavour)
    1: ("trinket", "Seal of the First Room", "You built a whole thing and someone else could walk it."),
    2: ("body", "Mantle of the Second Gate", "Two dungeons behind you. The armor remembers both."),
    3: ("head", "Crown of the Specialty", "Your title is carved on the inside, where only you can read it."),
    4: ("main", "Masterwork", "The weapon a Master carries. It is the work itself."),
}


def item_key(major: str, slot: str, rarity: str) -> str:
    return f"{major}:{slot}:{rarity}"


def describe_item(major: str, slot: str, rarity: str, name_override: str | None = None,
                  flavour_override: str | None = None) -> dict:
    base, flav = GEAR.get(major, GEAR["undecided"]).get(slot, ("Relic", ""))
    stat, table = SLOT_EFFECT[slot]
    bonus = table[RARITY_RANK[rarity]]
    return {"key": item_key(major, slot, rarity), "slot": slot, "rarity": rarity, "color": RARITY_COLOR[rarity],
            "name": name_override or f"{RARITY_ADJ[rarity]} {base}", "flavour": flavour_override or flav,
            "stat": stat, "bonus": bonus, "major": major}


def starter_kit(major: str) -> list[dict]:
    return [describe_item(major, s, "common") for s in SLOTS]


def roll_loot(q: Quest, member_major: str, rng: random.Random) -> dict | None:
    """Rolled when a quest completes. Capstones drop their set piece; others drop with 60% chance."""
    if q.capstone and q.rank in CAPSTONE_GEAR:
        slot, name, flav = CAPSTONE_GEAR[q.rank]
        rarity = RARITY[q.difficulty]
        d = describe_item(member_major, slot, rarity, name, flav)
        d["key"] = f"capstone:{q.rank}:{member_major}"
        d["set_piece"] = True
        return d
    if rng.random() > 0.6:
        return None
    rarity = RARITY[q.difficulty]
    if rng.random() < 0.1 and RARITY_RANK[rarity] < 4:
        rarity = list(RARITY_RANK)[RARITY_RANK[rarity] + 1]
    owners = [m for m in q.required_for if m != "all"]
    major = member_major if (member_major in GEAR and (not owners or member_major in owners or q.elective)) else (owners[0] if owners and owners[0] in GEAR else member_major)
    return describe_item(major, rng.choice(SLOTS), rarity)


def gear_totals(equipped: list[dict]) -> dict:
    t = {"lore": 0, "craft": 0, "dodge": 0, "cleanse": 0, "focus": 0}
    for g in equipped:
        t[g["stat"]] = t.get(g["stat"], 0) + g["bonus"]
    t["dodge"] = min(MAX_DODGE_PCT, t["dodge"])
    t["cleanse"] = min(1, t["cleanse"])
    return t


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


def boss_for(q: Quest) -> dict:
    subjects = [s.lower() for s in (q.raw.get("subjects") or [])]
    h = int(hashlib.sha1(q.id.encode()).hexdigest(), 16)
    name = NAMES[h % len(NAMES)]
    domain = next((DOMAIN[s] for s in subjects if s in DOMAIN), None) or (subjects[0].replace("-", " ").title() if subjects else "the Unknown")
    look = "drake" if q.capstone else next((k for k, keys in LOOK if (set(subjects) & keys) or q.track in keys), "knight")
    epithet = "Dragon" if q.capstone else EPITHET.get(q.difficulty, "Keeper")
    total = len(q.quiz)
    verb, line = MOVES[look]
    return {
        "name": f"{name}, {epithet} of {domain}", "short": name, "epithet": epithet, "domain": domain, "look": look,
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
        "dodge": [f"{n} {boss['verb']}, and you are already elsewhere.", "Your armor turns the blow. Dodged."],
        "steady": ["You brace. Half the blow lands.", "Resolve holds. It only grazes you."],
        "cleanse": ["Your trinket burns the curse away.", "The debuff lifts."],
        "win": [f"{n} falls. The room goes quiet.", f"{n} is beaten. The way forward is open."],
        "lose": [f"{n} stands over you. Regroup and return.", "You are knocked down. The boss room closes for now."],
    }
    return rng.choice(lines[kind])


# ------------------------------------------------------------------ debuffs
DEBUFFS = {
    "dazed": {"name": "Dazed", "text": "The choices shuffle next turn."},
    "slowed": {"name": "Slowed", "text": "A short wait before you can answer next turn."},
    "blinded": {"name": "Blinded", "text": "No hint next turn."},
}


def debuff_for(subject: str | None, rng: random.Random) -> str:
    return rng.choice(list(DEBUFFS))


def crit_chance(focus: int, gear_focus: int, seconds: float | None) -> int:
    speed = 0
    if seconds is not None and seconds <= SPEED_BONUS_SECONDS:
        speed = round(15 * (1 - seconds / SPEED_BONUS_SECONDS))
    return min(40, 5 + focus + gear_focus + speed)
