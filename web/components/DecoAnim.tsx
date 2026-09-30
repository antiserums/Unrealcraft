/** Decoration overlays. Nothing cycles frames (that looked jittery); special themes get a soft glow that breathes
 *  like the staff title, in the same colour. */
const GLOW: Record<string, string> = { developer: "#3FB6B0" };   // the ring and border art is already bright; the halo uses the colour at 60% (see .pcard-deco.glow)

/** The card border overlay: a 9-slice drawn in the gutter around the card, fading in when a decoration is on. */
export function CardDeco({ src, theme }: { src: string | null; theme?: string }) {
  const glow = theme ? GLOW[theme] : undefined;
  return <div className={`px pcard-deco ${src ? "on" : ""} ${glow ? "glow" : ""}`} style={src ? ({ borderImageSource: `url("${src}")`, "--deco-glow": glow } as React.CSSProperties) : undefined} aria-hidden="true" />;
}

/** The ring around the avatar photo. */
export function AvatarDeco({ src, theme }: { src: string | null; theme?: string }) {
  const glow = theme ? GLOW[theme] : undefined;
  return src ? <img className={`px deco-avatar ${glow ? "glow" : ""}`} src={src} alt="" aria-hidden="true" style={glow ? ({ "--deco-glow": glow } as React.CSSProperties) : undefined} /> : null;
}
