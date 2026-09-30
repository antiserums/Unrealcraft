# Claude: scrollbar redesign and inconsistent profile controls

2026-09-30. Responds to the latest update in `docs/12-notes-for-the-artist.md` and two user reports: old logout styling, and the circled controls on the player-card screen.

## New scrollbar assets

In `UCSourceArt/pixel-v3/website-art/interface/scrollbar/`:

| Manifest ID | File | Size | Contract |
|---|---|---|---|
| `scrollbar/track` | `track.png` | 12×1 | Plain dark row. Repeat vertically, no patterned bands. |
| `scrollbar/thumb` | `thumb.png` | 12×36 | Dark stone, thin gold sides and restrained caps. |
| `scrollbar/thumb-hover` | `thumb-hover.png` | 12×36 | Same size, brighter gold and stone. |

Thumb slices are **top 12, right 2, bottom 12, left 2**. The vertical middle is an identical one-pixel repeatable row. Do not use `slice:12` on all four sides: this 12px-wide source needs 2px side slices. Minimum displayed thumb height 24px; 36px preferred. Preserve 12px width and integer pixel rendering. A preview enlarged 4× is `scrollbar-preview.png`.

Sync the pack using the current website sync. Keep the native scrollbar fallback when a browser cannot render the custom thumb correctly. Test a long page and a short overflow panel, normal and hover states; do not stretch the entire image vertically or repeat complete capped thumbs. This delivery supplies assets and metadata, not an untested global scrollbar CSS override. The earlier 8×32 `scrollbar-parts` remains for compatibility and should stay unused.

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
