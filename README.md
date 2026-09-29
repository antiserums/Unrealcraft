# Unrealcraft

**Server:** https://discord.gg/Y2yDDNQQw

A Discord learning RPG for Unreal Engine 5. Members earn ranks by finishing quests: read the official docs, do the work in-engine,
pass a quiz and submit proof. Chat does not earn XP. After a short shared Starter Quests, the path is personalized by **major**.
The bot is the **Quartermaster**.

**Status:** the Quartermaster is live on the Unrealcraft server. See [CHANGELOG.md](CHANGELOG.md).

## Releasing an update (patch notes)
Patch notes are only posted for versions that have been **pushed to GitHub as a tag**.
1. Make the change and test it.
2. Pick the next version with [Semantic Versioning](https://semver.org) (rules at the top of `CHANGELOG.md`):
   fixes → PATCH, new stuff → MINOR, breaking for members → MAJOR.
3. Add an entry at the **top** of `CHANGELOG.md`, e.g. `## v0.2.0 · 2026-10-02 · Short title`, then bullets for members.
   `python bot/tools/validate_curriculum.py` checks the format and that the version went up.
4. Commit, tag and push:
   ```bash
   git add -A && git commit -m "v0.2.0: short title" && git tag -a v0.2.0 -m "v0.2.0" && git push --follow-tags
   ```
5. Within a minute the Quartermaster sees the new tag on GitHub and posts the entry to **#patch-notes**
   (one message per version, never edited, so the channel is the full history). Restart the bot if the update changed its code.

If members report problems after an update, they use **#help-desk → 🐞 Server / bot problem**, which includes the
bot version and alerts #mod-log.

## Layout
```
CHANGELOG.md           patch notes (top entry is posted to #patch-notes)
curriculum/            source of truth for quests (YAML)
  majors.yaml          ranks, XP thresholds, seals, majors, tasters, capstones
  orientation.yaml     O1–O8 + 4 electives (Discord literacy)
  spine.yaml           S1–S11 Starter Quests + Rank 0 meta electives
  level_design_r1.yaml Rank 1 world/lighting + Level Design (full quizzes)
  level_design_r2.yaml Rank 2 shared Blueprint + Level Design (full quizzes)
  level_design_r3.yaml Rank 3 shared characters-anim + bay-design (full quizzes)
  tasters.yaml         cross-major tasters (C++ hello, GAS, lighting pass, pickup loop, master material)
  programming_stub.yaml, lookdev_stub.yaml   R1–R3 stubs (no quizzes yet)
  VERIFIED_URLS.md     Epic doc slugs checked against the live UE 5.8 docs index
docs/
  01-server-structure.md   channels, roles, colors, permission tables
  02-promotion-dms.md      6-line briefings for every rank jump + #rank-ups card
  03-commands.md           command list, submit routing, schema notes
  04-discord-setup-checklist.md
  05-path-mocks.md         /path for a Level Design vs Programming Greenlit
  06-community-rules.md
bot/
  registrar/               discord.py 2.x package (cogs: onboarding, majors, quests, quiz, ranks)
  db/schema.sql            SQLite
  config/unlocks.yaml      role, channel and category IDs
  tools/validate_curriculum.py
```

## Run (test server)
Requires Python 3.11+.
```bash
cd bot
python -m venv .venv && .venv/Scripts/activate      # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env                                # fill in DISCORD_TOKEN and GUILD_ID
python tools/validate_curriculum.py --path level_design
python -m registrar
```
Then follow `docs/04-discord-setup-checklist.md` sections E–G.

## Design rules the code enforces
- Rank-up = XP threshold **and** every required quest, taster and capstone for the current rank passed. Chat XP is 0.
- One visible rank role at a time. Specialty roles are separate permission-only roles that stay with the member after Rank 3.
- The `/quest` picker order is: Orientation → Starter Quests → missing required taster → major-required at the current rank → 2 major electives + 1 adjacent.
- Level designers are never gated on C++, and programmers are never gated on a hero lighting reel.
- Verification: R0–1 use quiz + honor system, R2 needs a peer or mentor, R3–4 a mentor or two peers, R5–6 a human mentor only.

## Adding quests
Edit YAML, run `python tools/validate_curriculum.py --warnings`, then use `/admin reload-curriculum`. Only use slugs from
`curriculum/VERIFIED_URLS.md` as `official_url`; otherwise write `TODO_URL`.
