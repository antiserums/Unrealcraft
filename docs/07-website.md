# Website and API

The website is the source of truth for members, XP, ranks, progress, quizzes and submissions. The Quartermaster bot
mirrors that state into Discord (roles, DMs, channel cards) and shows link cards only. See the plan for the full
picture; this page is the practical guide.

## Parts

| Folder | What | Runs on |
|---|---|---|
| `api/` | FastAPI service. Owns the database and every rule (quest picker, rank gates, tier counts, quiz grading). Reuses the rules engine in `bot/registrar/curriculum.py`. | http://localhost:8000 |
| `web/` | Next.js site. Proxies `/api/*` to the API so cookies stay same-origin. | http://localhost:3000 |
| `bot/` | Quartermaster. Still writes the shared SQLite file until phase 2. | Discord |
| `curriculum/` | YAML quests, unchanged. Loaded by both the bot and the API. | |

Data lives in `bot/data/registrar.db` (SQLite, WAL mode). The API opens the same file. Postgres can replace it later.

## First-time setup (Windows server)

1. **Discord application** (Developer Portal → the Quartermaster's application → OAuth2):
   - Copy the *Client ID* and reset/copy the *Client Secret*.
   - Add a redirect: `http://localhost:3000/api/auth/discord/callback`. Add one per hostname you will open the site
     from (for example `http://your-pc-name:3000/api/auth/discord/callback` on the LAN).
2. **API**: `cd api`, `py -3 -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`, copy `.env.example`
   to `.env` and fill in `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_GUILD_ID`, `SESSION_SECRET` (any long
   random string) and `DISCORD_REDIRECT_URI` (must match the portal exactly).
3. **Web**: install Node.js LTS, `cd web`, `npm install`, copy `.env.example` to `.env.local`.
4. **Run**: `.\run.ps1` from the repo root starts API, site and bot in three windows. `.\run.ps1 api` runs one.

Login flow: the site sends you to Discord, Discord sends you back to the API, the API checks that you are a member of
the server, then sets a signed cookie. No Discord tokens are stored.

## Phases

- **Phase 1 (done):** read-only site. Login, home with "Continue questing", quest browser, quest pages, path, profile,
  leaderboard, changelog. The bot is unchanged.
- **RPG phase A (done):** the quiz is a turn-based boss fight on the site (`/quests/{id}/fight`). Right answer = hit,
  wrong answer = wound (+ a one-turn debuff), pass rules unchanged. Gear may afford one dodge per fight. Crits give a
  little bonus XP (25/day cap). Bosses are generated from quest data (`api/app/rpg.py`). Winning writes the same rows
  the Discord quiz wrote (quiz_attempts, quest_progress, xp_log, kv fact) and an `events` row that the bot's `sync`
  cog picks up every 20 s to run promotion checks and orientation steps.
- **RPG phase B (done):** profile split in three. `/me` is a shareable player card (motto, nameplate colour,
  up to three featured achievements, public toggle; `/members/{id}` shows the same card, without login when
  public). `/me/wardrobe` is the look and the outfits. `/me/achievements` lists every achievement with progress
  (`GET /me/achievements`, defined in `api/app/rpg.py` `ACHIEVEMENTS`). Stats are no longer shown anywhere;
  the fight still uses the hidden values for crit chance and damage. Outfits are cosmetic only: whole sets
  unlocked by capstones, ranks and achievements, worn one at a time and switchable.
- **Phase 2 (done):** the chest. `POST /me/quests/{id}/submit` (multipart: text, ue_version, up to 4 images) with the
  bot's routing rules (auto/honor accept at once and complete the quest; peer/mentor/human wait for a review). The chest
  only shows once the boss is beaten. Images live in `api/data/uploads/<member>/` and are served to logged-in members
  at `/api/uploads/...`. The bot mirrors website turn-ins (forum post, review or spot-check card) from `events`.
  No cooldown on retrying a boss; the 120-minute cooldown after a reviewer's Fail still applies to the chest.
- **Reviews on the site (done):** `/review` is the mentor inbox (pending, waiting on others, recent), `/review/{id}`
  shows the turn-in with screenshots, earlier attempts and the quest's checklist, and records Pass / Changes / Fail.
  Only mentors review (staff mentor role, rank 6, `ADMIN_IDS`, or the dev login); one verdict decides. The bot's
  buttons enforce the same rule. A decision emits `submission_decided`, which the bot mirrors into Discord.
- **Staff roles:** `app/staff.py`. `ADMIN_IDS` and `DEVELOPER_IDS` get everything unlocked (outfits, cosmetics,
  locked dungeons), the admin panel and the review inbox, with an Admin / Developer nameplate. `MENTOR_IDS` (or the
  Discord mentor role / rank 6) get the review inbox only and a Mentor nameplate. The local dev login counts as
  a developer.
- **Admin panel (done):** `/admin` for admins and developers: stats, member search, the events queue and an
  admin log; `/admin/members/{id}` grants or clears quests, sets rank/major (emits `rank_set` so the bot swaps
  roles), gives XP or medals, and resets an account. Every action lands in `admin_log`.
- **Entitlements (done):** every unlock an account can hold is an entitlement: outfits, nameplate colours, avatar
  frames, player card frames, titles ("Kai, the Learner", shown after the name on the card, the member page and
  the leaderboard; "None" hides it) and achievements. `app/entitlements.py` merges the built-in catalog
  (`rpg.py` `default_entitlements()`, seeded from the art pack) with the `entitlements` table, where admins add,
  edit or switch rows off (`/admin/entitlements`). Unlock rules: starter, rank, achievement, medal, staff role, or
  granted only. `entitlement_grants` hands one member one entitlement from their admin page whatever the rule says.
  Achievements count one of: quests done, first-try boss wins, accepted work, readings, streak, capstones, or a
  medal with the achievement's key. New art still comes only from the synced art pack; a row points at an art id.
- **Quest editor (done):** `/admin/quests` lists the catalog; `/admin/quests/{id}` (or `new`) edits one quest as a
  form (every field, a quiz editor, flavors as YAML) or as raw YAML. Saving validates the quest against the whole
  catalog, rewrites its curriculum file with `yaml.safe_dump` (comments in that file are lost, so hand-written
  files are best edited by hand), and reloads the API's catalog. New quests default to `curriculum/admin.yaml`.
  The bot keeps its own copy: run `/admin reload-curriculum` on Discord afterwards.
- **Next:** retire the Discord quiz and submit commands; dungeon map; port the pack's renderer for appearance.
- **Phase 3:** reviews and promotions on the site; event outbox for the bot (roles, DMs, #rank-ups).
- **Phase 4:** slim the bot to link cards; orientation events reported to the API; staff panel.
- **Phase 5:** customization, leaderboard by major, helper karma, daily quest.

## API endpoints (phase 1)

```
GET  /health
GET  /auth/discord            GET /auth/discord/callback      POST /auth/logout
GET  /catalog/majors          GET /catalog/quests?major=&tier=&subject=&q=     GET /catalog/quests/{id}
GET  /catalog/subjects        GET /changelog
GET  /me                      GET /me/next                    GET /me/path
GET  /members/{id}            GET /leaderboard?period=week|month|all
GET  /me/character            PATCH /me/character {wear, nameplate, avatar_frame, card_frame, title, banner (motto), featured, public, style, appearance}; GET /me/card; GET /me/achievements       POST /me/quests/{id}/read
GET  /admin/curriculum        GET /admin/curriculum/quests/{id}   POST /admin/curriculum/quests {quest|yaml, file, replace}   DELETE /admin/curriculum/quests/{id}   POST /admin/curriculum/reload
GET  /admin/entitlements      PUT /admin/entitlements/{kind}/{id}   DELETE /admin/entitlements/{kind}/{id}   POST /admin/members/{id}/entitlements {kind, id, remove}
POST /me/quests/{id}/fight    GET /fights/{id}   POST /fights/{id}/turn {answer, seconds}   POST /fights/{id}/retreat
GET  /catalog/quests/{id}/boss
POST /me/quests/{id}/submit   multipart text, ue_version, files[]     GET /uploads/{member}/{file}
GET  /auth/dev-login          local testing only, when DEV_LOGIN_ID is set in api/.env
```

Quiz answers are never sent to the browser; `/catalog/quests/{id}` returns questions and choices only.
