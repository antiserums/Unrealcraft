# Claude handoff: Unrealcraft website art

## Scope and current contract

This completes the user's art list A–D, assets 1–17, as an additive pack at
`UCSourceArt/pixel-v3/website-art/`. All website-facing images are PNGs at their
specified logical resolutions. `manifest.json` is the authoritative list of
paths, dimensions, sheet cells and identifiers. `source/` contains generated
masters; do not serve those as finished assets. `prompts/` records the built-in
ImageGen prompts. No image contains intentional text or a game/engine logo.

Checked against the website's `docs/08-art-pack.md`,
`docs/09-playercard-art-spec.md`, `tools/sync_art.py`, `web/lib/art.ts`, and
`api/app/rpg.py`. Existing character sets, the living-town banner, profile
frames, and the legacy eight-entry badge array retain their paths and IDs.

## Sync and integration — current website contract

The current website already integrates this pack. Run its existing
`python tools/sync_art.py` from Unrealcraft using the working Python environment.
It reads every group from this pack's manifest, copies canonical PNGs, and emits
`website_art.images` plus `website_art.arenas` in the version-3 main manifest.
Do not replace that integration with the older assets-only shape.

Use `siteArt(m, "combat-status/dazed")` for an individual icon,
`siteArt(m, "header-review")` for a standalone image, and
`siteArtGroup(m, "quest-state")` for a group. The existing helpers and Manifest
type already support this. New filenames and IDs are additive.

The optional `tools/sync_website_art.py --site <Unrealcraft>` in this pack also
emits the current images/arenas shape, retaining legacy main-manifest fields.
It is a fallback for older checkout workflows; the current site's standard
sync is sufficient for PNGs. No application source was changed in this delivery.

`theme.css` is an opt-in skin example with paths relative to the pack folder.
If Claude imports those rules into globals.css, change URLs to
`/art/website-art/...`. Alternatively copy theme.css beside the exported art
and load it from there. The optional helper copies it; the website's base sync
currently copies PNGs only. Do not apply the new classes globally without
checking input sizing and layout. Keep native input/button semantics.

See **SITE-AUDIT.md** for the route-by-route placement plan and
**integration-map.json** for exact key mappings. **theme-preview.html** shows
the real skin PNGs around live HTML text; labels are never baked into the art.

## Dimensions and composition

- UI frame variants: 96x96, 20px nine-slice corners, 4px exterior transparent
  padding, 1px repeat period. The centre remains transparent. Use border-image
  slice 20 WITHOUT `fill`; retain the page's dark panel fill underneath.
  These are generic panel frames, not replacements for the 352x252 player-card
  decorations or 48x48 avatar rings. Their slicing contracts are different.
- Divider: 256x16. Section title plate: 320x48, blank centre.
- Button sheet: 3 columns x 2 rows; cells 96x32. Top row primary gold,
  bottom row secondary stone; columns normal, hover, pressed. Use unchanged
  geometry when swapping states. Text and focus indicators belong to the site.
- Progress track and fill: separate 128x16 files. Fill rectangle is recorded
  in the track's manifest entry. Sample the plain central fill rows, repeat
  horizontally inside that rectangle and clip to progress. Do not scale the
  track endcaps with the percentage.
- Icons: 32x32 cells, 3px transparent padding. Each requested group has its
  own even-grid sheet AND individual icon exports. Empty unused cells remain
  transparent. Prefer individual files unless sprite-sheet use is beneficial.
- Arenas: 480x270, wall/floor join approximately y132, fighter ground y232,
  top 41px quiet. Draw at 2x (960x540), keeping the site's y464 foot baseline.
  Use the manifest's groundY rather than guessing from the bottom of the PNG.
  The current arenaBackground() already includes these arenas and selects by
  quest ID; preserve its ground alignment.
- Stone tile: 256x256, repeat both axes; keep text on dark low-contrast regions.
- Spot illustrations: 160x120 with transparent padding.
- Ten page header strips: 960x160, 6:1. Preserve ratio; do not stretch height.
- Site emblem: sheet includes both 32x32 and 16x16 crops with explicit rects.
  Individual sizes are also provided. Use the native 16px version for tiny UI.

Use nearest-neighbour sampling and integer display scales. 32px icons become
64px at 2x (not 60px). For responsive layouts, clip or select a smaller integer
scale instead of applying fractional transforms that blur the pixel grid.

## Exact achievement mappings

Do not reorder the existing `badges[]` array or reuse its numerical indexes.
Use these new named files by achievement key:

| rpg.py achievement key | New icon ID |
|---|---|
| rooms_50 | dungeons-50 |
| rooms_150 | dungeons-150 |
| focus_50 | first-try-wins-50 |
| craft_10 | works-accepted-10 |
| lore_50 | readings-50 |
| streak_30 | streak-30 |
| capstone_4 | capstones-4 |
| specs_7 | all-specializations |
| cross_25 | outside-field-25 |

These files are in `icons/achievement-badges/`. The images express achievements
symbolically; the site supplies the exact counts as labels/tooltips.

Specialization art uses hyphenated IDs; map them to API underscore IDs:
`level_design -> level-design`, `lookdev -> environment-art`,
`tech_art -> tech-art`, `gameplay_design -> gameplay-design`; programming,
animation and cinematics keep their names. Confirm against the active catalog
rather than deriving labels from filenames. The current specArtId() already handles lookdev.

The six rank crests include Orientation as requested. This adds artwork only;
it does not insert a new XP rank or change RANK_UP_NAMES/default entitlements.
The five difficulty IDs are presentation marks, not changes to quiz difficulty.

## Validation and remaining application work

See qa.json, theme-validation.json and sync-validation.json. Claude still needs
to wire the new groups into the components listed in SITE-AUDIT.md and check
authenticated layouts. Public-site review is complete; protected screens were
reviewed from source. Existing live integrations are preserved.

## Website theme extension

Form fields and tabs each have four states in 96x32 source cells. Message panels
have four 160x64 source cells. Inventory slots have four 48x48 source cells.
All have individual exports and 2x2 sheets. States use identical registered
geometry, 4px outer alpha padding, 12px nine-slice regions and plain repeating
edge middles. Use a 12px border-image slice with fill for field/tab/message
plates; native input controls should be at least 48px tall to leave room for
text. Do not force the source height onto a native element with 24px of border.

Inventory slots are fixed 48x48 (or integer 2x) backgrounds; their icon content
sits inside 8px padding. The tooltip is a 160x64 plate with a 12px slice.
The two scrollbar parts have their own exported crops and repeat axes in the
manifest; preserve native scrolling and keyboard access. Custom scrollbar
art is optional because browser support differs.

All theme images are blank: titles, labels, focus semantics, success/error
messages and tooltip text remain in the website. The checked example CSS uses
explicit focus outlines. Always accompany status colour with visible words.

## Foundation achievement mappings

Use group achievement-foundations for first_blood -> first-blood, rooms_10 ->
dungeons-10, focus_10 -> first-try-wins-10, craft_1 -> work-accepted-1, lore_10 ->
readings-10, streak_7 -> streak-7, capstone_1 -> capstone-1, specs_3 ->
specializations-3. Extend achievementBadge() with a full group/id mapping,
not only a filename inside achievement-badges. Preserve the legacy badge
index fallback for dynamic rank medals and custom admin achievements.

Staff crests are separate from the earned rank ladder. Map developer/admin/mentor
from the API role; Senior and Lead are reserved guild labels, not automatic
privilege grants. Do not alter entitlement IDs or staff permissions.
