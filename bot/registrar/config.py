"""Environment + unlocks.yaml loading."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

BOT_ROOT = Path(__file__).resolve().parent.parent
BOT_NAME = "Quartermaster"
SIGNOFF = "— Quartermaster · Unrealcraft"


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int | None
    db_path: Path
    curriculum_dir: Path
    unlocks_path: Path
    log_level: str


def load_settings() -> Settings:
    load_dotenv(BOT_ROOT / ".env")

    def _p(name: str, default: str) -> Path:
        p = Path(os.getenv(name, default))
        return p if p.is_absolute() else (BOT_ROOT / p).resolve()

    gid = os.getenv("GUILD_ID", "").strip()
    return Settings(
        token=os.environ.get("DISCORD_TOKEN", ""),
        guild_id=int(gid) if gid else None,
        db_path=_p("DB_PATH", "data/registrar.db"),
        curriculum_dir=_p("CURRICULUM_DIR", "../curriculum"),
        unlocks_path=_p("UNLOCKS_PATH", "config/unlocks.yaml"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


class Unlocks:
    """Thin accessor over config/unlocks.yaml. A 0 means the ID isn't configured yet."""

    def __init__(self, path: Path):
        self.path = path
        self.data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def role(self, *keys) -> int:
        node = self.data.get("roles", {})
        for k in keys:
            node = (node or {}).get(k, 0)
        return int(node or 0)

    def channel(self, *keys) -> int:
        node = self.data.get("channels", {})
        for k in keys:
            node = (node or {}).get(k, 0)
        return int(node or 0)

    def categories_for_rank(self, rank: int) -> list[int]:
        names = (self.data.get("unlock_at_rank") or {}).get(rank, []) or []
        cats = self.data.get("categories", {}) or {}
        return [int(cats.get(n, 0) or 0) for n in names if cats.get(n)]

    def rank_role(self, rank: int, seal: str | None) -> int:
        if rank == 3:
            return self.role("specialist", seal) if seal else 0
        return self.role("rank", rank)

    def all_rank_roles(self) -> list[int]:
        ids = [int(v or 0) for v in (self.data.get("roles", {}).get("rank") or {}).values()]
        ids += [int(v or 0) for v in (self.data.get("roles", {}).get("specialist") or {}).values()]
        return [i for i in ids if i]
