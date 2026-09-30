"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type { SheetSpec } from "@/lib/art";
import { Character, RARITY_COLOR } from "./Figure";

export type Outfit = { id: string; name: string; flavour: string; kind: string; major: string; tier: string; color: string; art_id: string; owned: boolean; earned_at: string | null; hint: string | null; worn: boolean };
export type Char = {
  worn: Outfit; outfits: Outfit[]; new_outfits: string[]; style: string; body: string; styles: string[];
  cosmetics: { nameplate?: string; banner?: string; appearance?: Record<string, string>; outfit?: string; style?: string };
  nameplate_colors: string[]; slots: string[]; major: string;
};
/** sheets: body -> style -> set -> sheet, so a try-on can show any set in any style without a round trip. */
export type ArtProps = { sheets: Record<string, Record<string, Record<string, SheetSpec>>>; icons: Record<string, string>; bodies: string[] };
/** What the closet is currently showing (worn or tried on), for a parent that draws the preview itself. */
export type TryOn = { outfit: Outfit; style: string; body: string; sheet: SheetSpec | null };

const TIER_NAME: Record<string, string> = { novice: "Novice", apprentice: "Apprentice", adept: "Adept", expert: "Expert", master: "Master" };
const RARITY_OF_TIER: Record<string, string> = { novice: "common", apprentice: "uncommon", adept: "rare", expert: "epic", master: "legendary" };
const STYLE_LABEL: Record<string, string> = { melee: "Sword & shield", caster: "Staff & orb" };
const BODY_LABEL: Record<string, string> = { body_a: "Athletic", body_b: "Curved" };
type Kind = "all" | "rank" | "reward";
const KIND_LABEL: Record<Kind, string> = { all: "All", rank: "Rank", reward: "Reward" };
const TIER_ORDER = ["novice", "apprentice", "adept", "expert", "master"];

/** The closet. With `mirror` (default) it draws its own figure on the left; with `mirror={false}` the parent shows
 *  the preview (the player card) and gets every selection through `onPreview`. Wear, weapons and build save as picked. */
