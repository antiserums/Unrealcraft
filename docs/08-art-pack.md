# Art pack integration (UCSourceArt)

The art lives in a separate repo, `UCSourceArt`, produced by another AI. The website consumes it; it never
generates art. This page is the contract between the two: what the site expects, where it looks, and which IDs it
needs. The pack's own rules (canvas, draw order, occlusion, naming) are in `UCSourceArt/art-and-overlay-spec.txt`
and are followed as written.

## How art reaches the site

```bash
py -3 tools/sync_art.py            # pack assumed at ../UCSourceArt; or pass a path
```

The script copies finished PNG exports into `web/public/art/` (git-ignored) and writes `web/public/art/manifest.json`.
Newest `_v###` wins. The site reads the manifest on each request (cached 10 s). Any ID with no export falls back to
the built-in flat SVG silhouette, so nothing breaks while the pack is incomplete. Re-run the script after every drop.

## Style the site already follows

From the concept board (`concepts/art-direction-v001.png`): hand-painted stylized fantasy, teal cloth and runes,
warm gold trim, brown leather, friendly hero, imposing non-gory creatures. The site's theme uses the same pair:
gold (`--gold`) for frames, titles and buttons; teal (`--teal`) for health bars and highlights; dark plates behind.
Rarity is shown as a colored frame around icons and a dot next to names, never baked into the art.

## IDs the site uses

**Gear.** One art id per major and slot, rarity handled by the frame: `gear_<major>_<slot>`.
Majors: `level_design`, `programming`, `lookdev` (Environment Art), `tech_art`, `gameplay_design`, `animation`,
`cinematics`, `undecided`. Slots (same nine as the pack): `head`, `chest`, `hands`, `legs`, `feet`, `weapon`,
`offhand`, `cape`, `shoulders`. That is 72 designs, each with an icon and fitted overlays. Until a major has its own
set, the pack's warrior / ranger / spellcaster designs can stand in through `metadata/<id>.json` aliases (see below).
Capstone set pieces reuse the major's slot art.

**Creatures.** Ordinary quest rooms use the six enemies, capstones use the three bosses:
`enemy_crystal_slime`, `enemy_crystal_crawler`, `enemy_moss_imp`, `enemy_thorn_sentinel`, `enemy_rune_wisp`,
`enemy_broken_construct`, `boss_compiler_golem`, `boss_blueprint_hydra`, `boss_optimization_wyrm`.
The site picks the creature from the quest's subject (lighting → rune wisp, AI → thorn sentinel, and so on; see
`ENEMY_FOR_LOOK` in `api/app/rpg.py`) and names it with the pack's boss title for capstones.

**Character bases and appearance.** `characters/bases/<body>_<part>_v###.png` for `body-a` and `body-b`.
Appearance options (skin, face, hair, hair color, eyes, facial hair, markings) are read from
`metadata/*.json` files that carry an `appearance` object, e.g. `{"appearance": {"skin": ["skin-1", ...]}}`.
The character sheet shows a selector per option that exists; the member's choices are saved as
`cosmetics.appearance` and never affect learning or stats.

## File names the sync script understands

```
gear/icons/<id>_icon_v001.png
gear/overlays/<id>_body-a_<part>_v001.png      part = head | chest | hands | legs | feet | weapon | offhand |
                                                       back | straps | shoulders | hair-rear | hair-front | fx
characters/bases/body-a_body_v001.png, body-a_face_v001.png, ...
enemies/<id>_full_v001.png   enemies/<id>_portrait_v001.png
bosses/<id>_full_v001.png    bosses/<id>_portrait_v001.png
metadata/<id>.json           optional: {"id": ..., "layersOverride": [{"z": 60, "file": "gear/overlays/..png", "body": "body-a"}]}
```

Draw order (z) comes from the spec: back 10, body 20, face 30, legs 40, feet 50, chest 60, face-front 70,
hair-rear 80, shoulders 90, hair-front 100, head 110, hands 120, weapon/offhand 130, straps 140, fx 150.
A `layersOverride` in metadata replaces the filename-derived layers when an item needs a custom split.

## Sizes on the site

Character: 170 px tall on the sheet, 150 px in the fight. Boss: 170 px in the fight, 92 px on the room card.
Icons: 44 px in the inventory, 28 px in the equipped list. Review exports at those sizes.
