"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Card, CosmeticOption } from "@/lib/api";
import type { SheetSpec } from "@/lib/art";
import PlayerCard from "./PlayerCard";

type DecoImages = { avatar: Record<string, string>; card: Record<string, string> };
type Draft = { motto: string; nameplate: string; avatar_frame: string; card_frame: string; featured: string[] };
type Kind = "nameplate" | "avatar_frame" | "card_frame";

/** The player card with its editor. View mode shows the card and an Edit profile button. Edit mode keeps a draft:
 *  every pick previews on the card at once, and Save sends the whole draft in one request; Cancel drops it. */
export default function CardStudio({ initial, sheet, badges, deco, shareUrl }:
  { initial: Card; sheet: SheetSpec | null; badges: Record<string, string | null>; deco: DecoImages; shareUrl: string }) {
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const fromCard = (x: Card): Draft => ({ motto: x.motto, nameplate: x.nameplate_id, avatar_frame: x.avatar_frame, card_frame: x.card_frame, featured: x.cosmetics.featured ?? x.featured.map((a) => a.key) });
  const [draft, setDraft] = useState<Draft>(fromCard(initial));
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [hover, setHover] = useState<{ kind: Kind; o: CosmeticOption } | null>(null);
  const opts = c.cosmetic_options;

  // the card as the draft would make it
  const plate = opts.nameplate.find((o) => o.id === draft.nameplate);
  const preview: Card = {
    ...c, motto: draft.motto, nameplate: plate?.value ?? c.nameplate, nameplate_id: draft.nameplate,
    avatar_frame: draft.avatar_frame, card_frame: draft.card_frame,
    featured: draft.featured.map((k) => c.earned_achievements.find((a) => a.key === k)).filter(Boolean) as Card["featured"],
  };
  const shown = editing ? preview : c;
  const decoNow = { avatar: deco.avatar[shown.avatar_frame] ?? null, card: deco.card[shown.card_frame] ?? null };

  async function patch(body: Record<string, unknown>) {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    if (r.ok) { setC(j); setDraft(fromCard(j)); router.refresh(); return true; }
    setErr(j.detail ?? "Could not save that."); setBusy(false); return false;
  }
  async function save() {
    const ok = await patch({ banner: draft.motto, nameplate: draft.nameplate, avatar_frame: draft.avatar_frame, card_frame: draft.card_frame, featured: draft.featured });
    if (ok) { setEditing(false); setBusy(false); }
  }
  function cancel() { setDraft(fromCard(c)); setEditing(false); setErr(null); }
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
    <div className="two">
      <PlayerCard c={shown} sheet={sheet} badges={badges} deco={decoNow} />
      <div>
        {!editing ? (
          <div className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="eyebrow">Your card</div>
              <button className="primary" onClick={() => setEditing(true)}>Edit profile</button>
            </div>
            <ul className="plain small" style={{ marginTop: 10 }}>
              <li>Motto: {c.motto ? <i>“{c.motto}”</i> : <span className="muted">none</span>}</li>
              <li>Nameplate: <span style={{ color: c.nameplate, fontWeight: 600 }}>{plate?.name ?? c.nameplate_id}</span></li>
              <li>Avatar decoration: {opts.avatar_frame.find((o) => o.id === c.avatar_frame)?.name ?? c.avatar_frame}</li>
              <li>Card decoration: {opts.card_frame.find((o) => o.id === c.card_frame)?.name ?? c.card_frame}</li>
              <li>Unlocked: {owned("nameplate")}/{opts.nameplate.length} colours · {owned("avatar_frame")}/{opts.avatar_frame.length} avatar · {owned("card_frame")}/{opts.card_frame.length} card</li>
            </ul>
            <div className="pick-head"><span className="small muted">Sharing</span></div>
            <label className="row small" style={{ gap: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={c.public} disabled={busy} onChange={(e) => patch({ public: e.target.checked }).then(() => setBusy(false))} />
              <span>Anyone with the link can see this card{c.public ? "" : " (guild members only right now)"}</span>
            </label>
            <div className="row" style={{ gap: 8, marginTop: 8 }}>
              <input type="text" readOnly value={shareUrl} onFocus={(e) => e.currentTarget.select()} style={{ flex: 1, minWidth: 160, fontFamily: "var(--mono)", fontSize: 12 }} />
              <button type="button" onClick={copy}>{copied ? "Copied" : "Copy link"}</button>
            </div>
            {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
          </div>
        ) : (
          <div className="card editor">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="eyebrow">Editing your card</div>
              <div className="row" style={{ gap: 6 }}>
                <button onClick={cancel} disabled={busy}>Cancel</button>
                <button className="primary" onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save"}</button>
              </div>
            </div>
            <p className="small muted" style={{ margin: "6px 0 0" }}>Changes show on the card as you pick. Nothing is kept until you press Save.</p>

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
            {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
            <div className="row" style={{ gap: 6, marginTop: 14, justifyContent: "flex-end" }}>
              <button onClick={cancel} disabled={busy}>Cancel</button>
              <button className="primary" onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save"}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
