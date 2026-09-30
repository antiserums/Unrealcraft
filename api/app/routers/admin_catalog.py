"""Admin panel, part two: the curriculum and the entitlement catalog.

Quests: the YAML under curriculum/ stays the source of truth, so adding or editing a quest here rewrites that file
(`yaml.safe_dump`; comments in that one file are lost) and reloads the API's catalog. The bot keeps its own copy:
run `/admin reload-curriculum` on Discord after a change.
Entitlements: rows in the `entitlements` table override or extend the built-ins (see entitlements.py); direct
grants hand one member one entitlement.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from registrar.curriculum import META_FILES, TIERS, VERIFY_TYPES, Catalog, Quest  # noqa: E402

from .. import entitlements as ent
from ..config import settings
from .admin import admin_only

router = APIRouter(prefix="/admin", tags=["admin"])

QUEST_KEYS = ["id", "rank", "difficulty", "specializations", "subjects", "required_spine", "first_steps", "required", "taster", "taster_for",
              "capstone", "title", "time_min", "needs_others", "official_url", "backup_url",
              "extra_urls", "community_urls", "checklist", "done_when", "xp", "verify_type", "action_key", "next_hint", "quiz", "flavors"]
FILE_RE = re.compile(r"^[a-z0-9_]+\.yaml$")
ID_RE = re.compile(r"^[A-Z]{1,4}\d{1,4}[A-Z]?$")
DEFAULT_FILE = "admin.yaml"


# ------------------------------------------------------------------ curriculum
def _clean(raw: dict) -> dict:
    """The quest as it goes to disk: known keys first, in the usual order, never the loader's `_file`."""
    out = {k: raw[k] for k in QUEST_KEYS if k in raw and raw[k] is not None}
    out.update({k: v for k, v in raw.items() if k not in out and not k.startswith("_") and v is not None})
    return out


def _dump(doc: dict) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)


