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

**Outfits.** Gear is cosmetic: a set is a whole outfit unlocked by a quest, a rank or an achievement, and the
member wears one set at a time. One art id per set: `set_<id>`. The ids are listed by `GET /api/me/character`
(`outfits[].art_id`) and defined in `api/app/rpg.py` (`build_sets`): `set_wayfarer` (starter), four achievement
sets (`set_first_blood`, `set_flawless_10`, `set_streak_30`, `set_reader_50`), four rank sets per major
(`set_<major>_r1` … `_r4`) and four capstone sets per major (`set_<major>_cap1` … `_cap4`). That is 61 sets; each
needs an icon and fitted overlays for every slot it covers. Rank sets of one major may share a base design with
different trim; the site does not care how they are made, only that the ids match.

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
gear/icons/set_<id>_icon_v001.png
gear/overlays/set_<id>_body-a_<part>_v001.png      part = head | chest | hands | legs | feet | weapon | offhand |
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
Icons: 44 px in the wardrobe. Review exports at those sizes.
