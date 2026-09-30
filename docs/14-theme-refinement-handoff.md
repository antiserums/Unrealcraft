# Claude handoff: theme refinements

2026-09-30. Read this after `docs/12-notes-for-the-artist.md`. The circled statistics screenshot is diagnosed separately in `docs/13-statistics-art-fix.md` / `CLAUDE-SCREENSHOT-FIX.md`.

## Delivery

Source pack: `C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/website-art/`.

The pack now contains **74 groups and 268 canonical PNGs**, including **23 new groups / 79 new PNGs** in this refinement. Generated masters are in `source/`; serve only the manifest exports. Existing assets remain available. The revised assets use new IDs so deployment is deliberate.

Open `refinement-preview.html` for the assembled controls and mobile header crops. `refinement.css` provides working reference rules; it is not automatically applied to the live site. All labels are HTML. The full inventory is `manifest.json`; use `website_art.images` through the site's existing art loader after sync.

## Response to the artist notes

| Request | Delivered / integration contract |
|---|---|
| 1. Taller buttons | `buttons-tall/{gold,stone}-{normal,hover,pressed,disabled}`. Eight 96×48 PNGs and a sheet. Solid dark centres, restrained trim. Slice **12 14 12 14**, one-pixel repeatable middle. Centre is 68×24. Keep original 96×32 files for compact controls. Prefer a 48px control height with 12px vertical / 20px horizontal padding. Do not squeeze the new art back into the current 34–38px treatment without checking label clearance. Pressed states preserve normal silhouettes and use darker palette steps. |
| 2. Plain progress middle | `progress-track-v2`, 128×16, slice **5** on all sides. No middle ornaments. `progress-fill-strip`, **1×6**, is the tightly cropped approved gold fill, with no transparent margins. Repeat horizontally at `1px 6px`, position `0 0`, inside a 6px-high fill element. No positive vertical offset. |
| 3. Small navigation / utility icons | `navigation-16/<existing-name>` (8) and `utility-16/<existing-name>` (16). Separate generated designs exported on a 16×16 grid with 2px transparent padding. Existing 32px sets stay. Render at 16px or an integer multiple. |
| 4. Header slices | `section-header-v2`, 320×48, slice **12 16 12 16** and a one-pixel repeatable middle. Padding 12px 20px. Keep the old header available until switched. |
| 5. Scrollbar location | Canonical frame paths now `interface/scrollbar-parts/{track,thumb}.png`; IDs remain `scrollbar-parts/track` and `/thumb`. Old `icons/scrollbar-parts/` copies remain compatibility aliases. Update hardcoded CSS paths before removing aliases. The supplied sync helper copies aliases as well. |
| 6. Mobile headers | All ten headers now have `header-<name>-narrow`, **480×160**, exact centre crops of the existing 960×160 artwork. The currently reviewed `PageHeader` does not select these automatically: add a responsive source/background below 600px. For crisp pixels, display at natural size and crop overflow in smaller containers instead of fractional resampling. |
| 7. Larger arenas | All three extra arenas have `<existing-arena-id>-4x`, **1920×1080**, exact nearest-neighbour 4× exports. Kind is `arena-large`, so they do not become duplicate selectable arenas. Ground Y is 928 in export pixels; logical fight layout stays 480×270 / ground Y 232. |
| 8–9. Unused crests / tooltip | No integration required. Existing files retained. |

## Additional controls supplied

- `selection-controls`: eight 16×16 states: checkbox off/on/mixed/disabled and radio off/on/focus/disabled. Keep real input semantics, labels, keyboard operation and focus styling; the image is decoration. A disabled control still needs its actual disabled attribute.
- `answer-plates`: normal/selected/correct/incorrect 96×48 plates, slice 12 14 12 14. Allow multiline answers to grow vertically and keep textual state feedback; colour alone is insufficient.
- `statistics`: twelve 16×16 dashboard icons. Members is a cloaked bust; pending and all-time deliberately share the hourglass motif. IDs in the manifest are authoritative.
- `divider-gem-v2`: 256×16, reduced side padding, simpler gold line and teal centre. Display at 256×16, or 512×32 in a full 32px-high container. Never put the 32px rendering inside the current 16px-high pseudo-element.

## Fix the screenshot on the website

The screenshot issues have both asset and CSS causes. See `docs/13-statistics-art-fix.md` for selectors and evidence.

1. `.section-h::after` currently clips a 512×32 divider into a 16px-high box. Use the new divider at native size, `height:16px`, and enough heading padding; or make the box 32px high for 2× rendering.
2. Replace the ornamented track with `progress-track-v2`; slice 5 and repeat. Use the new fill strip at `0 0`, not positive `0 5px` / `0 7px`. The positive offset is why the fill disappears.
3. Scope gold fill styling to XP. Current broad `!important` styling overrides hero/boss health colours. Preserve semantic green/red health styling separately.
4. Remove the 192×24 (1.5×) progress image scaling. Use native pixel borders with a taller repeating centre or an exact 2× treatment.

## Remaining website integration work

The live app CSS and components were left for Claude to change. Assets alone cannot fix those selectors.

- Wire the taller primary/secondary buttons, their hover/pressed/disabled states and visible keyboard focus.
- Select 16px icon IDs at small UI sizes; do not downscale the older 32px set.
- Wire checkbox/radio art in quest editing and profile privacy controls, and answer plates in quiz choices.
- Use statistics icons beside dashboard labels where useful. Keep decorative images out of accessible names.
- Use the existing art for remaining checklist/status, lock, chest and banner-control emoji where those occur.
- Rarity frame assets already exist; areas showing CSS-only rarity colours need integration, not another asset pack.
- Appearance options beyond the body require the existing character renderer/customization work to be wired. This delivery does not implement character rendering.
- Native select options cannot reliably contain images; keep native text options or intentionally implement an accessible custom selector.

## Sync and verification

Run the website's current art sync from `Unrealcraft` using its configured Python environment. It already enumerates the pack manifest. Verify the new IDs resolve in `web/public/art/manifest.json`. The fallback `tools/sync_website_art.py --site <Unrealcraft>` in this pack was tested against an isolated copy of the current website manifest: it preserves legacy sections, resolves all paths and is idempotent.

Checks completed:

- 268 canonical PNGs: exact dimensions, approved palette, binary alpha, individual exports matching sheet cells; zero errors (`qa.json`).
- Assembled reference preview: desktop and 390px mobile, no broken images or horizontal overflow. Button labels, divider and 0/25/50/100% fills inspected in-browser.
- Pressed-state missing bottom rims caught and repaired before delivery.
- Three 4× arena exports remain excluded from the selectable logical arena map.

Coverage limitation: `http://localhost:3000/` opened logged out in the available browser. Public page styling was checked live; member/staff screens were source-reviewed and the user's screenshot was inspected. They were **not** all visually verified in a signed-in session. Claude should verify dashboard, profile, wardrobe, quest/quiz, review queue and admin editor after wiring these changes, at desktop and phone widths.

Do not mark the full site visually approved solely because the asset checks pass.
