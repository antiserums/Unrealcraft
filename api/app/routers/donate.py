"""Donations through Stripe Checkout. Five dollars or more, once, opens the Patron set.

Flow: the member presses Donate on /donate -> POST /me/donate/checkout makes a Stripe Checkout Session carrying
the member's Discord id -> Stripe hosts the payment page -> Stripe calls POST /stripe/webhook
(checkout.session.completed) -> the payment is recorded and the `supporter` medal granted, which the entitlement
rules turn into the outfit and both frames.

Keys live only in api/.env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_CURRENCY (default usd). Without a
secret key the /donate page says donations open soon, and staff can still mark supporters by hand."""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..session import current_member

log = logging.getLogger("unrealcraft.donate")
router = APIRouter(tags=["donate"])
MIN_CENTS = 500
MAX_CENTS = 100_000


def _stripe():
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key:
        return None
    try:
        import stripe
    except ImportError:
        log.warning("STRIPE_SECRET_KEY is set but the stripe package is not installed (pip install stripe)")
        return None
    stripe.api_key = key
    return stripe


def _currency() -> str:
    return os.getenv("STRIPE_CURRENCY", "usd").strip().lower() or "usd"


class Checkout(BaseModel):
    amount: int          # whole units of the currency


@router.get("/donate/status")
async def status(request: Request):
    """Whether donations are open (for the /donate page), the currency and the minimum."""
    return {"open": _stripe() is not None, "currency": _currency(), "minimum": MIN_CENTS // 100}


@router.post("/me/donate/checkout")
async def checkout(body: Checkout, request: Request, member=Depends(current_member)):
    stripe = _stripe()
    if stripe is None:
        raise HTTPException(503, "Donations are not open yet.")
    cents = int(body.amount) * 100
    if not MIN_CENTS <= cents <= MAX_CENTS:
        raise HTTPException(400, f"Pick an amount between {MIN_CENTS // 100} and {MAX_CENTS // 100}.")
    origin = settings.web_origin.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            submit_type="donate",
            line_items=[{"quantity": 1, "price_data": {"currency": _currency(), "unit_amount": cents,
                                                       "product_data": {"name": "Donation to Unrealcraft",
                                                                        "description": "A thank-you gift. Opens the Patron set on the site."}}}],
            client_reference_id=str(member["id"]),
            metadata={"discord_id": str(member["id"]), "name": str(member.get("name") or "")},
            success_url=f"{origin}/donate?thanks=1",
            cancel_url=f"{origin}/donate?cancelled=1",
        )
    except Exception as e:                       # network, bad key, Stripe outage: say so plainly
        log.exception("stripe checkout failed")
        raise HTTPException(502, "Stripe did not accept the request. Try again in a moment.") from e
    return {"url": session.url}


@router.post("/stripe/webhook")
async def webhook(request: Request):
    stripe = _stripe()
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if stripe is None or not secret:
        raise HTTPException(503, "Webhook not configured.")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except Exception as e:
        raise HTTPException(400, "Bad signature.") from e
    if event["type"] != "checkout.session.completed":
        return {"ok": True, "ignored": event["type"]}
    s = event["data"]["object"]
    if s.get("payment_status") not in (None, "paid"):
        return {"ok": True, "ignored": "unpaid"}
    ref = s.get("client_reference_id") or (s.get("metadata") or {}).get("discord_id")
    if not ref or not str(ref).isdigit():
        log.warning("donation without a member id: %s", s.get("id"))
        return {"ok": True, "ignored": "no member"}
    uid = int(ref)
    amount = int(s.get("amount_total") or 0)
    rdb = request.app.state.rpg
    new = await rdb.record_donation(uid, s["id"], amount, str(s.get("currency") or _currency()))
    if new and amount >= MIN_CENTS:
        await rdb.ensure_character(uid)
        if await rdb.grant_medal(uid, "supporter"):
            await rdb.emit("supporter", uid, {"amount": amount, "currency": s.get("currency")})
            log.info("supporter medal granted to %s", uid)
    return {"ok": True}
