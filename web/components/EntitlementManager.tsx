"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { EntitlementKind } from "@/lib/api";

export type EntRow = { kind: EntitlementKind; id: string; name: string; desc: string; data: Record<string, unknown>; unlock: Record<string, unknown>; sort: number; enabled: boolean; builtin: boolean; custom: boolean; hint: string | null };
export type EntitlementData = {
  rows: EntRow[]; kinds: EntitlementKind[]; kind_label: Record<string, string>; unlock_types: string[]; counters: string[]; counter_label: Record<string, string>;
  ranks: { n: number; title: string }[]; achievement_keys: string[]; tiers: string[];
};
type Art = { sets: { id: string; name: string }[]; avatar: string[]; card: string[]; badges: { n: number; name: string }[]; banners?: string[] };
type Draft = { kind: EntitlementKind; id: string; name: string; desc: string; sort: string; enabled: boolean; unlock_type: string; unlock_n: string; unlock_key: string; unlock_role: string; unlock_hint: string;
  value: string; art: string; art_id: string; tier: string; set_kind: string; of: string; need: string; icon: string; badge: string; outfit: string };

const UNLOCK_LABEL: Record<string, string> = { starter: "Everyone", rank: "Reach a rank", achievement: "Earn an achievement", medal: "Hold a medal", staff: "Staff role", granted: "Only when staff grant it" };

function blank(kind: EntitlementKind): Draft {
  return { kind, id: "", name: "", desc: "", sort: "100", enabled: true, unlock_type: kind === "achievement" ? "starter" : "granted", unlock_n: "1", unlock_key: "", unlock_role: "mentor", unlock_hint: "",
    value: "#4AA3B5", art: "", art_id: "", tier: "adept", set_kind: "reward", of: "done", need: "10", icon: "🏅", badge: "", outfit: "" };
}
function fromRow(r: EntRow): Draft {
  const d = r.data, u = r.unlock;
  return { ...blank(r.kind), id: r.id, name: r.name, desc: r.desc, sort: String(r.sort), enabled: r.enabled, unlock_type: String(u.type ?? "starter"), unlock_n: String(u.n ?? "1"), unlock_key: String(u.key ?? ""),
    unlock_role: String(u.role ?? "mentor"), unlock_hint: String(u.hint ?? ""), value: String(d.value ?? "#4AA3B5"), art: String(d.art ?? ""), art_id: String(d.art_id ?? ""), tier: String(d.tier ?? "adept"),
    set_kind: String(d.set_kind ?? "reward"), of: String(d.of ?? "done"), need: String(d.need ?? "1"), icon: String(d.icon ?? "🏅"), badge: String(d.badge ?? ""), outfit: String(d.outfit ?? "") };
}
function toBody(x: Draft) {
  const unlock: Record<string, unknown> = { type: x.unlock_type, hint: x.unlock_hint || undefined };
  if (x.unlock_type === "rank") unlock.n = Number(x.unlock_n);
  if (x.unlock_type === "achievement" || x.unlock_type === "medal") unlock.key = x.unlock_key.trim();
  if (x.unlock_type === "staff") unlock.role = x.unlock_role;
  const data: Record<string, unknown> = {};
  if (x.kind === "nameplate") data.value = x.value.trim();
  if (x.kind === "avatar_frame" || x.kind === "card_frame") data.art = x.id === "none" ? null : x.art;
  if (x.kind === "home_banner") data.art = x.id === "town" ? null : x.art;
  if (x.kind === "outfit") { data.art_id = x.art_id; data.tier = x.tier; data.set_kind = x.set_kind; }
  if (x.kind === "achievement") { data.of = x.of; data.need = Number(x.need); data.icon = x.icon; if (x.badge) data.badge = Number(x.badge); if (x.outfit) data.outfit = x.outfit; }
  return { name: x.name.trim(), desc: x.desc.trim(), unlock, data, sort: Number(x.sort) || 100, enabled: x.enabled };
}

