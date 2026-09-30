import type { ReactNode } from "react";
import { loadManifest, siteArt } from "@/lib/art";

/** Pieces drawn from the pack's website-art folder. Each one falls back to the plain version when the art is
 *  missing, so the site still reads the same without the pack. */

/** A page title on its 960 x 160 header strip. The strip's centre is kept dark for the words. */
export async function PageHeader({ art, title, eyebrow }: { art: string; title: ReactNode; eyebrow?: ReactNode }) {
  const m = await loadManifest();
  const src = siteArt(m, art);
  if (!src) return <>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1></>;
  const narrow = siteArt(m, `${art}-narrow`) ?? src;           // a 480 x 160 centre crop for phones
  return (
    <header className="page-header" style={{ "--hdr": `url("${src}")`, "--hdr-narrow": `url("${narrow}")` } as React.CSSProperties}>
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      <h1>{title}</h1>
    </header>
  );
}

/** A card with a small illustration beside the words: empty lists, locked things, a page that is not there. */
export async function Spot({ art, children }: { art: string; children: ReactNode }) {
  const src = siteArt(await loadManifest(), `${art}`);
  return (
    <div className={`card spot ${src ? "" : "muted"}`}>
      {src && <img className="px" src={src} width={160} height={120} alt="" />}
      <div>{children}</div>
    </div>
  );
}

/** A 32 px pixel icon, drawn at a whole-number scale. */
export function Px({ src, scale = 1, className = "" }: { src: string | null | undefined; scale?: 1 | 2; className?: string }) {
  if (!src) return null;
  return <img className={`px pxi ${className}`} src={src} width={32 * scale} height={32 * scale} alt="" />;
}
