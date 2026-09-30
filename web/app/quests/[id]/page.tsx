import Link from "next/link";
import { notFound } from "next/navigation";
import BossCard, { type BossInfo } from "@/components/BossCard";
import Chest from "@/components/Chest";
import { TierBadge } from "@/components/QuestCard";
import ReadingList from "@/components/ReadingList";
import { api, type Me, type Progress, type QuestFull } from "@/lib/api";
import { creatureSheet, loadManifest } from "@/lib/art";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

const MARK: Record<string, string> = { done: "✅", todo: "☐", on_submit: "📎", honor: "▫", optional: "⏳" };
const HINT: Record<string, string> = {
  done: "Done", todo: "Not yet", on_submit: "Checked when you send your work",
  honor: "On your honor", optional: "Optional until the server is bigger",
};

export async function generateMetadata({ params }: PageProps<"/quests/[id]">) {
  const { id } = await params;
  return { title: id };
}

export default async function Quest({ params }: PageProps<"/quests/[id]">) {
  const t = await getT();
  const { id } = await params;
  const [data, me, boss, manifest] = await Promise.all([api<{ quest: QuestFull; progress: Progress }>(`/catalog/quests/${id}`), api<Me>("/me"), api<BossInfo>(`/catalog/quests/${id}/boss`), loadManifest()]);
  if (!data) notFound();
  const { quest: q, progress: p } = data;
  const kind = q.kind === "capstone" ? `★ ${t("Capstone")}` : q.kind === "elective" ? t("Elective") : t("Required");
  const rankLabel = q.rank < 0 ? t("Orientation") : t("Rank {n}", { n: q.rank });
  const step = { n: 1 };
  const next = () => step.n++;
  const login = <a href={`/api/auth/discord?next=/quests/${q.id}`}>{t("Log in")}</a>;
  return (
    <>
      <div className="row" style={{ marginBottom: 6 }}>
        <TierBadge tier={q.tier} />
        <span className="pill">{rankLabel}</span>
        <span className="pill">{kind}</span>
        <span className="pill">{t(q.owner)}</span>
        {p?.status === "done" && <span className="status done">✔ {t("Done")}{p.completed_at ? ` · ${p.completed_at.slice(0, 10)}` : ""}</span>}
      </div>
      <h1><span className="muted">{q.id}</span> · {q.title}</h1>
      {q.why && <p style={{ fontSize: 16, fontStyle: "italic" }}>{q.why}</p>}
      <div className="row muted small" style={{ marginBottom: 18 }}>
        <span><b>{t("{xp} XP", { xp: q.xp })}</b></span>{q.time_min && <span>· {t("about {n} min", { n: q.time_min })}</span>}
        {q.has_quiz && <span>· {t("quiz of {n}", { n: q.quiz_len })}</span>}<span>· {t("proof: {type}", { type: q.verify_type })}</span>
        {q.subjects.map((s) => <span key={s} className="pill">{s}</span>)}
      </div>

      <div className="two">
        <div>
          {q.reading.length > 0 && (
            <section className="card" style={{ marginBottom: 14 }}>
              <h3>📖 {t("Step {n}: Read this first", { n: next() })}</h3>
              <ReadingList questId={q.id} reading={q.reading} loggedIn={!!me} />
              {q.has_quiz && <p className="muted small" style={{ margin: 0 }}>{t("The boss asks about these pages. Opening them raises your Lore.")}</p>}
            </section>
          )}
          {q.checklist.length > 0 && (
            <section className="card" style={{ marginBottom: 14 }}>
              <h3>🛠️ {q.rank >= 0 ? t("Step {n}: Do this in Unreal", { n: next() }) : t("Step {n}: Do this", { n: next() })}</h3>
              <ul className="check">
                {q.checklist.map((c, i) => (
                  <li key={i}><span className="mark" title={HINT[c.state] ? t(HINT[c.state]) : undefined}>{MARK[c.state]}</span><span>{c.text}</span></li>
                ))}
              </ul>
              {q.do && <p className="small" style={{ marginTop: 10 }}><b>{t("Your version:")}</b> {q.do}</p>}
            </section>
          )}
          {q.has_quiz && boss && (
            <section style={{ marginBottom: 14 }}>
              <h3>⚔️ {t("Step {n}: Fight the boss (the quiz)", { n: next() })}</h3>
              <BossCard boss={boss} questId={q.id} sheet={creatureSheet(manifest, boss.creature)} canFight={!!me && !!p?.unlocked && !p?.quiz_passed}
                reason={!me ? t("Log in to fight.") : !p?.unlocked ? t("Locked until you rank up.") : p?.quiz_passed ? t("Beaten. The boss stays down.") : undefined} />
            </section>
          )}
          {(() => {
            const bossDown = !q.has_quiz || !!p?.quiz_passed;
            const done = p?.status === "done";
            if (q.verify_type === "action" && q.id !== "O5") return (
              <section className="card" id="claim"><h3>✅ {t("Step {n}: Done when", { n: next() })}</h3><p>{q.done_when ?? "—"}</p><p className="muted">{t("Nothing to send. This ticks itself when you do it on the site.")}</p></section>);
            if (q.verify_type === "quiz") return (
              <section className="card" id="claim"><h3>{done ? "✅" : "🎁"} {done ? t("Step {n}: Dungeon cleared", { n: next() }) : t("Step {n}: Beat the boss to clear the dungeon", { n: next() })}</h3><p className="muted">{q.done_when ?? t("Beating the boss completes this quest.")}</p></section>);
            if (!me) return (
              <section className="card" id="claim"><h3>🎁 {t("Step {n}: Claim the chest", { n: next() })}</h3><p><b>{t("Done when:")}</b> {q.done_when ?? "—"}</p><p className="muted">{rich(t("{login} to send your work."), { login })}</p></section>);
            if (!p?.unlocked) return null;
            if (done) return (
              <section className="card" id="claim"><h3>✅ {t("Step {n}: Chest opened", { n: next() })}</h3><p className="muted">{p?.completed_at ? t("You cleared this dungeon on {date}.", { date: p.completed_at.slice(0, 10) }) : t("You cleared this dungeon.")}</p></section>);
            if (!bossDown) return (
              <section className="card lock" id="claim"><h3>🔒 {t("Step {n}: The chest", { n: next() })}</h3><p className="muted">{t("Locked. Beat the boss first, then send your work here.")}</p></section>);
            return (
              <section className="card" id="claim">
                <h3>🎁 {t("Step {n}: Claim the chest", { n: next() })}</h3>
                <p><b>{t("Done when:")}</b> {q.done_when ?? "—"}</p>
                <Chest questId={q.id} verifyType={q.verify_type} ueVersion={me.ue_version} previous={p.submissions} isO5={q.id === "O5"} />
              </section>);
          })()}
        </div>
        <aside>
          <div className="card">
            <div className="eyebrow">{t("Your progress")}</div>
            {!me ? (
              <p className="small" style={{ marginTop: 8 }}>{rich(t("{login} to track this quest."), { login })}</p>
            ) : !p?.unlocked ? (
              <p className="small muted" style={{ marginTop: 8 }}>{t("Locked. This is a Rank {quest} quest; you are Rank {you}.", { quest: q.rank, you: me.rank })}</p>
            ) : (
              <ul className="plain small" style={{ marginTop: 8 }}>
                <li>{rich(t("Status: {status}"), { status: <b>{p.status ?? t("not started")}</b> })}</li>
                {q.has_quiz && <li>{p.quiz_passed ? t("Quiz: passed") : t("Quiz: not passed ({n} attempts)", { n: p.quiz_attempts })}</li>}
                {p.submissions.length > 0 && <li>{t("Last submission: {status} ({route})", { status: p.submissions[0].status, route: p.submissions[0].route })}</li>}
              </ul>
            )}
          </div>
          {q.has_quiz && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="eyebrow">{t("Quiz preview")}</div>
              <p className="small muted" style={{ margin: "6px 0 0" }}>{t("{n} questions, 4 choices each. You need {need} right. First-try pass earns a bonus.", { n: q.quiz.length, need: Math.ceil(q.quiz.length * 0.8) })}</p>
            </div>
          )}
          <p className="small" style={{ marginTop: 12 }}><Link href="/quests">← {t("All quests")}</Link></p>
        </aside>
      </div>
    </>
  );
}
