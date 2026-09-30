# 01 — Server structure (final)

> **Superseded (2026-09-30).** This describes the older design where the game was played in Discord. The website now runs quests, reviews and ranks; the Discord server is a guild hall. See `03-commands.md`, `04-discord-setup-checklist.md` and `07-website.md`. Kept for history.

Bot name: **Quartermaster**. It is used in every embed, DM and log line. Proctor, Foreman and Deanbot are retired.
Visual: dark UI. Embeds use `#1E1F22` backgrounds with the rank color as the accent bar. Gold is reserved for Lead.

Principle: **a channel exists only when someone at that rank has work to do in it.** The layout is built and repaired by the
bot (`/setup bootstrap`); this page describes it. 21 text/forum channels, 3 voice, 1 stage.

Everything a member can't see yet is listed in **#welcome → "Map: what opens when"**, and `/path` shows what opens next.

## Categories and channels

`[F]` = forum, `[A]` = announcement, `[V]` = voice, `[S]` = stage, `(ro)` = read-only.

| Category | Channels | Who sees it |
|---|---|---|
| 00 · GATE | #welcome (the one start page: how it works, commands, what opens when, help, rules, Start Questing + Rules quiz buttons), #announcements [A], #patch-notes [A], #epic-games-resources (ro), #rank-ups (ro) | everyone |
| 01 · GUILD HUB | #general, #introductions, #showcase [F], #help-desk [F] (Unreal help + server/bot problems), #suggestions [F] | everyone who accepted the rules |
| 02 · QUEST BOARD | #quest-log (ro, from Novice), #starter-quests, then one forum per major: #level-design, #environment-art, #tech-art, #gameplay-design, #animation, #programming, #cinematics (everyone reads all; you post in your major's) | quest board from Orientation; each forum at its rank |
| 03 · TOWN HALL | ➕ Join to create [V]: joining it makes your own room (rename / user limit; deleted after 5 min empty), Lecture Hall [S] (speak: Senior+, Mentor, Mod) | anyone who started Orientation (Recruit) |
| 04 · STAFF | #mod-log (also gets 🐞 bug-report alerts), #curriculum-wip, #mentor-queue | staff (+ Senior read queue, Lead) |

**Major forums:** one thread per thing you're building (tags WIP / Help / Done). Every `/submit` is also posted there with the
Turn-in tag so others can see and cheer it. Lessons come through `/quest` cards, not channels.

**Specialty:** from Rank 3 the member's major is their specialty and joins the title (Expert · Level Design). Nothing is picked separately. There are no specialty channels; critique happens in #showcase with the Critique-wanted tag.

**Pinned messages:** each channel has at most one pinned bot message. The bot edits it in place when wording changes (`/setup sync-pins`) and deletes any other stray bot posts.
is a private room for `/critique` and specialty work.

Phase 5 adds systems (R4) and net/GAS + shipping (R5) forums to QUEST BOARD; nothing is created early.

