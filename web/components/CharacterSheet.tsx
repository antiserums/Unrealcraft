"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Character, ItemIcon } from "./Figure";

export type Outfit = { id: string; name: string; flavour: string; major: string; tier: string; color: string; art_id: string; owned: boolean; earned_at: string | null; hint: string | null; worn: boolean };
export type Char = {
  worn: Outfit; outfits: Outfit[]; new_outfits: string[];
  cosmetics: { nameplate?: string; banner?: string; appearance?: Record<string, string>; outfit?: string };
  nameplate_colors: string[]; slots: string[]; major: string;
};
export type ArtProps = { layers: string[] | null; icons: Record<string, string>; appearance: Record<string, string[]> };
const APPEARANCE_LABEL: Record<string, string> = { body: "Body", skin: "Skin", face: "Face", hair: "Hair", hair_color: "Hair color", eye_color: "Eyes", facial_hair: "Facial hair", markings: "Markings" };
const TIER_NAME: Record<string, string> = { novice: "Novice", apprentice: "Apprentice", adept: "Adept", expert: "Expert", master: "Master" };
const RARITY_OF_TIER: Record<string, string> = { novice: "common", apprentice: "uncommon", adept: "rare", expert: "epic", master: "legendary" };

export default function CharacterSheet({ initial, fallbackColor, art }: { initial: Char; fallbackColor: string; art: ArtProps }) {
  const router = useRouter();
  const [c, setC] = useState<Char>(initial);
  const [busy, setBusy] = useState(false);
  const color = c.cosmetics.nameplate ?? fallbackColor;
  const owned = c.outfits.filter((o) => o.owned);
  const locked = c.outfits.filter((o) => !o.owned);

  async function patch(body: Record<string, unknown>) {
    setBusy(true);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) { setC(await r.json()); router.refresh(); }   // the layered figure is rendered on the server
    setBusy(false);
  }
  const appearanceKeys = Object.keys(art.appearance ?? {});

  return (
    <div>
      <div>
        <div className="card" style={{ display: "flex", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <Character outfit={c.worn.id} layers={art.layers} color={color} size={170} />
          <div style={{ flex: 1, minWidth: 220 }}>
            <div className="eyebrow">Wearing</div>
            <div style={{ margin: "4px 0 2px" }}><b style={{ color: c.worn.color, fontSize: 16 }}>{c.worn.name}</b></div>
            <div className="small muted"><i>{c.worn.flavour}</i></div>
            {appearanceKeys.length > 0 ? (
              <>
                <div className="eyebrow" style={{ marginTop: 12 }}>Appearance</div>
                <div className="row" style={{ gap: 8, marginTop: 6 }}>
                  {appearanceKeys.map((k) => (
                    <label key={k} className="small" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                      <span className="muted">{APPEARANCE_LABEL[k] ?? k}</span>
                      <select value={c.cosmetics.appearance?.[k] ?? art.appearance[k][0]} disabled={busy} onChange={(e) => patch({ appearance: { [k]: e.target.value } })}>
                        {art.appearance[k].map((v) => <option key={v} value={v}>{v.replace(/[-_]/g, " ")}</option>)}
                      </select>
                    </label>
                  ))}
                </div>
              </>
            ) : (
              <p className="small muted" style={{ marginTop: 10 }}>Appearance options (body, skin, hair, face) arrive with the art pack.</p>
            )}
          </div>
        </div>

        <div className="section-h"><h2>Wardrobe</h2><span className="muted small">{owned.length} outfit{owned.length === 1 ? "" : "s"} earned · outfits are looks only, no stats</span></div>
        <div className="grid">
          {owned.map((o) => (
            <div key={o.id} className="card qcard" style={{ borderColor: o.worn ? "var(--gold)" : undefined }}>
              <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                <div className="row" style={{ gap: 10 }}>
                  <ItemIcon icon={art.icons[o.art_id]} rarity={RARITY_OF_TIER[o.tier]} />
                  <div>
                    <div className="title">{o.name}</div>
                    <div className="small muted" style={{ color: o.color }}>{TIER_NAME[o.tier]} set{o.earned_at ? ` · earned ${o.earned_at.slice(0, 10)}` : ""}</div>
                  </div>
                </div>
                {o.worn ? <span className="status now">Wearing</span> : <button onClick={() => patch({ wear: o.id })} disabled={busy}>Wear</button>}
              </div>
              <div className="small muted"><i>{o.flavour}</i></div>
            </div>
          ))}
        </div>
        {locked.length > 0 && (
          <>
            <div className="section-h"><h2>Not yet earned</h2><span className="muted small">{locked.length} to find</span></div>
            <div className="grid lock">
              {locked.map((o) => (
                <div key={o.id} className="card qcard">
                  <div className="row" style={{ gap: 10 }}>
                    <ItemIcon icon={null} rarity={RARITY_OF_TIER[o.tier]} />
                    <div>
                      <div className="title">🔒 {o.name}</div>
                      <div className="small muted" style={{ color: o.color }}>{TIER_NAME[o.tier]} set</div>
                    </div>
                  </div>
                  <div className="small">{o.hint}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