/** The entitlement catalog: one tab per kind, a table of rows, and an add / edit form. */
export default function EntitlementManager({ data, art }: { data: EntitlementData; art: Art }) {
  const router = useRouter();
  const [kind, setKind] = useState<EntitlementKind>("title");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const rows = data.rows.filter((r) => r.kind === kind);
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setDraft((d) => (d ? { ...d, [k]: v } : d));

  async function call(method: string, path: string, body?: unknown) {
    setBusy(true); setErr(null); setMsg(null);
    const r = await fetch(`/api/admin/entitlements${path}`, { method, headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    const j = await r.json();
    setBusy(false);
    if (!r.ok) { setErr(j.detail ?? "Failed."); return false; }
    setMsg(j.message); router.refresh(); return true;
  }
  async function save() { if (draft && await call("PUT", `/${draft.kind}/${draft.id.trim().toLowerCase()}`, toBody(draft))) setDraft(null); }
  async function toggle(r: EntRow) { await call("PUT", `/${r.kind}/${r.id}`, { ...toBody(fromRow(r)), enabled: !r.enabled }); }
  async function reset(r: EntRow) { if (confirm(r.builtin ? `Reset ${r.id} to its built-in version?` : `Remove ${r.id}? Members who chose it fall back to a starter.`)) await call("DELETE", `/${r.kind}/${r.id}`); }

  const ruleText = (r: EntRow) => r.kind === "achievement" ? `${r.data.need} × ${data.counter_label[String(r.data.of)] ?? r.data.of}` : `${UNLOCK_LABEL[String(r.unlock.type)] ?? r.unlock.type}${r.hint ? ` · ${r.hint}` : ""}`;
  const dataText = (r: EntRow) => {
    if (r.kind === "nameplate") return <span className="row" style={{ gap: 6 }}><span style={{ width: 14, height: 14, borderRadius: "50%", background: String(r.data.value), display: "inline-block" }} /><code>{String(r.data.value)}</code></span>;
    if (r.kind === "avatar_frame" || r.kind === "card_frame" || r.kind === "home_banner") return <code>{r.data.art ? String(r.data.art) : "—"}</code>;
    if (r.kind === "outfit") return <span><code>{String(r.data.art_id)}</code> · {String(r.data.tier)} · {String(r.data.set_kind)}</span>;
    if (r.kind === "achievement") return <span>{String(r.data.icon ?? "")} badge {String(r.data.badge ?? "—")}{r.data.outfit ? ` · outfit ${r.data.outfit}` : ""}</span>;
    return null;
  };

  return (
    <>
      <div className="subnav">
        {data.kinds.map((k) => <a key={k} href="#" className={kind === k ? "on" : ""} onClick={(e) => { e.preventDefault(); setKind(k); setDraft(null); }}>{data.kind_label[k]}s</a>)}
      </div>
      {msg && <div className="note small" style={{ marginBottom: 10 }}>{msg}</div>}
      {err && <div className="note small" style={{ marginBottom: 10, borderColor: "var(--bad)" }}>{err}</div>}
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
        <span className="muted small">{rows.length} {data.kind_label[kind].toLowerCase()}{rows.length === 1 ? "" : "s"} · {rows.filter((r) => r.custom).length} edited or added here</span>
        <button className="primary" onClick={() => setDraft(blank(kind))}>New {data.kind_label[kind].toLowerCase()}</button>
      </div>

      {draft && (
        <div className="card adm" style={{ marginBottom: 14 }}>
          <div className="eyebrow">{draft.id && rows.some((r) => r.id === draft.id) ? `Editing ${draft.id}` : `New ${data.kind_label[draft.kind].toLowerCase()}`}</div>
          <div className="adm-grid">
            <div><label>Id (letters, digits, underscores)</label><input value={draft.id} onChange={(e) => set("id", e.target.value.toLowerCase())} placeholder="the_bold" /></div>
            <div><label>Name{draft.kind === "title" ? " (shown after the member's name)" : ""}</label><input value={draft.name} onChange={(e) => set("name", e.target.value)} placeholder={draft.kind === "title" ? "the Bold" : "Name"} /></div>
            <div className="wide" style={{ marginTop: 0 }}><label>Description</label><input value={draft.desc} onChange={(e) => set("desc", e.target.value)} /></div>

            {draft.kind === "nameplate" && <div><label>Colour</label><div className="row" style={{ gap: 6 }}><input type="color" value={/^#[0-9a-fA-F]{6}$/.test(draft.value) ? draft.value : "#4AA3B5"} onChange={(e) => set("value", e.target.value.toUpperCase())} style={{ width: 44, padding: 2 }} /><input value={draft.value} onChange={(e) => set("value", e.target.value)} /></div></div>}
            {(draft.kind === "avatar_frame" || draft.kind === "card_frame") && (
              <div><label>Art (from the art pack)</label><select value={draft.art} onChange={(e) => set("art", e.target.value)}><option value="">pick one</option>{(draft.kind === "avatar_frame" ? art.avatar : art.card).map((a) => <option key={a} value={a}>{a}</option>)}</select></div>
            )}
            {draft.kind === "home_banner" && (
              <div><label>Scene (banners/rank-banners in the art pack)</label><select value={draft.art} onChange={(e) => set("art", e.target.value)}><option value="">the river town</option>{(art.banners ?? []).map((a) => <option key={a} value={a}>{a}</option>)}</select></div>
            )}
            {draft.kind === "outfit" && <>
              <div><label>Set (from the art pack)</label><select value={draft.art_id} onChange={(e) => set("art_id", e.target.value)}><option value="">pick one</option>{art.sets.map((s) => <option key={s.id} value={s.id}>{s.id} · {s.name}</option>)}</select></div>
              <div><label>Tier colour</label><select value={draft.tier} onChange={(e) => set("tier", e.target.value)}>{data.tiers.map((t) => <option key={t} value={t}>{t}</option>)}</select></div>
              <div><label>Wardrobe tab</label><select value={draft.set_kind} onChange={(e) => set("set_kind", e.target.value)}><option value="rank">rank</option><option value="reward">reward</option><option value="exclusive">exclusive</option></select></div>
            </>}
            {draft.kind === "achievement" ? <>
              <div><label>Counts</label><select value={draft.of} onChange={(e) => set("of", e.target.value)}>{data.counters.map((c) => <option key={c} value={c}>{data.counter_label[c]}</option>)}</select></div>
              <div><label>Need</label><input type="number" min={1} value={draft.need} onChange={(e) => set("need", e.target.value)} /></div>
              <div><label>Icon (emoji)</label><input value={draft.icon} onChange={(e) => set("icon", e.target.value)} /></div>
              <div><label>Badge art</label><select value={draft.badge} onChange={(e) => set("badge", e.target.value)}><option value="">none</option>{art.badges.map((b) => <option key={b.n} value={b.n}>{b.n} · {b.name}</option>)}</select></div>
              <div><label>Outfit it unlocks (optional, for the achievements page)</label><input value={draft.outfit} onChange={(e) => set("outfit", e.target.value)} placeholder="set id" /></div>
              {draft.of === "medal" && <div className="wide small muted" style={{ marginTop: 0 }}>Earned when the member holds a medal whose key is this achievement&apos;s id. Grant medals on a member&apos;s admin page.</div>}
            </> : <>
              <div><label>Unlocked by</label><select value={draft.unlock_type} onChange={(e) => set("unlock_type", e.target.value)}>{data.unlock_types.map((t) => <option key={t} value={t}>{UNLOCK_LABEL[t]}</option>)}</select></div>
              {draft.unlock_type === "rank" && <div><label>Rank</label><select value={draft.unlock_n} onChange={(e) => set("unlock_n", e.target.value)}>{data.ranks.map((r) => <option key={r.n} value={r.n}>{r.n} · {r.title}</option>)}</select></div>}
              {draft.unlock_type === "achievement" && <div><label>Achievement</label><select value={draft.unlock_key} onChange={(e) => set("unlock_key", e.target.value)}><option value="">pick one</option>{data.achievement_keys.map((k) => <option key={k} value={k}>{k}</option>)}</select></div>}
              {draft.unlock_type === "medal" && <div><label>Medal key</label><input value={draft.unlock_key} onChange={(e) => set("unlock_key", e.target.value)} placeholder="first_blood" /></div>}
              {draft.unlock_type === "staff" && <div><label>Role</label><select value={draft.unlock_role} onChange={(e) => set("unlock_role", e.target.value)}><option value="admin">admin</option><option value="developer">developer</option><option value="mentor">mentor</option></select></div>}
              <div><label>Locked hint (optional)</label><input value={draft.unlock_hint} onChange={(e) => set("unlock_hint", e.target.value)} placeholder="Shown on the locked tile" /></div>
            </>}
            <div><label>Sort</label><input type="number" value={draft.sort} onChange={(e) => set("sort", e.target.value)} /></div>
            <div><label>Enabled</label><label className="row" style={{ gap: 5, textTransform: "none", letterSpacing: 0, fontSize: 13, color: "var(--ink)" }}><input type="checkbox" checked={draft.enabled} onChange={(e) => set("enabled", e.target.checked)} /> members can see and earn it</label></div>
          </div>
          <div className="row" style={{ gap: 6, marginTop: 12 }}>
            <button className="primary" onClick={save} disabled={busy || !draft.id || !draft.name}>{busy ? "Saving…" : "Save"}</button>
            <button onClick={() => setDraft(null)} disabled={busy}>Cancel</button>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: "auto" }}>
        <table className="adm">
          <thead><tr><th>Id</th><th>Name</th><th>Rule</th><th>Details</th><th>Source</th><th></th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={`ent-row ${r.enabled ? "" : "off"}`}>
                <td><code>{r.id}</code></td>
                <td><b>{r.name}</b>{r.desc && <div className="small muted">{r.desc}</div>}</td>
                <td className="small">{ruleText(r)}</td>
                <td className="small">{dataText(r)}</td>
                <td className="small muted">{r.builtin ? (r.custom ? "built-in, edited" : "built-in") : "added here"}{!r.enabled && " · off"}</td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <button onClick={() => setDraft(fromRow(r))} disabled={busy} style={{ padding: "3px 8px", fontSize: 11 }}>Edit</button>{" "}
                  <button onClick={() => toggle(r)} disabled={busy || r.id === "none"} style={{ padding: "3px 8px", fontSize: 11 }}>{r.enabled ? "Switch off" : "Switch on"}</button>{" "}
                  {r.custom && <button onClick={() => reset(r)} disabled={busy} style={{ padding: "3px 8px", fontSize: 11 }}>{r.builtin ? "Reset" : "Remove"}</button>}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={6} className="muted">Nothing here yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
