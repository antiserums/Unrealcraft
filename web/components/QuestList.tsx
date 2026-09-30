"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

export type QuestRow = { id: string; title: string; rank: number; difficulty: string; specializations: string[]; xp: number; verify_type: string; file: string; quiz_len: number; kind: string; taster_for: string[] };
export type Curriculum = {
  dir: string; files: string[]; default_file: string; specializations: { key: string; title: string }[]; verify_types: string[];
  tiers: Record<string, { name: string; quiz_len: number }>; ranks: { n: number; title: string }[]; quests: QuestRow[];
};

/** The quest table on the admin panel: filter by text, file or rank; open one to edit it. */
export default function QuestList({ cur }: { cur: Curriculum }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [file, setFile] = useState("");
  const [rank, setRank] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return cur.quests.filter((x) => (!needle || x.id.toLowerCase().includes(needle) || (x.title ?? "").toLowerCase().includes(needle) || x.specializations.some((s) => s.includes(needle)))
      && (!file || x.file === file) && (rank === "" || String(x.rank) === rank)).slice(0, 300);
  }, [cur.quests, q, file, rank]);

  async function reload() {
    setBusy(true); setMsg(null);
    const r = await fetch("/api/admin/curriculum/reload", { method: "POST" });
    const j = await r.json();
    setMsg(r.ok ? j.message : j.detail ?? "Reload failed.");
    setBusy(false); router.refresh();
  }

  return (
    <>
      <div className="adm-form" style={{ marginBottom: 10 }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="id, title or specialization" style={{ width: 220 }} />
        <select value={file} onChange={(e) => setFile(e.target.value)}><option value="">every file</option>{cur.files.map((f) => <option key={f} value={f}>{f}</option>)}</select>
        <select value={rank} onChange={(e) => setRank(e.target.value)}><option value="">every rank</option>{cur.ranks.map((r) => <option key={r.n} value={r.n}>{r.n} · {r.title}</option>)}</select>
        <Link className="btn primary" href="/admin/quests/new">New quest</Link>
        <button onClick={reload} disabled={busy}>Reload from disk</button>
        {msg && <span className="small muted">{msg}</span>}
      </div>
      <div className="card" style={{ padding: 0, overflow: "auto" }}>
        <table className="adm">
          <thead><tr><th>Id</th><th>Title</th><th>Rank</th><th>Tier</th><th>Specializations</th><th>Kind</th><th>XP</th><th>Verify</th><th>Quiz</th><th>File</th></tr></thead>
          <tbody>
            {shown.map((x) => (
              <tr key={x.id}>
                <td><Link href={`/admin/quests/${x.id}`}><code>{x.id}</code></Link></td>
                <td><Link href={`/admin/quests/${x.id}`}>{x.title}</Link></td>
                <td>{x.rank}</td><td>{x.difficulty}</td><td className="muted">{x.specializations.join(", ")}{x.taster_for.length ? ` (taster: ${x.taster_for.join(", ")})` : ""}</td><td className="muted">{x.kind}</td><td>{x.xp}</td><td className="muted">{x.verify_type}</td><td>{x.quiz_len}</td><td className="muted">{x.file}</td>
              </tr>
            ))}
            {shown.length === 0 && <tr><td colSpan={10} className="muted">No quests match.</td></tr>}
          </tbody>
        </table>
      </div>
      {cur.quests.length > 300 && shown.length === 300 && <p className="small muted">Showing the first 300. Narrow the filter to see the rest.</p>}
    </>
  );
}
