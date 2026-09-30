# Claude handoff: current website art and remaining fixes

2026-09-30. This is the single current handoff. It consolidates and supersedes handoffs 10, 13, 14, 15 and 16 for the current website-theme work. Earlier documents are historical records; their inventory counts and retained-file claims may be stale.

## Current state and priority

Source pack: `C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/website-art/`.

**70 groups, 262 canonical PNGs.** The current manifest is authoritative. The latest artist notes confirm the previous refinement is integrated. Remaining work is to wire the new scrollbar, fix the inconsistent controls listed below, and cross-check deployed copies against the cleanup ledger. The artist has changed assets and documentation, not application components or CSS.

1. Fix logout and the circled profile controls using the existing revised button family.
2. Integrate the new 12px scrollbar with its exact slice contract.
3. Cross-check deleted source assets, remove obsolete deployed copies, and retire old button/tab art only after replacing active consumers.
4. Validate signed-in screens at desktop and phone widths.

## Existing refined asset contracts

- `buttons-tall/{gold,stone}-{normal,hover,pressed,disabled}`: 96×48, slices top/bottom 12 and left/right 14, one-pixel repeatable middle. Prefer 48px controls and 12px vertical / 20px horizontal padding. Keep label alignment consistent across states.
- `answer-plates/{normal,selected,correct,incorrect}`: same size/slices; allow multiline answers to grow.
- `progress-track-v2`: 128×16, slice 5. `progress-fill-strip`: 1×6, repeat horizontally at position 0 0. Scope gold fill to XP; preserve health colours. No positive vertical fill offset or fractional 1.5× image scaling.
- `divider-gem-v2`: 256×16. Native display needs a 16px-high container; 2× display needs 512×32 and a full 32px-high container. Earlier screenshot clipping came from a 32px image in a 16px box.
- `utility-16`, `navigation-16`, `statistics`, `selection-controls`: 16px exports; render at integer sizes. Preserve semantic inputs and visible keyboard focus.
- Ten `header-<name>-narrow` assets: 480×160 centre crops for narrow screens. Three `<arena-id>-4x` assets: 1920×1080; logical layout remains 480×270 with ground Y 232 (928 in the large export).
- Section header plates and tooltip art are now retired. Keep headings on the divider treatment.

`refinement.css` is reference CSS, not an automatic application override. `index.html` is the current asset gallery. `refinement-preview.html` demonstrates the retained controls; `scrollbar-preview.png` shows the new thumb states enlarged 4×.

## New scrollbar assets

In `UCSourceArt/pixel-v3/website-art/interface/scrollbar/`:

| Manifest ID | File | Size | Contract |
|---|---|---|---|
| `scrollbar/track` | `track.png` | 12×1 | Plain dark row. Repeat vertically, no patterned bands. |
| `scrollbar/thumb` | `thumb.png` | 12×36 | Dark stone, thin gold sides and restrained caps. |
| `scrollbar/thumb-hover` | `thumb-hover.png` | 12×36 | Same size, brighter gold and stone. |

Thumb slices are **top 12, right 2, bottom 12, left 2**. The vertical middle is an identical one-pixel repeatable row. Do not use `slice:12` on all four sides: this 12px-wide source needs 2px side slices. Minimum displayed thumb height 24px; 36px preferred. Preserve 12px width and integer pixel rendering. A preview enlarged 4× is `scrollbar-preview.png`.

Sync the pack using the current website sync. Keep the native scrollbar fallback when a browser cannot render the custom thumb correctly. Test a long page and a short overflow panel, normal and hover states; do not stretch the entire image vertically or repeat complete capped thumbs. This delivery supplies assets and metadata, not an untested global scrollbar CSS override. The earlier 8×32 scrollbar-parts has been removed from the source pack; see the cleanup section below.

## Logout — confirmed old override

`web/app/globals.css:637` explicitly assigns `interface/buttons/stone-normal.png` to `.nav form button` and `.banner-btn`, overriding the new tall-button normal state. Hover/active rules above it still reference the new family, causing mixed families/slice geometry across states.

The user now explicitly wants logout updated, superseding the original note to retain the old small logout plate. Remove that old override for logout and apply the revised stone button consistently, with matching normal/hover/pressed/disabled geometry. If it must remain compact, crop the uniform vertical centre from the revised family or adjust the control layout; do not return to the old family or squash the whole image. Check the top bar width and translated label lengths. Keep the existing POST logout action in `components/Nav.tsx` unchanged.

## Player-card screenshot — confirmed selectors and components

1. **Edit wardrobe:** `web/components/CardStudio.tsx:103` is a plain `<button>` with no `.btn` or `.primary`. The refined skin selector in `globals.css:625` matches `.btn`, `button.primary`, and `.nav form button`, so this secondary action is skipped. Apply the shared revised secondary-button class. Check all CardStudio action rows, including Cancel, not only the circled button.
2. **Change:** `web/components/SpecializationPicker.tsx` renders its closed-state Change button without a theme class; its Cancel button is also unclassified. Apply the same revised secondary-button style and all states. Save is already primary. Preserve event handlers and disabled behaviour.
3. **Player Card / Achievements tabs:** `.subnav a` in `globals.css:668–673` still uses the earlier `interface/tab-plates/*` art. The user wants these brought into the revised family too. Use the revised stone plate for inactive tabs and gold for the active tab, with matching slices, readable text/icon spacing, hover and keyboard focus. Keep navigation links and current-page semantics; do not turn links into form buttons.
4. **Specialization chips:** `SpecializationPicker` uses `.pill` with an inline primary border colour. `.pill` at `globals.css:143` still draws a gradient, rounded CSS border and inset shadow. Replace this scoped specialization-chip appearance with flat dark stone/leather, crisp one-pixel borders and a restrained gold primary accent, consistent with the new controls. These are informational labels, not buttons: do not add hover/click behaviour or bulky button frames. Allow the chip row to wrap on phones; preserve the primary label and full specialization names. Avoid globally changing staff-title pills or achievement badges.

