"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

type Rank = { n: number; title: string; xp: number };

/** Admin actions on one member. Every call goes to /api/admin/members/{id}/... and is written to the admin log. */
export default function AdminActions({ uid, ranks, seals, majors, current }: { uid: number; ranks: Rank[]; seals: string[]; majors: string[]; current: { rank: number; seal: string; major: string } }) {
  const router = useRouter();
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [quest, setQuest] = useState("");
  const [withXp, setWithXp] = useState(true);
  const [rank, setRank] = useState(String(current.rank));
  const [seal, setSeal] = useState(current.seal);
  const [major, setMajor] = useState(current.major);
  const [xp, setXp] = useState("");
  const [reason, setReason] = useState("testing");
  const [medal, setMedal] = useState("");
  const [confirm, setConfirm] = useState("");
  const [deleteUser, setDeleteUser] = useState(false);

  async function post(path: string, body: Record<string, unknown>) {
    setBusy(true); setErr(null); setMsg(null);
    const r = await fetch(`/api/admin/members/${uid}/${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    if (!r.ok) setErr(j.detail ?? "Failed."); else { setMsg(j.message); router.refresh(); }
    setBusy(false);
  }

  return (
    <div className="card">
      <div className="eyebrow">Actions</div>
      {msg && <div className="note small" style={{ marginTop: 8 }}>{msg}</div>}
      {err && <div className="note small" style={{ marginTop: 8, borderColor: "var(--bad)" }}>{err}</div>}

      <h3 style={{ marginTop: 14 }}>Quest</h3>
      <div className="adm-form">
        <input value={quest} onChange={(e) => setQuest(e.target.value)} placeholder="quest id, e.g. LDQ21" style={{ width: 160 }} />
        <label className="small muted row" style={{ gap: 4 }}><input type="checkbox" checked={withXp} onChange={(e) => setWithXp(e.target.checked)} /> give XP</label>
        <button className="primary" disabled={busy || !quest} onClick={() => post("quests", { quest_id: quest, action: "done", xp: withXp })}>Mark done</button>
        <button disabled={busy || !quest} onClick={() => post("quests", { quest_id: quest, action: "clear" })}>Clear</button>
      </div>
      <div className="small muted" style={{ marginTop: 4 }}>Marks the quest done (quiz passed) and, with XP, awards its XP. The bot then checks for a promotion.</div>

      <h3 style={{ marginTop: 16 }}>Rank and major</h3>
      <div className="adm-form">
        <select value={rank} onChange={(e) => setRank(e.target.value)}>
          <option value="-1">-1 · Orientation</option>
          {ranks.map((r) => <option key={r.n} value={r.n}>{r.n} · {r.title} ({r.xp} XP)</option>)}
        </select>
        <select value={seal} onChange={(e) => setSeal(e.target.value)}>
          <option value="">no seal</option>
          {seals.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={major} onChange={(e) => setMajor(e.target.value)}>
          {majors.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <button className="primary" disabled={busy} onClick={() => post("rank", { rank: Number(rank), seal, major })}>Set</button>
      </div>
      <div className="small muted" style={{ marginTop: 4 }}>XP is raised to the rank's floor if it is below it. The bot swaps Discord roles within a minute.</div>

      <h3 style={{ marginTop: 16 }}>XP</h3>
      <div className="adm-form">
        <input type="number" value={xp} onChange={(e) => setXp(e.target.value)} placeholder="+/- amount" style={{ width: 110 }} />
        <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="reason" style={{ width: 160 }} />
        <button className="primary" disabled={busy || !xp} onClick={() => post("xp", { amount: Number(xp), reason })}>Apply</button>
      </div>

      <h3 style={{ marginTop: 16 }}>Medal</h3>
      <div className="adm-form">
        <input value={medal} onChange={(e) => setMedal(e.target.value)} placeholder="first_blood, jump_0_1 …" style={{ width: 200 }} />
        <button className="primary" disabled={busy || !medal} onClick={() => post("medal", { key: medal })}>Grant</button>
        <button disabled={busy || !medal} onClick={() => post("medal", { key: medal, remove: true })}>Remove</button>
      </div>

      <h3 style={{ marginTop: 16, color: "var(--bad)" }}>Reset this account</h3>
      <div className="small muted">Wipes progress, XP, medals, turn-ins, fights, outfits and saved name. Type the member id to confirm.</div>
      <div className="adm-form">
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder={String(uid)} style={{ width: 200 }} />
        <label className="small muted row" style={{ gap: 4 }}><input type="checkbox" checked={deleteUser} onChange={(e) => setDeleteUser(e.target.checked)} /> delete the user row too</label>
        <button className="danger" disabled={busy || confirm !== String(uid)} onClick={() => post("reset", { confirm, delete_user: deleteUser })}>Reset</button>
      </div>
    </div>
  );
}
