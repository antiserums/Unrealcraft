import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

type Row = { id: number | string; xp: number; rank: number; rank_title: string; rank_color: string; specialization_title: string; name: string | null; avatar: string | null; staff?: string | null; title?: string | null };
export async function generateMetadata() {
  const t = await getT();
  return { title: t("Leaderboard") };
}

export default async function Leaderboard({ searchParams }: PageProps<"/leaderboard">) {
  const t = await getT();
  const { period } = await searchParams;
  const p = typeof period === "string" && ["week", "month", "all"].includes(period) ? period : "week";
  const data = (await api<{ period: string; rows: Row[] }>(`/leaderboard?period=${p}`)) ?? { period: p, rows: [] };
  return (
    <>
      <PageHeader art="header-leaderboard" title={t("Leaderboard")} />
      <div className="row" style={{ marginBottom: 14 }}>
        {(["week", "month", "all"] as const).map((k) => (
          <Link key={k} href={`/leaderboard?period=${k}`} className={`btn ${p === k ? "primary" : ""}`}>{k === "all" ? t("All time") : k === "month" ? t("This month") : t("This week")}</Link>
        ))}
      </div>
      <div className="card">
        <table className="lb">
          <thead><tr><th>#</th><th>{t("Member")}</th><th>{t("Rank")}</th><th>{t("Specialization")}</th><th>{t("XP")}</th></tr></thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={r.id}>
                <td>{i + 1}</td>
                <td><Link href={`/members/${r.id}`} className="row" style={{ gap: 8, display: "inline-flex" }}>{r.avatar && <img className="avatar" src={r.avatar} alt="" />}{r.name ?? t("Member {id}", { id: String(r.id).slice(-4) })}{r.title && <span className="muted">, {t(r.title)}</span>}</Link></td>
                <td><span className={r.staff ? "staff-title" : ""} style={{ color: r.rank_color, fontWeight: 600 }}>{t(r.rank_title)}</span></td>
                <td className="muted">{t(r.specialization_title)}</td>
                <td><b>{r.xp}</b></td>
              </tr>
            ))}
            {data.rows.length === 0 && <tr><td colSpan={5} className="muted">{t("No XP earned in this period yet.")}</td></tr>}
          </tbody>
        </table>
        <p className="muted small" style={{ margin: "10px 0 0" }}>{t("Names and avatars appear once a member has logged in here at least once. Cards open for members; owners can make theirs public.")}</p>
      </div>
    </>
  );
}
