import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import AdminActions from "@/components/AdminActions";
import { api, type Me, type QuestSummary } from "@/lib/api";

export type AdminMember = {
  user: Record<string, string | number | null>;
  card: { name: string | null; avatar: string | null; rank_title: string; rank_color: string; major_title: string; worn: { name: string }; achievements_earned: number; achievements_total: number; cosmetics: Record<string, unknown> };
  progress: { quest_id: string; status: string; quiz_passed: number; completed_at: string | null; quest: QuestSummary | null }[];
  medals: { medal_key: string; earned_at: string }[];
  xp_recent: { amount: number; reason: string; created_at: string }[];
  submissions: { id: number; quest_id: string; status: string; route: string; notes: string | null; created_at: string }[];
  ranks: { n: number; title: string; xp: number }[]; majors: string[];
};

export default async function AdminMember({ params }: PageProps<"/admin/members/[id]">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/admin/members/${id}`);
  const m = await api<AdminMember>(`/admin/members/${id}`);
  if (!m) notFound();
  const u = m.user;
  return (
    <>
      <div className="eyebrow"><Link href="/admin">← Admin panel</Link></div>
      <h1>{m.card.name ?? `Member ${id}`}</h1>
      <p className="muted small">
        <code>{id}</code> · <span style={{ color: m.card.rank_color }}>{m.card.rank_title}</span> (rank {u.rank}) · {m.card.major_title} · {u.xp} XP · streak {u.streak_days} · wearing {m.card.worn.name} · {m.card.achievements_earned}/{m.card.achievements_total} achievements · <Link href={`/members/${id}`}>player card</Link>
      </p>
      <div className="two">
        <div>
          <AdminActions uid={Number(id)} ranks={m.ranks} majors={m.majors} current={{ rank: Number(u.rank), major: String(u.major) }} />
        </div>
        <div>
          <div className="card">
            <div className="eyebrow">Progress · {m.progress.filter((p) => p.status === "done").length} done</div>
            <div style={{ maxHeight: 320, overflow: "auto", marginTop: 6 }}>
              <table className="adm">
                <tbody>{m.progress.map((p) => <tr key={p.quest_id}><td><Link href={`/quests/${p.quest_id}`}>{p.quest_id}</Link></td><td className="muted">{p.quest?.title ?? "?"}</td><td>{p.status}{p.quiz_passed ? " · quiz" : ""}</td><td className="muted">{p.completed_at?.slice(0, 10) ?? ""}</td></tr>)}
                  {m.progress.length === 0 && <tr><td className="muted">Nothing yet.</td></tr>}</tbody>
              </table>
            </div>
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="eyebrow">Medals</div>
            <div className="small" style={{ marginTop: 6 }}>{m.medals.length ? m.medals.map((x) => <span key={x.medal_key} className="pill" style={{ marginRight: 6 }}>{x.medal_key}</span>) : <span className="muted">None.</span>}</div>
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="eyebrow">Recent XP</div>
            <table className="adm" style={{ marginTop: 6 }}><tbody>{m.xp_recent.map((x, i) => <tr key={i}><td>{x.amount > 0 ? `+${x.amount}` : x.amount}</td><td>{x.reason}</td><td className="muted">{x.created_at.slice(0, 16).replace("T", " ")}</td></tr>)}{m.xp_recent.length === 0 && <tr><td className="muted">Nothing yet.</td></tr>}</tbody></table>
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="eyebrow">Turn-ins</div>
            <table className="adm" style={{ marginTop: 6 }}><tbody>{m.submissions.map((s) => <tr key={s.id}><td><Link href={`/review/${s.id}`}>#{s.id}</Link></td><td>{s.quest_id}</td><td>{s.status}</td><td className="muted">{s.route}</td><td className="muted">{s.created_at.slice(0, 10)}</td></tr>)}{m.submissions.length === 0 && <tr><td className="muted">None.</td></tr>}</tbody></table>
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="eyebrow">Raw user row</div>
            <pre className="notes small" style={{ marginTop: 6 }}>{JSON.stringify(u, null, 1)}</pre>
          </div>
        </div>
      </div>
    </>
  );
}
