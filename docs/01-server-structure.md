# 01 — Server structure (final)

Bot name: **Quartermaster**. It is used in every embed, DM and log line. Proctor, Foreman and Deanbot are retired.
Visual: dark UI. Embeds use `#1E1F22` backgrounds with the rank or Specialty color as the accent bar. Gold is reserved for Studio Lead.

Principle: **a channel exists only when someone at that rank has work to do in it.** The layout is built and repaired by the
bot (`/setup bootstrap`); this page describes it. 21 text/forum channels, 3 voice, 1 stage.

Everything a member can't see yet is listed in **#welcome → "Map: what opens when"**, and `/path` shows what opens next.

## Categories and channels

`[F]` = forum, `[A]` = announcement, `[V]` = voice, `[S]` = stage, `(ro)` = read-only.

| Category | Channels | Who sees it |
|---|---|---|
| 00 · GATE | #welcome (the one start page: how it works, commands, what opens when, help, rules, Start your first quest + Rules quiz buttons), #announcements [A], #patch-notes [A], #epic-games-resources (ro), #rank-ups (ro) | everyone |
| 01 · GUILD HUB | #general, #introductions, #showcase [F], #help-desk [F] (Unreal help + server/bot problems), #suggestions [F] | everyone who accepted the rules |
| 02 · VOICE ROOMS | Studio Floor [V], Pair Program [V] (connect R2+), Critique Room [V] (connect R3+), Lecture Hall [S] (speak: Architect+, Mentor, Mod) | anyone who started Orientation (Recruit) |
| 03 · WORKSHOP | #quest-board (ro, from Orientation), #starter-quests, then one forum per major: #level-design, #environment-art, #tech-art, #gameplay-design, #animation, #programming, #cinematics (everyone reads all; you post in your major's) | quest board from Orientation; each forum at its rank |
| 04 · STAFF | #mod-log (also gets 🐞 bug-report alerts), #curriculum-wip, #mentor-queue | staff (+ Architect read queue, Lead) |

**Workshop forums:** one thread per thing you're building (tags WIP / Help / Done). Every `/submit` is also posted there with the
Turn-in tag so others can see and cheer it. Lessons come through `/quest` cards, not channels.

**Specialty:** at Rank 3 each member picks a Specialty (Design, Environment Art, Anim or Code) matching their major. It sets their title (Specialist · Design). There are no separate Specialty channels; critique happens in #showcase with the Critique-wanted tag.

**Pinned messages:** each channel has at most one pinned bot message. The bot edits it in place when wording changes (`/setup sync-pins`) and deletes any other stray bot posts.
is a private room for `/critique` and specialty work; the `Specialty · X` role keeps it open after Rank 3.

Phase 5 adds systems (R4) and net/GAS + shipping (R5) forums to WORKSHOP; nothing is created early.

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
| 7 | Studio Lead | `#D4AF37` gold | ✔ | ✔ | R6 |
| 8 | Systems Architect | `#8E6CCF` violet | ✔ | ✔ | R5 |
| 9 | Engineer | `#8A9BA8` steel | ✔ | ✔ | R4 |
| 10 | Specialist · Environment Art | `#D9824A` | ✖ | ✔ | R3 Specialty |
| 11 | Specialist · Design | `#4FA36C` | ✖ | ✔ | R3 Specialty |
| 12 | Specialist · Anim | `#C85C8E` | ✖ | ✔ | R3 Specialty |
| 13 | Specialist · Code | `#4AA3B5` | ✖ | ✔ | R3 Specialty |
| 14 | Gameplay Prototyper | `#3D7DD8` blueprint blue | ✖ | ✖ | R2 |
| 15 | Blockout Artist | `#B5714B` clay | ✖ | ✖ | R1 |
| 16 | Greenlit | `#7A8C7E` gray-green | ✖ | ✖ | R0 |
| 17 | Oriented / Recruit | no color | ✖ | ✖ | Recruit = in Orientation (sees Training). Oriented = finished it, kept for life. |
| 19 | Major · Level Design … Major · Undecided (8) | no color | ✖ | ✖ | Used for filtering and pings only. |
| 20 | Medal roles | — | — | — | **None.** Medals live in the DB and on the /rank card, not in the role list. |
| 21 | Alumni / Visiting Mentor / Founding Crew | `#A0A0A0` | ✖ | ✖ | Honorary, not XP. |
| 22 | On Leave | `#555555` | ✖ | ✖ | Pauses streak decay and nudges. |

