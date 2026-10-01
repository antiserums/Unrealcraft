# Claude handoff: rank banner unlocks, website theme polish and Patron rewards

2026-09-30. Single current artist handoff. The newest delivery is four entirely new rank-unlocked banner locations. Earlier website-theme and Patron integration notes remain below.

## New rank banners — ready for integration

Source folder: **C:/Users/killt/Documents/GitHub/UCSourceArt/pixel-v3/banners/rank-banners/**.

| Unlock rank | ID / minRank | Scene |
| --- | --- | --- |
| Apprentice | apprentice / 1 | Mossgate Guild Outpost: ancient oak, training yard, forest stream and watermill |
| Adept | adept / 2 | Moonmere Academy: lakeside observatory, crystal telescope and island shrine |
| Expert | expert / 3 | Emberfall Bastion: dragon-guarded mountain fortress, causeway and hydraulic forge |
| Master | master / 4 | Crown of the Aether: floating celestial capital, garden canal and cascading islands |

These are different locations with different layouts, not recolors or upgrades of the original town. The user explicitly requested completely new scenes. Early town-remix drafts were discarded and are not delivered. Keep the original living-town as the starting/default choice.

### Feature parity and files

Every scene has animated water/waterfalls, foliage, drifting sky detail, a turning wheel interior, three walking people, two workers, spring/summer/autumn/winter, seasonal particles, local device time, manual hour, dawn/day/dusk/night, pause, reduced motion and hidden-tab suspension. Water and sky masks, wheel occlusions and walking routes are authored separately for each scene.

- Four per-rank living-town.js entry modules export **LivingTown**, compatible with HeroBanner's current constructor/method interface.
- shared/living-scene.js and shared/people.png are required shared dependencies; keep this relative folder structure.
- Each rank has assets/scene.png and assets/masks.png at **960×320**. Masks are technical data, never display them.
- Eight seasonal day/night PNG stills per rank: **32 stills** total.
- Four seasonal daytime WebP loops per rank: **16 loops**, each24 seconds /192 frames /8fps. Live renderer targets12fps. These are fallbacks/review loops; only the live component follows the visitor's clock.
- manifest.json records unlock IDs/minimum rank numbers, entry modules, stills, loops, alt text and runtimeFiles. Use that allowlist; source/ and qa/ are not production dependencies.

### Required Claude integration

1. Extend tools/sync_art.py: it currently syncs only banners/living-town. **Running it unchanged will not install these new banners.** Copy the delivered sync_rank_banners.py helper next to sync_art.py, import sync_rank_banners, and assign **m["rank_banners"] = sync_rank_banners(PACK, OUT)** before saving the site manifest. Alternatively implement the equivalent allowlist copy and mapping. The helper returns paths relative to public/art, matching the existing manifest convention. It does not overwrite existing living_town entries.
2. Extend web/lib/art.ts to read rank_banners and apply the existing /art/ URL prefix. Each selected scene supplies script, stills and seasons, compatible with the current LivingTownArt object; retain name, alt and minRank for selection UI.
3. Add banner selection to the existing banner settings controls. Use the member's authoritative RPG rank: the current API maps1 Apprentice,2 Adept,3 Expert,4 Master. Unlock all banners where minRank <= member rank, keeping earlier choices available. Default new visitors/Novices to the original town. Validate a saved selection against current unlocks; do not trust a local-storage value to grant access. No ranks or rewards were granted by the artist.
4. Pass the selected scene object to HeroBanner. Destroy the old instance on selection change, then initialize the new module. Keep season, time and pause choices when switching; use the same controls and reduced-motion behavior. Set canvas accessible text from the scene's alt description rather than the existing town-only description.
5. Keep source960×320 and responsive3:1, image-rendering:pixelated. No smooth resizing or different crop per rank. The module resolves its own assets relative to its URL; do not flatten folders or copy just the scene PNG.
6. Keep local time as the default and the manual override choices. For fallback stills in local mode, choose day/night using the device's current hour. The current HeroBanner fallback expression only tests the manual hour and otherwise picks day; fix that when adding these scenes so a failed/reduced-motion fallback at night does not show daylight.
7. Verify every unlock boundary (0–4), saved earlier-rank choice, unavailable selection fallback, all four seasons, manual dawn/day/dusk/night, local clock, pause/play, reduced motion, narrow layout and repeated banner switching. The art preview is intentionally ungated so all ranks can be reviewed.

### Review and validation

Serve index.html in the rank-banners folder for an interactive review. overview.png is the four-location contact sheet. Per-rank qa/seasons-day-night.png shows all seasonal stills. validation.json records all six moving layers, zero changed pixels outside water/foliage/sky/wheel masks, local/manual time, reduced motion and exact24-second cycle seams. browser-validation.json and sync-validation.json describe their separate checks and scope.

The artist has not edited the website app or live public art. This delivery requires the sync extension and selector/unlock wiring above. All existing main-banner and website-theme art remains available; no art was retired in this delivery.

---

## Previous delivery: website theme polish and Patron rewards

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

