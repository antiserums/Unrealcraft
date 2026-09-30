"""Onboarding profile: Discord Questions → hidden roles → how the Quartermaster shapes the path.

One source of truth. setup_server builds the Discord questions and roles from QUESTIONS.
The bot reads a member's roles back into a profile dict: {"major": "...", "exp": "...", "curious": [...], ...}.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Answer:
    value: str
    title: str
    description: str
    emoji: str


@dataclass
class Question:
    key: str                  # profile key
    title: str
    role_prefix: str          # role name = f"{role_prefix} · {answer.title_short}"
    answers: list[Answer]
    required: bool = False
    single: bool = True
    pre_join: bool = True     # Discord allows max 4 pre-join questions; the rest live on Channels & Roles
    role_names: dict[str, str] = field(default_factory=dict)   # value -> role name override


MAJOR_ROLE_NAMES = {
    "level_design": "Major · Level Design", "lookdev": "Major · Environment Art", "tech_art": "Major · Tech Art",
    "gameplay_design": "Major · Gameplay Design", "animation": "Major · Animation",
    "programming": "Major · Programming", "cinematics": "Major · Cinematics", "undecided": "Major · Undecided",
}

QUESTIONS: list[Question] = [
    Question("major", "What do you want to learn in Unreal? (pick all that apply)", "Major", required=True,
             single=False, role_names=MAJOR_ROLE_NAMES,
             answers=[
                 Answer("level_design", "Building levels & spaces", "Layouts, flow, encounters (Level Design)", "🧱"),
                 Answer("lookdev", "Making worlds look great", "Materials, lighting, mood (Environment Art)", "🎨"),
                 Answer("tech_art", "Shaders, VFX & tools", "The tech behind the art (Tech Art)", "🧪"),
                 Answer("gameplay_design", "Making games fun", "Rules, loops, game feel (Gameplay Design)", "🎮"),
                 Answer("animation", "Bringing characters to life", "AnimBPs, rigs, motion (Animation)", "🏃"),
                 Answer("programming", "Coding games", "Blueprint → C++ systems (Programming)", "💻"),
                 Answer("cinematics", "Cameras & storytelling", "Sequencer, shots, renders (Cinematics)", "🎬"),
                 Answer("undecided", "Not sure yet", "Try a bit of everything; pick by Rank 2", "🧭"),
             ]),
    Question("exp", "How much Unreal have you used?", "Exp", required=True, answers=[
        Answer("new", "Never opened it", "Start from zero, we've got you", "🌱"),
        Answer("tutorials", "Followed some tutorials", "Know the editor a little", "📺"),
        Answer("built", "Built my own small project", "Comfortable in the editor", "🔨"),
        Answer("shipped", "Shipped something / use it at work", "You could teach the basics", "🚀"),
    ]),
    Question("code", "Do you code?", "Code", answers=[
        Answer("none", "No, and I'd rather not", "We'll keep code optional for you", "🙅"),
        Answer("blueprint", "Blueprint only", "Visual scripting is my thing", "🔷"),
        Answer("some", "Some C++ or another language", "I can read code", "📖"),
        Answer("cpp", "Comfortable with C++", "Bring on the IDE", "⚙️"),
    ]),
    Question("curious", "What else are you curious about?", "Curious", single=False, answers=[
        Answer("lighting", "Lighting", "Lumen, mood, readability", "💡"),
        Answer("materials", "Materials", "Shaders and surfaces", "🧴"),
        Answer("blueprint", "Blueprint", "Making things interactive", "🔷"),
        Answer("animation", "Animation", "Characters in motion", "🏃"),
        Answer("cpp", "C++", "Under the hood", "⚙️"),
        Answer("vfx", "VFX / Niagara", "Particles and effects", "✨"),
        Answer("world", "Landscapes & worlds", "Terrain, foliage, PCG", "🏔️"),
        Answer("cinematics", "Cinematics", "Sequencer and cameras", "🎬"),
    ]),
    Question("goal", "What are your goals? (pick all that apply)", "Goal", pre_join=False, single=False, answers=[
        Answer("career", "A job in games", "Portfolio-first", "💼"),
        Answer("indie", "Make my own game", "Ship something playable", "🕹️"),
        Answer("student", "School or a course", "Keep up and get ahead", "🎓"),
        Answer("hobby", "For fun", "No pressure", "🎈"),
    ]),
    Question("pace", "How much time can you put in per week?", "Pace", pre_join=False, answers=[
        Answer("light", "Under 2 hours", "A quest now and then", "🐢"),
        Answer("steady", "2–5 hours", "A few quests a week", "🚶"),
        Answer("focused", "5–10 hours", "Serious progress", "🏃"),
        Answer("intense", "10+ hours", "All in", "🔥"),
    ]),
]

PACE_HOURS = {"light": 1.5, "steady": 3.5, "focused": 7.5, "intense": 12}

# curiosity → quest subjects/tracks it matches
CURIOUS_MATCH = {
    "lighting": {"lighting", "lumen", "exposure", "post-process", "lookdev"},
    "materials": {"materials", "material", "shaders", "decals"},
    "blueprint": {"blueprint", "interaction", "bp"},
    "animation": {"animation", "anim", "montage", "retargeting"},
    "cpp": {"cpp", "c++", "code", "programming"},
    "vfx": {"niagara", "vfx", "fx"},
    "world": {"landscape", "foliage", "pcg", "water", "world"},
    "cinematics": {"sequencer", "cinematics", "camera", "cameras"},
}

# curiosity → which major it points to (for Undecided suggestions)
CURIOUS_TO_MAJOR = {"lighting": "lookdev", "materials": "lookdev", "blueprint": "gameplay_design",
                    "animation": "animation", "cpp": "programming", "vfx": "tech_art", "world": "level_design",
                    "cinematics": "cinematics"}


SHORT = {"cpp": "C++", "vfx": "VFX", "world": "Worlds", "new": "New", "built": "Built a project",
         "shipped": "Shipped", "none": "No code", "some": "Some code"}


def role_name(q: Question, a: Answer) -> str:
    """Short, hidden role names, e.g. 'Exp · Built a project', 'Curious · VFX', 'Code · C++'."""
    return q.role_names.get(a.value) or f"{q.role_prefix} · {SHORT.get(a.value, a.value.replace('_', ' ').title())}"


def all_role_names() -> list[tuple[str, str, str]]:
    """(role name, question key, answer value) for every profile answer except majors (created elsewhere)."""
    return [(role_name(q, a), q.key, a.value) for q in QUESTIONS if q.key != "major" for a in q.answers]


def profile_from_roles(role_names: set[str]) -> dict:
    prof: dict = {"curious": []}
    for q in QUESTIONS:
        for a in q.answers:
            if role_name(q, a) in role_names:
                if q.single:
                    prof[q.key] = a.value
                else:
                    prof.setdefault(q.key, []).append(a.value)
    # multi-answer questions are stored under plural keys
    prof["majors"] = prof.pop("major", [])
    prof["goals"] = prof.pop("goal", [])
    return prof


def can_test_out(prof: dict) -> bool:
    return prof.get("exp") in ("built", "shipped")


def suggested_major(prof: dict) -> str | None:
    votes: dict[str, int] = {}
    for c in prof.get("curious") or []:
        m = CURIOUS_TO_MAJOR.get(c)
        if m:
            votes[m] = votes.get(m, 0) + 1
    return max(votes, key=votes.get) if votes else None


def quest_matches_curious(q, prof: dict) -> int:
    words = {s.lower() for s in (q.raw.get("subjects") or [])} | {q.track}
    return sum(1 for c in prof.get("curious") or [] if words & CURIOUS_MATCH.get(c, set()))


GOAL_SUBJECTS = {"career": {"meta", "critique", "review", "showcase", "screenshots", "video"},
                 "indie": {"blueprint", "interaction", "gameplay", "loop", "hud"}}


def elective_score(q, prof: dict, major: str | None = None) -> int:
    """Higher = suggest earlier. Curiosity and other picked majors count double, goal fit once."""
    words = {s.lower() for s in (q.raw.get("subjects") or [])}
    goal_words = set().union(*[GOAL_SUBJECTS.get(g, set()) for g in prof.get("goals") or []]) if prof.get("goals") else set()
    interests = [m for m in prof.get("majors") or [] if m != major]
    interest_hit = any(q.required and q.in_specialization(m) for m in interests)
    return 2 * quest_matches_curious(q, prof) + 2 * interest_hit + (1 if words & goal_words else 0)
