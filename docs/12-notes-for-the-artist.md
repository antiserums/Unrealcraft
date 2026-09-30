# Notes for the artist — website art, 30 September 2026

## Update after the refinement delivery (`docs/14-theme-refinement-handoff.md`)

Everything from the refinement is wired: tall buttons (with disabled and focus states), progress track v2 with the
fill strip at 0 0 (health bars keep their own colours), divider v2 at native size, narrow headers below 600 px,
the 4x arenas as the fight's large background, checkbox and radio art, answer plates in the quiz (normal, hover,
and the picked answer turns correct or incorrect for the moment before the next turn), statistics icons on the home
and admin dashboards, and the scrollbar paths moved to `interface/`.

Please fix next:

1. **Scrollbar (`scrollbar-parts/track`, `thumb`, 8 x 32 each).** It looks bad on the site and needs a redesign.
   The thumb reads as a flat grey bar and the track pattern repeats every 32 px, which shows as stripes on a
   full-page scrollbar. Ask: a 12 px wide set, drawn for a dark page: a plain, quiet track (a single 1 px
   repeatable row is fine, no pattern) and a thumb with a 9-slice contract (top cap, 1 px repeatable middle,
   bottom cap, e.g. 12 x 36 with `slice: 12`) in stone with a thin gold edge, plus a hover state. Put them in
   `interface/scrollbar/` with `track.png`, `thumb.png`, `thumb-hover.png` and slice metadata in the manifest.
   Until then the site keeps the browser's own scrollbar.
2. **Button plate text room.** The tall plates work, but at the site's 13 px button text the words sit a little
   low inside the plate. If you revise them, move the visual centre of the plate 1 px up (the bottom rim is one
   pixel heavier than the top). Small thing.
3. **Statistics icons at 16 px** are hard to read against the dark tiles (the members bust and the hourglass in
   particular). A touch more contrast, or a 1 px dark outline, would help. Optional.

Still open on the site's side (nothing for you to do):

- **Navigation icons in the top bar.** Even at 16 px the four links plus the emblem do not fit on one line inside
  the 1040 px bar, so the top bar still has no icons. `navigation-16` is unused; `utility-16` is used for the
  language picker and reading links. No new art needed unless we redesign the bar.
- **Section header plate v2** is synced but not placed. The section headings use the divider; the plate would
  double up. Nothing to do.
- **Rarity frames** (`ui/rarity/*.svg`) still draw as CSS colours on the wardrobe tiles. That is site work, not art.

Original notes follow, kept for the record.

Everything from both deliveries is synced and on the site (see `docs/08-art-pack.md` for where each piece shows).
These are the pieces that do not quite work as delivered, with what would fix them. Nothing here is urgent; the
site falls back to its own CSS wherever a piece is left out.

## Please fix

1. **Button plates (`interface/buttons/*`, 96 x 32).** The trims are 10 px top and bottom, so only 12 px is left
   for the words. Site buttons are 34 to 38 px tall, and the text sits right against the trim. Ask: a taller
   variant, 96 x 48, same ends and same look, with a plain 1 px repeatable middle. Keep the 32 px one for small
   buttons (Log out, Filter).
2. **Progress track (`interface/progress-track.png`).** The middle of the track has small ornaments, so when the
   track is stretched with a 5 px slice they repeat as tick marks. Ask: ornaments only on the end caps, and a
   plain middle, so any width reads clean. Same for `progress-fill.png`.
3. **Navigation and utility icons at 16 px.** The 32 px navigation icons do not fit the top bar (it wrapped onto
   two lines), and downscaling pixel art blurs it. Ask: native 16 x 16 versions of `icons/navigation` and
   `icons/utility`, drawn on a 16 px grid, not scaled from the 32 px ones. The 32 px set is used on tabs and
   buttons and stays.
4. **Section title plate (`interface/section-header.png`, 320 x 48).** It has no slice metadata and its ends are
   part of the picture, so it cannot stretch to a heading of any length. Ask: a 9-slice version (like the panels,
   with `slice` in the manifest and a plain repeatable middle), or leave it out.
5. **Scrollbar parts are listed under `icons/`.** The manifest puts `scrollbar-parts/track.png` and `thumb.png` in
   `icons/scrollbar-parts/`, while the other interface pieces live in `interface/`. Not broken, just odd. If you
   move them, update the manifest paths.

## Nice to have

6. **Header strips on phones.** The 960 x 160 strips are shown at 104 px tall on a phone, which crops the sides
   heavily. A 480 x 160 centre crop per header (same art, tighter) would look better below 600 px. Name them
   `header-<name>-narrow` and the site will pick them up.
7. **Larger arenas.** The three new arenas are 480 x 270 only. They are drawn at 2x on the site and look right,
   but the training chamber also ships a 1920 x 1080 version. Optional.
8. **Senior and Lead crests** are synced but unused, because the catalog has no such ranks yet. Nothing to do.
9. **Tooltip plate** is unused. The site uses the browser's own tooltips. Nothing to do unless we build custom ones.

## What is confirmed working

Page headers (all ten), specialization emblems, rank and staff crests, difficulty marks, quest-step and
quest-state icons, combat-status icons, all seventeen achievement badges, the four arenas with the y = 232 ground
line, the five spot illustrations plus guild entry, rest-and-retry, chest-pending and connection-lost, the stone
tile, gem divider, stone-gold panel, form fields, tab plates, message panels, inventory slots, banner-control icons,
rewards and utility icons, and the site emblem in the tab.
