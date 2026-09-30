"""Environment for the Unrealcraft API. Secrets come from api/.env (git-ignored)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = API_ROOT.parent

# The rules engine (quest picker, rank gates, tier counts) lives in the bot package and has no Discord imports.
# Until it moves to a shared package, import it from there.
sys.path.insert(0, str(REPO_ROOT / "bot"))


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    redirect_uri: str
    guild_id: int
    session_secret: str
    web_origin: str
    db_path: Path
    curriculum_dir: Path
    changelog_path: Path
    uploads_dir: Path
    bot_service_token: str
    log_level: str
    unlocks_path: Path            # the bot's config/unlocks.yaml: role ids for mentor and rank checks
    admin_ids: frozenset[int]     # Discord ids that can always review (ADMIN_IDS, comma-separated)


def _p(name: str, default: str) -> Path:
    p = Path(os.getenv(name, default))
    return p if p.is_absolute() else (API_ROOT / p).resolve()


def load_settings() -> Settings:
    load_dotenv(API_ROOT / ".env")
    gid = os.getenv("DISCORD_GUILD_ID", "").strip()
    return Settings(
        client_id=os.getenv("DISCORD_CLIENT_ID", ""),
        client_secret=os.getenv("DISCORD_CLIENT_SECRET", ""),
        redirect_uri=os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/api/auth/discord/callback"),
        guild_id=int(gid) if gid else 0,
        session_secret=os.getenv("SESSION_SECRET", ""),
        web_origin=os.getenv("WEB_ORIGIN", "http://localhost:3000"),
        db_path=_p("DB_PATH", "../bot/data/registrar.db"),
        curriculum_dir=_p("CURRICULUM_DIR", "../curriculum"),
        changelog_path=_p("CHANGELOG_PATH", "../CHANGELOG.md"),
        uploads_dir=_p("UPLOADS_DIR", "data/uploads"),
        bot_service_token=os.getenv("BOT_SERVICE_TOKEN", ""),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        unlocks_path=_p("UNLOCKS_PATH", "../bot/config/unlocks.yaml"),
        admin_ids=frozenset(int(x) for x in os.getenv("ADMIN_IDS", "").replace(";", ",").split(",") if x.strip().isdigit()),
    )


settings = load_settings()
