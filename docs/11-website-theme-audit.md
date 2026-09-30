# Website art audit — 30 September 2026

Audited the running site at http://localhost:3000 and all 24 page route templates in `Unrealcraft/web/app`. Public pages were reviewed in the browser; authenticated gameplay, profile editing, review and admin states were checked from source. No quizzes, submissions, reviews or account settings were changed.

## What was already working

The site already loads the earlier website-art pack through `tools/sync_art.py`, `siteArt()` and `siteArtGroup()`. The town banner, page headers, interface borders, step icons, arena selection and named high-tier achievement badges have integration code. The public player card uses the existing developer decoration and outfit successfully. Preserve those assets and their geometry.

## Gaps addressed by this delivery

- Website theme skin: four states each for form fields, tabs, message panels and inventory slots; a tooltip plate and vertical scrollbar parts. Includes slice metadata, repeatable edges, example CSS and a browser-checked theme preview.
- Combat: vitality, wounds, steady, focus, craft, critical hits, all three actual debuffs, hints, retreat and victory; a rest illustration for defeat.
- Quest progress and review: todo, next, done, skipped, locked, pending, changes, fail, required, elective, capstone and proof. Pending chest illustration matches the submission state.
- Controls: search, filters, navigation, disclosure, sharing, editing, saving, visibility, help and language.
- Identity: separate developer, admin and mentor crests; Senior and Lead presentation crests for the guild ladder. These do not grant roles or alter rank rules.
- Achievements: eight named foundation badges complete the 17 seeded achievement keys alongside the previous nine advanced badges. Runtime rank medals keep the legacy fallback.
- Rewards: XP, streak, outfit, avatar frame, card frame, title, colour and rank advancement.
- Banner controls: four seasons, local clock, dawn/day/dusk/night, play, pause and still image.
- Missing page decoration: guild, library, player chamber, review study and admin command room headers; login and connection-error illustrations.

## Route coverage and intended placements

| Route / screen | Audit method | Art decision |
|---|---|---|
| `/` | Live + source | Keep living town; use banner-controls and rewards in existing controls/stats. |
| `/quests` | Live + source | Keep header-quests; quest-state badges and utility search/filter. Existing difficulty icons already work. |
| `/path` → `/quests?view=path` | Source | Keep header-path and locked-gate; use quest-state now/done/skipped. |
| `/quests/[id]` | Live O1 + source | Replace step emoji with existing quest-steps; use quest-state for checklist and chest status. |
| `/quests/[id]/fight` | Source, login required | Combat-status icons; rest-and-retry for lose; existing quest-complete for win. Existing sprites and arenas stay. |
| Submission / chest | Source, login required | chest-pending while awaiting review; existing quest-complete when accepted; changes/fail icons with reviewer text. |
| `/how-it-works` | Live + source | header-library; keep existing four steps, specialization icons and rank crests. |
| `/mission` | Live + source | header-guild. |
| `/leaderboard` | Live + source | Keep header-leaderboard; staff crests alongside staff labels, earned rank crests alongside ranks. |
| `/members/[id]` | Live public card + source | Optional header-player above card; preserve exact card and avatar frame sizing. |
| `/me` | Source, login required | header-player; utility sharing/privacy/save and rewards category icons in CardStudio. |
| `/me/wardrobe` | Source, login required | Keep header-wardrobe and fitted preset sprites; existing set icons; utility controls only. |
| `/me/achievements` | Source, login required | Keep header-achievements; add eight named foundation mappings. |
| `/review` | Source, staff required | header-review, mentor crest, quest-state pending; keep sleeping-dragon empty state. |
| `/review/[id]` | Source, staff required | Same header; done/changes/fail next to verdict labels. |
| `/admin` | Source, staff required | header-admin, staff-crests, search/filter controls. |
| `/admin/members/[id]` | Source, staff required | Staff crest and utility controls; retain player-card decoration contract. |
| `/admin/quests` | Source, staff required | header-admin, existing quest-board icon, utility controls. |
| `/admin/quests/[id]` | Source, staff required | utility edit/save/proof and quest-state markers; keep form mostly text. |
| `/admin/entitlements` | Source, staff required | rewards category icons; preserve numeric legacy badge picker until Claude adds named assets. |
| `/faq` | Live + source | header-library and utility expand/collapse/help. |
| `/changelog` | Live + source | header-library as optional shared archive header; retain readable release text. |
| `/login` | Live + source | guild-entry beside sign-in explanation; keep provider name as website text. |
| `/privacy`, `/terms` | Live + source | Existing quiet panel/divider is sufficient; no new decorative scene needed. |
| Not found | Source | Existing lantern-signpost already covers it. |
| Loading / service failure | Source | quest-state/pending for busy; connection-lost for failed requests with retry text. |

## Integration findings for Claude

1. **Use the current sync directly.** It already reads arbitrary manifest groups and emits `website_art.images` and `website_art.arenas`. Earlier handoff instructions to extend the Manifest type or patch arena selection are obsolete. The optional standalone helper has been updated to emit this current shape too.
2. **Environment Art is `lookdev`.** `specArtId()` already maps it correctly. The original handoff's `environment_art` example was wrong and is corrected.
3. The remaining emoji are in `Fight.tsx`, `Chest.tsx`, `PathView.tsx`, quest detail headings, `CardStudio.tsx`, `HeroBanner.tsx`, and some rank summaries. Replace decorative marks with PNGs where useful, while keeping visible accessible labels.
4. Native `<option>` elements cannot reliably contain images. Keep their text labels; show art beside the closed control or selected summary instead.
5. New staff art is presentation only. Do not determine permissions from a crest, numeric rank, or a filename. Use the existing API staff role. Senior/Lead assets are reserved until the actual catalog supplies those labels.
6. Pixel presentation still has application-level limitations: responsive fractional scaling, CSS soft glow on the old developer card, and 34x42 achievement image boxes can differ from the latest strict style. Use 32x32 or 64x64 for these square icons, `image-rendering: pixelated`, and avoid applying new blur/drop-shadow effects. This delivery does not rewrite those components.
7. No combat animation or armour rework is implied by this audit. The existing preset sheets and aligned layers stay authoritative; new status icons do not modify gameplay.

## Verification limits

The source audit covers every route template and the shared art-bearing components. Browser review covers public routes and a public player card. Authenticated layouts still need Claude's logged-in visual check after wiring the new images. Asset validation checks export dimensions, palette, binary transparency, padding, crop equality and manifest resolution. It cannot prove that every application state has been wired by Claude.
