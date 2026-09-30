# Claude handoff: website theme polish and Patron rewards

2026-09-30. This is the single current artist handoff responding to docs/19-artist-handoff.md. It supersedes the earlier Patron-only version of this file. The website theme polish is now delivered too.

## Website theme changes ready to sync

Source: C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/website-art/.

| Group | Delivered | Integration |
| --- | --- | --- |
| buttons-tall | All eight gold/stone states retain 96×48 dimensions; every pixel moved up one row with no clipping | Change both source slices and rendered border widths to **11 14 13 14**, in top/right/bottom/left order |
| statistics | members, pending and all-time replaced at 16×16; brighter simplified bust and gold/teal hourglass | Existing IDs and paths; render at 16px or whole-number multiples |
| tier-plates | Novice, Apprentice, Adept, Expert and Master now **64×32**, from 64×28 | Keep slice8, rendered trim8px and minimum height32px; preserve mark32×32 |

The two affected sheets were rebuilt in lockstep with their individual files. Manifest entries and reference refinement.css are updated. Total: 16 individual PNG replacements plus two sheets. All existing IDs stay valid. No assets were deleted or newly retired in this pass. Do not bring back retired assets from historical previews or backups; retired-assets.json remains the prior cleanup ledger.

### Apply on the website

1. Run the existing tools/sync_art.py from Unrealcraft with its configured Python environment. It copies the canonical assets and rebuilds public/art/manifest.json. The source manifest contains slice metadata; **the generated site manifest only maps image paths**, so the CSS values below still need changing explicitly.
2. In web/app/globals.css, update the base tall-button rule for .btn, button.primary and .nav form button, plus the .subnav a rule. Replace the 12 14 source slice / 12px 14px width pair with:

   border-image: url("/art/website-art/interface/buttons-tall/stone-normal.png") 11 14 13 14 fill / 11px 14px 13px 14px stretch;

   Retain the existing gold overrides and hover/pressed/disabled source swaps. Do not apply the new slices to unrelated tabs, answer plates or other image families. The reference refinement.css uses repeat; the site's existing stretch is also valid because the middle repeats at one pixel.
3. The one-pixel correction is already in the PNGs. Keep label placement unchanged for the first check; do not shift the whole button or apply another one-pixel image transform. Compare the actual site font at13px against the review page. If the label baseline still needs optical adjustment with that font, adjust its text wrapper only after visual inspection.
4. Update the tier CSS comment from64×28 to64×32. Its existing min-height32px, .has-mark padding and8px slices are compatible. Keep the icon's32px line box inside the badge box; do not scale the plate by32/28.
5. Hard reload after sync to avoid stale PNGs. Check logout, Edit profile, Edit wardrobe, View as others, Change specialization, and Player card/Achievements navigation. These previously mixed styles; request19 reports them integrated. This pass updates the art and handoff, and does not assert a fresh authenticated-route verification.

### What is already in the website theme pack

Request19 reports these live: ten page headers and narrow crops, stone background, four arenas, spot illustrations, emblem, buttons/tabs and form states, messages, quiz answers, inventory and rarity frames, progress track/fill, divider, scrollbar, rank/staff/specialization/navigation/utility/achievement/statistics icons, chips, plain/hover panels, default avatar/card borders, swatches, ornaments, upload plate and leaderboard rows. The earlier CSS-leftover art was not omitted from the pack; this handoff now covers the additional polish explicitly.

Keep picker-slots, avatar-ring/plain-64, leather/parchment panels and senior/lead crests in the pack as request19 directs, even though the site currently does not use them.

### Website theme validation

site-polish-validation.json: all268 canonical PNGs checked for manifest dimensions, palette and binary alpha; affected sheet cells match individual files; changed nine-slice middles repeat at one pixel; statistics keep2px clear padding; button registration is exactly one pixel upward.

site-polish-preview.html shows before/after button states with13px labels, icons at16px and enlarged, and all five tier plates with32px difficulty marks. Review captures and the isolated site-sync check accompany this delivery. The preview uses Georgia; the live site's display font still needs the integration check above. No app code or public art was edited by the artist in this pass.

