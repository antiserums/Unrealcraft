import Link from "next/link";
import type { QuestSummary } from "@/lib/api";

export function TierBadge({ tier }: { tier: QuestSummary["tier"] }) {
  return <span className="tier" style={{ background: tier.color }}>{tier.emoji} {tier.name}</span>;
}

export default function QuestCard({ q, showStatus = false }: { q: QuestSummary; showStatus?: boolean }) {
  const cls = ["card", "qcard", q.status ?? ""].join(" ");
  const kind = q.kind === "capstone" ? "★ Capstone" : q.kind === "elective" ? "Elective" : "Required";
  return (
    <Link href={`/quests/${q.id}`} className={cls} style={{ color: "inherit", textDecoration: "none" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <TierBadge tier={q.tier} />
        {showStatus && q.status && (
          <span className={`status ${q.status}`}>
            {q.status === "done" ? "✔ Done" : q.status === "now" ? "▶ Up next" : q.status === "skipped" ? "Skipped" : ""}
          </span>
        )}
      </div>
      <div className="title"><span className="muted">{q.id}</span> · {q.title}</div>
      <div className="meta">
        <span>{kind}</span>
        <span>·</span>
        <span>{q.xp} XP</span>
        {q.time_min && <><span>·</span><span>~{q.time_min} min</span></>}
        {q.has_quiz && <><span>·</span><span>quiz {q.quiz_len}</span></>}
        {q.tag && <><span>·</span><span className="tag">{q.tag}</span></>}
      </div>
      <div className="meta"><span className="pill">{q.owner}</span>{q.subjects.slice(0, 3).map((s) => <span key={s} className="pill">{s}</span>)}</div>
    </Link>
  );
}
