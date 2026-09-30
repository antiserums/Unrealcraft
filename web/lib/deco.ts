/** Client-safe helpers for the card decorations (no filesystem imports). */
import type { CSSProperties } from "react";

export type Inset = { top: number; right: number; bottom: number; left: number };

/** Gutter padding (CSS px) so a card border's band hugs the card: the band's inner edge at 2x, plus a hair. */
export function gutterFor(inset: Inset | undefined): CSSProperties {
  const i = inset ?? { top: 16, right: 10, bottom: 16, left: 10 };
  return { paddingTop: i.top * 2 + 2, paddingRight: i.right * 2 + 2, paddingBottom: i.bottom * 2 + 2, paddingLeft: i.left * 2 + 2 };
}
