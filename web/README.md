# Unrealcraft website

Next.js (App Router, TypeScript). The browser only talks to this app; `/api/*` is proxied to the FastAPI service in
`../api` (see `next.config.ts`), so the session cookie stays same-origin.

```bash
npm install
cp .env.example .env.local     # API_URL=http://localhost:8000
npm run dev                    # http://localhost:3000
```

Pages: `/` (home: continue questing), `/quests` (browser), `/quests/[id]`, `/path`, `/me`, `/members/[id]`,
`/leaderboard`, `/changelog`, `/login`. Server components fetch the API with `lib/api.ts`, which forwards the cookie.
