"""Signed-cookie sessions. Nothing is stored server-side, so logging in never writes to the database."""
from __future__ import annotations

from fastapi import HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import settings

COOKIE = "uc_session"
MAX_AGE = 30 * 24 * 3600


def _serializer() -> URLSafeTimedSerializer:
    if not settings.session_secret:
        raise RuntimeError("SESSION_SECRET is not set in api/.env")
    return URLSafeTimedSerializer(settings.session_secret, salt="uc-session")


def set_session(resp: Response, data: dict) -> None:
    resp.set_cookie(COOKIE, _serializer().dumps(data), max_age=MAX_AGE, httponly=True, samesite="lax",
                    secure=settings.web_origin.startswith("https://"), path="/")


def clear_session(resp: Response) -> None:
    resp.delete_cookie(COOKIE, path="/")


def read_session(request: Request) -> dict | None:
    raw = request.cookies.get(COOKIE)
    if not raw:
        return None
    try:
        return _serializer().loads(raw, max_age=MAX_AGE)
    except BadSignature:
        return None


def current_member(request: Request) -> dict:
    """FastAPI dependency: the logged-in member ({id, name, avatar}) or 401."""
    s = read_session(request)
    if not s:
        raise HTTPException(401, "Log in with Discord first.")
    return s


def current_member_or_none(request: Request) -> dict | None:
    return read_session(request)
