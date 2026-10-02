import QuestCard, { cardCtx } from "@/components/QuestCard";
import type { PathData } from "@/lib/api";
import { siteArt } from "@/lib/art";
import { rich } from "@/lib/i18n-config";

/** The member's own road through the curriculum: what is next, what is done, what the next rank opens. */
export default async function PathView({ p }: { p: PathData }) {
  const ctx = await cardCtx();
  const t = ctx.t;
  const gate = siteArt(ctx.m, "locked-gate");
  const extras = p.specializations.filter((s) => !s.primary).map((s) => t(s.title)).join(", ");
  const specTitle = t(p.specialization_title);
  const locked = p.locked;
  const needs = !locked ? "" : locked.gate_tier
    ? (locked.n === 1
      ? t("needs {xp} XP + Starter Quests + {need} {tier} quests", { xp: locked.xp, need: locked.gate_tier.need, tier: t(locked.gate_tier.name) })
      : t("needs {xp} XP + Rank {n} path + {need} {tier} quests", { xp: locked.xp, n: locked.n - 1, need: locked.gate_tier.need, tier: t(locked.gate_tier.name) }))
    : (locked.n === 1
      ? t("needs {xp} XP + Starter Quests", { xp: locked.xp })
      : t("needs {xp} XP + Rank {n} path", { xp: locked.xp, n: locked.n - 1 }));
  return (
    <>
      <p className="muted">
        <span className="eyebrow" style={{ marginRight: 8 }}>{specTitle}{extras ? ` (+ ${extras})` : ""} · {t("Rank {n}", { n: p.rank })}</span>
        {t("Why this next: {reason}", { reason: p.reason })}
      </p>
      {p.sections.map((s) => (
        <section key={s.key}>
          <div className="section-h">
            <h2>{s.title}</h2>
            <span className="muted small">{t("{done}/{total} done", { done: s.quests.filter((q) => q.status === "done").length, total: s.quests.length })}</span>
          </div>
          {s.tier && (
            <div className="note small" style={{ marginBottom: 10 }}>
              {s.tier.emoji} {rich(t("{tier} quests: {count} done. Any {tier} quest in {spec} counts; {available} exist so far.", { tier: t(s.tier.name), spec: specTitle, available: s.tier.available }), { count: <b>{s.tier.done}/{s.tier.need}</b> })}
            </div>
          )}
          <div className="grid">{s.quests.map((q) => <QuestCard key={q.id} q={q} ctx={ctx} showStatus />)}</div>
        </section>
      ))}
      {locked && (
        <section className="lock">
          {gate && <img className="px lock-art" src={gate} width={160} height={120} alt="" />}
          <div className="section-h">
            <h2>🔒 {t("Rank {n}", { n: locked.n })} · {t(locked.title)}</h2>
            <span className="muted small">
              {needs}
            </span>
          </div>
          <div className="grid">{locked.quests.slice(0, 6).map((q) => <QuestCard key={q.id} q={q} ctx={ctx} />)}</div>
          {locked.tasters.length > 0 && (
            <p className="small muted" style={{ marginTop: 10 }}>
              {t("Tasters: {list}", { list: locked.tasters.map((g) => g.map((x) => `${x.id} ${x.title}`).join(` ${t("or")} `)).join("; ") })}
            </p>
          )}
          {locked.capstone && <p className="small"><b>★ {t("Capstone:")}</b> {locked.capstone.title}. {locked.capstone.brief}</p>}
        </section>
      )}
    </>
  );
}