def _load_file(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    doc = doc or {}
    doc.setdefault("quests", [])
    doc["quests"] = doc["quests"] or []
    return doc


def _summary(q: Quest) -> dict:
    return {"id": q.id, "title": q.raw.get("title"), "rank": q.rank, "difficulty": q.difficulty, "specializations": q.specializations,
            "xp": q.xp, "verify_type": q.raw.get("verify_type"), "file": q.raw.get("_file"), "quiz_len": len(q.quiz),
            "kind": "capstone" if q.capstone else ("required" if q.required else "elective"), "taster_for": q.taster_for}


@router.get("/curriculum")
async def curriculum(request: Request, _=Depends(admin_only)):
    cat: Catalog = request.app.state.catalog
    files = sorted(p.name for p in Path(settings.curriculum_dir).glob("*.yaml") if p.name not in META_FILES)
    return {"dir": str(settings.curriculum_dir), "files": files, "default_file": DEFAULT_FILE,
            "specializations": [{"key": k, "title": cat.title_of(k)} for k in cat.specializations if k != "undecided"],
            "verify_types": sorted(VERIFY_TYPES), "tiers": {k: {"name": v["name"], "quiz_len": v["quiz_len"]} for k, v in TIERS.items()},
            "ranks": [{"n": n, "title": r["title"]} for n, r in sorted(cat.ranks.items())],
            "quests": [_summary(q) for q in cat.sorted(cat.quests.values())]}


@router.get("/curriculum/quests/{qid}")
async def curriculum_quest(qid: str, request: Request, _=Depends(admin_only)):
    q = request.app.state.catalog.quests.get(qid)
    if not q:
        raise HTTPException(404, "No such quest.")
    raw = _clean(q.raw)
    return {"quest": raw, "file": q.raw.get("_file"), "yaml": _dump(raw), "summary": _summary(q)}


class QuestSave(BaseModel):
    quest: dict | None = None      # the quest as a dict …
    yaml: str | None = None        # … or as YAML text (one quest, no `quests:` wrapper)
    file: str | None = None        # which curriculum file; a new quest defaults to admin.yaml
    replace: str | None = None     # when editing: the id it had before (it may be renamed)


def _parse(body: QuestSave) -> dict:
    raw = body.quest
    if raw is None and body.yaml is not None:
        try:
            raw = yaml.safe_load(body.yaml)
        except yaml.YAMLError as e:
            raise HTTPException(400, f"YAML does not parse: {str(e).splitlines()[0]}")
    if not isinstance(raw, dict):
        raise HTTPException(400, "Send the quest as an object or as YAML text.")
    if isinstance(raw.get("quests"), list) and len(raw["quests"]) == 1:
        raw = raw["quests"][0]
    raw = {k: v for k, v in raw.items() if not str(k).startswith("_")}
    qid = str(raw.get("id", "")).strip().upper()
    if not ID_RE.match(qid):
        raise HTTPException(400, "Quest id: letters then a number, like LDQ41 or SQ7.")
    raw["id"] = qid
    for k in ("rank", "xp", "time_min"):
        if raw.get(k) not in (None, ""):
            try:
                raw[k] = int(raw[k])
            except (TypeError, ValueError):
                raise HTTPException(400, f"{k} must be a whole number.")
    for k in ("subjects", "specializations", "taster_for", "extra_urls", "community_urls", "checklist"):
        v = raw.get(k)
        if isinstance(v, str):
            raw[k] = [s.strip() for s in re.split(r"[\n,]" if k != "checklist" else r"\n", v) if s.strip()]
    for k in ("required_spine", "first_steps", "required", "taster", "capstone", "needs_others"):
        if k in raw:
            raw[k] = bool(raw[k])
    for k in ("elective", "track", "required_for_majors", "taster_for_majors", "adjacent_for"):
        raw.pop(k, None)                                  # the older shape; the loader no longer reads these
    if isinstance(raw.get("flavors"), str):                 # the form sends flavors as YAML text
        try:
            raw["flavors"] = yaml.safe_load(raw["flavors"]) or {}
        except yaml.YAMLError as e:
            raise HTTPException(400, f"Flavors YAML does not parse: {str(e).splitlines()[0]}")
        if not isinstance(raw["flavors"], dict):
            raise HTTPException(400, "Flavors must be a map of major -> {why, do}.")
    for k in ("backup_url", "action_key", "next_hint"):
        if raw.get(k) == "":
            raw[k] = None
    if isinstance(raw.get("quiz"), list):
        for item in raw["quiz"]:
            if isinstance(item, dict) and "answer_index" in item:
                try:
                    item["answer_index"] = int(item["answer_index"])
                except (TypeError, ValueError):
                    raise HTTPException(400, "Each quiz answer_index must be a number.")
    return raw


def _validate(request: Request, raw: dict, file: str, replace: str | None) -> list[str]:
    """Errors this quest adds to the catalog (the catalog's existing warnings are not the admin's problem)."""
    cat: Catalog = request.app.state.catalog
    base_errs, _ = cat.validate()
    quests = {k: Quest(dict(v.raw)) for k, v in cat.quests.items()}
    if replace and replace != raw["id"]:
        quests.pop(replace, None)
    elif not replace and raw["id"] in quests:
        raise HTTPException(409, f"{raw['id']} already exists (in {quests[raw['id']].raw.get('_file')}). Open it to edit it.")
    quests[raw["id"]] = Quest({**raw, "_file": file})
    errs, warns = Catalog(quests, cat.meta).validate()
    new_errs = [e for e in errs if e not in base_errs]
    if new_errs:
        raise HTTPException(400, "Fix these first: " + " · ".join(new_errs[:8]))
    return [w for w in warns if w.startswith(f"{raw['id']} (")]


def _write(raw: dict, file: str, old_id: str | None, old_file: str | None) -> None:
    d = Path(settings.curriculum_dir)
    if old_id and old_file and old_file != file:            # moved to another file: drop it from the old one
        p = d / old_file
        doc = _load_file(p)
        doc["quests"] = [q for q in doc["quests"] if q.get("id") != old_id]
        p.write_text(_dump(doc), encoding="utf-8")
    p = d / file
    doc = _load_file(p)
    clean = _clean(raw)
    for i, q in enumerate(doc["quests"]):
        if q.get("id") in (old_id, raw["id"]):
            doc["quests"][i] = clean
            break
    else:
        doc["quests"].append(clean)
    p.write_text(_dump(doc), encoding="utf-8")


def _reload(request: Request) -> Catalog:
    from ..main import load_catalog
    request.app.state.catalog = load_catalog()
    return request.app.state.catalog


@router.post("/curriculum/quests")
async def save_quest(body: QuestSave, request: Request, admin=Depends(admin_only)):
    cat: Catalog = request.app.state.catalog
    raw = _parse(body)
    old = cat.quests.get(body.replace) if body.replace else None
    if body.replace and not old:
        raise HTTPException(404, "The quest you are editing no longer exists.")
    file = (body.file or (old.raw.get("_file") if old else None) or DEFAULT_FILE).strip()
    if not FILE_RE.match(file) or file in META_FILES:
        raise HTTPException(400, "File name: lower-case letters, digits, underscores, ending in .yaml.")
    warns = _validate(request, raw, file, body.replace)
    _write(raw, file, old.id if old else None, old.raw.get("_file") if old else None)
    _reload(request)
    await request.app.state.rpg.admin_log(admin["id"], "save_quest", None, {"quest": raw["id"], "file": file, "new": not old})
    return {"ok": True, "id": raw["id"], "file": file, "warnings": warns,
            "message": f"{raw['id']} {'updated' if old else 'added'} in {file}. Run /admin reload-curriculum on Discord so the bot sees it."}


@router.delete("/curriculum/quests/{qid}")
async def delete_quest(qid: str, request: Request, admin=Depends(admin_only)):
    cat: Catalog = request.app.state.catalog
    q = cat.quests.get(qid)
    if not q:
        raise HTTPException(404, "No such quest.")
    quests = {k: v for k, v in cat.quests.items() if k != qid}
    base_errs, _ = cat.validate()
    errs, _ = Catalog(quests, cat.meta).validate()
    new_errs = [e for e in errs if e not in base_errs]
    if new_errs:
        raise HTTPException(400, "Something still points at this quest: " + " · ".join(new_errs[:5]))
    p = Path(settings.curriculum_dir) / q.raw["_file"]
    doc = _load_file(p)
    doc["quests"] = [x for x in doc["quests"] if x.get("id") != qid]
    if doc["quests"] or [k for k in doc if k != "quests"]:
        p.write_text(_dump(doc), encoding="utf-8")
    else:
        p.unlink()                                   # an admin file with nothing left in it goes away
    _reload(request)
    await request.app.state.rpg.admin_log(admin["id"], "delete_quest", None, {"quest": qid, "file": q.raw["_file"]})
    return {"ok": True, "message": f"{qid} removed from {q.raw['_file']}. Members who finished it keep their progress row."}


@router.post("/curriculum/reload")
async def reload_curriculum(request: Request, admin=Depends(admin_only)):
    try:
        cat = _reload(request)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "message": f"Reloaded {len(cat.quests)} quests."}


