# Statistics screenshot: art and CSS diagnosis

User screenshot received 30 September 2026. Checked against canonical PNGs and current web/app/globals.css.

## Section dividers — application layout

At globals.css:610, `.section-h::after` has height 16px but the divider background is drawn at 512px 32px. This clips the 2x image vertically. The source PNG also has considerable horizontal transparent padding, which makes the visible ornament start away from the heading edge. The same rule affects both circled statistics headings.

Choose one whole-number size, and give the pseudo-element its full height. A compact fix using the existing asset is:

```css
html.site-art .section-h { padding-bottom: 20px; }
html.site-art .section-h::after {
  left: 0; right: auto; bottom: 0;
  width: 256px; max-width: 100%; height: 16px;
  background: url('/art/website-art/interface/divider-gem.png') left center / 256px 16px no-repeat;
  image-rendering: pixelated;
}
```

If using 2x, reserve 32px height and corresponding heading padding. Do not stretch the entire ornament to arbitrary heading widths. The artist is supplying a tighter divider and a repeatable section plate in the refinement delivery; their manifest dimensions supersede this fallback snippet when selected.

## Progress bar — shared art and application issues

- Artist: progress-track has decoration inside the stretchable region. Repeating that region duplicates ornaments. Replace with the refined track with plain middle and ornaments restricted to the 5px caps.
- Application: globals.css:699 positions progress-fill at positive y=5px. Its opaque rows are already y=5..10 in the source, so they land y=10..15 in a 6px-high span and are hidden. Use y=-5px at native scale, or use the new tightly cropped fill strip.
- Application: `.bar.big > span` scales the image to 192x24 (1.5x) and positions it at +7px. That also clips the fill and breaks the whole-pixel grid. Use a native-height fill strip repeated horizontally, or an integer 2x strip.
- Application: `background: ... !important` on all bar spans overrides the hero/boss health colours. Scope gold art to XP bars; preserve green/red health presentation or use supplied colour-specific strips.

Check 0%, 25%, 50%, 100%, narrow and wide bars, and both health-bar sides. Ensure no fill crosses the end caps. Text, progress percentage and bar semantics stay in application code.

This note identifies the source and proposed fix; it does not claim the live CSS has been edited.
