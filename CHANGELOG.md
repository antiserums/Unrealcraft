# Changelog

Newest first. A version is **released** when its tag (e.g. `v0.2.0`) is pushed to GitHub. The Quartermaster checks
GitHub every minute and posts each newly released entry to #patch-notes, one message per version, so the channel
keeps the full history. To fix a mistake in a released entry, edit it and push; the Quartermaster
updates that version's existing message instead of posting a new one.

Format: `## vMAJOR.MINOR.PATCH.BUILD · YYYY-MM-DD`, then a plain list of changes. No titles or summaries.

A version has four numbers, the way an Unreal Engine build carries a changelist number (`py -3 tools/version.py next minor` prints the next one):
- **MAJOR** (v1.0.0 → v2.0.0): breaking for members: progress reset, ranks or XP rebalanced, commands removed or renamed.
- **MINOR** (v1.2.0 → v1.3.0): new things that don't break anything: quests, channels, commands, features.
- **PATCH** (v1.2.3 → v1.2.4): fixes only: typos, links, bugs, wording.
- **BUILD** (v1.2.3.**700**): the number of commits in the repo at that release. It only ever goes up.
  Releases before v0.11 have no build number.
- While MAJOR is **0**, Unrealcraft is pre-release and anything may still change between MINOR versions.
  **v1.0.0** marks the official public launch.

## v0.10.1 · 2026-09-29
- **Start quiz** now goes straight to question 1. No second Start quiz button.
- **Open the guide** is on every quiz question, so the reading is always one tap away.
- Quizzes are shown as colored cards: the question, ✅ Correct / ❌ Not quite, and your result.

## v0.10.0 · 2026-09-29
- New voice rooms: join **➕ Join to create** and the Quartermaster makes a room just for you and moves you in.
- Rename your room or set a user limit with the buttons in its chat, or type `/room rename` / `/room limit`.
- If you leave your room, it passes to someone still inside. A room is deleted after 5 minutes with nobody in it.
- Studio Floor, Pair Program and Critique Room are gone. Rank 2 now opens peer reviews; Rank 3 opens your Specialty title and `/critique`.
- The Orientation voice step counts 1 minute in any voice room.
- VOICE ROOMS is now **TOWN HALL**, and it sits below the quests.
- WORKSHOP is now **QUEST BOARD**. #quest-board is now **#quest-log**.
- The Workshop forums are now called your major forums.

## v0.9.1 · 2026-09-29
- The rules are rewritten in plain, friendly English. **Be kind** is now rule 1. Nothing new is required of you.

## v0.9.0 · 2026-09-29
- Quests can now link hand-picked free guides from the community, not only Epic's docs. They show after the Epic links.
- Rule 7 is now **Good sources only**: Epic docs plus hand-picked free community guides. Still no pirated or re-hosted paid courses.
- #quest-board and #epic-games-resources no longer say the reading is official Epic docs only.

## v0.8.0 · 2026-09-29
- Your public Turn-in post now shows the result: passed, changes requested or not passed.
- Review results and mentor notes are posted in your turn-in thread (with a **Send my work again** button) as well as by DM.
- Every 5th Rank 0–1 turn-in gets a quick spot check from a mentor. A flag only sends you a kind note; you keep your XP.
- #mentor-queue cards close once they are reviewed, and a pinned guide explains how the queue works.
- Pinned messages in #quest-board, #help-desk, #showcase, #mentor-queue, #epic-games-resources and every Workshop forum now use short colored cards, like #welcome.

## v0.7.0 · 2026-09-29
- Starter Quests are numbered **Q1–Q11** (were S1–S11). Your progress carried over.
- Workshop forums are named for the majors: #level-design, #environment-art, #tech-art, #gameplay-design, #animation, #programming, #cinematics.
- #foundations is now #starter-quests. The old #world-lighting, #materials, #blueprint and #characters-anim forums are gone.
- Everyone can read every major forum after Orientation. You can post in #starter-quests and in the forums of the majors you picked.
- Turn-ins are posted to #starter-quests (Starter Quests) or your major's forum.
- Rank-ups now unlock the Blockout showcase tag (Rank 1), Pair Program voice (Rank 2) and the Critique Room plus your Specialty title (Rank 3).
- **Send my work** form: a separate field for your Unreal version, clear instructions for what to write, and an upload box that says exactly what to upload (up to 4 files).
- Removed the **I found it** button from #quest-board. Pressing **Continue your quest** there completes that Orientation step.
- The #welcome button is now **Start Questing**.

