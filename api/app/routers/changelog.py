from __future__ import annotations

from fastapi import APIRouter

from registrar import release  # noqa: E402

from ..config import settings

router = APIRouter(tags=["changelog"])


@router.get("/changelog")
async def changelog():
    es = release.entries(settings.changelog_path)
    return {"current": es[0]["version"] if es else None, "entries": es}
