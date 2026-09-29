import { notFound, redirect } from "next/navigation";
import { api, type Me } from "@/lib/api";

export default async function Member({ params }: PageProps<"/members/[id]">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/members/${id}`);
  const m = await api<Me>(`/members/${id}`);
  if (!m) notFound();
  return (
    <>
      <div className="eyebrow">Member</div>
      <h1><span style={{ color: m.rank_color }}>{m.rank_title}</span> · {m.major_title}</h1>
      <div className="card">
        <div className="row" style={{ gap: 24 }}>
          <div className="stat"><b>{m.xp}</b><span className="muted small">XP</span></div>
          <div className="stat"><b>{m.done_count}</b><span className="muted small">quests done</span></div>
          <div className="stat"><b>{m.streak_days}</b><span className="muted small">day streak</span></div>
          <div className="stat"><b>{m.medals.length}</b><span className="muted small">medals</span></div>
        </div>
        <p className="muted small" style={{ margin: "10px 0 0" }}>Display names and avatars show once members have logged in here.</p>
      </div>
    </>
  );
}
