import Link from "next/link";
import { notFound } from "next/navigation";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type Progress, type QuestFull } from "@/lib/api";

const MARK: Record<string, string> = { done: "✅", todo: "☐", on_submit: "📎", honor: "▫", optional: "⏳" };
const HINT: Record<string, string> = {
  done: "Seen by the Quartermaster", todo: "Not yet", on_submit: "Checked when you send your work",
  honor: "On your honor", optional: "Optional until the server is bigger",
};

export async function generateMetadata({ params }: PageProps<"/quests/[id]">) {
  const { id } = await params;
  return { title: id };
}

export default async function Quest({ params }: PageProps<"/quests/[id]">) {
  const { id } = await params;
  const [data, me] = await Promise.all([api<{ quest: QuestFull; progress: Progress }>(`/catalog/quests/${id}`), api<Me>("/me")]);
  if (!data) notFound();
  const { quest: q, progress: p } = data;
  const kind = q.kind === "capstone" ? "★ Capstone" : q.kind === "elective" ? "Elective" : "Required";
  const rankLabel = q.rank < 0 ? "Orientation" : `Rank ${q.rank}`;
  const step = { n: 1 };
  const next = () => step.n++;
  return (
    <>
      <div className="row" style={{ marginBottom: 6 }}>
        <TierBadge tier={q.tier} />
        <span className="pill">{rankLabel}</span>
        <span className="pill">{kind}</span>
        <span className="pill">{q.owner}</span>
        {p?.status === "done" && <span className="status done">✔ Done{p.completed_at ? ` · ${p.completed_at.slice(0, 10)}` : ""}</span>}
      </div>
      <h1><span className="muted">{q.id}</span> · {q.title}</h1>
      {q.why && <p style={{ fontSize: 16, fontStyle: "italic" }}>{q.why}</p>}
      <div className="row muted small" style={{ marginBottom: 18 }}>
        <span><b>{q.xp} XP</b></span>{q.time_min && <span>· about {q.time_min} min</span>}
        {q.has_quiz && <span>· quiz of {q.quiz_len}</span>}<span>· proof: {q.verify_type}</span>
        {q.subjects.map((s) => <span key={s} className="pill">{s}</span>)}
      </div>

      <div className="two">
        <div>
          {q.reading.length > 0 && (
            <section className="card" style={{ marginBottom: 14 }}>
              <h3>📖 Step {next()}: Read this first</h3>
              <ol className="steps">
                {q.reading.map((r) => (
                  <li key={r.url}><a href={r.url} target="_blank" rel="noreferrer">{r.label}</a>{r.kind === "community" && <span className="tag"> · community</span>}</li>
                ))}
              </ol>
              {q.has_quiz && <p className="muted small" style={{ margin: 0 }}>The quiz asks about these pages.</p>}
            </section>
          )}
          {q.checklist.length > 0 && (
            <section className="card" style={{ marginBottom: 14 }}>
              <h3>🛠️ Step {next()}: Do this{q.rank >= 0 ? " in Unreal" : ""}</h3>
              <ul className="check">
                {q.checklist.map((c, i) => (
                  <li key={i}><span className="mark" title={HINT[c.state]}>{MARK[c.state]}</span><span>{c.text}</span></li>
                ))}
              </ul>
              {q.do && <p className="small" style={{ marginTop: 10 }}><b>Your version:</b> {q.do}</p>}
            </section>
          )}
          <section className="card">
            <h3>✅ Step {next()}: How to finish</h3>
            <p><b>Done when:</b> {q.done_when ?? "—"}</p>
            {q.verify_type === "action" ? (
              <p className="muted">Nothing to send. The Quartermaster ticks this when it sees you do it.</p>
            ) : (
              <p className="muted">
                {q.has_quiz ? "Pass the quiz" : "Send your work"}{q.has_quiz && q.verify_type !== "quiz" ? ", then send your work" : ""}.
                Quizzes and submissions move to this page in the next update; for now use <code>/quiz {q.id}</code>{q.verify_type !== "quiz" && <> and <code>/submit {q.id}</code></>} in Discord.
              </p>
            )}
          </section>
        </div>
        <aside>
          <div className="card">
            <div className="eyebrow">Your progress</div>
            {!me ? (
              <p className="small" style={{ marginTop: 8 }}><a href={`/api/auth/discord?next=/quests/${q.id}`}>Log in</a> to track this quest.</p>
            ) : !p?.unlocked ? (
              <p className="small muted" style={{ marginTop: 8 }}>Locked. This is a Rank {q.rank} quest; you are Rank {me.rank}.</p>
            ) : (
              <ul className="plain small" style={{ marginTop: 8 }}>
                <li>Status: <b>{p.status ?? "not started"}</b></li>
                {q.has_quiz && <li>Quiz: {p.quiz_passed ? "passed" : `not passed (${p.quiz_attempts} attempts)`}</li>}
                {p.submissions.length > 0 && <li>Last submission: {p.submissions[0].status} ({p.submissions[0].route})</li>}
              </ul>
            )}
          </div>
          {q.has_quiz && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="eyebrow">Quiz preview</div>
              <p className="small muted" style={{ margin: "6px 0 0" }}>{q.quiz.length} questions, 4 choices each. You need {Math.ceil(q.quiz.length * 0.8)} right. First-try pass earns a bonus.</p>
            </div>
          )}
          <p className="small" style={{ marginTop: 12 }}><Link href="/quests">← All quests</Link></p>
        </aside>
      </div>
    </>
  );
}
