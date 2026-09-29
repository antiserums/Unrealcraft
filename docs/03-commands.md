# 03 — Commands and data

Slash commands only. No prefix commands and no message-content intent except for reading the #help-desk template (see below).

## User
| Command | Rank | Does |
|---|---|---|
| /start | any | Opens the Orientation embed (O1–O8 checklist with live ticks). Idempotent. |
| /help-server | any | Short manual: the loop, 5 commands, where to ask. |
| /where `thing` | any | Autocomplete: submit, ask for help, see my rank, find C++, showcase, change major. Replies with a channel link or command and one sentence. |
| /major `major` | any | Set major. Free once before R3; after that, starts a respec (4 quests). |
| /minor `major` | R3+ | Optional second focus. Earns a medal. It is not a ladder. |
| /path | any | Personal tree: ✔ done, ▶ now, 🔒 locked-for-rank, ◇ optional shelf. |
| /quest `[id]` | any | No arg: the picker's next quest + 2 electives + 1 adjacent. With id: that quest's embed. |
| /quiz `id` | any | Ephemeral quiz, one question per step, with buttons. |
| /submit `id` `proof` `[attachment]` | any | Creates a submission and routes it by verify_type/rank. 2h cooldown per quest after a Fail. |
| /rank `[member]` | any | Rank card: major, seal, XP bar, streak, next unlock, medals. |
| /tree | any | The full catalog as ranks × tracks. Same for everyone, no personalization. |
| /leaderboard `[scope]` | any | Weekly XP (quests only), by major or server-wide. |
| /profile `[ue_version]` | any | Show or set profile fields. |
| /post `[forum]` | R0+ | Opens the New post dialog (title, WIP/Help/Done, quest, details with engine version, up to 4 files) for a Workshop forum you have unlocked. Also a **New post** button on each forum's pinned intro. |
| /skip-voice | Orientation | Completes O7 without voice. |
| /room rename `name` · /room limit `n` | owner of a voice room | Rename your join-to-create voice room or cap how many can join (0 = no limit). Same as the buttons in the room's chat. |
| /skip-elective `id` | any | Hides an elective from /quest suggestions. |
| /critique `link` `question` | R3+ | Opens a #showcase post tagged Critique-wanted and pings people with the same Specialty. |

## Mentor / reviewer
| Command | Who | Does |
|---|---|---|
| /mentor-review `submission` `verdict` `[notes]` | Mentor, Lead, eligible peers | Pass / Changes / Fail. These are also buttons on the queue embed. |

## Staff
| Command | Who | Does |
|---|---|---|
| /grant-xp `member` `amount` `reason` | Mod | Logged to #mod-log and xp_log. Never auto. |
| /curriculum-add `yaml_attachment` | Curriculum | Validate and upsert quests. Dry-run by default. |
| /curriculum-propose-publish `proposal_id` | Curriculum | Promote an Architect's proposal. |
| /commend `member` `note` | Lead+ | +medal Teacher progress / a public note. No XP. |
| /raid `start/end` `quest_id` | Architect+, Staff | Weekly raid. |
| /admin bootstrap · sync-perms · reload-curriculum | Owner | Phase 2 setup helpers. |

## Architect+
| /curriculum-propose `yaml_attachment` | Architect+ | Drafts to #curriculum-wip. |

## How checklists are verified
Each checklist line in the YAML can have a `check:` (engine: `bot/registrar/checks.py`). `/quest` and `/start` show:
✅ the bot saw it · ☐ not yet · 📎 checked when you /submit · ▫ honor (only for work done inside Unreal).

| Check | Seen when | Used by |
|---|---|---|
| `fact: rules.accepted` | Rules Screening "I've read and agree" (member stops being *pending*) | O1 (+ /start is blocked until then) |
| `fact: quiz.<ID>` | quiz passed | O1 |
| `fact: cmd.major / cmd.rank / cmd.quest / cmd.path / cmd.profile_version / cmd.skip_voice` | slash command used | O2, O3, O7, O-E1 |
| `fact: btn.clockin` | pinned button pressed | O4 |
| `fact: submit.O5` | `/submit O5 READY` | O5 |
| `fact: thread.help_desk` | post created through the **Unreal help** or **Server / bot problem** form | (recorded; no step uses it now) |
| `any: [voice.studio_floor, cmd.skip_voice]` | 60 s in any voice room | O7 |
| `fact: react.showcase` | reaction on someone else's showcase post | O8 |
| `fact: msg.<channel>` | any message in that channel (author + channel only, no Message Content intent) | O-E3 |
| `fact: nick.major` | nickname contains `|` | O-E2 |
| `attachment: image / video` | file attached on /submit (content type checked) | screenshot quests (default), R0-META-01/02 |
| `min_length: N` | proof text length | writeup quests (default 80), META-03, R0-E-06 |
| `link: showcase, on: others / own` | pasted message link is fetched: right server, right channel, your message, someone else's (or your own) post | R0-META-04/05 |

Quests whose every line is a `fact` check complete themselves; there is nothing to press. `/submit` is refused while any ✅-type line is still ☐.
Reading can't be observed by Discord, so reading is proven by the quiz.

## Routing a /submit
| Rank of quest | verify_type | Route |
|---|---|---|
| −1 | action | auto |
| 0–1 | quiz | auto on quiz pass |
| 0–1 | screenshot/writeup | honor system: auto-Pass, logged, spot-checkable |
| 2 | any | peer (R2+, cap 3/day) **or** mentor in #mentor-queue |
| 3–4 | any | mentor **or** two peer Approves (peers of rank ≥ quest rank) |
| 5–6 | any | human mentor only. Architect/Lead promotions also need staff sign-off, plus 2 vouchers for Lead. |

A capstone Pass triggers `check_promotion()`, which promotes only if XP ≥ threshold **and** every required quest and taster for the rank is done.

## SQLite schema
See `bot/db/schema.sql`. Tables: users, quests, submissions, unlocks, xp_log, medals, quest_progress, quiz_attempts, raids, review_actions, kv.
The brief listed the first six. The rest are the minimum the commands above need, for example the per-user completion state, the peer-review
daily cap and the submit cooldown.
