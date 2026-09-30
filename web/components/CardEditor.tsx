"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Card } from "@/lib/api";

/** The owner's controls for the player card: motto, nameplate colour, frames, featured achievements, sharing.
 *  Colours and frames are unlockables: locked ones show with their hint and cannot be picked. */
export default function CardEditor({ initial, shareUrl }: { initial: Card; shareUrl: string }) {
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const [motto, setMotto] = useState(initial.motto);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
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

  return (
    <div className="card editor">
      <div className="eyebrow">Your card</div>

      <label className="small muted" htmlFor="motto" style={{ display: "block", marginTop: 10 }}>Motto (40 letters)</label>
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); patch({ banner: motto }); }}>
        <input id="motto" type="text" value={motto} maxLength={40} onChange={(e) => setMotto(e.target.value)} placeholder="Something short and true" style={{ flex: 1, minWidth: 160 }} />
        <button type="submit" disabled={busy || motto === c.motto}>Save</button>
      </form>

      <div className="small muted" style={{ marginTop: 14 }}>Nameplate colour <span className="muted">· {owned("nameplate")}/{opts.nameplate.length} unlocked</span></div>
      <div className="row" style={{ gap: 6, marginTop: 6 }}>
        {opts.nameplate.map((o) => (
          <button key={o.id} onClick={() => o.owned && patch({ nameplate: o.id })} disabled={busy || !o.owned} aria-label={o.name} title={o.owned ? o.name : `${o.name} · ${o.hint}`}
            className={`swatch ${o.owned ? "" : "locked"}`}
            style={{ background: o.value, borderColor: c.nameplate_id === o.id ? "#fff" : "transparent", boxShadow: c.nameplate_id === o.id ? `0 0 0 2px ${o.value}` : "none" }}>
            {!o.owned && <span className="swatch-lock">🔒</span>}
          </button>
        ))}
      </div>

      <div className="small muted" style={{ marginTop: 14 }}>Avatar frame <span className="muted">· {owned("avatar_frame")}/{opts.avatar_frame.length} unlocked</span></div>
      <div className="row" style={{ gap: 6, marginTop: 6 }}>
        {opts.avatar_frame.map((o) => (
          <button key={o.id} onClick={() => o.owned && patch({ avatar_frame: o.id })} disabled={busy || !o.owned} title={o.owned ? o.name : `${o.name} · ${o.hint}`}
            className={`chip ${c.avatar_frame === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`}>
            <span className={`pcard-avatar mini frame-${o.id}`}><span>{(c.name ?? "?").slice(0, 1)}</span></span>{o.owned ? o.name : `🔒 ${o.name}`}
          </button>
        ))}
      </div>

      <div className="small muted" style={{ marginTop: 14 }}>Card frame <span className="muted">· {owned("card_frame")}/{opts.card_frame.length} unlocked</span></div>
      <div className="row" style={{ gap: 6, marginTop: 6 }}>
        {opts.card_frame.map((o) => (
          <button key={o.id} onClick={() => o.owned && patch({ card_frame: o.id })} disabled={busy || !o.owned} title={o.owned ? o.name : `${o.name} · ${o.hint}`}
            className={`chip ${c.card_frame === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`}>
            <span className={`frame-swatch frame-${o.id}`} />{o.owned ? o.name : `🔒 ${o.name}`}
          </button>
        ))}
      </div>
      {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}

      <div className="small muted" style={{ marginTop: 14 }}>Shown on the card (pick up to three)</div>
      {c.earned_achievements.length ? (
        <div className="row" style={{ gap: 6, marginTop: 6 }}>
          {c.earned_achievements.map((a) => (
            <button key={a.key} onClick={() => toggleFeat(a.key)} disabled={busy} className={featured.includes(a.key) ? "primary" : ""} title={a.desc} style={{ padding: "6px 10px", fontSize: 12 }}>
              {a.icon} {a.name}
            </button>
          ))}
        </div>
      ) : <div className="small" style={{ marginTop: 6 }}>Nothing earned yet. Finish a quest.</div>}

      <div className="small muted" style={{ marginTop: 14 }}>Sharing</div>
      <label className="row small" style={{ gap: 8, marginTop: 6, cursor: "pointer" }}>
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
