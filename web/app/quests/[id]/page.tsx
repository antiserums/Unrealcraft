import Link from "next/link";
import { notFound } from "next/navigation";
import BossCard, { type BossInfo } from "@/components/BossCard";
import Chest from "@/components/Chest";
import { TierBadge } from "@/components/QuestCard";
import ReadingList from "@/components/ReadingList";
import { api, type Me, type Progress, type QuestFull } from "@/lib/api";
import { creatureImage, loadManifest } from "@/lib/art";

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
  const [data, me, boss, manifest] = await Promise.all([api<{ quest: QuestFull; progress: Progress }>(`/catalog/quests/${id}`), api<Me>("/me"), api<BossInfo>(`/catalog/quests/${id}/boss`), loadManifest()]);
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
              <ReadingList questId={q.id} reading={q.reading} loggedIn={!!me} />
              {q.has_quiz && <p className="muted small" style={{ margin: 0 }}>The boss asks about these pages. Opening them raises your Lore.</p>}
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
          {q.has_quiz && boss && (
            <section style={{ marginBottom: 14 }}>
              <h3>⚔️ Step {next()}: Fight the boss (the quiz)</h3>
              <BossCard boss={boss} questId={q.id} image={creatureImage(manifest, boss.creature)} canFight={!!me && !!p?.unlocked && !p?.quiz_passed}
                reason={!me ? "Log in to fight." : !p?.unlocked ? "Locked until you rank up." : p?.quiz_passed ? "Beaten. The boss stays down." : undefined} />
            </section>
          )}
          {(() => {
            const bossDown = !q.has_quiz || !!p?.quiz_passed;
            const done = p?.status === "done";
            if (q.verify_type === "action") return (
              <section className="card" id="claim"><h3>✅ Step {next()}: Done when</h3><p>{q.done_when ?? "—"}</p><p className="muted">Nothing to send. The Quartermaster ticks this when it sees you do it.</p></section>);
            if (q.verify_type === "quiz") return (
              <section className="card" id="claim"><h3>{done ? "✅" : "🎁"} Step {next()}: {done ? "Room cleared" : "Beat the boss to clear the room"}</h3><p className="muted">{q.done_when ?? "Beating the boss completes this quest."}</p></section>);
            if (!me) return (
              <section className="card" id="claim"><h3>🎁 Step {next()}: Claim the chest</h3><p><b>Done when:</b> {q.done_when ?? "—"}</p><p className="muted"><a href={`/api/auth/discord?next=/quests/${q.id}`}>Log in</a> to send your work.</p></section>);
            if (!p?.unlocked) return null;
            if (done) return (
              <section className="card" id="claim"><h3>✅ Step {next()}: Chest opened</h3><p className="muted">You cleared this room{p?.completed_at ? ` on ${p.completed_at.slice(0, 10)}` : ""}.</p></section>);
            if (!bossDown) return (
              <section className="card lock" id="claim"><h3>🔒 Step {next()}: The chest</h3><p className="muted">Locked. Beat the boss first, then send your work here.</p></section>);
            return (
              <section className="card" id="claim">
                <h3>🎁 Step {next()}: Claim the chest</h3>
                <p><b>Done when:</b> {q.done_when ?? "—"}</p>
                <Chest questId={q.id} verifyType={q.verify_type} ueVersion={me.ue_version} previous={p.submissions} isO5={q.id === "O5"} />
              </section>);
          })()}
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
