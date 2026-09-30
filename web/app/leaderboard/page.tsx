import Link from "next/link";
import { api } from "@/lib/api";

type Row = { id: number | string; xp: number; rank: number; rank_title: string; rank_color: string; major_title: string; name: string | null; avatar: string | null };
export const metadata = { title: "Leaderboard" };

export default async function Leaderboard({ searchParams }: PageProps<"/leaderboard">) {
  const { period } = await searchParams;
  const p = typeof period === "string" && ["week", "month", "all"].includes(period) ? period : "week";
  const data = (await api<{ period: string; rows: Row[] }>(`/leaderboard?period=${p}`)) ?? { period: p, rows: [] };
  return (
    <>
      <h1>Leaderboard</h1>
      <div className="row" style={{ marginBottom: 14 }}>
        {(["week", "month", "all"] as const).map((k) => (
          <Link key={k} href={`/leaderboard?period=${k}`} className={`btn ${p === k ? "primary" : ""}`}>{k === "all" ? "All time" : `This ${k}`}</Link>
        ))}
      </div>
      <div className="card">
        <table className="lb">
          <thead><tr><th>#</th><th>Member</th><th>Rank</th><th>Major</th><th>XP</th></tr></thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={r.id}>
                <td>{i + 1}</td>
                <td><Link href={`/members/${r.id}`} className="row" style={{ gap: 8, display: "inline-flex" }}>{r.avatar && <img className="avatar" src={r.avatar} alt="" />}{r.name ?? `Member ${String(r.id).slice(-4)}`}</Link></td>
                <td><span style={{ color: r.rank_color, fontWeight: 600 }}>{r.rank_title}</span></td>
                <td className="muted">{r.major_title}</td>
                <td><b>{r.xp}</b></td>
              </tr>
            ))}
            {data.rows.length === 0 && <tr><td colSpan={5} className="muted">No XP earned in this period yet.</td></tr>}
          </tbody>
        </table>
        <p className="muted small" style={{ margin: "10px 0 0" }}>Names and avatars appear once a member has logged in here at least once. Cards open for members; owners can make theirs public.</p>
      </div>
    </>
  );
}
