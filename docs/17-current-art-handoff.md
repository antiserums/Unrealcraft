# Claude handoff: Support-page Patron rewards

2026-09-30. Single current handoff, responding to `docs/19-artist-handoff.md`. The **website remains the objective**: this delivery fills the existing Support-page reward placeholders. Prior theme work is already integrated according to that document.

## Delivered under the existing `supporter` ID

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

## Metadata updated

- `metadata/pack.json`: one new `sets` entry,11 new `items`, new atlas entry; existing entries preserved.
- `metadata/pack.js`: kept in step with the JSON for source-pack previews.
- `metadata/character-presets.json`: four `supporter` presets with existing animation contracts and complete equipment IDs.
- `profile-decorations/manifest.json`: supporter theme and two static frame entries; existing themes/animations preserved.

These are main character/decorations assets, **not website-art interface assets**. No new entries belong in `website-art/manifest.json`. No existing art was retired by this delivery.

## Website integration

Run the existing `tools/sync_art.py` with the configured Python environment from Unrealcraft. It already recognizes the paths and strips `14-` to produce the `supporter` decoration key. Expected resulting manifest entries:

- `presets.body_a.supporter.melee` and `.caster`
- `presets.body_b.supporter.melee` and `.caster`
- `sets.supporter.name = "Patron's Regalia"`
- `icons.supporter = "gear/icons/set_supporter_chest.png"`
- `decorations.avatar.supporter` and `decorations.card.supporter`

Keep the existing API gate: the `supporter` medal unlocks the already-defined outfit/avatar/card entitlements. Do not grant medals or bypass that gate merely because the art now exists. The artist did not alter the app, Support-page copy, accounts or grants.

After sync, verify the Support-page reward display and the existing wardrobe/Edit profile selections with an authorized test account. Equip both body/style combinations, check sword/shield versus staff/orb, run a quiz fight and confirm the frame alignment at desktop and narrow widths. A non-supporter should retain the existing locked behaviour.

## Validation and preview

`supporter/index.html` shows the four loadouts and all24 animation previews; `supporter/preview.png` is the static overview. Preview WebPs loop for review, while the site's sheet metadata retains the one-shot actions. Do not use those review loops instead of the character sheets in production.

`supporter/qa.json`: four sheets,96 nonempty pose frames, no boundary clipping, binary alpha,11 correctly sized icons and clear avatar/card openings. Browser preview:25 images loaded with no broken sources. `supporter/sync-validation.json` records the website-sync contract check.

Optional small polish in request19 was left unchanged: button alignment, statistics icon contrast and28px tier plates. Request19 explicitly permits the existing tier overhang. Keep its listed unused assets in the pack as requested; no further cleanup was performed.

Use `docs/19-artist-handoff.md` for the site's status and this document for the new delivery. Older artist handoffs are historical records.
