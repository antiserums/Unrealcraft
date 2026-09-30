/** Client-safe helpers for the card decorations (no filesystem imports).
 *  The card is 640 x 440 and border art is 352 x 252 at 2x with the card in its centre 320 x 220, so the gutter
 *  around the card is a constant 32 px on every side, decoration or not. That constancy is what keeps the card
 *  from moving when a decoration is switched on or off. */
import type { CSSProperties } from "react";

export const GUTTER = 32;
export const gutter: CSSProperties = { padding: GUTTER };
