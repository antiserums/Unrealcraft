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

## v0.4.0 · 2026-09-29 · Live Orientation page
The Orientation page now updates by itself, plus an important fix.

### Orientation
- While the Orientation page is open, it updates the moment you finish a step: the progress bar, the ✅ marks, the 👉 Next step and the buttons. (Discord allows this for 15 minutes; press the green button in #welcome for a fresh page.)

### Names
- **Lookdev / Env Art** is now called **Environment Art**, both as a major and as a Rank 3 Specialty. If you already had the role, it was renamed for you.

### Fixes
- Fixed a bug where finishing a quest stopped halfway. Your XP was saved, but the bot never checked if you had finished Orientation or earned a promotion. Nobody lost progress.

## v0.3.2 · 2026-09-29 · Start your first quest
One clear button to begin.

### #welcome
- The page now has one green button: **⚔️ Start your first quest**. It opens the rules quiz, which is your first quest.
- After you pass, press **🧭 See my next steps** to see the rest of Orientation. The green button shows your steps from then on.
- `/start` does the same thing as the button.

## v0.3.1 · 2026-09-29 · Clearer first step
Small fixes to make the first step easier.

### Orientation
- Step 1 is now **only the rules quiz**. Pass it and the step is done.
- One rules quiz question was confusing. It asked which answer is *not* allowed. It now asks for the **good** answer.

### Quests
- Quest cards now say exactly how to finish a quest: pass the quiz only, the bot ticks it for you, or quiz then `/submit`.

## v0.3.0 · 2026-09-29 · Easier start
Starting out is now simpler and easier to read, including for people who don't speak English as a first language.

### #welcome is the one start page
- #how-this-place-works is merged into #welcome. One page, short sentences: what Unrealcraft is, 3 steps to start, the 5 commands, what opens at each rank, where to get help, and the rules.
- Buttons on the page: **Start Orientation** and **📝 Rules quiz**, so you don't need to type to begin.
- You can now use commands like `/start` and `/quiz O1` in #welcome. It stays a commands-only channel; please chat in #general.

### Orientation
- New Orientation page: a progress bar, a **👉 Next** step, and one short line per step.
- Buttons for the steps you can do with a click: **Rules quiz** and **Skip voice**.
- All 8 steps are rewritten in plain English, with simpler names (e.g. **Try 3 commands**, **Practice sending work**, **Visit voice chat**).
- The rules quiz uses simpler questions.
- On #quest-board the button is now called **I found it**.

## v0.2.0 · 2026-09-29 · Pick more than one answer
Joining now lets you tell us everything you're into, not just one thing.

### Join questions
- **What do you want to learn in Unreal?** now accepts several answers.
- If you pick more than one, the Quartermaster DMs you buttons to choose your **main path** (your major). The others stay as interests.
- **What are your goals?** (on Channels & Roles) now accepts several answers too, e.g. a job in games *and* making your own game.
- Experience, coding and weekly time stay single-answer, since only one can be true.

### Your path
- Quests from your other interests are suggested first in `/quest` and move up your `/path` shelf.
- Suggestions blend all your goals: career picks favour portfolio and critique quests, indie picks favour playable ones.

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
