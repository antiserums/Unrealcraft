# Art requests: what still looks like plain CSS — 30 September 2026

For the artist. Everything from handoffs 10 to 17 is on the site. This is the list of things that are still drawn
by CSS (gradients, rounded borders, emoji, plain colour blocks) and would look better as pixel art in the same
style as the rest of the pack. Sizes use the same rules as before: draw on the pixel grid, transparent PNG,
9-slice pieces with `slice` in the manifest and a one-pixel repeatable middle, states as separate files under one
group. Nothing here changes what anything does; it is all looks.

The first item is the one the user circled on the player card.

## 1. Chips and pills (the circled one)

Small labels used everywhere: the specialization chips on the player card ("Level Design · primary",
"Programming"), the subject tags on quest cards ("install", "graybox"), the owner label ("Everyone", "Tasters"),
the "Required / Elective" word, and the rank pill next to the name in the top bar ("Developer", "Novice").

Ask: group `chips`, 9-slice plates 48 x 24, `slice: 6`, one-pixel repeatable middle, 2 px clear padding:
- `chips/stone` — the default: dark stone, thin bronze edge.
- `chips/primary` — gold edge, slightly warmer fill (the primary specialization).
- `chips/muted` — quieter, for subject tags.
- `chips/rank` — a plate whose edge can take a colour: draw the edge in pure white (#ffffff) on a dark fill so
  the site can tint it with the rank colour (`mask` or `filter`). If tinting is not workable, skip this one.
Text stays HTML; the plate must read at 22 to 26 px tall with 11 to 12 px text.

## 2. Tier badge ("NOVICE" on every quest card)

Today: a flat colour block behind the difficulty mark and the word. Ask: `tier-plates/{novice,apprentice,adept,
expert,master}`, 9-slice 64 x 28, `slice: 8`, each in its tier colour (green, copper, blue, purple, red as the
site uses them, see `curriculum/specializations.yaml` ranks `color`), with room for the 32 px mark on the left.

## 3. Card corners and the panel that most cards use

Only step cards, illustration cards and the fight result use `panel-stone-gold`; every other `.card` still has
CSS gold corner ticks and a gradient. Ask: a quieter panel for general use, `panel-stone-plain`, 96 x 96,
`slice: 20`, thin bronze edge with small gold corner marks and a transparent centre, so it can sit behind text
all over the site without being loud. Also a `panel-stone-hover` (same geometry, edge one step brighter) for
quest cards, which light up on hover.

## 4. Avatar ring and the initial circle

Members without a Discord avatar get a CSS circle with their first letter, and everyone's avatar sits in a CSS
ring when no frame is worn. Ask: `avatar-ring/plain` 48 x 48 (same contract as the profile-decorations avatar
rings, transparent centre) and `avatar-ring/plain-64` at 64 x 64 for the home page ribbon.

## 5. Player card frame when no card frame is worn

The bare card is a CSS box with corner ticks. Ask: `card-frame/plain`, 352 x 252 with the same 16 px inset
contract as the profile-decorations card borders, in stone and bronze with a small gold mark top centre. This is
the "no decoration" look, so keep it quiet.

## 6. Colour swatches and the picker tiles

Nameplate colours are CSS circles; title choices and frame choices are CSS boxes with a gold outline when
selected. Ask: `picker-slots/{normal,selected,locked}` 32 x 32 (same idea as the inventory slots but square and
smaller), and `swatch-ring` 28 x 28, a ring with a transparent centre that the colour shows through.

## 7. Eyebrow mark and small ornaments

The "❖" before every small gold heading, the diamond in the footer and the "◆" in the top banner divider are
text glyphs. Ask: `ornaments/{diamond-8,diamond-12,diamond-16}` (8, 12 and 16 px) in gold, and
`ornaments/rule-end` 16 x 16 for the ends of thin rules.

## 8. Rank pill and staff glow

The staff pill ("Developer") pulses with a CSS glow. If you want it to look drawn: `chips/staff-{developer,
admin,mentor}` 48 x 24, `slice: 6`, in each role's colour (teal developer, gold admin, violet mentor). Optional.

## 9. File input and the turn-in box

The chest's file picker is the browser's own control and the turn-in box is a CSS gradient. Ask:
`interface/upload-plate` 160 x 64, `slice: 12`, a leather plate with a small chest or scroll mark at the left,
transparent centre for the text. The chest "open" state can reuse `panel-parchment`, which we already have.

## 10. Leaderboard table

Rows are CSS stripes. Ask: `interface/row-plate` 96 x 32, `slice: 4`, a very quiet leather row with a one-pixel
repeatable middle, and `interface/row-plate-top` for the header row with a gold underline. Optional; the table
reads fine as it is.

## 11. Rarity frames (already in the pack, not yet drawn)

`ui/rarity/*.svg` exist but the wardrobe tiles still show rarity as a coloured edge. Nothing new to draw; we
will wire the existing SVGs unless you would rather supply 48 x 48 PNG frames matching the inventory slots
(`rarity-slots/{common,uncommon,rare,epic,legendary}` with the same 8 px padding). Say which.

## Not needed

Buttons, tabs, form fields, message panels, inventory slots, progress bars, scrollbar, headers, dividers,
icons, badges, crests, arenas and the spot illustrations are all done. The top bar stays text-only on purpose.

## Delivery

Same as before: add the groups to `website-art/manifest.json` with sizes and `slice` where it applies, canonical
PNGs only, and a line in the handoff saying which group replaces which CSS. The site's sync picks them up; the
CSS side is ours.

## 12. The Patron set (new, needed for the Support page)

Members who donate get one thank-you set, the same for everyone, looks only. It needs the same three pieces the
staff sets have, in the same contracts:

- **Outfit `supporter`, "Patron's Regalia"**: deep wine (#5a1e2a range) and gold, the guild emblem on the
  shoulder. Character sheets like every other set: `characters/presets/<body>/supporter_<style>/sheet.png` for
  both bodies and both styles (4 x 6 frames of 128 px), plus the wardrobe icon `gear/icons/set_supporter_chest.png`
  and the other slot icons, and an entry in `metadata/character-presets.json` and `pack.json` `sets`.
- **Avatar frame `profile-decorations/avatar/NN-supporter.png`** (48 px ring, transparent centre): wine-red
  enamel and gold, a small heart at the top.
- **Card frame `profile-decorations/card/NN-supporter.png`** (352 x 252, card in the centre 320 x 220): the same
  enamel and gold. A gentle animated version is welcome but not required.

The site already lists these under the ids `supporter` (outfit) and `supporter` (avatar and card decorations),
so they show up as soon as the files are synced. Until then the outfit falls back to the plain figure.
