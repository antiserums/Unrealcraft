"""Discord OAuth2 login. Scopes: identify (who you are) + guilds.members.read (are you on the server)."""
from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from .config import settings
from .session import clear_session, set_session

router = APIRouter(prefix="/auth", tags=["auth"])
DISCORD = "https://discord.com/api/v10"
SCOPES = "identify guilds.members.read"
STATE_COOKIE = "uc_oauth_state"


@router.get("/discord")
async def start(request: Request, next: str = "/"):
    if not settings.client_id:
        raise HTTPException(500, "DISCORD_CLIENT_ID is not set in api/.env")
    state = secrets.token_urlsafe(24)
    q = urlencode({"client_id": settings.client_id, "redirect_uri": settings.redirect_uri, "response_type": "code",
                   "scope": SCOPES, "state": state})
    resp = RedirectResponse(f"https://discord.com/oauth2/authorize?{q}", status_code=302)
    resp.set_cookie(STATE_COOKIE, f"{state}|{next[:200]}", max_age=600, httponly=True, samesite="lax", path="/")
    return resp


@router.get("/discord/callback")
async def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    saved = request.cookies.get(STATE_COOKIE, "")
    saved_state, _, next_url = saved.partition("|")
    if error or not code or not state or state != saved_state:
        return RedirectResponse(f"{settings.web_origin}/login?error=cancelled", status_code=302)

    async with httpx.AsyncClient(timeout=15) as http:
        tok = await http.post(f"{DISCORD}/oauth2/token", data={
            "client_id": settings.client_id, "client_secret": settings.client_secret,
            "grant_type": "authorization_code", "code": code, "redirect_uri": settings.redirect_uri,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if tok.status_code != 200:
            return RedirectResponse(f"{settings.web_origin}/login?error=token", status_code=302)
        access = tok.json()["access_token"]
        h = {"Authorization": f"Bearer {access}"}
        me = (await http.get(f"{DISCORD}/users/@me", headers=h)).json()
        member = await http.get(f"{DISCORD}/users/@me/guilds/{settings.guild_id}/member", headers=h)
        # We only needed the token for these two calls. Discord tokens are never stored.
        await http.post(f"{DISCORD}/oauth2/token/revoke",
                        data={"token": access, "client_id": settings.client_id, "client_secret": settings.client_secret})

    if member.status_code != 200:
        return RedirectResponse(f"{settings.web_origin}/login?error=not_member", status_code=302)
    m = member.json()
    avatar = me.get("avatar")
    avatar_url = (f"https://cdn.discordapp.com/avatars/{me['id']}/{avatar}.png?size=128" if avatar
                  else "https://cdn.discordapp.com/embed/avatars/0.png")
    data = {"id": int(me["id"]), "name": m.get("nick") or me.get("global_name") or me["username"],
            "username": me["username"], "avatar": avatar_url, "roles": m.get("roles", [])}
    dest = next_url if next_url.startswith("/") else "/"
    resp = RedirectResponse(f"{settings.web_origin}{dest}", status_code=302)
    set_session(resp, data)
    resp.delete_cookie(STATE_COOKIE, path="/")
    return resp


@router.post("/logout")
async def logout():
    resp = RedirectResponse(f"{settings.web_origin}/", status_code=303)
    clear_session(resp)
    return resp


@router.get("/dev-login")
async def dev_login(request: Request):
    """Local testing only: logs in as the Discord id in DEV_LOGIN_ID (api/.env). Off unless that variable is set."""
    import os
    uid = os.getenv("DEV_LOGIN_ID", "").strip()
    if not uid or not settings.web_origin.startswith("http://localhost"):
        raise HTTPException(404, "Not found.")
    resp = RedirectResponse(f"{settings.web_origin}/", status_code=302)
    set_session(resp, {"id": int(uid), "name": "Dev Tester", "username": "dev", "avatar": None, "roles": []})
    return resp