# ------------------------------------------------------------------ entitlements
async def _reload_ents(request: Request):
    request.app.state.ents = await ent.Entitlements.load(request.app.state.rpg)


@router.get("/entitlements")
async def list_entitlements(request: Request, _=Depends(admin_only)):
    cat: Catalog = request.app.state.catalog
    rows = [{**r, "hint": ent.hint_for(r["unlock"], cat.ranks)} for r in request.app.state.ents.rows]
    return {"rows": rows, "kinds": ent.KINDS, "kind_label": ent.KIND_LABEL, "unlock_types": ent.UNLOCK_TYPES,
            "counters": ent.COUNTERS, "counter_label": ent.COUNTER_LABEL, "ranks": [{"n": n, "title": r["title"]} for n, r in sorted(cat.ranks.items())],
            "achievement_keys": [r["id"] for r in request.app.state.ents.of("achievement")], "tiers": list(TIERS)}


class EntitlementBody(BaseModel):
    name: str
    desc: str = ""
    data: dict = {}
    unlock: dict = {"type": "starter"}
    sort: int = 100
    enabled: bool = True


@router.put("/entitlements/{kind}/{eid}")
async def save_entitlement(kind: str, eid: str, body: EntitlementBody, request: Request, admin=Depends(admin_only)):
    eid = eid.strip().lower()
    data = {k: v for k, v in body.data.items() if v not in (None, "")}
    unlock = {k: v for k, v in body.unlock.items() if v not in (None, "")}
    if kind == "achievement":
        unlock = {"type": "starter"}
        if "need" in data:
            try:
                data["need"] = int(data["need"])
            except (TypeError, ValueError):
                pass
        if "badge" in data:
            try:
                data["badge"] = int(data["badge"])
            except (TypeError, ValueError):
                data.pop("badge")
    if unlock.get("type") == "rank" and "n" in unlock:
        try:
            unlock["n"] = int(unlock["n"])
        except (TypeError, ValueError):
            pass
    errs = ent.validate_row(kind, eid, body.name, unlock, data)
    if errs:
        raise HTTPException(400, " ".join(errs))
    if unlock.get("type") == "achievement" and not request.app.state.ents.get("achievement", unlock["key"]):
        raise HTTPException(400, f"No achievement with key {unlock['key']}.")
    await request.app.state.rpg.entitlement_save(kind, eid, body.name.strip()[:60], body.desc.strip()[:200], data, unlock, body.sort, body.enabled)
    await _reload_ents(request)
    await request.app.state.rpg.admin_log(admin["id"], "save_entitlement", None, {"kind": kind, "id": eid, "enabled": body.enabled})
    return {"ok": True, "message": f"{ent.KIND_LABEL.get(kind, kind)} {eid} saved.", "row": request.app.state.ents.get(kind, eid)}


