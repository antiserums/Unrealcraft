"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Card } from "@/lib/api";

/** The owner's controls for the player card: motto, nameplate colour, featured achievements, sharing. */
export default function CardEditor({ initial, shareUrl }: { initial: Card; shareUrl: string }) {
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const [motto, setMotto] = useState(initial.motto);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const featured = c.cosmetics.featured ?? c.featured.map((a) => a.key);

  async function patch(body: Record<string, unknown>) {
    setBusy(true);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok) { setC(await r.json()); router.refresh(); }   // the card itself is rendered on the server
    setBusy(false);
  }
  function toggleFeat(key: string) {
    const next = featured.includes(key) ? featured.filter((k) => k !== key) : [...featured, key].slice(-3);
    patch({ featured: next });
  }
  async function copy() {
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* the field below can be copied by hand */ }
  }

  return (
    <div className="card editor">
      <div className="eyebrow">Your card</div>

      <label className="small muted" htmlFor="motto" style={{ display: "block", marginTop: 10 }}>Motto (40 letters)</label>
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); patch({ banner: motto }); }}>
        <input id="motto" type="text" value={motto} maxLength={40} onChange={(e) => setMotto(e.target.value)} placeholder="Something short and true" style={{ flex: 1, minWidth: 160 }} />
        <button type="submit" disabled={busy || motto === c.motto}>Save</button>
      </form>

      <div className="small muted" style={{ marginTop: 14 }}>Nameplate colour</div>
      <div className="row" style={{ gap: 6, marginTop: 6 }}>
        {c.nameplate_colors.map((col) => (
          <button key={col} onClick={() => patch({ nameplate: col })} disabled={busy} aria-label={col} className="swatch"
            style={{ background: col, borderColor: c.nameplate === col ? "#fff" : "transparent", boxShadow: c.nameplate === col ? `0 0 0 2px ${col}` : "none" }} />
        ))}
      </div>

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