### Discord Community features in use
Rules Screening (8 rules), Onboarding with 4 pre-join questions + 3 on Channels & Roles (see `bot/registrar/profile.py`),
Welcome Screen, AutoMod (mention spam, flagged words, spam → #mod-log), Server Guide (set by hand; bots can't).

---

## Roles (top → bottom in role list; order matters)

| # | Role | Color | Hoist | Mentionable | Notes |
|---|---|---|---|---|---|
| 1 | Owner | — | ✔ | ✖ | |
| 2 | Mod | `#E0E0E0` | ✔ | ✔ | |
| 3 | **Quartermaster** (bot) | — | ✖ | ✖ | **Must sit above every role it assigns.** |
| 4 | Curriculum | `#B0A48A` | ✖ | ✔ | Edits catalog. Staff only. |
| 5 | Mentor | `#6FB3A0` | ✖ | ✔ | Reviews. |
| 6 | Mentor-in-Training | `#6FB3A0` @60% | ✖ | ✖ | R3+ eligible. Queue read. |
| 7 | Lead | `#D4AF37` gold | ✔ | ✔ | R6 |
| 8 | Senior | `#8E6CCF` violet | ✔ | ✔ | R5 |
| 9 | Master | `#8A9BA8` steel | ✔ | ✔ | R4 |
| 10 | Expert | `#D9824A` | ✖ | ✔ | R3 |
| 11 | Adept | `#3D7DD8` blueprint blue | ✖ | ✖ | R2 |
| 15 | Apprentice | `#B5714B` clay | ✖ | ✖ | R1 |
| 16 | Novice | `#7A8C7E` gray-green | ✖ | ✖ | R0 |
| 17 | Oriented / Recruit | no color | ✖ | ✖ | Legacy, removed by the bot. Everyone starts as Novice now. |
| 19 | Major · Level Design … Major · Undecided (8) | no color | ✖ | ✖ | Used for filtering and pings only. |
| 20 | Medal roles | — | — | — | **None.** Medals live in the DB and on the /rank card, not in the role list. |
| 21 | Alumni / Visiting Mentor / Founding Crew | `#A0A0A0` | ✖ | ✖ | Honorary, not XP. |
| 22 | On Leave | `#555555` | ✖ | ✖ | Pauses streak decay and nudges. |

**One visible rank role at a time.** On promotion the Quartermaster removes the old rank role and adds the new one.

Hidden profile roles from onboarding: `Exp · …`, `Code · …`, `Curious · …`, `Goal · …`, `Pace · …`, `Ping · …`.

Nameplate (/rank card and nickname suffix, if enabled): `Novice · Design` (major hint before R3), `Apprentice`,
`Expert · Design`, `Master · Design`, `Senior · Code`, `Lead`.

---

## Permission model

Cumulative access comes from **category overwrites that allow every rank role at or above the unlock rank.** Example: WORLD & LIGHTING
allows Blockout, Adept, all four Expert roles, Master, Senior and Lead. It denies @everyone.
The Quartermaster keeps these overwrites in sync from `config/unlocks.yaml`. Do not hand-edit them after `/admin sync-perms` has run.

### Channel visibility by rank
| Area | Pre-Orient | R0 | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|---|
| GATE | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| HUB, TRAINING | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Starter Quests | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| World & Lighting | — | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Materials, Blueprint | — | — | — | ✔ | ✔ | ✔ | ✔ | ✔ |
| Characters & Anim | — | — | — | — | ✔ | ✔ | ✔ | ✔ |
| systems-cpp | — | — | — | — | peek (code majors, ro) | ✔ (code majors) | ✔ | ✔ |
| systems-art | — | — | — | — | — | ✔ (art majors) | ✔ | ✔ |
| net-gas, shipping | — | — | — | — | — | — | ✔ | ✔ |
| #curriculum-wip | — | — | — | — | — | — | — | ✔ |
| #mentor-queue | — | — | — | — | — | — | read | read+buttons |

### Powers (enforced by the Quartermaster, not Discord permissions)
| Power | R0 | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|
| Showcase tag Blockout | | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Peer-approve submissions of ranks… | | | 0–1 (3/day) | 0–2 | 0–3 | 0–4 | all |
| /critique | | | | ✔ | ✔ | ✔ | ✔ |
| 1.25× XP on quests in your major | | | | ✔ | ✔ | ✔ | ✔ |
| Mentor-in-Training eligible | | | | apply | ✔ | ✔ | ✔ |
| 30-day workshop thread | | | | | ✔ | ✔ | ✔ |
| Author side quests (/curriculum-propose) | | | | | | ✔ | ✔ |
| Host Stage / weekly raid | | | | | | ✔ | ✔ |
| /commend, /title (approved list) | | | | | | | ✔ |

Lead **cannot** ban, kick, manage roles, or use /grant-xp or economy commands. Those stay Mod/Owner only.

### Discord permission bits (per role; everything not listed is off)
| Role | Server-level extras |
|---|---|
| @everyone | View GATE only, Read History, Add Reactions (GATE ro), Use Application Commands |
| Oriented | Send Messages, Send in Threads, Create Public Threads, Attach Files, Embed Links, Connect/Speak in ➕ Join to create and the rooms it makes |
| Master+ | (hoisted) |
| Senior+ | Request to Speak/Speak in Lecture Hall stage, Manage Threads in own track lab |
| Lead | Manage Messages in #showcase and #help-desk (pin/unpin), Priority Speaker |
| Mentor | Manage Threads in tracks, Manage Messages in turn-ins forums |
| Mod | Kick, Timeout, Manage Messages, Manage Threads, View Audit Log |
| Quartermaster | Manage Roles, Manage Channels, Manage Threads, Send Messages, Embed Links, Attach Files, Read History, Add Reactions, Manage Nicknames (optional), Use Application Commands |

---

## Unlock map (source of truth: `bot/config/unlocks.yaml`)
Each rank maps to one role and a list of categories. The Quartermaster reads role and category IDs from that file.
The `/admin bootstrap` command in Phase 2 can create them and write the IDs back.