## v0.6.1 · 2026-09-29
- Channel names in quests and quizzes (like #welcome) are now clickable links.
- S1 question 5 points to the server rules in #welcome.

## v0.6.0 · 2026-09-29
- After Orientation, quests only work in #quest-board: `/quest`, `/quiz`, `/submit` and the quest buttons.
- Using them anywhere else shows a **Go to #quest-board** button.
- Orientation still happens in #welcome. `/rank`, `/path`, the help desk and Workshop posts work anywhere.
- The Orientation done page, the #welcome button, the Greenlit message, #welcome and #quest-board all explain this.

## v0.5.0 · 2026-09-29
- Orientation is 6 steps. Removed **Ask a question** and **Cheer someone's work**.
- Every step and screen has a button to the next thing, so you never need to type a command (typing still works).
- The #welcome button is now **Start / continue your quest** and always takes you to your next step.
- Orientation buttons: rules quiz, a dropdown to pick what to learn, Show my rank / next quest / path, open #quest-board, a practice-send form, join voice or skip.
- After Orientation your quests are in #quest-board. Its pinned message has a **Continue your quest** button, and commands work there.
- Quest cards start with the reading (Step 1), then what to do in Unreal (Step 2), then how to finish (Step 3).
- Quest cards have **Open the guide**, **Start quiz**, **Send my work** (a form with file upload) and **Next quest** buttons.
- Quizzes show the guide and a **Start quiz** button before the first question. A failed quiz shows **Try again** and the guide.
- While the server has fewer than 20 members, quests that need other people (peer review, critique, playtests) are hidden or optional.
- Server admins can review turn-ins.
- Patch notes are just the version, date and list of changes.

## v0.4.0 · 2026-09-29
- The Orientation page updates by itself when you finish a step (for 15 minutes after you open it).
- Renamed **Lookdev / Env Art** to **Environment Art** (major and Rank 3 Specialty). Existing roles were renamed.
- Fixed: finishing a quest stopped before checking for Orientation completion and promotions. XP was always saved.

## v0.3.2 · 2026-09-29
- #welcome has one green button that opens the rules quiz, your first quest.
- After passing the quiz, a **See my next steps** button opens the rest of Orientation.
- `/start` does the same as the button.

## v0.3.1 · 2026-09-29
- Orientation step 1 is only the rules quiz.
- Replaced a confusing rules quiz question with a clearer one.
- Quest cards say exactly how to finish: quiz only, automatic, or quiz then `/submit`.

## v0.3.0 · 2026-09-29
- Merged #how-this-place-works into #welcome: one page with what Unrealcraft is, how to start, the 5 commands, what opens at each rank, help and the rules.
- Commands like `/start` and `/quiz` work in #welcome. It is commands-only; chat goes in #general.
- New Orientation page: progress bar, a Next step, one short line per step, and buttons for the rules quiz and skipping voice.
- Orientation steps and the rules quiz rewritten in plain English with simpler names.
- #quest-board button renamed to **I found it**.

## v0.2.0 · 2026-09-29
- Join question **What do you want to learn in Unreal?** accepts several answers.
- With several answers, the Quartermaster DMs buttons to choose your main path (major). The others count as interests.
- Join question **What are your goals?** accepts several answers.
- Quests from your interests are suggested first and move up your `/path` shelf.
- Suggestions take all your goals into account.

## v0.1.0 · 2026-09-29
- Server layout: GATE (#welcome, #how-this-place-works, #announcements, #patch-notes, #epic-games-resources, #rank-ups), Guild Hub (#general, #introductions, #showcase, #help-desk, #suggestions), Voice Rooms (Studio Floor, Pair Program, Critique Room, Lecture Hall), Workshop (#quest-board and track forums) and Staff.
- Workshop forums that open by rank: #foundations, #world-lighting, #materials, #blueprint, #characters-anim.
- 55 roles: 7 ranks, 4 Specialist titles, 8 majors, staff, ping and hidden profile roles.
- Rules Screening with 8 rules, welcome screen and AutoMod.
- One pinned guide per channel, edited in place when it changes.
- Join questions (what you want to learn, experience, coding, interests, goals, weekly time, pings) that shape your path: test-outs, tasters, suggestions and a time estimate.
- Orientation (8 steps), ticked automatically when the bot sees you do each one.
- Starter Quests: 11 quests from installing UE5 to a first room, light, material, Blueprint and C++ awareness.
- Level Design path through Rank 3 with quizzes; Programming and Lookdev paths drafted; cross-major tasters.
- Every quest links official Epic Games documentation, checked against the UE 5.8 docs.
- Quiz answers shuffled on every attempt.
- Checklists show what the bot saw and what's left; screenshots, clips, links and writeups are checked on `/submit`.
- Commands: `/start`, `/quest`, `/quiz`, `/submit`, `/rank`, `/path`, `/major`, `/minor`, `/profile`, `/post`, `/where`, `/help-server`, `/tree`, `/skip-voice`, `/skip-elective`.
- **New post** form in Workshop forums; turn-ins are posted to the track forum automatically.
- Ranks: Greenlit → Blockout Artist → Gameplay Prototyper → Specialist → Engineer → Systems Architect → Studio Lead. Promotions need XP and a capstone; chat gives no XP.
- Promotions swap your rank role, open channels, send a DM, post in #rank-ups and award a medal.
- Rank 3 Specialty (Design, Lookdev, Anim or Code) sets your title.
- Rank 2+ turn-ins go to peer or mentor review.
- #help-desk with **Unreal help** and **Server / bot problem** forms; bug reports alert staff.
- Patch notes posted here for every release pushed to GitHub, using semantic versioning.
