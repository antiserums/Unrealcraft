# Claude handoff: remaining CSS theme art

2026-09-30. This is the **single current handoff**, updated for `docs/18-art-requests-css-leftovers.md`. That request confirms earlier handoffs are integrated; do not redo those migrations. This delivery adds **27 canonical PNGs**. Current manifest: **94 entries, 268 canonical PNGs**. Individual states have direct IDs containing `/` rather than sheet wrappers.

Source pack: `C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/website-art/`.

Use `manifest.json` for exact paths/sizes/slices, `css-leftovers-assets.json` for this delivery only, and `css-leftovers-preview.html` for the assembled example. Generated masters in `source/` are not runtime assets. All labels remain HTML. Application code/CSS was left for Claude as requested.

## CSS-to-art mapping

Paths are relative to the pack; IDs resolve through `website_art.images` after sync.

| Replace | IDs → files | Contract |
|---|---|---|
| Specialization chips, owner/required/elective labels, subject tags | `chips/{stone,primary,muted}` → `interface/chips/<state>.png` | 48×24; slice6; 2px outer padding. Stone default, primary warm/gold, muted tags. |
| Staff pill glow | `chips/staff-{developer,admin,mentor}` → same folder | 48×24; slice6. Teal, gold, violet. Use drawn borders instead of pulsing box glow. |
| Quest tier colour block | `tier-plates/{novice,apprentice,adept,expert,master}` → `interface/tier-plates/<tier>.png` | 64×28; slice8; dark centre for HTML text/icon. |
| General card gradient/corner ticks | `panel-stone-plain` → `interface/panel-stone-plain.png` | 96×96; slice20; transparent centre. Flat background may sit beneath. |
| Quest-card hover edge | `panel-stone-hover` → `interface/panel-stone-hover.png` | Same size, slices and alpha silhouette; brighter material ramp. |
| Default avatar outline / initial fallback | `avatar-ring/plain`, `avatar-ring/plain-64` → `interface/avatar-ring/<name>.png` | 48×48 and64×64; transparent circular apertures. Initial stays HTML. |
| Bare player-card border | `card-frame/plain` → `interface/card-frame/plain.png` | 352×252; inset16; card rect320×220; slice44. Thin bronze/stone band with tiny top gold mark. Only when no decoration equipped. |
| Title/frame picker boxes | `picker-slots/{normal,selected,locked}` → `interface/picker-slots/<state>.png` | Fixed32×32; content inset8; clear16×16 centre. Long title labels belong beside the small tile, not squeezed inside. |
| Nameplate colour circle border | `swatch-ring` → `interface/swatch-ring.png` | Fixed28×28; clear18px-diameter centre. Place colour underneath. |
| Decorative heading/footer/divider glyphs | `ornaments/{diamond-8,diamond-12,diamond-16,rule-end}` → `icons/ornaments/<name>.png` | 8×8,12×12,16×16,16×16. Decorative, empty alt/aria-hidden. |
| Upload / turn-in gradient | `upload-plate` → `interface/upload-plate.png` | 160×64; slice12; transparent centre. Tiny chest mark in fixed top-left corner so repeating edges cannot duplicate it. Keep native input semantics and HTML filenames. Open state can reuse panel-parchment. |
| Leaderboard stripes | `row-plate`, `row-plate-top` → `interface/<id>.png` | 96×32; slice4; quiet leather, header gold underline. Keep semantic table markup. |

All sliced pieces have a one-pixel repeatable middle. Slice values apply to all four sides unless stated otherwise.

## Decisions and sizing details

**Tier colours follow the YAML named in the request.** The prose says purple/red for Expert/Master, but `curriculum/specializations.yaml` defines Novice `#7A8C7E`, Apprentice `#B5714B`, Adept `#3D7DD8`, Expert `#D9824A`, Master `#8A9BA8`. The art uses those values: orange Expert, steel Master. These five accents plus mentor violet `#8E6CCF` extend the palette. Keep code and art aligned to the YAML.

**32px icon versus28px plate:** a32px mark cannot fit entirely inside a28px-high plate. Give the native32 icon a32px line box, centre the28px plate behind it, and allow2px overflow per edge. Reserve at least40px left content space and grow the plate horizontally for text. Do not clip or fractionally squash the icon. A separately designed smaller mark is not part of this delivery.

**Optional tintable `chips/rank` was skipped**, as the request permits. A whole-image filter or alpha mask would also tint/mask the dark fill. Explicit staff chips are supplied; regular ranks can use the neutral stone/primary plate and existing coloured HTML text. Do not request a nonexistent `chips/rank` ID or tint the entire plate.

**Rarity: use the existing `ui/rarity/*.svg`.** No duplicate PNG set was added. Wire existing frames over wardrobe tiles while preserving selected/locked states.

- Chip example: `border-image: url(...) 6 fill / 6px repeat`, border0, height24px, line-height12px, padding6px 10px. Preview uses12px text and a long primary-specialization label. Wrap chip rows. Check22/26px variants if the site uses them; preview uses24px.
- Panel example: `border-image: url(...) 20 / 20px repeat`; centre is clear. Remove the old gradient and gold pseudo-corner ticks rather than layering both.
- Avatar48: centre24,24; clear radius17.5; photo radius16 under the existing decoration contract. At2× it is a96px overlay around a64px photo.
- Avatar64: centre32,32; clear radius24, i.e.48px opening. Keep the photo at44px diameter or less for a gap at native display. The64px dimension is the overlay canvas, not a64px photo aperture. If the home ribbon uses a64px photo, deliberately adjust overlay layout rather than covering the photo.
- Swatch: centre14,14; clear radius9. Colour goes beneath; retain an accessible HTML name.
- Plain card: logical card starts16,16 and ends336,236. Preserve the existing32-screen-pixel gutter at2×. Responsive corners are44 source pixels. Do not also draw CSS corner ticks. The tiny top accent can use the existing repeating-border treatment.
- Picker slots are32px with a16px clear content region; they are not interchangeable with inventory48px slots.
- Use native sizes or integer scaling and `image-rendering:pixelated`. Repeat slice edges; preserve corners. No global tint or soft glow over these borders.

## Integration and verification

1. Run the existing art sync. Confirm every ID in `css-leftovers-assets.json` resolves in `website_art.images`. The current sync accepts direct IDs with `/`; no custom group parser is needed.
2. Apply the mapping above. Remove duplicate gradients, pseudo-corners, outlines and pill glow only on migrated elements. Preserve event handlers, disabled/selected states, file input behaviour and keyboard focus.
3. Check signed-in home/profile/quests/wardrobe/chest/leaderboard at desktop and390px width, including long/localized labels. Confirm rings and plain card borders do not overlap content; equipped frames must suppress plain defaults.
4. Request18 says earlier migrations are complete. Do not restore retired art from historical handoffs. The cleanup ledger remains an audit record; this delivery deletes no additional art.

Artist checks:27 new PNGs pass dimensions, palette, binary alpha, repeatable slice middles, transparent ring apertures and card-content clearance. Full current pack:268 canonical PNGs, zero QA errors. Isolated sync preserves legacy sections, resolves all runtime paths and is idempotent. Assembled preview has no broken images or page overflow on desktop and390px width; chips/tier text/panel spacing inspected.

Reports: `qa.json`, `css-leftovers-validation.json`, `sync-validation.json`. The preview is an art integration example, not evidence the live signed-in website has already been changed. Update code/CSS and perform that final visual check before marking the site complete.
