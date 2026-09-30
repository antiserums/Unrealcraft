# 05 — /path mocks: Level Design Novice vs Programming Novice

> **Superseded (2026-09-30).** This describes the older design where the game was played in Discord. The website now runs quests, reviews and ranks; the Discord server is a guild hall. See `03-commands.md`, `04-discord-setup-checklist.md` and `07-website.md`. Kept for history.

Both members joined the same day, finished the first steps (O1–O5), and have done SQ1–SQ6 of the Starter Quests.
The output below was worked out by hand from `Catalog.path_lines()` against the current YAML. The first steps are hidden once they are complete.

## Level Design · Novice
```
STARTER QUESTS (everyone)
  ✔ SQ1         Install the engine
  ✔ SQ2         Blank vs Third Person
  ✔ SQ3         Fly the viewport
  ✔ SQ4         A tidy Content Drawer
  ✔ SQ5         Move things on purpose
  ✔ SQ6         Graybox a room
  ▶ SQ7         One readable lighting pass
  · SQ8         One material instance
  · SQ9         One Blueprint interact
  · SQ10        Walk your space
  · SQ11        What C++ is for
🔒 RANK 1 · BLOCKOUT ARTIST · Level Design: needs 650 XP + Starter Quests
  🔒 LDQ11   Build a metrics gym
  🔒 LDQ12   Blockout toolkit
  🔒 LDQ13   Three routes
  🔒 LDQ14   Sightlines and landmarks
  🔒 … 7 more
  🔒 taster: EAQ11 Foliage that doesn't block routes
  ★ capstone: Three-route courtyard
◇ OPTIONAL SHELF: other majors' work. Nothing here gates you. It opens by rank.
  ◇ Tasters                    R1–2   4 quests
  ◇ Environment Art            R1–3   20 quests
  ◇ Programming                R1–3   19 quests
  ◇ Animation                  R3     5 quests
```
Nothing in this member's required path involves C++. They see C++ only as SQ11 (a 15-minute read), one Rank 2 taster
(`PQ17` or `PQ18`, their choice), and the Programming entry on the optional shelf.

## Programming · Novice
```
STARTER QUESTS (everyone)
  ✔ SQ1         Install the engine
  ✔ SQ2         Blank vs Third Person
  ✔ SQ3         Fly the viewport
  ✔ SQ4         A tidy Content Drawer
  ✔ SQ5         Move things on purpose
  ✔ SQ6         Graybox a room
  ▶ SQ7         One readable lighting pass
  · SQ8         One material instance
  · SQ9         One Blueprint interact
  · SQ10        Walk your space
  · SQ11        What C++ is for
🔒 RANK 1 · BLOCKOUT ARTIST · Programming: needs 650 XP + Starter Quests
  🔒 PQ1   Debug room toolkit
  🔒 PQ2   Output Log and the Blueprint debugger
  🔒 PQ3   Read the Third Person template
  🔒 PQ4   A tiny test-harness level
  🔒 taster: LDQ19 Walk-and-note a courtyard
  ★ capstone: Debug room
◇ OPTIONAL SHELF: other majors' work. Nothing here gates you. It opens by rank.
  ◇ Level Design               R1–3   26 quests
  ◇ Environment Art            R1–3   21 quests
  ◇ Tasters                    R2     4 quests
  ◇ Animation                  R3     5 quests
```
The programmer's only lighting work is SQ7, which everyone does, and `EAQ22` at Rank 2 (one pass on their own loop).
There is no hero lighting reel and no courtyard capstone. The Level Design courtyard is a 25-minute walk-and-note taster.

## What `/quest` says to each right now
Both get **SQ7** because the Starter Quests come before major work. The `Why this one:` footer reads "Starter Quests", and the flavor lines differ:
- LD: *"Light is how you tell players where to go."*
- Programming: *"Readable is enough. You owe one more pass at Rank 2, on your own loop, and that's it."*
