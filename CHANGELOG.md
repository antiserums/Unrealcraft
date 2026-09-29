# Changelog

Newest first. A version is **released** when its tag (e.g. `v0.2.0`) is pushed to GitHub. The Quartermaster checks
GitHub every minute and posts each newly released entry to #patch-notes, one message per version, so the channel
keeps the full history. To fix a mistake in a released entry, edit it and push; the Quartermaster
updates that version's existing message instead of posting a new one.

Format: `## vMAJOR.MINOR.PATCH · YYYY-MM-DD · Short title`, an optional one-line summary, then `### Section`
headings with bullet points (each section becomes a block in the Discord post; keep each under ~1000 characters).

Versions follow [Semantic Versioning](https://semver.org):
- **MAJOR** (v1.0.0 → v2.0.0): breaking for members: progress reset, ranks or XP rebalanced, commands removed or renamed.
- **MINOR** (v1.2.0 → v1.3.0): new things that don't break anything: quests, channels, commands, features.
- **PATCH** (v1.2.3 → v1.2.4): fixes only: typos, links, bugs, wording.
- While MAJOR is **0**, Unrealcraft is pre-release and anything may still change between MINOR versions.
  **v1.0.0** marks the official public launch.

## v0.1.0 · 2026-09-29 · First release
Everything built for the first version of Unrealcraft and its bot, the Quartermaster.

### Server
- Built the full server layout: **GATE** (#welcome, #how-this-place-works, #announcements, #patch-notes, #epic-games-resources, #rank-ups), **Guild Hub** (#general, #introductions, #showcase, #help-desk, #suggestions), **Voice Rooms** (Studio Floor, Pair Program, Critique Room, Lecture Hall stage), **Workshop** (#quest-board plus one forum per track) and **Staff**.
- Workshop forums open by rank: #foundations (Greenlit), #world-lighting (Blockout Artist), #materials and #blueprint (Gameplay Prototyper), #characters-anim (Specialist).
- 55 roles: 7 ranks with colors, 4 Specialist titles, 8 majors, staff roles, ping roles and hidden profile roles.
- Community features on: Rules Screening with the 8 server rules, welcome screen, AutoMod (mention spam, flagged words, spam, with alerts to staff).
- Every channel has at most one pinned guide from the Quartermaster, edited in place when it changes.

### Joining and Orientation
- Join questions: what you want to learn (sets your major), your Unreal experience, whether you code, what you're curious about, plus goal, weekly time and pings on the Channels & Roles page.
- The Quartermaster uses your answers: experienced members can **test out** of Starter Quests, non-coders get a non-C++ taster, curiosities decide which extra quests are suggested, and your weekly time gives an estimate for your next rank.
- **Orientation** (8 steps) teaches the server before Unreal. Every step is ticked automatically when the bot sees you do it, including accepting the rules.

### Quests and curriculum
- **Starter Quests**: 11 quests everyone does, from installing UE5 to a first room, light, material, Blueprint and C++ awareness.
- **Level Design** path fully written through Rank 3 with 5-question quizzes; **Programming** and **Lookdev** paths drafted; cross-major tasters.
- Every quest links official Epic Games documentation, checked against the live UE 5.8 docs.
- Quiz answers are shuffled on every attempt.
- Checklists show ✅ what the bot saw, ☐ what's left and 📎 what's checked on submit; screenshots, clips, message links and writeups are verified when you `/submit`.

### Commands
- `/start`, `/quest`, `/quiz`, `/submit`, `/rank`, `/path`, `/major`, `/minor`, `/profile`, `/post`, `/where`, `/help-server`, `/tree`, `/skip-voice`, `/skip-elective`.
- **New post** form in every Workshop forum (title, WIP/Help/Done, quest, details, up to 4 files); turn-ins are posted to the track forum automatically.

### Ranks and reviews
- Greenlit → Blockout Artist → Gameplay Prototyper → Specialist → Engineer → Systems Architect → Studio Lead. Promotions need XP **and** your major's capstone; chat never earns XP.
- Promotions swap your rank role, open new channels, send a briefing DM, post a card in #rank-ups and award a medal.
- At Rank 3 you pick a **Specialty** (Design, Lookdev, Anim or Code) for your title.
- Rank 2+ turn-ins go to peer or mentor review with Pass / Changes / Fail.

### Help and updates
- #help-desk: **🛠️ Unreal help** and **🐞 Server / bot problem** forms; bug reports include the bot version and alert staff.
- Patch notes: every release pushed to GitHub is posted here, versioned with semantic versioning.
