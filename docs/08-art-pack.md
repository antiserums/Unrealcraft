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

**Home banner.** `banners/` holds the 3:1 town banner. `banners/living-town/` is the artist's canvas component
(`living-town.js` plus `assets/`): protected water, foliage, clouds, a waterwheel, villagers, four seasons and
lighting that follows the visitor's clock, with a manual hour. The sync copies the script, its assets and one
still per season and time (`living_town` in the manifest); `HeroBanner.tsx` loads the script as a browser module
straight from `public/art`, shows the matching still until the canvas has drawn, and puts a small ⚙ in the corner
with season and time choices (My time, Dawn, Day, Dusk, Night) plus a pause. Choices persist under the artist's
own storage key `uc-living-town-v2`, so their preview page and the site agree. The component honours
`prefers-reduced-motion` itself. `banners/animated/` (the earlier 6-second WebP loop) stays as the fallback when
the living-town folder is absent, and the plain still when neither is.

**Outfit sets.** The pack's eleven sets are the built-in catalog (`api/app/rpg.py`, `default_entitlements`;
admins can add rows that point at these art ids under `/admin/entitlements`):
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

## Website art (`website-art/`)

Interface pieces, icons, page headers, spot illustrations, three more arenas, a stone tile and the site emblem.
`tools/sync_art.py` copies every PNG the pack's `website-art/manifest.json` lists and adds `website_art` to the
site manifest: `images` maps `"<group>"` or `"<group>/<frame>"` to a path, `arenas` lists the extra fight rooms.
The artist's own `sync_website_art.py` is not needed. Helpers are in `web/lib/art.ts` (`siteArt`, `siteArtGroup`,
`achievementBadge`, `difficultyArt`, `rankCrest`, `specArtId`) and `web/components/SiteArt.tsx` (`PageHeader`,
`Spot`, `Px`). The layout adds the class `site-art` to `<html>` when the art is present; every style that needs
an image hangs off that class, so without the pack the site looks as it did before.

| Art | Where it shows |
|---|---|
| `headers/*` (960 x 160) | Quest board (board and path), leaderboard, wardrobe, achievements, player card (own and others'), mission (guild), how it works, FAQ and changelog (library), review inbox, admin pages |
| `icons/specializations`, `quest-steps`, `rank-crests` | How it works: the seven fields, the four steps, the ladder |
| `icons/difficulty` | The tier badge on every quest card |
| `icons/achievement-badges`, `achievement-foundations` | All seventeen seeded achievements by key (`NAMED_BADGE` in `art.ts`); rank medals and admin-made achievements use the older index badges |
| `icons/quest-state` | Done, up next and skipped on quest cards; done and locked step headings on the quest page |
| `icons/combat-status` | In a fight: the debuff pill, the hint line, the vitality box, crits and victory in the result |
| `icons/staff-crests`, `rank-crests` | Leaderboard: a staff crest for developers, admins and mentors, else the rank crest |
| `icons/banner-controls` | The home banner's season and time-of-day menu |
| `arenas/*` | Boss fights. The room is picked from the quest id, so a quest always has the same room |
| `spots/*` | No quests match, review inbox empty, page not found, the locked rank on the path, a won fight, a lost fight (rest), work sent for review (chest pending), the login page (guild entry), a page that failed to load (connection lost, `app/error.tsx`) |
| `textures/stone-tile` | Page background |
| `interface/divider-gem` | The rule under section headings |
| `interface/panel-stone-gold` | Frame of step cards, spot cards and the fight result (9-slice, 20 px) |
| `interface/buttons-tall/*` | `.btn` and primary buttons, 96 x 48 plates (ends 14 px, trims 12 px, middle stretches); the 96 x 32 `buttons/*` plates on Log out and the banner buttons |
| `interface/answer-plates`, `icons/selection-controls`, `icons/statistics` | Quiz choices; checkboxes and radios; the number tiles on the home and admin dashboards |
| `header-*-narrow`, `<arena>-4x` | Header crops below 600 px; the 1920 x 1080 arenas as the fight's large background |
| `identity` emblem | Beside the site name and as the browser tab icon |

| `interface/form-fields`, `tab-plates`, `message-panels`, `inventory-slots`, `progress-*` | Inputs and selects, the sub-navigation tabs, `.note` boxes (`data-tone` success/warning/error), wardrobe tiles, progress bars. The scrollbar parts are not used; the artist is redesigning them |
| `icons/utility`, `rewards`, `navigation` | Buttons and links: Filter, Edit profile, View as others, Public/Private, external reading links, the language picker; reward lines in the fight result and on achievements; the sub-navigation tabs. `components/Ico.tsx` renders these by path, so client components can use them |

Not used yet: the leather and parchment panels, the section title plate (v1 and v2), the tooltip plate, the 16 px
navigation icons and the Senior and Lead crests (the catalog has no such ranks yet). Notes on what the artist should fix are in
`docs/12-notes-for-the-artist.md`; the artist's route-by-route plan is in `docs/11-website-theme-audit.md`.
