"""Support tickets: a member writes to staff from /support, staff answer from the admin panel.

Members: list and open their own tickets, reply, close. Staff (admins, developers and mentors): every ticket,
reply (which marks it answered), change status. Nothing here touches XP, ranks or entitlements."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..session import current_member
from ..staff import can_review, is_admin

router = APIRouter(tags=["tickets"])
CATEGORIES = ["account", "quest", "review", "bug", "donation", "other"]
STATUSES = ["open", "answered", "closed"]


def _staff(member: dict) -> bool:
    return is_admin(member) or can_review(member)


def staff_only(member=Depends(current_member)) -> dict:
    if not _staff(member):
        raise HTTPException(403, "Staff only.")
    return member


class NewTicket(BaseModel):
    category: str = "other"
    subject: str = Field(min_length=3, max_length=120)
    body: str = Field(min_length=10, max_length=4000)


class Reply(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class Status(BaseModel):
    status: str


def _public(t: dict) -> dict:
    out = {k: t[k] for k in ("id", "category", "subject", "status", "created_at", "updated_at", "member_id")}
    out["name"] = t.get("name")
    out["avatar"] = t.get("avatar")
    if isinstance(t.get("messages"), list):
        out["messages"] = [{"id": m["id"], "staff": bool(m["staff"]), "body": m["body"], "created_at": m["created_at"]} for m in t["messages"]]
    else:
        out["messages"] = t.get("messages", 0)
        out["last"] = t.get("last")
    return out


# ---------------------------------------------------------------- members
@router.get("/me/tickets")
async def my_tickets(request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    return {"tickets": [_public(t) for t in await rdb.tickets(uid=member["id"])], "categories": CATEGORIES}


@router.post("/me/tickets")
async def open_ticket(body: NewTicket, request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Pick a category from the list.")
    if len(await rdb.tickets(uid=member["id"], status="open")) >= 5:
        raise HTTPException(429, "You have five open tickets already. Wait for an answer, or close one.")
    tid = await rdb.create_ticket(member["id"], body.category, body.subject.strip(), body.body.strip())
    await rdb.emit("ticket_opened", member["id"], {"ticket": tid, "category": body.category})
    return _public(await rdb.ticket(tid))


async def _mine(request: Request, tid: int, member: dict) -> dict:
    t = await request.app.state.rpg.ticket(tid)
    if not t or t["member_id"] != member["id"]:
        raise HTTPException(404, "No such ticket.")
    return t


@router.get("/me/tickets/{tid}")
async def my_ticket(tid: int, request: Request, member=Depends(current_member)):
    return _public(await _mine(request, tid, member))


@router.post("/me/tickets/{tid}/reply")
async def my_reply(tid: int, body: Reply, request: Request, member=Depends(current_member)):
    t = await _mine(request, tid, member)
    if t["status"] == "closed":
        raise HTTPException(409, "This ticket is closed. Open a new one.")
    rdb = request.app.state.rpg
    await rdb.ticket_reply(tid, member["id"], False, body.body.strip(), "open")
    return _public(await rdb.ticket(tid))


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
    return {"tickets": [_public(t) for t in await rdb.tickets(status=status)], "open": await rdb.open_ticket_count()}


@router.get("/admin/tickets/{tid}")
async def staff_ticket(tid: int, request: Request, _=Depends(staff_only)):
    t = await request.app.state.rpg.ticket(tid)
    if not t:
        raise HTTPException(404, "No such ticket.")
    return _public(t)


@router.post("/admin/tickets/{tid}/reply")
async def staff_reply(tid: int, body: Reply, request: Request, member=Depends(staff_only)):
    rdb = request.app.state.rpg
    t = await rdb.ticket(tid)
    if not t:
        raise HTTPException(404, "No such ticket.")
    await rdb.ticket_reply(tid, member["id"], True, body.body.strip(), "answered")
    await rdb.admin_log(member["id"], "ticket_reply", t["member_id"], {"ticket": tid})
    return _public(await rdb.ticket(tid))


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
