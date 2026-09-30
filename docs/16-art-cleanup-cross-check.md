# Claude: cross-check retired website art

2026-09-30. This supersedes earlier inventory counts. Current pack: **70 groups, 262 canonical PNGs**. The user requested unused art be removed and the website checked against the newer sources.

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
| scrollbar-parts | scrollbar/track, scrollbar/thumb, scrollbar/thumb-hover; see docs/15 |

The old `theme.css` and `theme-preview.html/png` were retired because they reference obsolete artwork. Use `refinement.css`, `refinement-preview.html` and the current manifest. Earlier screenshots and historical handoffs may show retired art; they are records, not the active asset contract.

## Kept deliberately

- Old `button-plates` and `tab-plates`: still referenced in `globals.css:637` and `668–673`. Fix logout/banner overrides and profile tabs as described in `docs/15-scrollbar-and-profile-controls.md`, then retire these groups in a second pass. Do not delete active dependencies first.
- `navigation-16`: despite the note saying unused in the top bar, `HeroBanner.tsx:95` uses its settings icon through `<Ico group="navigation" id="settings" size={16}>`. Keep this set unless that use is migrated.
- 480px arenas: retained as logical layout/source assets for the 4× exports.
- Character art, customization, profile frames, banner seasons/animation and rarity art: outside this confirmed website-theme retirement list. Rarity art has pending integration, so it is not classified as waste.

## Website cross-check and removal order

1. Read `retired-assets.json` from the current source pack. Search both literal `/art/website-art/` URLs and dynamic `Ico`/`siteArt` lookups; scanning filenames alone misses generated paths.
2. Confirm old IDs have no active consumers. Switch any remaining uses to the replacement IDs above. Resolve the controls in docs/15 before retiring old button/tab families.
3. Run the existing website art sync. Verify its merged `website_art.assets` and `images` no longer retain removed groups/frame IDs. Sync copying does not imply obsolete files were deleted.
4. Remove only the exact retired runtime paths under `web/public/art/website-art/` listed in the ledger after verifying they have no consumers. Skip source/prompts/preview paths if they were never deployed. Do not broadly delete the public art directory or touch unrelated art.
5. Check CSS URLs, dynamic icon URLs and the merged manifest for missing files. Review authenticated logout/profile tabs/Edit wardrobe/Change/Cancel, the progress bars, headings and scrollbar. Check hover/active/disabled/focus states and phone width.
6. After migrating old button/tab consumers, add their paths and replacements to the ledger and remove them from both source and public output.

The artist cleaned the source pack only. Public website copies and application code were left for Claude's requested cross-check. Recoverable copies are outside UCSourceArt at `C:/Users/killt/Documents/Codex/2026-09-29/please/outputs/retired-website-art-2026-09-30/`. No broad legacy/character asset deletion was performed.
