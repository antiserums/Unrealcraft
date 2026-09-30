"""Unrealcraft API. Run from the api/ folder: uvicorn app.main:app --port 8000 --reload"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from registrar.curriculum import Catalog  # noqa: E402  (bot package, path set in config)

from . import auth
from .config import settings
from .db import DB
from .entitlements import Entitlements
from .routers import admin, admin_catalog, catalog, changelog, donate, letters, me, members, review, rpg, submit, tickets
from .rpg_db import RpgDB

log = logging.getLogger("unrealcraft.api")


def load_catalog() -> Catalog:
    cat = Catalog.load(settings.curriculum_dir)
    errs, warns = cat.validate()
    if errs:
        raise RuntimeError("curriculum errors: " + "; ".join(errs[:5]))
    log.info("Loaded %d quests (%d warnings)", len(cat.quests), len(warns))
    return cat


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app.state.catalog = load_catalog()
    app.state.db = DB(settings.db_path)
    await app.state.db.open()
    app.state.rpg = RpgDB(app.state.db)
    await app.state.rpg.migrate()
    app.state.ents = await Entitlements.load(app.state.rpg)     # built-ins plus the admin table; reloaded after admin edits
    log.info("Database: %s", settings.db_path)
    yield
    await app.state.db.close()


class SafeJSONResponse(JSONResponse):
    """Discord ids are 64-bit; JavaScript numbers are exact only to 2**53. Any integer beyond that goes out as a
    string so the browser never rounds a member id (which broke every /members/{id} link)."""

    LIMIT = 2 ** 53

    @classmethod
    def _fix(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int) and abs(v) > cls.LIMIT:
            return str(v)
        if isinstance(v, dict):
            return {k: cls._fix(x) for k, x in v.items()}
        if isinstance(v, (list, tuple, set)):
            return [cls._fix(x) for x in v]
        return v

    def render(self, content) -> bytes:
        return super().render(self._fix(content))


app = FastAPI(title="Unrealcraft API", version="0.1.0", lifespan=lifespan, default_response_class=SafeJSONResponse)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(me.router)
app.include_router(members.router)
app.include_router(changelog.router)
app.include_router(rpg.router)
app.include_router(submit.router)
app.include_router(review.router)
app.include_router(admin.router)
app.include_router(admin_catalog.router)
app.include_router(tickets.router)
app.include_router(donate.router)
app.include_router(letters.router)


@app.get("/health")
async def health(request: Request):
    return {"ok": True, "quests": len(request.app.state.catalog.quests), "version": app.version}
