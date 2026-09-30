"""Mail (letters): the site's notifications, shown at /mail. A letter goes to one member, to every member, or to staff. The site writes
them itself when something happens (a ticket is answered or queued, work is reviewed, a rank is reached, a
donation lands), and admins write announcements and personal letters from the admin panel.

Audience (`member_id`): a Discord id for one member, 0 for everyone, -1 for staff (admins, developers, mentors).
Reads are per member in `letter_reads`, so an announcement is unread for each member until they open it."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..session import current_member
from ..staff import can_review, is_admin

router = APIRouter(tags=["letters"])
EVERYONE, STAFF = 0, -1
KINDS = ["letter", "announcement", "ticket", "review", "rank", "donation"]


def _staff(member: dict) -> bool:
    return is_admin(member) or can_review(member)


async def send_letter(request: Request, to: int, kind: str, title: str, body: str, link: str | None = None, sender: int | None = None) -> int:
    """Used by the other routers: write a letter to a member (to = id), everyone (0) or staff (-1)."""
    return await request.app.state.rpg.send_letter(to, kind, title, body, link, sender)


@router.get("/me/letters")
async def my_letters(request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    rows = await rdb.letters_for(member["id"], staff=_staff(member))
    return {"letters": rows, "unread": sum(1 for r in rows if not r["read"])}


@router.get("/me/letters/unread")
async def unread(request: Request, member=Depends(current_member)):
    return {"unread": await request.app.state.rpg.unread_letters(member["id"], staff=_staff(member))}


@router.post("/me/letters/{lid}/read")
async def mark_read(lid: int, request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    if not await rdb.letter_visible(lid, member["id"], staff=_staff(member)):
        raise HTTPException(404, "No such letter.")
    await rdb.mark_letter(member["id"], lid)
    return {"ok": True}


@router.post("/me/letters/read-all")
async def read_all(request: Request, member=Depends(current_member)):
    rdb = request.app.state.rpg
    for r in await rdb.letters_for(member["id"], staff=_staff(member)):
        if not r["read"]:
            await rdb.mark_letter(member["id"], r["id"])
    return {"ok": True}


# ---------------------------------------------------------------- admin
class Compose(BaseModel):
    to: str = "all"                  # "all", "staff" or a Discord id
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=6000)
    link: str | None = None


def admin_only(member=Depends(current_member)) -> dict:
    if not is_admin(member):
        raise HTTPException(403, "Admins and developers only.")
    return member


@router.post("/admin/letters")
async def compose(body: Compose, request: Request, admin=Depends(admin_only)):
    to = body.to.strip().lower()
    if to == "all":
        target, kind = EVERYONE, "announcement"
    elif to == "staff":
        target, kind = STAFF, "letter"
    elif to.isdigit():
        target, kind = int(to), "letter"
    else:
        raise HTTPException(400, "Send to 'all', 'staff' or a Discord id.")
    link = (body.link or "").strip() or None
    if link and not (link.startswith("/") or link.startswith("https://")):
        raise HTTPException(400, "A link must start with / or https://.")
    rdb = request.app.state.rpg
    lid = await rdb.send_letter(target, kind, body.title.strip(), body.body.strip(), link, admin["id"])
    await rdb.admin_log(admin["id"], "letter", target if target > 0 else None, {"letter": lid, "to": to})
    return {"id": lid}


@router.get("/admin/letters")
async def sent(request: Request, _=Depends(admin_only)):
    return {"letters": await request.app.state.rpg.letters_sent()}


@router.delete("/admin/letters/{lid}")
async def unsend(lid: int, request: Request, admin=Depends(admin_only)):
    rdb = request.app.state.rpg
    await rdb.delete_letter(lid)
    await rdb.admin_log(admin["id"], "letter_delete", None, {"letter": lid})
    return {"ok": True}
