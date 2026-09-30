# 03 — The Discord bot (Quartermaster)

The website is where Unrealcraft is played: quests, boss fights, turn-ins, reviews, ranks and entitlements. The
Discord server is the guild hall: a place to talk, ask for help and show progress. The bot is small on purpose.

## What the bot does
- **Builds the server** (`/setup bootstrap`): roles, categories, channels, forums, pins, Rules Screening, the
  welcome screen and AutoMod. Safe to re-run. IDs are written to `bot/config/unlocks.yaml`.
- **Keeps roles in step with the site** (`cogs/roles.py`): one rank role (swapped, never stacked) and one role
  per chosen specialization, the primary and every extra.
- **Announces rank-ups** in #rank-ups when the site promotes someone (Apprentice and above).
- **Posts patch notes** in #patch-notes for every version tag pushed to GitHub.
- **Join-to-create voice rooms** in Town Hall (`cogs/voice.py`).

It never grants XP, quests or ranks, and it does not read what members write (Message Content intent is off).

## Commands
| Command | Who | What it does |
|---|---|---|
| /site | anyone | A button to the website. |
| /card `[member]` | anyone | Rank, specializations, XP and quests done, with a link to the player card. |
| /room rename `name` · /room limit `n` | owner of a voice room | Rename your join-to-create room or cap how many can join. |
| /setup bootstrap | admin | Create or repair roles, channels and pins, then sync everyone's roles. |
| /setup sync-pins | admin | Update pinned messages in place and remove stray bot posts. |
| /setup sync-roles | admin | Make every member's roles match the site. |
| /setup patch-notes | admin | Post released versions missing from #patch-notes. |
| /setup reload-curriculum | admin | Reload ranks and specializations after the curriculum changed. |

## How the site talks to the bot
The API and the bot share one SQLite file. The API writes rows to `events`; the bot polls every 20 seconds.
Only three event types make the bot act:

| Event | Written when | Bot does |
|---|---|---|
| `rank_up` | the site promotes a member (`api/app/progress.py`) | swaps the rank role, posts the #rank-ups card |
| `rank_set` | an admin sets a rank in the admin panel | swaps the rank role |
| `specialization_set` | a member or an admin changes specializations | swaps the specialization roles |

Every other event type (`quest_completed`, `quiz_passed`, `submission_*`) is marked delivered and ignored. They
remain useful in the admin panel's event list.

## Where things moved
| Was a Discord command | Now |
|---|---|
| /start, /quiz, /quest, /submit, /skip-elective | the quest page on the site |
| /major, /minor | Specializations on the player card page (a primary plus extras) |
| /rank, /path, /tree, /profile | the player card, My path and the Quest Board |
| /mentor-review and the mentor queue | the review inbox on the site |
| /grant-xp, /admin … | the admin panel on the site |

## Settings (`bot/.env`)
`DISCORD_TOKEN`, `GUILD_ID`, `DB_PATH`, `CURRICULUM_DIR`, `UNLOCKS_PATH`, `LOG_LEVEL`, and `SITE_URL` (where the
site lives; pins, `/site` and `/card` link there).
