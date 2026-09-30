"""Support tickets: a member writes to staff from /support, staff answer from the admin panel.

Members: list and open their own tickets, reply, close. Staff (admins, developers and mentors): every ticket,
reply (which marks it answered), change status. Nothing here touches XP, ranks or entitlements."""
from __future__ import annotations

import json
import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from ..config import settings
from ..session import current_member
from ..staff import can_review, is_admin, nameplate_for, role_of_id
from .me import nameplate, rank_color
from .letters import STAFF, send_letter
from .submit import IMAGE_TYPES, MAX_BYTES, MAX_FILES

router = APIRouter(tags=["tickets"])
CATEGORIES = ["account", "quest", "review", "bug", "donation", "other"]
STATUSES = ["open", "answered", "closed"]


def _staff(member: dict) -> bool:
    return is_admin(member) or can_review(member)


def staff_only(member=Depends(current_member)) -> dict:
    if not _staff(member):
        raise HTTPException(403, "Staff only.")
    return member


class Status(BaseModel):
    status: str


async def _store(uid: int, files: list[UploadFile]) -> list[str]:
    """Screenshots on a ticket: the same folder and limits as the chest (data/uploads/<uid>/, members only)."""
    files = [f for f in files if f and f.filename]
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"At most {MAX_FILES} images.")
    for f in files:
        if f.content_type not in IMAGE_TYPES:
            raise HTTPException(400, f"{f.filename}: only PNG, JPG, WEBP or GIF.")
    folder = settings.uploads_dir / str(uid)
    folder.mkdir(parents=True, exist_ok=True)
    urls = []
    for f in files:
        data = await f.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(400, f"{f.filename} is larger than 8 MB.")
        name = secrets.token_urlsafe(12) + IMAGE_TYPES[f.content_type]
        (folder / name).write_bytes(data)
        urls.append(f"{settings.web_origin}/api/uploads/{uid}/{name}")
    return urls


def _text(body: str, lo: int, hi: int, what: str) -> str:
    body = body.strip()
    if not lo <= len(body) <= hi:
        raise HTTPException(400, f"{what} must be {lo} to {hi} characters.")
    return body


async def _author(request: Request, uid: int, cache: dict) -> dict:
    """Name, avatar and nameplate (staff role or rank title, with its colour) of whoever wrote a message."""
    if uid in cache:
        return cache[uid]
    rdb, db, cat = request.app.state.rpg, request.app.state.db, request.app.state.catalog
    u, _, _ = await db.user_state(uid)
    role = role_of_id(uid)
    plate = nameplate_for(role) or (nameplate(cat, u.get("rank", 0), u.get("major") or "undecided"), rank_color(cat, max(u.get("rank", 0), 0)))
    cache[uid] = {"id": uid, "name": await rdb.kv_get(uid, "web.name") or f"Member {str(uid)[-4:]}", "avatar": await rdb.kv_get(uid, "web.avatar"),
                  "rank_title": plate[0], "rank_color": plate[1], "staff": role}
    return cache[uid]


async def _public(t: dict, request: Request | None = None) -> dict:
    out = {k: t[k] for k in ("id", "category", "subject", "status", "created_at", "updated_at", "member_id")}
    out["name"] = t.get("name")
    out["avatar"] = t.get("avatar")
    if isinstance(t.get("messages"), list):
        cache: dict = {}
        out["messages"] = [{"id": m["id"], "staff": bool(m["staff"]), "body": m["body"], "created_at": m["created_at"],
                            "attachments": json.loads(m.get("attachments") or "[]"),
                            "author": await _author(request, m["author_id"], cache) if request else None} for m in t["messages"]]
        out["author"] = await _author(request, t["member_id"], cache) if request else None
    else:
        out["messages"] = t.get("messages", 0)
        out["last"] = t.get("last")
    return out


