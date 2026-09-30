"use client";
import { useState } from "react";
import { Character, GearDot, type GearMap } from "./Figure";

type Item = { id: number; slot: string; rarity: string; name: string; flavour: string | null; stat: string; bonus: number; equipped: number; source_quest: string | null; set_piece: number };
export type Char = {
  stats: Record<string, number>; stat_blurb: Record<string, string>; gear_totals: Record<string, number>;
  equipped: Record<string, Item>; inventory: Item[]; cosmetics: { nameplate?: string; banner?: string }; nameplate_colors: string[]; slots: string[]; major: string;
};
const SLOT_LABEL: Record<string, string> = { head: "Head", body: "Body", hands: "Hands", feet: "Feet", main: "Main hand", trinket: "Trinket" };
const EFFECT: Record<string, string> = { lore: "Lore", craft: "Craft", dodge: "dodge chance", cleanse: "cleanses a debuff", focus: "Focus" };

export default function CharacterSheet({ initial, fallbackColor }: { initial: Char; fallbackColor: string }) {
  const [c, setC] = useState<Char>(initial);
  const [busy, setBusy] = useState(false);
  const color = c.cosmetics.nameplate ?? fallbackColor;
  const gear: GearMap = Object.fromEntries(Object.entries(c.equipped).map(([k, v]) => [k, { rarity: v.rarity }]));

  async function patch(body: Record<string, unknown>) {
    setBusy(true);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) setC(await r.json());
    setBusy(false);
  }

  return (
    <div className="two">
      <div>
        <div className="card" style={{ display: "flex", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <Character gear={gear} color={color} size={170} />
          <div style={{ flex: 1, minWidth: 220 }}>
            <div className="eyebrow">Equipped</div>
            <ul className="plain small" style={{ marginTop: 6 }}>
              {c.slots.map((s) => {
                const it = c.equipped[s];
                return <li key={s}><span className="muted">{SLOT_LABEL[s]}:</span> {it ? <><GearDot rarity={it.rarity} /><b>{it.name}</b> <span className="muted">+{it.bonus} {EFFECT[it.stat]}{it.stat === "dodge" ? "%" : ""}</span></> : <span className="muted">empty</span>}</li>;
              })}
            </ul>
            <div className="eyebrow" style={{ marginTop: 10 }}>Nameplate color</div>
            <div className="row" style={{ gap: 6, marginTop: 6 }}>
              {c.nameplate_colors.map((col) => (
                <button key={col} onClick={() => patch({ nameplate: col })} disabled={busy} aria-label={col}
                  style={{ width: 26, height: 26, padding: 0, borderRadius: "50%", background: col, borderColor: color === col ? "#fff" : "transparent", boxShadow: color === col ? `0 0 0 2px ${col}` : "none" }} />
              ))}
            </div>
          </div>
        </div>
        <h2>Inventory</h2>
        <div className="grid">
          {c.inventory.map((it) => (
            <div key={it.id} className="card qcard" style={{ borderColor: it.equipped ? "var(--accent)" : undefined }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="pill" style={{ borderColor: "transparent", background: "var(--soft)" }}><GearDot rarity={it.rarity} />{it.rarity} {SLOT_LABEL[it.slot].toLowerCase()}</span>
                {it.equipped ? <span className="status now">Equipped</span> : <button onClick={() => patch({ equip: it.id })} disabled={busy}>Equip</button>}
              </div>
              <div className="title">{it.name}{it.set_piece ? " ★" : ""}</div>
              <div className="small muted"><i>{it.flavour}</i></div>
              <div className="meta"><span>+{it.bonus} {EFFECT[it.stat]}{it.stat === "dodge" ? "%" : ""}</span>{it.source_quest && <><span>·</span><span>from {it.source_quest}</span></>}</div>
            </div>
          ))}
        </div>
      </div>
      <aside>
        <div className="card">
          <div className="eyebrow">Stats</div>
          {Object.entries(c.stats).map(([k, v]) => (
            <div key={k} style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}><b style={{ textTransform: "capitalize" }}>{k}</b><b>{v}{c.gear_totals[k] ? <span className="muted"> +{c.gear_totals[k]}</span> : null}</b></div>
              <div className="small muted">{c.stat_blurb[k]}</div>
            </div>
          ))}
          <div className="small muted" style={{ marginTop: 8 }}>Gear: dodge {c.gear_totals.dodge}% (one per fight){c.gear_totals.cleanse ? ", cleanses one debuff" : ""}.</div>
        </div>
      </aside>
    </div>
  );
}