**One visible rank role at a time.** On promotion the Quartermaster removes the old rank role and adds the new one.
Specialist → Engineer removes `Specialist · X` but keeps `Specialty · X`.

Hidden profile roles from onboarding: `Exp · …`, `Code · …`, `Curious · …`, `Goal · …`, `Pace · …`, `Ping · …`.

Nameplate (/rank card and nickname suffix, if enabled): `Greenlit · Design` (major hint before R3), `Blockout Artist`,
`Specialist · Design`, `Engineer · Design`, `Architect · Code`, `Studio Lead`.

---

## Permission model

Cumulative access comes from **category overwrites that allow every rank role at or above the unlock rank.** Example: WORLD & LIGHTING
allows Blockout, Prototyper, all four Specialist roles, Engineer, Architect and Lead. It denies @everyone.
The Quartermaster keeps these overwrites in sync from `config/unlocks.yaml`. Do not hand-edit them after `/admin sync-perms` has run.

### Channel visibility by rank
| Area | Pre-Orient | R0 | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|---|
| GATE | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| HUB, TRAINING | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Foundations | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| World & Lighting | — | — | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Materials, Blueprint | — | — | — | ✔ | ✔ | ✔ | ✔ | ✔ |
| Characters & Anim | — | — | — | — | ✔ | ✔ | ✔ | ✔ |
| systems-cpp | — | — | — | — | peek (Code seal, ro) | ✔ (code majors) | ✔ | ✔ |
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
| 1.25× XP in-Specialty | | | | ✔ | ✔ | ✔ | ✔ |
| Mentor-in-Training eligible | | | | apply | ✔ | ✔ | ✔ |
| 30-day workshop thread | | | | | ✔ | ✔ | ✔ |
| Author side quests (/curriculum-propose) | | | | | | ✔ | ✔ |
| Host Stage / weekly raid | | | | | | ✔ | ✔ |
| /commend, /title (approved list) | | | | | | | ✔ |

Studio Lead **cannot** ban, kick, manage roles, or use /grant-xp or economy commands. Those stay Mod/Owner only.

### Discord permission bits (per role; everything not listed is off)
| Role | Server-level extras |
|---|---|
| @everyone | View GATE only, Read History, Add Reactions (GATE ro), Use Application Commands |
| Oriented | Send Messages, Send in Threads, Create Public Threads, Attach Files, Embed Links, Connect/Speak in Studio Floor |
| Prototyper+ | Connect Pair Program |
| Specialist+ | Connect Critique Room |
| Engineer+ | (hoisted) |
| Architect+ | Request to Speak/Speak in Lecture Hall stage, Manage Threads in own track lab |
| Studio Lead | Manage Messages in #showcase and #help-desk (pin/unpin), Priority Speaker |
| Mentor | Manage Threads in tracks, Manage Messages in turn-ins forums |
| Mod | Kick, Timeout, Manage Messages, Manage Threads, View Audit Log |
| Quartermaster | Manage Roles, Manage Channels, Manage Threads, Send Messages, Embed Links, Attach Files, Read History, Add Reactions, Manage Nicknames (optional), Use Application Commands |

---

## Unlock map (source of truth: `bot/config/unlocks.yaml`)
Each rank or Specialty maps to one role and a list of categories. The Quartermaster reads role and category IDs from that file.
The `/admin bootstrap` command in Phase 2 can create them and write the IDs back.