# ---------------------------------------------------------------- members
@router.get("/me/tickets")
async def my_tickets(request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    return {"tickets": [await _public(t) for t in await rdb.tickets(uid=member["id"])], "categories": CATEGORIES}


@router.post("/me/tickets")
async def open_ticket(request: Request, category: str = Form("other"), subject: str = Form(""), body: str = Form(""),
                      files: list[UploadFile] = File(default=[]), member=Depends(current_member)):
    rdb = request.app.state.rpg
    if category not in CATEGORIES:
        raise HTTPException(400, "Pick a category from the list.")
    subject = _text(subject, 3, 120, "The subject")
    body = _text(body, 10, 4000, "The message")
    if len(await rdb.tickets(uid=member["id"], status="open")) >= 5:
        raise HTTPException(429, "You have five open tickets already. Wait for an answer, or close one.")
    urls = await _store(member["id"], files)
    tid = await rdb.create_ticket(member["id"], category, subject, body, urls)
    await rdb.emit("ticket_opened", member["id"], {"ticket": tid, "category": category})
    await send_letter(request, STAFF, "ticket", f"New ticket #{tid}: {subject}", body[:300], f"/admin/tickets/{tid}")
    return await _public(await rdb.ticket(tid), request)


async def _mine(request: Request, tid: int, member: dict) -> dict:
    t = await request.app.state.rpg.ticket(tid)
    if not t or t["member_id"] != member["id"]:
        raise HTTPException(404, "No such ticket.")
    return t


@router.get("/me/tickets/{tid}")
async def my_ticket(tid: int, request: Request, member=Depends(current_member)):
    return await _public(await _mine(request, tid, member), request)


@router.post("/me/tickets/{tid}/reply")
async def my_reply(tid: int, request: Request, body: str = Form(""), files: list[UploadFile] = File(default=[]), member=Depends(current_member)):
    t = await _mine(request, tid, member)
    if t["status"] == "closed":
        raise HTTPException(409, "This ticket is closed. Open a new one.")
    body = _text(body, 1, 4000, "The message")
    rdb = request.app.state.rpg
    await rdb.ticket_reply(tid, member["id"], False, body, "open", await _store(member["id"], files))
    await send_letter(request, STAFF, "ticket", f"Reply on ticket #{tid}: {t['subject']}", body[:300], f"/admin/tickets/{tid}")
    return await _public(await rdb.ticket(tid), request)


@router.post("/me/tickets/{tid}/close")
async def my_close(tid: int, request: Request, member=Depends(current_member)):
    await _mine(request, tid, member)
    await request.app.state.rpg.ticket_status(tid, "closed")
    return {"ok": True}


# ---------------------------------------------------------------- staff
@router.get("/admin/tickets")
async def all_tickets(request: Request, status: str | None = None, _=Depends(staff_only)):
    rdb = request.app.state.rpg
    if status and status not in STATUSES:
        raise HTTPException(400, "Unknown status.")
    return {"tickets": [await _public(t) for t in await rdb.tickets(status=status)], "open": await rdb.open_ticket_count()}


@router.get("/admin/tickets/{tid}")
async def staff_ticket(tid: int, request: Request, _=Depends(staff_only)):
    t = await request.app.state.rpg.ticket(tid)
    if not t:
        raise HTTPException(404, "No such ticket.")
    return await _public(t, request)


@router.post("/admin/tickets/{tid}/reply")
async def staff_reply(tid: int, request: Request, body: str = Form(""), files: list[UploadFile] = File(default=[]), member=Depends(staff_only)):
    rdb = request.app.state.rpg
    t = await rdb.ticket(tid)
    if not t:
        raise HTTPException(404, "No such ticket.")
    body = _text(body, 1, 4000, "The message")
    await rdb.ticket_reply(tid, member["id"], True, body, "answered", await _store(member["id"], files))
    await send_letter(request, t["member_id"], "ticket", f"Your ticket #{tid} was answered", body[:300], f"/inbox?ticket={tid}")
    await rdb.admin_log(member["id"], "ticket_reply", t["member_id"], {"ticket": tid})
    return await _public(await rdb.ticket(tid), request)


@router.post("/admin/tickets/{tid}/status")
async def staff_status(tid: int, body: Status, request: Request, member=Depends(staff_only)):
    if body.status not in STATUSES:
        raise HTTPException(400, "Unknown status.")
    rdb = request.app.state.rpg
    t = await rdb.ticket(tid)
    if not t:
        raise HTTPException(404, "No such ticket.")
    await rdb.ticket_status(tid, body.status)
    await rdb.admin_log(member["id"], "ticket_status", t["member_id"], {"ticket": tid, "status": body.status})
    return {"ok": True}