## Patron rewards delivered previously — retain and sync

The reward delivery remains complete and is included here so Claude has one handoff. The following contracts are unchanged.

### Delivered under the existing `supporter` ID

Source root: `C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/`.

- Outfit: **Patron's Regalia**, deep wine and gold with shield/hammer/spark shoulder heraldry. Cosmetic only. No stats, rank changes or new entitlement rules.
- Four sheets: `characters/presets/{body_a,body_b}/supporter_{melee,caster}/sheet.png`. Each512×768, four columns and six rows of128×128 frames.
- Row order: idle, attack, cast, hit, victory, defeat. Four frames per row. Idle5fps; other rows8fps. Idle/victory loop; attack/cast/hit/defeat are one-shot, exactly as existing metadata specifies.
- Melee uses sword+shield; caster uses staff+orb. The local export positions the orb above the glove so it remains visible. All sprites use the current modular animation rig and its occlusion rules; hood opening was cleared so the face is visible.
- Eleven32×32 icons: `gear/icons/set_supporter_<type>.png`, where type is head, chest, legs, feet, hands, shoulders, back, sword, shield, staff or orb. **Chest is the wardrobe tile icon.** The main item slots remain weapon/offhand for sword/staff and shield/orb.
- Also included: `atlases/set_supporter.png`, cropped gear sprites,22 fitted wearable layers and matching base-occlusion masks. Existing metadata fields point to their files.
- Avatar: `profile-decorations/avatar/14-supporter.png`,48×48, clear radius17.5 around centre24,24; wine enamel/gold and a small top heart. Same photo contract as existing decorations.
- Card: `profile-decorations/card/14-supporter.png`,352×252, card rect320×220 at16,16, existing44px corner slices and thin registered edge rails. Transparent content area and heart corner crests.
- Profile frames are **static**. Optional animated frame variants were not required and were not added. The outfit has all six animation states.

### Metadata updated

- `metadata/pack.json`: one new `sets` entry,11 new `items`, new atlas entry; existing entries preserved.
- `metadata/pack.js`: kept in step with the JSON for source-pack previews.
- `metadata/character-presets.json`: four `supporter` presets with existing animation contracts and complete equipment IDs.
- `profile-decorations/manifest.json`: supporter theme and two static frame entries; existing themes/animations preserved.

These are main character/decorations assets, **not website-art interface assets**. No new entries belong in `website-art/manifest.json`. No existing art was retired by this delivery.

### Website integration

Run the existing `tools/sync_art.py` with the configured Python environment from Unrealcraft. It already recognizes the paths and strips `14-` to produce the `supporter` decoration key. Expected resulting manifest entries:

- `presets.body_a.supporter.melee` and `.caster`
- `presets.body_b.supporter.melee` and `.caster`
- `sets.supporter.name = "Patron's Regalia"`
- `icons.supporter = "gear/icons/set_supporter_chest.png"`
- `decorations.avatar.supporter` and `decorations.card.supporter`

Keep the existing API gate: the `supporter` medal unlocks the already-defined outfit/avatar/card entitlements. Do not grant medals or bypass that gate merely because the art now exists. The artist did not alter the app, Support-page copy, accounts or grants.

After sync, verify the Support-page reward display and the existing wardrobe/Edit profile selections with an authorized test account. Equip both body/style combinations, check sword/shield versus staff/orb, run a quiz fight and confirm the frame alignment at desktop and narrow widths. A non-supporter should retain the existing locked behaviour.

### Validation and preview

`supporter/index.html` shows the four loadouts and all24 animation previews; `supporter/preview.png` is the static overview. Preview WebPs loop for review, while the site's sheet metadata retains the one-shot actions. Do not use those review loops instead of the character sheets in production.

`supporter/qa.json`: four sheets,96 nonempty pose frames, no boundary clipping, binary alpha,11 correctly sized icons and clear avatar/card openings. Browser preview:25 images loaded with no broken sources. `supporter/sync-validation.json` records the website-sync contract check.

