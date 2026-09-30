# Art pack integration (UCSourceArt / pixel-v3)

The art lives in a separate folder, `UCSourceArt`, produced by another AI. The website consumes it; it never
generates art. This page is the contract between the two: what the site expects, where it looks, and which IDs it
needs. The pack's own rules are in `UCSourceArt/pixel-v3/INTEGRATION.txt` and `environments/AI-HANDOFF.txt` and
are followed as written: nearest-neighbour sampling, integer scales, the 480 x 270 arena drawn at 2x.

## How art reaches the site

```bash
py -3 tools/sync_art.py            # pack assumed at ../UCSourceArt (its pixel-v3 folder); or pass a path
```

The script copies the exports into `web/public/art/` (git-ignored, about 5 MB) and writes
`web/public/art/manifest.json`. The site reads the manifest on each request (cached 10 s). With no manifest every
figure falls back to the built-in flat SVG silhouettes, so nothing breaks. Re-run the script after every drop.

## What the pack ships and how the site uses it

**Characters.** 32 pre-rendered sprite sheets: 2 bodies x 8 sets x 2 equipment styles. Each sheet is 4 x 6
frames of 128 px: idle, attack, cast, hit, victory, defeat. The site picks the sheet from the member's body,
worn set and style (`GET /api/me/character` -> `body`, `worn.art_id`, `style`) and plays rows with
`components/Sprite.tsx`. The body occupies 64 x 96 px at (32, 12) of the frame, so cards and the wardrobe crop
to a tighter window (`HERO_CROP` in `Figure.tsx`); the fight draws the full frame so swings stay in view.

**Outfit sets.** The pack's eleven sets are the whole catalog (`api/app/rpg.py`, `build_sets`):
`novice` (starter), `apprentice`, `adept`, `expert`, `master` (rank 1 to 4, shared by every major), three
reward sets: `warrior` Ironwarden (first capstone cleared), `ranger` Thornwatch (fifty quests), `spellcaster`
Runekeeper (ten bosses beaten first try), and three exclusive sets (unlock type `staff`): `developer`
Sourceforged Sovereign, `admin` Sunforged Arbiter, `mentor` Astral Guide. Admins and developers own everything;
mentors own only the mentor set. The matching `admin`, `mentor` and `developer` avatar and card decorations
unlock the same way and glow in the role's nameplate colour. Set ids are the art ids. The wardrobe tile icon is the set's chest
piece (`gear/icons/set_<set>_chest.png`, 32 px).

**Equipment style.** `melee` (sword + shield) or `caster` (staff + orb), chosen in the wardrobe and saved as
`cosmetics.style`. In a fight a right answer plays `attack` for melee and `cast` for caster.

**Appearance.** Only the body (`body_a` Athletic, `body_b` Curved) is selectable. The exported sheets have a fixed
face, skin and hair; skin tones, hairstyles, faces and markings need the pack's compositing renderer
(`previews/renderer.js`) ported to the site, which is a later step.

**Creatures.** Six enemies (4 x 4 frames of 64 px: idle, attack, hit, defeat) drawn at 3x, three bosses (4 x 6
frames of 128 px: idle, attack, special, hit, taunt, defeat) drawn at 2x. Ordinary rooms use enemies, capstones
use bosses; the pick comes from the quest's subject (`ENEMY_FOR_LOOK`, `capstone_creature` in `rpg.py`).

**Arena.** `environments/dungeon-training-chamber-480x270.png` (and the 1920 x 1080 version) is the fight
background. The stage is a fixed 960 x 540 scene scaled down to fit its column: hero at (96, 256), boss on the
right, feet on the ground line y = 464 (232 x 2), health boxes in the top 15 percent, as the handoff suggests.

**Profile decorations.** `profile-decorations/avatar/NN-<theme>.png` (48 px rings, transparent centre) and
`profile-decorations/card/NN-<theme>.png` (352 x 252 borders with the card in the centre 320 x 220) for ten
themes: novice, apprentice, adept, expert, master, thornwood, emberforge, frostbound, celestial, dragonheart.
Exact rules are in `docs/09-playercard-art-spec.md`. The card sits in a constant 32 px gutter; the border is a
CSS 9-slice (`.pcard-deco`, corners 44 px) that fades in, and the ring overlays the avatar (`.deco-avatar`). The
same unlock rule opens a theme's ring and border (`DECORATIONS` in `rpg.py`).

**Badges and rarity.** Eight badges in `ui/badges/` are mapped to achievements by the `badge` index in
`ACHIEVEMENTS` (`rpg.py`); they show on the achievements page and the player card. Rarity frames in `ui/rarity/`
are copied but the site still draws rarity as a coloured frame.

## Manifest shape (version 3)

```
presets[body][set][style] = { sheet, frame: 128, columns: 4, animations: [{id,row,frames,fps,loop}] }
creatures[id]             = { sheet, kind, frame: 64|128, columns: 4, animations: [...] }
icons[set]                = "gear/icons/set_<set>_chest.png"
badges[]                  = { id, name, file }
environments[id]          = { path, large, width, height, groundY }
appearance                = { body: [...], style: [...] }
```

## Sizes on the site

Character: 176 x 232 px (2x, cropped) on the card and in the wardrobe mirror, 256 px full frame in the fight.
Enemies 192 px and bosses 256 px in the fight; 128 px on the room card. Icons 60 px tiles (2x of 32).
Always integer scales with `image-rendering: pixelated`.
