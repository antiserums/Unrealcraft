# Player card: exact dimensions for decoration art

Everything below is measured from the live site (`web/components/PlayerCard.tsx`, `web/app/globals.css`).
The card is a fixed canvas now, so art can be drawn to it exactly. Pixel art is shown at **2x**: one source
pixel = two screen pixels. "Source px" below means pixels in the PNG you deliver; "screen px" is what the site shows.

## The card (screen px, top-left origin)

| Part | x | y | width | height |
|---|---|---|---|---|
| Whole card | 0 | 0 | **640** | **440** |
| Border | 1 px solid `#A67F2E`, corner radius 8 px | | | |
| Header band (rank pill left, major right) | 1 | 1 | 638 | 52 |
| Body | 1 | 53 | 638 | 366 |
| Avatar photo (circle) | 19 | 83 | 64 | 64 |
| Name and motto (single line each) | 97 | 85 | up to 380 | 37 + 20 |
| XP bar block | 19 | 174 | 414 | 59 |
| Stats row | 19 | 247 | 414 | 82 |
| Character sprite | 451 | 71 | 170 | 258 |
| Featured achievements row | 19 | 343 | 602 | 58 |
| Footer band (text left and right) | 1 | 419 | 638 | 34 |

In source px (divide by 2): the card is **320 x 220**, header rows 0 to 26, footer rows 210 to 220,
avatar circle 32 px wide at (10, 42).

## Card border: what to deliver

One PNG per theme, **352 x 252 source px**, transparent everywhere except the art.

- The card occupies the centre **320 x 220** rectangle, from (16, 16) to (336, 236). Draw nothing opaque
  inside it except the allowances below. The site draws the card there; your art goes on top.
- The 16 px margin all around is for ornaments that hang outside the card.
- **Band:** 3 to 4 px thick, straddling the card edge: from 14 to 18 px on every side (so half outside, half
  over the card's own 1 px gold border). Same on all four sides, same on every theme. This is the one rule
  that stops the "cut off" problem: the site places the art so that x = 16 lands exactly on the card edge.
- **Corners:** may extend outward into the margin and inward up to a **28 x 28** source px square measured
  from the card corner. The header and footer text starts 32 px in from each side, so nothing is covered.
- **Edges away from corners:** ornaments may reach inward at most **6 px** past the band (to x or y = 22)
  along the top and bottom edges, and **4 px** along the left and right edges. Centre ornaments on the top
  edge (gems, crowns, moons) are fine within that; larger ones should hang outward into the margin instead.
- Corner radius of the card is 8 screen px = 4 source px; round the band's corners to match or square them,
  either reads fine.
- Deliver **exactly the same layout for all ten themes**. The site uses the same placement for every file.

The site will slice the PNG 9-way (corners 44 x 44, edges repeated) so the same file also fits the card on
narrow screens. Keep edge patterns tileable along their length: no single ornament that only works at the
exact centre unless it is small enough to repeat.

## Avatar ring: what to deliver

One PNG per theme, **48 x 48 source px** (shown at 96 screen px), transparent centre.

- The photo is a 32 px circle (64 screen px) centred in the canvas: centre (24, 24), radius 16.
- **Aperture:** leave a clear circle of at least **35 px diameter** (radius 17.5) so the photo never touches
  the ring: nothing opaque within radius 17 of the centre.
- **Band:** 2 to 3 px thick, from radius 17.5 to about 20.5.
- Ornaments (gems, leaves, horns) sit outside the band, within the 48 x 48 canvas; keep them off the top
  edge row 0 and the bottom row 47 so nothing clips.
- Same layout for all ten themes.

## File names and ids

Keep the current names and folders; the sync script reads them as they are:

```
profile-decorations/card/NN-<theme>.png      352 x 252
profile-decorations/avatar/NN-<theme>.png    48 x 48
```

Themes in order: novice, apprentice, adept, expert, master, thornwood, emberforge, frostbound, celestial,
dragonheart. Once these land, the site drops its per-theme measuring and uses a fixed 16 px inset for every
theme (`tools/sync_art.py`, `web/lib/deco.ts`).