export default function CharacterSheet({ initial, fallbackColor, art, mirror = true, onPreview }:
  { initial: Char; fallbackColor: string; art: ArtProps; mirror?: boolean; onPreview?: (t: TryOn) => void }) {
  const router = useRouter();
  const [c, setC] = useState<Char>(initial);
  const [busy, setBusy] = useState(false);
  const [kind, setKind] = useState<Kind>("all");
  const [showLocked, setShowLocked] = useState(true);
  const [selectedId, setSelectedId] = useState<string>(initial.worn.id);
  const color = c.cosmetics.nameplate ?? fallbackColor;
  const selected = c.outfits.find((o) => o.id === selectedId) ?? c.worn;
  const owned = c.outfits.filter((o) => o.owned).length;
  const sheet = art.sheets[c.body]?.[c.style]?.[selected.art_id] ?? null;
  const hasArt = Object.keys(art.sheets).length > 0;

  useEffect(() => { onPreview?.({ outfit: selected, style: c.style, body: c.body, sheet }); }, [selected, c.style, c.body, sheet]);  // eslint-disable-line react-hooks/exhaustive-deps

  const shown = useMemo(() => c.outfits
    .filter((o) => kind === "all" || o.kind === kind)
    .filter((o) => showLocked || o.owned)
    .sort((a, b) => Number(b.owned) - Number(a.owned) || TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier) || a.name.localeCompare(b.name)),
  [c.outfits, kind, showLocked]);

  async function patch(body: Record<string, unknown>) {
    setBusy(true);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) { setC(await r.json()); router.refresh(); }   // the figure on the player card is rendered on the server
    setBusy(false);
  }
  const trying = selected.id !== c.worn.id;

  const detail = (
    <div className="mirror-detail">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline" }}>
        <b style={{ color: selected.color, fontSize: 17 }}>{trying ? "Trying on: " : ""}{selected.name}</b>
        <span className="small muted">{TIER_NAME[selected.tier]} · {selected.kind} set</span>
      </div>
      <div className="small" style={{ margin: "4px 0 10px" }}><i>{selected.flavour}</i></div>
      {selected.owned ? (
        <div className="row">
          {selected.worn ? <span className="status now">✔ Wearing this</span> : <button className="primary" onClick={() => patch({ wear: selected.id })} disabled={busy}>Wear it</button>}
          {selected.earned_at && <span className="small muted">earned {selected.earned_at.slice(0, 10)}</span>}
        </div>
      ) : (
        <div className="note small">🔒 {selected.hint ?? "Not yet earned."}</div>
      )}
    </div>
  );
  const controls = (
    <div className="mirror-detail">
      <div className="row" style={{ gap: 18, alignItems: "flex-start" }}>
        <div>
          <div className="small muted">Weapons</div>
          <div className="subnav" style={{ margin: "6px 0 0" }}>
            {c.styles.map((s) => <a key={s} href="#" className={c.style === s ? "on" : ""} onClick={(e) => { e.preventDefault(); if (!busy && s !== c.style) patch({ style: s }); }}>{STYLE_LABEL[s] ?? s}</a>)}
          </div>
        </div>
        {art.bodies.length > 1 && (
          <div>
            <div className="small muted">Build</div>
            <div className="subnav" style={{ margin: "6px 0 0" }}>
              {art.bodies.map((b) => <a key={b} href="#" className={c.body === b ? "on" : ""} onClick={(e) => { e.preventDefault(); if (!busy && b !== c.body) patch({ appearance: { body: b } }); }}>{BODY_LABEL[b] ?? b}</a>)}
            </div>
          </div>
        )}
      </div>
      {!hasArt && <p className="small muted" style={{ margin: "8px 0 0" }}>Character art arrives with the art pack.</p>}
    </div>
  );

  const rack = (
    <div className="card rack">
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
        <div className="eyebrow">Outfits <span className="muted" style={{ letterSpacing: 0, textTransform: "none" }}>· {owned} of {c.outfits.length} earned</span></div>
        <label className="row small muted" style={{ gap: 6, cursor: "pointer" }}>
          <input type="checkbox" checked={showLocked} onChange={(e) => setShowLocked(e.target.checked)} /> show unearned
        </label>
      </div>
      <div className="subnav" style={{ marginBottom: 12 }}>
        {(Object.keys(KIND_LABEL) as Kind[]).map((k) => (
          <a key={k} href="#" className={kind === k ? "on" : ""} onClick={(e) => { e.preventDefault(); setKind(k); }}>{KIND_LABEL[k]}</a>
        ))}
      </div>
      <div className="tiles" role="listbox" aria-label="Outfits">
        {shown.map((o) => {
          const rc = RARITY_COLOR[RARITY_OF_TIER[o.tier]] ?? "#888";
          const icon = art.icons[o.art_id];
          return (
            <button key={o.id} type="button" role="option" aria-selected={o.id === selected.id} title={`${o.name} · ${TIER_NAME[o.tier]}`}
              className={`tile ${o.owned ? "" : "locked"} ${o.worn ? "worn" : ""} ${o.id === selected.id ? "selected" : ""}`}
              style={{ "--rc": rc } as React.CSSProperties} onClick={() => setSelectedId(o.id)}>
              {icon ? <img className="px" src={icon} alt="" /> : <span className="tile-swatch" />}
              {o.worn && <span className="tile-mark">✔</span>}
              {!o.owned && <span className="tile-lock">🔒</span>}
              {c.new_outfits.includes(o.id) && <span className="tile-new">new</span>}
            </button>
          );
        })}
        {shown.length === 0 && <div className="small muted">Nothing here yet.</div>}
      </div>
      {!mirror && <>{detail}{controls}</>}
      <div className="small muted" style={{ marginTop: 12 }}>Click a set to try it on{mirror ? " in the mirror" : ""}. Outfits change your look only, never a fight.</div>
    </div>
  );

  if (!mirror) return rack;
  return (
    <div className="closet">
      <div className="card mirror">
        <div className="eyebrow">{trying ? "Trying on" : "Wearing"}</div>
        <div className="mirror-stage">
          <Character outfit={selected.id} sheet={sheet} weapon={c.style} color={color} size={190} scale={2} />
        </div>
        {detail}
        {controls}
      </div>
      {rack}
    </div>
  );
}
