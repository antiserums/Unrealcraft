"""Unrealcraft API. Run from the api/ folder: uvicorn app.main:app --port 8000 --reload"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from registrar.curriculum import Catalog  # noqa: E402  (bot package, path set in config)

from . import auth
from .config import settings
from .db import DB
from .routers import catalog, changelog, me, members

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
    log.info("Database: %s", settings.db_path)
    yield
    await app.state.db.close()


app = FastAPI(title="Unrealcraft API", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(me.router)
app.include_router(members.router)
app.include_router(changelog.router)


@app.get("/health")
async def health(request: Request):
    return {"ok": True, "quests": len(request.app.state.catalog.quests), "version": app.version}
