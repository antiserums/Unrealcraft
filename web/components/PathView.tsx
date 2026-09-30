import QuestCard from "@/components/QuestCard";
import type { PathData } from "@/lib/api";

/** The member's own road through the curriculum: what is next, what is done, what the next rank opens. */
export default function PathView({ p }: { p: PathData }) {
  return (
    <>
      <p className="muted">
        <span className="eyebrow" style={{ marginRight: 8 }}>{p.specialization_title}{p.specializations.filter((s) => !s.primary).length ? ` (+ ${p.specializations.filter((s) => !s.primary).map((s) => s.title).join(", ")})` : ""} · {p.rank < 0 ? "Orientation" : `Rank ${p.rank}`}</span>
        Why this next: {p.reason}
      </p>
      {p.sections.map((s) => (
        <section key={s.key}>
          <div className="section-h">
            <h2>{s.title}</h2>
            <span className="muted small">{s.quests.filter((q) => q.status === "done").length}/{s.quests.length} done</span>
          </div>
          {s.tier && (
            <div className="note small" style={{ marginBottom: 10 }}>
              {s.tier.emoji} {s.tier.name} quests: <b>{s.tier.done}/{s.tier.need}</b> done. Any {s.tier.name} quest in {p.specialization_title} counts; {s.tier.available} exist so far.
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
