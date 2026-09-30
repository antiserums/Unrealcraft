"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Card, CosmeticOption } from "@/lib/api";
import type { SheetSpec } from "@/lib/art";
import { gutterFor, type Inset } from "@/lib/deco";
import CharacterSheet, { type ArtProps, type Char } from "./CharacterSheet";
import PlayerCard from "./PlayerCard";

type DecoImages = { avatar: Record<string, string>; card: Record<string, string>; inset: Record<string, Inset> };
type Draft = { motto: string; nameplate: string; avatar_frame: string; card_frame: string; featured: string[]; public: boolean };
type Kind = "nameplate" | "avatar_frame" | "card_frame";
type Mode = "view" | "profile" | "wardrobe";

/** The player card page. View mode: the card and two buttons. Edit profile: a draft (motto, colour, decorations,
 *  featured achievements, sharing) previews on the card and is saved in one request. Edit wardrobe: the closet
 *  (outfits, weapons, build) opens beneath the card; its changes save as you pick, like before. */
export default function CardStudio({ initial, sheet, badges, deco, shareUrl, wardrobe }:
  { initial: Card; sheet: SheetSpec | null; badges: Record<string, string | null>; deco: DecoImages; shareUrl: string;
    wardrobe: { char: Char; art: ArtProps } | null }) {
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const fromCard = (x: Card): Draft => ({ motto: x.motto, nameplate: x.nameplate_id, avatar_frame: x.avatar_frame, card_frame: x.card_frame, featured: x.cosmetics.featured ?? x.featured.map((a) => a.key), public: x.public });
  const [draft, setDraft] = useState<Draft>(fromCard(initial));
  const [mode, setMode] = useState<Mode>("view");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [hover, setHover] = useState<{ kind: Kind; o: CosmeticOption } | null>(null);
  const opts = c.cosmetic_options;

  // the server re-renders the page after wardrobe changes; take the fresh card unless a profile draft is open
  useEffect(() => { if (mode !== "profile") { setC(initial); setDraft(fromCard(initial)); } }, [initial]);  // eslint-disable-line react-hooks/exhaustive-deps

  const plate = opts.nameplate.find((o) => o.id === draft.nameplate);
  const preview: Card = {
    ...c, motto: draft.motto, nameplate: plate?.value ?? c.nameplate, nameplate_id: draft.nameplate,
    avatar_frame: draft.avatar_frame, card_frame: draft.card_frame,
    featured: draft.featured.map((k) => c.earned_achievements.find((a) => a.key === k)).filter(Boolean) as Card["featured"],
  };
  const shown = mode === "profile" ? preview : c;
  const cardArt = deco.card[shown.card_frame] ?? null;
  const avatarArt = deco.avatar[shown.avatar_frame] ?? null;

  async function patch(body: Record<string, unknown>) {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    setBusy(false);
    if (r.ok) { setC(j); setDraft(fromCard(j)); router.refresh(); return true; }
    setErr(j.detail ?? "Could not save that."); return false;
  }
  async function save() {
    if (await patch({ banner: draft.motto, nameplate: draft.nameplate, avatar_frame: draft.avatar_frame, card_frame: draft.card_frame, featured: draft.featured, public: draft.public })) setMode("view");
  }
  function cancel() { setDraft(fromCard(c)); setMode("view"); setErr(null); }
  function toggleFeat(key: string) {
    setDraft((d) => ({ ...d, featured: d.featured.includes(key) ? d.featured.filter((k) => k !== key) : [...d.featured, key].slice(-3) }));
  }
  async function copy() {
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* the field can be copied by hand */ }
  }
  const dirty = JSON.stringify(draft) !== JSON.stringify(fromCard(c));
  const owned = (k: Kind) => opts[k].filter((o) => o.owned).length;
  const detail = (k: Kind) => {
    const o = hover?.kind === k ? hover.o : opts[k].find((x) => x.id === draft[k]);
    if (!o) return null;
    return <div className="pick-detail"><b>{o.name}</b>{o.desc ? <span className="muted"> · {o.desc}</span> : null}{o.owned ? <span className="muted"> · {o.id === draft[k] ? "selected" : "unlocked"}</span> : <span style={{ color: "var(--warn)" }}> · 🔒 {o.hint}</span>}</div>;
  };
  const tile = (k: Kind, o: CosmeticOption) => ({
    type: "button" as const, disabled: busy || !o.owned, title: o.owned ? o.name : `${o.name} · ${o.hint}`,
    className: `pick ${draft[k] === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`,
    onMouseEnter: () => setHover({ kind: k, o }), onMouseLeave: () => setHover(null), onFocus: () => setHover({ kind: k, o }), onBlur: () => setHover(null),
    onClick: () => o.owned && setDraft((d) => ({ ...d, [k]: o.id })),
  });

  return (
    <div className="studio">
      <div className={`studio-card ${cardArt ? "framed" : ""}`} style={cardArt ? gutterFor(deco.inset[shown.card_frame]) : undefined}>
        {cardArt && <div className="px pcard-deco" style={{ borderImageSource: `url("${cardArt}")` }} aria-hidden="true" />}
        <PlayerCard c={shown} sheet={sheet} badges={badges} deco={{ avatar: avatarArt, card: null }} />
      </div>

      {mode === "view" && (
        <div className="studio-actions">
          <button className="primary" onClick={() => setMode("profile")}>Edit profile</button>
          {wardrobe && <button onClick={() => setMode("wardrobe")}>Edit wardrobe</button>}
          <Link className="btn" href={`/members/${c.id}`}>View as others</Link>
        </div>
      )}

      {mode === "wardrobe" && wardrobe && (
        <div className="studio-panel">
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
            <div><div className="eyebrow">Wardrobe</div><div className="small muted">Outfits, weapons and build save as you pick; the card above follows.</div></div>
            <button className="primary" onClick={() => setMode("view")}>Done</button>
          </div>
          <CharacterSheet initial={wardrobe.char} fallbackColor={c.nameplate} art={wardrobe.art} />
        </div>
      )}

      {mode === "profile" && (
        <div className="card studio-panel editor">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="eyebrow">Editing your profile</div>
              <div className="small muted">Changes show on the card as you pick. Nothing is kept until you press Save.</div>
            </div>
            <div className="row" style={{ gap: 6 }}>
              <button onClick={cancel} disabled={busy}>Cancel</button>
              <button className="primary" onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save"}</button>
            </div>
          </div>

          <div className="edit-grid" style={{ marginTop: 6 }}>
            <div>
              <label className="small muted" htmlFor="motto" style={{ display: "block", marginTop: 12 }}>Motto (40 letters)</label>
              <input id="motto" type="text" value={draft.motto} maxLength={40} onChange={(e) => setDraft((d) => ({ ...d, motto: e.target.value }))} placeholder="Something short and true" style={{ width: "100%", marginTop: 4 }} />

              <div className="pick-head"><span className="small muted">Nameplate colour</span><span className="small muted">{owned("nameplate")}/{opts.nameplate.length}</span></div>
              <div className="pick-grid">
                {opts.nameplate.map((o) => (
                  <button key={o.id} {...tile("nameplate", o)} aria-label={o.name} style={{ width: 28, height: 28, borderRadius: "50%", background: o.value }}>
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("nameplate")}

              <div className="pick-head"><span className="small muted">Shown on the card</span><span className="small muted">up to three</span></div>
              {c.earned_achievements.length ? (
                <div className="row" style={{ gap: 6 }}>
                  {c.earned_achievements.map((a) => (
                    <button key={a.key} onClick={() => toggleFeat(a.key)} disabled={busy} className={draft.featured.includes(a.key) ? "primary" : ""} title={a.desc} style={{ padding: "5px 9px", fontSize: 11 }}>
                      {a.icon} {a.name}
                    </button>
                  ))}
                </div>
              ) : <div className="small">Nothing earned yet. Finish a quest.</div>}

              <div className="pick-head"><span className="small muted">Sharing</span></div>
              <label className="row small" style={{ gap: 8, cursor: "pointer" }}>
                <input type="checkbox" checked={draft.public} disabled={busy} onChange={(e) => setDraft((d) => ({ ...d, public: e.target.checked }))} />
                <span>Anyone with the link can see this card{draft.public ? "" : " (guild members only)"}</span>
              </label>
              <div className="row" style={{ gap: 8, marginTop: 8 }}>
                <input type="text" readOnly value={shareUrl} onFocus={(e) => e.currentTarget.select()} style={{ flex: 1, minWidth: 160, fontFamily: "var(--mono)", fontSize: 12 }} />
                <button type="button" onClick={copy}>{copied ? "Copied" : "Copy link"}</button>
              </div>
            </div>

            <div>
              <div className="pick-head"><span className="small muted">Avatar decoration</span><span className="small muted">{owned("avatar_frame")}/{opts.avatar_frame.length}</span></div>
              <div className="pick-grid">
                {opts.avatar_frame.map((o) => (
                  <button key={o.id} {...tile("avatar_frame", o)} aria-label={o.name} style={{ width: 52, height: 52, borderRadius: 8 }}>
                    <span className="pick-av" />
                    {deco.avatar[o.id] ? <img className="px" src={deco.avatar[o.id]} alt="" style={{ position: "absolute", inset: 2, width: 48, height: 48 }} /> : o.id === "none" ? null : <span className="pick-swatch" />}
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("avatar_frame")}

              <div className="pick-head"><span className="small muted">Card decoration</span><span className="small muted">{owned("card_frame")}/{opts.card_frame.length}</span></div>
              <div className="pick-grid">
                {opts.card_frame.map((o) => (
                  <button key={o.id} {...tile("card_frame", o)} aria-label={o.name} style={{ width: 72, height: 58, borderRadius: 6 }}>
                    {deco.card[o.id] ? <img className="px" src={deco.card[o.id]} alt="" style={{ position: "absolute", inset: 3, width: 66, height: 52 }} /> : o.id === "none" ? <span className="pick-none">none</span> : <span className="pick-swatch" />}
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("card_frame")}
            </div>
          </div>
          {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
        </div>
      )}
    </div>
  );
}
