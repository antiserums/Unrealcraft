# 05 — /path mocks: Level Design Greenlit vs Programming Greenlit

Both members joined the same day, finished Orientation, and have done S1–S6 of the Starter Quests.
The output below was worked out by hand from `Catalog.path_lines()` against the current YAML. Orientation is hidden once it's complete.

## Level Design · Greenlit
```
STARTER QUESTS (everyone)
  ✔ S1         Install the engine
  ✔ S2         Blank vs Third Person
  ✔ S3         Fly the viewport
  ✔ S4         A tidy Content Drawer
  ✔ S5         Move things on purpose
  ✔ S6         Graybox a room
  ▶ S7         One readable lighting pass
  · S8         One material instance
  · S9         One Blueprint interact
  · S10        Walk your space
  · S11        What C++ is for
🔒 RANK 1 · BLOCKOUT ARTIST · Level Design: needs 650 XP + Starter Quests
  🔒 R1-LD-01   Build a metrics gym
  🔒 R1-LD-02   Blockout toolkit
  🔒 R1-LD-03   Three routes
  🔒 R1-LD-04   Sightlines and landmarks
  🔒 … 7 more
  🔒 taster: R1-WL-09 Foliage that doesn't block routes
  ★ capstone: Three-route courtyard
◇ OPTIONAL SHELF: other majors' work. Nothing here gates you. It opens by rank.
  ◇ Tasters                    R1–2   4 quests
  ◇ Lookdev / Environment Art  R1–3   20 quests
  ◇ Programming                R1–3   19 quests
  ◇ Animation                  R3     5 quests
```
Nothing in this member's required path involves C++. They see C++ only as S11 (a 15-minute read), one Rank 2 taster
(`T-CPP-HELLO` or `T-GAS-VIDEO`, their choice), and the Programming entry on the optional shelf.

## Programming · Greenlit
```
STARTER QUESTS (everyone)
  ✔ S1         Install the engine
  ✔ S2         Blank vs Third Person
  ✔ S3         Fly the viewport
  ✔ S4         A tidy Content Drawer
  ✔ S5         Move things on purpose
  ✔ S6         Graybox a room
  ▶ S7         One readable lighting pass
  · S8         One material instance
  · S9         One Blueprint interact
  · S10        Walk your space
  · S11        What C++ is for
🔒 RANK 1 · BLOCKOUT ARTIST · Programming: needs 650 XP + Starter Quests
  🔒 R1-PR-01   Debug room toolkit
  🔒 R1-PR-02   Output Log and the Blueprint debugger
  🔒 R1-PR-03   Read the Third Person template
  🔒 R1-PR-04   A tiny test-harness level
  🔒 taster: R1-LD-T1 Walk-and-note a courtyard
  ★ capstone: Debug room
◇ OPTIONAL SHELF: other majors' work. Nothing here gates you. It opens by rank.
  ◇ Level Design               R1–3   26 quests
  ◇ Lookdev / Environment Art  R1–3   21 quests
  ◇ Tasters                    R2     4 quests
  ◇ Animation                  R3     5 quests
```
The programmer's only lighting work is S7, which everyone does, and `T-LIGHT-PASS` at Rank 2 (one pass on their own loop).
There is no hero lighting reel and no courtyard capstone. The Level Design courtyard is a 25-minute walk-and-note taster.

## What `/quest` says to each right now
Both get **S7** because the Starter Quests come before major work. The `Why this one:` footer reads "Starter Quests", and the flavor lines differ:
- LD: *"Light is how you tell players where to go."*
- Programming: *"Readable is enough. You owe one more pass at Rank 2, on your own loop, and that's it."*
