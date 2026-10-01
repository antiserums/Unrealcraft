import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import BossCard, { type BossInfo } from "@/components/BossCard";
import Chest from "@/components/Chest";
import { Boss } from "@/components/Figure";
import { TierBadge } from "@/components/QuestCard";
import ReadingList from "@/components/ReadingList";
import { api, type Me, type Progress, type QuestFull } from "@/lib/api";
import { arenaBackground, creatureSheet, loadManifest, siteArt } from "@/lib/art";
import { Px } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

// the mark at the end of a checklist line; plain "do it yourself" lines carry none
const MARK: Record<string, string> = { done: "✅", on_submit: "📎", optional: "⏳" };
const HINT: Record<string, string> = {
  done: "Done", todo: "Not yet", on_submit: "Checked when you send your work",
  honor: "On your honor", optional: "Optional until the server is bigger",
};

type StepState = "open" | "now" | "done" | "locked";

/** One stop on the quest's trail: a round marker on the line, and the card beside it. */
function Step({ state, mark, title, id, children }: { state: StepState; mark: ReactNode; title: ReactNode; id?: string; children: ReactNode }) {
  return (
    <li className={`qstep ${state}`} id={id}>
      <span className="qstep-mark">{mark}</span>
      <section className="card">
        <h3>{title}</h3>
        {children}
      </section>
    </li>
  );
}

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
  const rankLabel = q.first_steps ? t("First steps") : t("Rank {n}", { n: q.rank });
  // Icons: the pack's when it is there, the old emoji when it is not.
  const ico = (id: string, fallback: string) => { const src = siteArt(manifest, id); return src ? <Px src={src} /> : <>{fallback}</>; };
  const step = { n: 1 };
  const next = () => step.n++;
  const login = <a href={`/api/auth/discord?next=/quests/${q.id}`}>{t("Log in")}</a>;

  const done = p?.status === "done";
  const bossDown = !q.has_quiz || !!p?.quiz_passed;
  const open = !!me && !!p?.unlocked;                       // the member may play this quest
  const canFight = open && q.has_quiz && !p?.quiz_passed;
  const fightable = q.has_quiz && !!boss;
  const arena = arenaBackground(manifest, q.id);
  const bossSheet = boss ? creatureSheet(manifest, boss.creature) : null;
  const stepMark = (state: StepState, icon: string, fallback: string) =>
    state === "done" ? ico("quest-state/done", "✅") : state === "locked" ? ico("quest-state/locked", "🔒") : ico(icon, fallback);

  // the last stop: what "finished" means for this quest, and where the work is sent
  const claim: { state: StepState; icon: [string, string]; title: (n: number) => string; body: ReactNode } | null = (() => {
    if (q.verify_type === "action" && q.id !== "O5") return {
      state: done ? "done" : "open", icon: ["quest-state/done", "✅"], title: (n) => t("Step {n}: Done when", { n }),
      body: <><p>{q.done_when ?? "—"}</p><p className="muted" style={{ marginBottom: 0 }}>{t("Nothing to send. This ticks itself when you do it on the site.")}</p></> };
    if (q.verify_type === "quiz") return {
      state: done ? "done" : "open", icon: ["quest-steps/turn-in", "🎁"],
      title: (n) => done ? t("Step {n}: Dungeon cleared", { n }) : t("Step {n}: Beat the boss to clear the dungeon", { n }),
      body: <p className="muted" style={{ marginBottom: 0 }}>{q.done_when ?? t("Beating the boss completes this quest.")}</p> };
    if (!me) return {
      state: "open", icon: ["quest-steps/turn-in", "🎁"], title: (n) => t("Step {n}: Claim the chest", { n }),
      body: <><p><b>{t("Done when:")}</b> {q.done_when ?? "—"}</p><p className="muted" style={{ marginBottom: 0 }}>{rich(t("{login} to send your work."), { login })}</p></> };
    if (!p?.unlocked) return null;
    if (done) return {
      state: "done", icon: ["quest-state/done", "✅"], title: (n) => t("Step {n}: Chest opened", { n }),
      body: <p className="muted" style={{ marginBottom: 0 }}>{p?.completed_at ? t("You cleared this dungeon on {date}.", { date: p.completed_at.slice(0, 10) }) : t("You cleared this dungeon.")}</p> };
    if (!bossDown) return {
      state: "locked", icon: ["quest-state/locked", "🔒"], title: (n) => t("Step {n}: The chest", { n }),
      body: <p className="muted" style={{ marginBottom: 0 }}>{t("Locked. Beat the boss first, then send your work here.")}</p> };
    return {
      state: "now", icon: ["quest-steps/turn-in", "🎁"], title: (n) => t("Step {n}: Claim the chest", { n }),
      body: <><p><b>{t("Done when:")}</b> {q.done_when ?? "—"}</p>
        <Chest pendingArt={siteArt(manifest, "chest-pending")} questId={q.id} verifyType={q.verify_type} ueVersion={me.ue_version} previous={p.submissions} isO5={q.id === "O5"} /></> };
  })();
  const readN = q.reading.length > 0 ? next() : 0;
  const doN = q.checklist.length > 0 ? next() : 0;
  const bossN = fightable ? next() : 0;
  const claimTitle = claim ? claim.title(next()) : "";

  // how far along the member is: the boss, then the chest
  const stages = (q.has_quiz ? 1 : 0) + (q.verify_type !== "quiz" ? 1 : 0);
  const cleared = done ? stages : (q.has_quiz && p?.quiz_passed ? 1 : 0);
  const pct = stages ? Math.round((cleared / stages) * 100) : done ? 100 : 0;

  return (
    <div className="quest-page" style={{ "--tier": q.tier.color } as React.CSSProperties}>
      <nav className="crumbs" aria-label={t("Quest Board")}>
        <Link href="/quests">← {t("Quest Board")}</Link><span aria-hidden>◆</span><span>{q.id}</span>
      </nav>

      <header className={`qhero ${done ? "cleared" : ""}`} style={arena ? { "--arena": `url("${arena.large ?? arena.small}")` } as React.CSSProperties : undefined}>
        <div className="qhero-bg" aria-hidden />
        <div className="qhero-text">
          <div className="row qhero-tags">
            <TierBadge tier={q.tier} />
            <span className="pill">{rankLabel}</span>
            <span className="pill">{kind}</span>
            <span className="pill">{t(q.owner)}</span>
            {q.subjects.map((s) => <span key={s} className="pill">{s}</span>)}
          </div>
          <h1><span className="qhero-id">{q.id}</span>{q.title}</h1>
          {q.why && <p className="qhero-why">{q.why}</p>}
          {done && <span className="status done">✔ {t("Done")}{p?.completed_at ? ` · ${p.completed_at.slice(0, 10)}` : ""}</span>}
          {!!me && p && !p.unlocked && <span className="status skipped">🔒 {t("Locked until you rank up.")}</span>}
        </div>
        {fightable && boss && (
          <>
            <div className="qhero-boss"><Boss look={boss.look} sheet={bossSheet} color={boss.color} size={110} pose={p?.quiz_passed ? "dead" : "idle"} scale={bossSheet && bossSheet.frame <= 64 ? 2 : 1} /></div>
            <div className="qhero-plate">
              <div className="eyebrow" style={{ color: boss.color }}>{boss.kind === "boss" ? t("Boss of this dungeon") : t("Guardian of this dungeon")}</div>
              <b>{boss.name}</b>
            </div>
          </>
        )}
      </header>

      <dl className="qstats">
        <div className="qstat">{ico("rewards/xp", "✨")}<div><dt>{t("Reward")}</dt><dd>{t("{xp} XP", { xp: q.xp })}</dd></div></div>
        {q.time_min && <div className="qstat">{ico("quest-state/pending", "⏳")}<div><dt>{t("Time")}</dt><dd>{t("about {n} min", { n: q.time_min })}</dd></div></div>}
        {q.has_quiz && <div className="qstat">{ico("quest-steps/boss", "⚔️")}<div><dt>{t("Boss fight")}</dt><dd>{t("quiz of {n}", { n: q.quiz_len })}</dd></div></div>}
        <div className="qstat">{ico("quest-state/proof", "📎")}<div><dt>{t("Proof")}</dt><dd>{q.verify_type}</dd></div></div>
      </dl>

      <div className="quest-body">
        <ol className="qsteps">
          {q.reading.length > 0 && (
            <Step state={done ? "done" : "open"} mark={stepMark(done ? "done" : "open", "quest-steps/read", "📖")} title={t("Step {n}: Read this first", { n: readN })}>
              <ReadingList questId={q.id} reading={q.reading} loggedIn={!!me} />
              {q.has_quiz && <p className="muted small" style={{ margin: 0 }}>{t("The boss asks about these pages. Opening them raises your Lore.")}</p>}
            </Step>
          )}
          {q.checklist.length > 0 && (
            <Step state={done ? "done" : "open"} mark={stepMark(done ? "done" : "open", "quest-steps/build", "🛠️")} title={q.first_steps ? t("Step {n}: Do this", { n: doN }) : t("Step {n}: Do this in Unreal", { n: doN })}>
              <ol className="qcheck">
                {q.checklist.map((c, i) => (
                  <li key={i} className={c.state}><span>{c.text}</span>{MARK[c.state] && <span className="mark" title={HINT[c.state] ? t(HINT[c.state]) : undefined}>{MARK[c.state]}</span>}</li>
                ))}
              </ol>
              {q.do && <p className="small qdo"><b>{t("Your version:")}</b> {q.do}</p>}
            </Step>
          )}
          {fightable && boss && (
            <Step state={p?.quiz_passed ? "done" : "open"} mark={stepMark(p?.quiz_passed ? "done" : "open", "quest-steps/boss", "⚔️")} title={t("Step {n}: Fight the boss (the quiz)", { n: bossN })}>
              <BossCard boss={boss} questId={q.id} canFight={canFight}
                note={t("{n} questions, 4 choices each. You need {need} right. First-try pass earns a bonus.", { n: q.quiz.length, need: Math.ceil(q.quiz.length * 0.8) })}
                reason={!me ? t("Log in to fight.") : !p?.unlocked ? t("Locked until you rank up.") : p?.quiz_passed ? t("Beaten. The boss stays down.") : undefined} />
            </Step>
          )}
          {claim && <Step state={claim.state} id="claim" mark={stepMark(claim.state, claim.icon[0], claim.icon[1])} title={claimTitle}>{claim.body}</Step>}
        </ol>

        <aside className="quest-side">
          <div className="card">
            <div className="eyebrow">{t("Your progress")}</div>
            {!me ? (
              <p className="small" style={{ margin: "8px 0 0" }}>{rich(t("{login} to track this quest."), { login })}</p>
            ) : !p?.unlocked ? (
              <p className="small muted" style={{ margin: "8px 0 0" }}>{t("Locked. This is a Rank {quest} quest; you are Rank {you}.", { quest: q.rank, you: me.rank })}</p>
            ) : (
              <>
                <div className="bar qprog-bar"><span style={{ width: `${pct}%`, background: q.tier.color, color: q.tier.color }} /></div>
                <ul className="qprog small">
                  <li className={done ? "ok" : ""}>{rich(t("Status: {status}"), { status: <b>{p.status ?? t("not started")}</b> })}</li>
                  {q.has_quiz && <li className={p.quiz_passed ? "ok" : ""}>{p.quiz_passed ? t("Quiz: passed") : t("Quiz: not passed ({n} attempts)", { n: p.quiz_attempts })}</li>}
                  {q.verify_type !== "quiz" && q.verify_type !== "action" && (
                    <li className={done ? "ok" : ""}>{p.submissions.length > 0 ? t("Last submission: {status} ({route})", { status: p.submissions[0].status, route: p.submissions[0].route }) : t("No work sent yet")}</li>
                  )}
                </ul>
                {done ? <Link className="btn primary qcta" href="/">{t("Next dungeon")}</Link>
                  : canFight ? <Link className="btn primary qcta" href={`/quests/${q.id}/fight`}>⚔️ {t("Enter the fight")}</Link>
                  : claim?.state === "now" ? <a className="btn primary qcta" href="#claim">{t("Open the chest")}</a> : null}
              </>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