@router.delete("/entitlements/{kind}/{eid}")
async def delete_entitlement(kind: str, eid: str, request: Request, admin=Depends(admin_only)):
    row = request.app.state.ents.get(kind, eid)
    if not row:
        raise HTTPException(404, "No such entitlement.")
    n = await request.app.state.rpg.entitlement_delete(kind, eid)
    await _reload_ents(request)
    await request.app.state.rpg.admin_log(admin["id"], "delete_entitlement", None, {"kind": kind, "id": eid, "builtin": row["builtin"]})
    msg = f"{eid} reset to its built-in version." if row["builtin"] else (f"{eid} removed." if n else "Nothing to remove.")
    return {"ok": True, "message": msg}


class GrantBody(BaseModel):
    kind: str
    id: str
    remove: bool = False


@router.post("/members/{uid}/entitlements")
async def grant_entitlement(uid: int, body: GrantBody, request: Request, admin=Depends(admin_only)):
    rdb = request.app.state.rpg
    if not await request.app.state.db.user(uid):
        raise HTTPException(404, "No such member.")
    row = request.app.state.ents.get(body.kind, body.id)
    if not row:
        raise HTTPException(404, "No such entitlement.")
    if body.remove:
        await rdb.revoke(uid, body.kind, body.id)
        if body.kind == "outfit":
            await rdb.conn.execute("DELETE FROM outfits WHERE member_id=? AND set_id=? AND source='granted'", (uid, body.id))
            await rdb.conn.commit()
    else:
        await rdb.grant(uid, body.kind, body.id, admin["id"])
    await rdb.admin_log(admin["id"], "grant_entitlement", uid, {"kind": body.kind, "id": body.id, "remove": body.remove})
    return {"ok": True, "message": f"{ent.KIND_LABEL.get(body.kind, body.kind)} {row['name']} {'revoked' if body.remove else 'granted'}."}
