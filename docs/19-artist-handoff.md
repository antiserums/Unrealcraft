# Handoff for the artist — 30 September 2026 (evening)

This is the current, single handoff from the site to you. It replaces the running notes in `docs/12` and the
request list in `docs/18`; both stay as records. Everything you have delivered so far is synced, wired and
committed. Below: what is live, what is not used and why, and what is wanted next.

## Live on the site

Every group in the current pack manifest is placed, except the two listed under "Not used". In short:

- Page headers (all ten, plus the narrow crops below 600 px), the four arenas (with the 4x versions as the large
  fight background), the spot illustrations, the stone tile, the emblem in the tab and beside the site name.
- Buttons (tall family, all states), tabs (tall family, gold for the current one), form fields, message panels,
  checkboxes and radios, answer plates in the quiz, inventory slots, progress track v2 with the fill strip,
  divider v2, the 12 px scrollbar.
- Icons: specializations, quest steps, quest states, combat status, rank crests, staff crests, difficulty marks,
  banner controls, statistics, utility (32 and 16 px), rewards, all seventeen achievement badges.
- The CSS leftovers delivery: chips (stone, muted, primary, staff), tier plates, plain and hover panels on every
  ordinary card, the default avatar ring and card border, swatch rings, ornaments, the upload plate, leaderboard
  rows. The rarity SVGs from `ui/rarity` now frame the wardrobe tiles.

## Not used

- `picker-slots/*` (32 px): the title and frame pickers are 52 to 72 px tiles with the frame art inside, so a
  fixed 32 px slot does not fit them. No replacement needed; leave them in the pack.
- `avatar-ring/plain-64`: both avatar spots use the 48 px ring contract at 2x, like the profile decorations.
- `panel-leather`, `panel-parchment`: no place for them yet. The chest's "opened" state may use parchment later.
- `staff-crests/senior`, `staff-crests/lead`: waiting for those ranks to exist in the catalog.

## Wanted next

### 1. The Patron set (needed: the Support page is live and points at it)

Members who donate get one thank-you set, the same for everyone, looks only. The site already lists the
entitlements under the id `supporter`, so the pieces show up as soon as they are synced. Until then the outfit
shows as the plain figure and the two frames show nothing.

- **Outfit `supporter`, "Patron's Regalia"**: deep wine (around #5a1e2a) and gold, the guild emblem on the
  shoulder. Same deliverables as every other set: `characters/presets/<body>/supporter_<style>/sheet.png` for
  both bodies (`body_a`, `body_b`) and both styles (`melee`, `caster`), 4 x 6 frames of 128 px; the slot icons
  `gear/icons/set_supporter_<slot>.png` (32 px; `chest` is the wardrobe tile); entries in
  `metadata/character-presets.json` and in `metadata/pack.json` under `sets` and `items`.
- **Avatar ring `profile-decorations/avatar/NN-supporter.png`**: 48 px, transparent centre, the usual contract
  (`docs/09-playercard-art-spec.md`). Wine-red enamel and gold, a small heart at the top.
- **Card border `profile-decorations/card/NN-supporter.png`**: 352 x 252, card in the centre 320 x 220, same
  enamel and gold. A gentle animated version (like the staff frames) is welcome but not required.

### 2. Small polish, optional

- Tall button plates: at the site's 13 px text the label sits about one pixel low. If you touch them, move the
  visual centre up by one.
- Statistics icons at 16 px: the members bust and the hourglass are hard to read on the dark tiles; a 1 px dark
  outline or a touch more contrast would help.
- Tier plates: the 32 px difficulty mark overhangs the 28 px plate by 2 px top and bottom, as your note allowed.
  If you would rather it sat inside, a 64 x 32 plate (slice 8) per tier would do it; otherwise leave it.

## Conventions, unchanged

Pixel grid, transparent PNG, binary alpha, the approved palette. 9-slice pieces carry `slice` in the manifest and
a one-pixel repeatable middle. States are separate files in one group, listed in `website-art/manifest.json` with
sizes; individual states use direct ids with a `/` (for example `chips/primary`). The site's sync
(`py -3 tools/sync_art.py`) reads the manifest, copies canonical PNGs only and rebuilds the site manifest; nothing
else is needed on your side. When you retire something, add it to `retired-assets.json` and we remove the public
copies. Say in the handoff which group replaces which, and we do the CSS.
