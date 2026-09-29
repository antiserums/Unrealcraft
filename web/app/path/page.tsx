import { redirect } from "next/navigation";
import QuestCard from "@/components/QuestCard";
import { api, type PathData } from "@/lib/api";

export const metadata = { title: "My path" };

export default async function Path() {
  const p = await api<PathData>("/me/path");
  if (!p) redirect("/api/auth/discord?next=/path");
  return (
    <>
      <div className="eyebrow">{p.major_title} · Rank {p.rank < 0 ? "Orientation" : p.rank}</div>
      <h1>My path</h1>
      <p className="muted">Why this next: {p.reason}</p>
      {p.sections.map((s) => (
        <section key={s.key}>
          <div className="section-h">
            <h2>{s.title}</h2>
            <span className="muted small">{s.quests.filter((q) => q.status === "done").length}/{s.quests.length} done</span>
          </div>
          {s.tier && (
            <div className="note small" style={{ marginBottom: 10 }}>
              {s.tier.emoji} {s.tier.name} quests: <b>{s.tier.done}/{s.tier.need}</b> done. Any {s.tier.name} quest in {p.major_title} counts; {s.tier.available} exist so far.
            </div>
          )}
          <div className="grid">{s.quests.map((q) => <QuestCard key={q.id} q={q} showStatus />)}</div>
        </section>
      ))}
      {p.locked && (
        <section className="lock">
          <div className="section-h">
            <h2>🔒 Rank {p.locked.n} · {p.locked.title}</h2>
            <span className="muted small">
              needs {p.locked.xp} XP + {p.locked.n === 1 ? "Starter Quests" : `Rank ${p.locked.n - 1} path`}
              {p.locked.gate_tier && ` + ${p.locked.gate_tier.need} ${p.locked.gate_tier.name} quests`}
            </span>
          </div>
          {p.locked.opens && <p className="small muted">Opens: {p.locked.opens}</p>}
          <div className="grid">{p.locked.quests.slice(0, 6).map((q) => <QuestCard key={q.id} q={q} />)}</div>
          {p.locked.tasters.length > 0 && (
            <p className="small muted" style={{ marginTop: 10 }}>
              Tasters: {p.locked.tasters.map((g) => g.map((t) => `${t.id} ${t.title}`).join(" or ")).join("; ")}
            </p>
          )}
          {p.locked.capstone && <p className="small"><b>★ Capstone:</b> {p.locked.capstone.title}. {p.locked.capstone.brief}</p>}
        </section>
      )}
    </>
  );
}
