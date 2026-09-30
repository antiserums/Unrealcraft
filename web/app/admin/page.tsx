import Link from "next/link";
import { redirect } from "next/navigation";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Admin" };

type Overview = {
  stats: Record<string, number>; db_path: string; curriculum_dir: string; admin_ids: number[];
  events: { id: number; type: string; member_id: number; payload: string; created_at: string; delivered: number }[];
  log: { id: number; admin_id: number; action: string; target_id: number | null; detail: string; created_at: string }[];
  pending: { id: number; user_id: number; quest_id: string; route: string; created_at: string }[];
};
type MemberRow = { discord_id: number; name: string | null; avatar: string | null; major: string; rank: number; xp: number; done: number; streak_days: number; created_at: string };

const LABEL: Record<string, string> = { members: "members", members_logged_in: "logged in on the site", quests_done: "quests done", pending_reviews: "pending reviews", fights_today: "fights today", fights_total: "fights ever", events_undelivered: "events waiting for the bot", xp_total: "XP awarded", quests_in_catalog: "quests in catalog" };

export default async function Admin({ searchParams }: PageProps<"/admin">) {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/admin");
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q : "";
  const [o, m] = await Promise.all([api<Overview>("/admin"), api<{ members: MemberRow[] }>(`/admin/members?q=${encodeURIComponent(q)}`)]);
  if (!o) return <><h1>Admin</h1><div className="card">Admins only. Add your Discord id to <code>ADMIN_IDS</code> in <code>api/.env</code> and restart the API.</div></>;
  return (
    <>
      <div className="eyebrow">Staff</div>
      <h1>Admin panel</h1>
      <p className="muted small">Database: <code>{o.db_path}</code> · curriculum: <code>{o.curriculum_dir}</code> · admins: {o.admin_ids.length ? o.admin_ids.join(", ") : "none set (dev login only)"}</p>

      <div className="stats-grid">
        {Object.entries(o.stats).map(([k, v]) => <div key={k} className="card stat"><b>{v}</b><span className="muted small">{LABEL[k] ?? k}</span></div>)}
      </div>

      <div className="section-h"><h2>Members</h2><span className="muted small">search by Discord id or display name</span></div>
      <form className="filters" method="get">
        <input name="q" defaultValue={q} placeholder="id or name" />
        <button type="submit" className="primary">Search</button>
        {q && <Link className="btn" href="/admin">Clear</Link>}
      </form>
      <div className="card" style={{ padding: 0, overflow: "auto" }}>
        <table className="adm">
          <thead><tr><th>Member</th><th>Id</th><th>Rank</th><th>Major</th><th>XP</th><th>Done</th><th>Streak</th><th>Since</th></tr></thead>
          <tbody>
            {(m?.members ?? []).map((r) => (
              <tr key={r.discord_id}>
                <td><Link href={`/admin/members/${r.discord_id}`}>{r.name ?? <span className="muted">not logged in yet</span>}</Link></td>
                <td><code>{r.discord_id}</code></td><td>{r.rank}</td><td>{r.major}</td><td>{r.xp}</td><td>{r.done}</td><td>{r.streak_days}</td><td className="muted">{r.created_at.slice(0, 10)}</td>
              </tr>
            ))}
            {(m?.members ?? []).length === 0 && <tr><td colSpan={8} className="muted">No members match.</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="two" style={{ marginTop: 24 }}>
        <div>
          <div className="section-h"><h2>Events for the bot</h2><span className="muted small">newest first · the bot polls every 20 s</span></div>
          <div className="card" style={{ padding: 0, overflow: "auto", maxHeight: 420 }}>
            <table className="adm">
              <thead><tr><th>#</th><th>Type</th><th>Member</th><th>Payload</th><th>Sent</th></tr></thead>
              <tbody>{o.events.map((e) => <tr key={e.id}><td>{e.id}</td><td>{e.type}</td><td><Link href={`/admin/members/${e.member_id}`}><code>{e.member_id}</code></Link></td><td><code>{e.payload.slice(0, 90)}</code></td><td>{e.delivered ? "✔" : <span style={{ color: "var(--warn)" }}>waiting</span>}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
        <div>
          <div className="section-h"><h2>Admin log</h2></div>
          <div className="card" style={{ padding: 0, overflow: "auto", maxHeight: 420 }}>
            <table className="adm">
              <thead><tr><th>When</th><th>Admin</th><th>Action</th><th>Target</th><th>Detail</th></tr></thead>
              <tbody>
                {o.log.map((l) => <tr key={l.id}><td className="muted">{l.created_at.slice(5, 16).replace("T", " ")}</td><td><code>{l.admin_id}</code></td><td>{l.action}</td><td>{l.target_id ? <Link href={`/admin/members/${l.target_id}`}><code>{l.target_id}</code></Link> : ""}</td><td><code>{l.detail.slice(0, 80)}</code></td></tr>)}
                {o.log.length === 0 && <tr><td colSpan={5} className="muted">Nothing yet.</td></tr>}
              </tbody>
            </table>
          </div>
          {o.pending.length > 0 && <p className="small" style={{ marginTop: 10 }}>{o.pending.length} turn-in{o.pending.length === 1 ? "" : "s"} waiting in the <Link href="/review">review inbox</Link>.</p>}
        </div>
      </div>
    </>
  );
}
