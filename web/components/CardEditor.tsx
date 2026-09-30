"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Card, CosmeticOption } from "@/lib/api";

type DecoImages = { avatar: Record<string, string>; card: Record<string, string> };

/** The owner's controls for the player card. Cosmetics are picked from compact tile grids (like a chat app's
 *  profile shop): the card on the left is the live preview, so tiles stay small; hover or select a tile to read
 *  its name and how to unlock it. Locked tiles are dimmed and cannot be picked. */
export default function CardEditor({ initial, shareUrl, deco }: { initial: Card; shareUrl: string; deco: DecoImages }) {
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const [motto, setMotto] = useState(initial.motto);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [hover, setHover] = useState<{ kind: string; o: CosmeticOption } | null>(null);
  const featured = c.cosmetics.featured ?? c.featured.map((a) => a.key);
  const opts = c.cosmetic_options;

  async function patch(body: Record<string, unknown>) {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) { setC(await r.json()); router.refresh(); }   // the card itself is rendered on the server
    else setErr((await r.json()).detail ?? "Could not save that.");
    setBusy(false);
  }
  function toggleFeat(key: string) {
    const next = featured.includes(key) ? featured.filter((k) => k !== key) : [...featured, key].slice(-3);
    patch({ featured: next });
  }
  async function copy() {
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* the field below can be copied by hand */ }
  }
  const owned = (k: "nameplate" | "avatar_frame" | "card_frame") => opts[k].filter((o) => o.owned).length;
  const current = (k: "nameplate" | "avatar_frame" | "card_frame") => k === "nameplate" ? c.nameplate_id : k === "avatar_frame" ? c.avatar_frame : c.card_frame;
  const detail = (k: "nameplate" | "avatar_frame" | "card_frame") => {
    const o = hover?.kind === k ? hover.o : opts[k].find((x) => x.id === current(k));
    if (!o) return null;
    return <div className="pick-detail"><b>{o.name}</b>{o.desc ? <span className="muted"> · {o.desc}</span> : null}{o.owned ? <span className="muted"> · {o.id === current(k) ? "in use" : "unlocked"}</span> : <span style={{ color: "var(--warn)" }}> · 🔒 {o.hint}</span>}</div>;
  };
  const tileProps = (k: "nameplate" | "avatar_frame" | "card_frame", o: CosmeticOption) => ({
    type: "button" as const, disabled: busy || !o.owned, title: o.owned ? o.name : `${o.name} · ${o.hint}`,
    className: `pick ${current(k) === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`,
    onMouseEnter: () => setHover({ kind: k, o }), onMouseLeave: () => setHover(null), onFocus: () => setHover({ kind: k, o }), onBlur: () => setHover(null),
    onClick: () => o.owned && patch({ [k]: o.id }),
  });

  return (
    <div className="card editor">
      <div className="eyebrow">Your card</div>

      <label className="small muted" htmlFor="motto" style={{ display: "block", marginTop: 10 }}>Motto (40 letters)</label>
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); patch({ banner: motto }); }}>
        <input id="motto" type="text" value={motto} maxLength={40} onChange={(e) => setMotto(e.target.value)} placeholder="Something short and true" style={{ flex: 1, minWidth: 160 }} />
        <button type="submit" disabled={busy || motto === c.motto}>Save</button>
      </form>

      <div className="pick-head"><span className="small muted">Nameplate colour</span><span className="small muted">{owned("nameplate")}/{opts.nameplate.length}</span></div>
      <div className="pick-grid">
        {opts.nameplate.map((o) => (
          <button key={o.id} {...tileProps("nameplate", o)} aria-label={o.name} style={{ width: 28, height: 28, borderRadius: "50%", background: o.value }}>
            {!o.owned && <span className="pick-lock">🔒</span>}
          </button>
        ))}
      </div>
      {detail("nameplate")}

      <div className="pick-head"><span className="small muted">Avatar decoration</span><span className="small muted">{owned("avatar_frame")}/{opts.avatar_frame.length}</span></div>
      <div className="pick-grid">
        {opts.avatar_frame.map((o) => (
          <button key={o.id} {...tileProps("avatar_frame", o)} aria-label={o.name} style={{ width: 52, height: 52, borderRadius: 8 }}>
            <span className="pick-av" />
            {deco.avatar[o.id] ? <img className="px" src={deco.avatar[o.id]} alt="" style={{ position: "absolute", inset: 2, width: 48, height: 48 }} /> : <span className="pick-swatch" />}
            {!o.owned && <span className="pick-lock">🔒</span>}
          </button>
        ))}
      </div>
      {detail("avatar_frame")}

      <div className="pick-head"><span className="small muted">Card decoration</span><span className="small muted">{owned("card_frame")}/{opts.card_frame.length}</span></div>
      <div className="pick-grid">
        {opts.card_frame.map((o) => (
          <button key={o.id} {...tileProps("card_frame", o)} aria-label={o.name} style={{ width: 72, height: 58, borderRadius: 6 }}>
            {deco.card[o.id] ? <img className="px" src={deco.card[o.id]} alt="" style={{ position: "absolute", inset: 3, width: 66, height: 52 }} /> : <span className="pick-swatch" />}
            {!o.owned && <span className="pick-lock">🔒</span>}
          </button>
        ))}
      </div>
      {detail("card_frame")}
      {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}

      <div className="pick-head"><span className="small muted">Shown on the card</span><span className="small muted">up to three</span></div>
      {c.earned_achievements.length ? (
        <div className="row" style={{ gap: 6 }}>
          {c.earned_achievements.map((a) => (
            <button key={a.key} onClick={() => toggleFeat(a.key)} disabled={busy} className={featured.includes(a.key) ? "primary" : ""} title={a.desc} style={{ padding: "5px 9px", fontSize: 11 }}>
              {a.icon} {a.name}
            </button>
          ))}
        </div>
      ) : <div className="small">Nothing earned yet. Finish a quest.</div>}

      <div className="pick-head"><span className="small muted">Sharing</span></div>
      <label className="row small" style={{ gap: 8, cursor: "pointer" }}>
        <input type="checkbox" checked={c.public} disabled={busy} onChange={(e) => patch({ public: e.target.checked })} />
        <span>Anyone with the link can see this card{c.public ? "" : " (guild members only right now)"}</span>
      </label>
      <div className="row" style={{ gap: 8, marginTop: 8 }}>
        <input type="text" readOnly value={shareUrl} onFocus={(e) => e.currentTarget.select()} style={{ flex: 1, minWidth: 160, fontFamily: "var(--mono)", fontSize: 12 }} />
        <button type="button" onClick={copy}>{copied ? "Copied" : "Copy link"}</button>
      </div>
    </div>
  );
}