Use explicit shared control classes rather than theming every `button` indiscriminately: inventory slots, banner controls, quiz answers and icon-only buttons have their own contracts. Audit other plain secondary action buttons for the same omission.

## Acceptance checks for Claude

- Sign in and inspect logout, profile tabs, Edit profile / Edit wardrobe / View as others, Change, Save and Cancel.
- Normal, hover, pressed, disabled and keyboard focus must use consistent plate geometry; no old art flashing between states.
- Centre labels optically; the artist note about the one-pixel low text position remains a small alignment follow-up, not fixed by this scrollbar delivery.
- Check desktop and 390px width, long/translated labels, specialization wrapping and no overlap with the player-card frame.
- Inspect the real browser scrollbar on a long page for repeated stripes, clean caps and hover contrast; retain native fallback when unsupported.

The application CSS/components were **not changed** by the artist in this delivery. These are verified integration findings for Claude to fix. The screenshot source is `codex-clipboard-02763ef4-0742-4399-bf86-708731744448.png`. New scrollbar files pass logical-size, palette and alpha validation; the 12-row middle is byte-identical throughout each thumb.

## Removed from the source pack

`retired-assets.json` is the exact deletion ledger: 28 paths with SHA-256 hashes, seven retired groups, replacements, and backup location. Nine were canonical runtime PNGs; the rest were compatibility aliases, retired generated masters/prompts and obsolete theme preview files. Current manifest entries and gallery were updated.

| Removed group | Replacement / action |
|---|---|
| divider-gem | divider-gem-v2 |
| progress-track | progress-track-v2 |
| progress-fill | progress-fill-strip |
| section-header | Use divider-gem-v2; headings do not need both treatments |
| section-header-v2 | Same; confirmed unplaced in artist notes |
| tooltip-plate | Native browser tooltip; no replacement image |
| scrollbar-parts | scrollbar/track, scrollbar/thumb, scrollbar/thumb-hover; see scrollbar contract above |

The old `theme.css` and `theme-preview.html/png` were retired because they reference obsolete artwork. Use `refinement.css`, `refinement-preview.html` and the current manifest. Earlier screenshots and historical handoffs may show retired art; they are records, not the active asset contract.

## Kept deliberately

- Old `button-plates` and `tab-plates`: still referenced in `globals.css:637` and `668–673`. Fix logout/banner overrides and profile tabs as described above, then retire these groups in a second pass. Do not delete active dependencies first.
- `navigation-16`: despite the note saying unused in the top bar, `HeroBanner.tsx:95` uses its settings icon through `<Ico group="navigation" id="settings" size={16}>`. Keep this set unless that use is migrated.
- 480px arenas: retained as logical layout/source assets for the 4× exports.
- Character art, customization, profile frames, banner seasons/animation and rarity art: outside this confirmed website-theme retirement list. Rarity art has pending integration, so it is not classified as waste.

## Website cross-check and removal order

1. Read `retired-assets.json` from the current source pack. Search both literal `/art/website-art/` URLs and dynamic `Ico`/`siteArt` lookups; scanning filenames alone misses generated paths.
2. Confirm old IDs have no active consumers. Switch any remaining uses to the replacement IDs above. Resolve the controls above before retiring old button/tab families.
3. Run the existing website art sync. Verify its merged `website_art.assets` and `images` no longer retain removed groups/frame IDs. Sync copying does not imply obsolete files were deleted.
4. Remove only the exact retired runtime paths under `web/public/art/website-art/` listed in the ledger after verifying they have no consumers. Skip source/prompts/preview paths if they were never deployed. Do not broadly delete the public art directory or touch unrelated art.
5. Check CSS URLs, dynamic icon URLs and the merged manifest for missing files. Review authenticated logout/profile tabs/Edit wardrobe/Change/Cancel, the progress bars, headings and scrollbar. Check hover/active/disabled/focus states and phone width.
6. After migrating old button/tab consumers, add their paths and replacements to the ledger and remove them from both source and public output.

The artist cleaned the source pack only. Public website copies and application code were left for Claude's requested cross-check. Recoverable copies are outside UCSourceArt at `C:/Users/killt/Documents/Codex/2026-09-29/please/outputs/retired-website-art-2026-09-30/`. No broad legacy/character asset deletion was performed.

## Verification and coverage

- Current pack: all 262 canonical PNGs pass dimension, palette, binary-alpha and sheet/frame checks.
- Cleanup: all 28 ledger files absent from UCSourceArt; no active manifest files missing.
- Sync tested on an isolated copy of the current main manifest: 264 files copied, legacy sections preserved, all runtime paths resolve, repeated sync is idempotent. See `qa.json` and `sync-validation.json`.
- Previous assembled refinement preview checked on desktop and at 390px: no broken images or horizontal overflow.
- Browser session available to the artist was logged out. The user's profile screenshot and source were inspected, but authenticated member/staff screens were not comprehensively verified live. Claude must perform that final signed-in review.
- Optional artist follow-up from notes/12: improve contrast of the 16px members/hourglass icons. This was not included in the scrollbar delivery.

Line numbers describe the inspected source and may shift. Find the named selector/component before editing. Report which controls were updated, which obsolete public files were removed, and any remaining active reference that prevented a deletion.
