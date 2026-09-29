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
- **Phase 2:** quizzes and submissions on the site; the API becomes the only writer; the bot reads from the API.
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
```

Quiz answers are never sent to the browser; `/catalog/quests/{id}` returns questions and choices only.
