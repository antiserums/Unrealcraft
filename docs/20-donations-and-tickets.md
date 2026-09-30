# Donations (Stripe) and support tickets

## Support tickets

- Members open tickets on `/support` (category, subject, text), see their own list and each thread, reply and
  close. Five open tickets at most per member. Guests see the help text and a login button.
- Staff (admins, developers and mentors) answer in the admin panel: `/admin/tickets` (filter by open, answered,
  closed) and `/admin/tickets/<id>`. A staff reply marks the ticket answered; a member reply reopens it; either
  side can close it, staff can reopen. Replies and status changes are written to the admin log.
- API: `GET/POST /me/tickets`, `GET /me/tickets/{id}`, `POST /me/tickets/{id}/reply`, `POST /me/tickets/{id}/close`;
  staff: `GET /admin/tickets?status=`, `GET /admin/tickets/{id}`, `POST /admin/tickets/{id}/reply`,
  `POST /admin/tickets/{id}/status`. Tables `tickets` and `ticket_messages` (`api/app/rpg_db.py`). Opening a
  ticket emits a `ticket_opened` event; the bot ignores it for now.
- Tickets are not e-mailed anywhere. Staff need to look at `/admin/tickets`; the count of open tickets shows on
  the Open filter button.

## Donations

Nothing on the site is for sale. A donation of the minimum (5 USD) or more, once, is thanked with the Patron set:
the `supporter` outfit, avatar frame and card frame, all opened by the `supporter` medal.

- `/donate` shows the amount buttons and a Donate button when Stripe is configured, otherwise "Donations open
  soon". The member must be logged in, because the payment must be tied to a Discord id.
- `POST /me/donate/checkout {amount}` creates a Stripe Checkout Session (mode payment, `client_reference_id` =
  Discord id, min 5, max 1000) and returns its URL. Stripe hosts the card form; the site never sees card data.
- `POST /stripe/webhook` receives `checkout.session.completed`, checks the signature, records the payment in
  `donations` (one row per session id, so retries are harmless) and grants the `supporter` medal when the amount
  is at least the minimum. It emits a `supporter` event.
- Staff can still grant the medal by hand: admin panel -> member -> Mark as supporter. Use it when a donation
  came in some other way or a webhook was missed.

### Setting Stripe up (one time)

1. In the Stripe dashboard, Developers -> API keys: copy the **secret key** (starts with `sk_live_` or, for
   testing, `sk_test_`). Put it in `api/.env` as `STRIPE_SECRET_KEY=`. Never commit `.env`.
2. Developers -> Webhooks -> Add endpoint: URL `https://<your public site>/api/stripe/webhook`, event
   `checkout.session.completed`. Copy the **signing secret** (`whsec_…`) into `api/.env` as
   `STRIPE_WEBHOOK_SECRET=`. The site must be reachable from the internet for this; on the LAN-only server,
   use the Stripe CLI while testing: `stripe listen --forward-to localhost:8000/stripe/webhook`, which prints a
   temporary `whsec_` to use.
3. Optional: `STRIPE_CURRENCY=usd` (any Stripe currency code; the minimum stays "5 units").
4. Restart the API. `GET /donate/status` should say `"open": true`.
5. Test with a Stripe test key and the test card `4242 4242 4242 4242`: donate on `/donate`, then check the
   wardrobe for the Patron set and `donations` in the database.
6. Settings -> Branding in Stripe: set the name and logo shown on the Checkout page.

The `/api/...` prefix is the website's proxy to the API (`web/next.config.ts`). If the API is exposed directly,
point the webhook at `/stripe/webhook` on it instead.

## Inbox (mail and notifications)

The inbox at `/inbox` (the envelope in the top bar shows the unread count; `/mail` and `/letters` redirect).
One list of everything, newest first: sender, subject, a coloured type tag (ticket, review, announcement, letter,
rank, thank-you) and a preview; unread rows are bold with a gold dot. Clicking a row opens that mail in place of
the list, with Back, newer/older, a Mark read/unread button and an action button that names where it goes
(the ticket, the quest, the wardrobe). Opening marks it read; "Mark all read" above the list clears the lot.

- A letter goes to one member, to everyone (`member_id` 0, an announcement) or to staff (`member_id` -1). Reads
  are per member (`letter_reads`). Announcements written before a member joined are not shown to them.
- The site writes letters itself: a new ticket or a member's reply (to staff), a staff answer (to the member), a
  review decision (to the member, with the reviewer's note), a rank-up, and a donation thank-you.
- Admins write announcements and personal letters at `/admin/letters` (to everyone, staff, or a Discord id, with
  an optional link), see what was sent and how many opened it, and can unsend a letter.
- API: `GET /me/letters`, `GET /me/letters/unread`, `POST /me/letters/{id}/read`, `POST /me/letters/read-all`;
  admin: `GET/POST /admin/letters`, `DELETE /admin/letters/{id}`. `letters_unread` rides on `/me`.
