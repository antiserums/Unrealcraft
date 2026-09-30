import Link from "next/link";
import type { QuestSummary } from "@/lib/api";
import { difficultyArt, loadManifest } from "@/lib/art";
import { getT } from "@/lib/i18n";

export async function TierBadge({ tier }: { tier: QuestSummary["tier"] }) {
  const [t, m] = await Promise.all([getT(), loadManifest()]);
  const mark = difficultyArt(m, tier.name);
  return <span className={`tier ${mark ? "has-mark" : ""}`} style={{ background: tier.color }}>{mark ? <img className="px" src={mark} width={32} height={32} alt="" /> : tier.emoji} {t(tier.name)}</span>;
}

export default async function QuestCard({ q, showStatus = false }: { q: QuestSummary; showStatus?: boolean }) {
  const t = await getT();
  const cls = ["card", "qcard", q.status ?? ""].join(" ");
  const kind = q.kind === "capstone" ? `★ ${t("Capstone")}` : q.kind === "elective" ? t("Elective") : t("Required");
  return (
    <Link href={`/quests/${q.id}`} className={cls} style={{ color: "inherit", textDecoration: "none", "--tier": q.tier.color } as React.CSSProperties}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <TierBadge tier={q.tier} />
        {showStatus && q.status && (
          <span className={`status ${q.status}`}>
            {q.status === "done" ? `✔ ${t("Done")}` : q.status === "now" ? `▶ ${t("Up next")}` : q.status === "skipped" ? t("Skipped") : ""}
          </span>
        )}
      </div>
      <div className="title"><span className="muted">{q.id}</span> · {q.title}</div>
      <div className="meta">
        <span>{kind}</span>
        <span>·</span>
        <span>{t("{xp} XP", { xp: q.xp })}</span>
        {q.time_min && <><span>·</span><span>{t("~{n} min", { n: q.time_min })}</span></>}
        {q.has_quiz && <><span>·</span><span>{t("quiz {n}", { n: q.quiz_len })}</span></>}
        {q.tag && <><span>·</span><span className="tag">{q.tag}</span></>}
      </div>
      <div className="meta"><span className="pill">{t(q.owner)}</span>{q.subjects.slice(0, 3).map((s) => <span key={s} className="pill">{s}</span>)}</div>
    </Link>
  );
}
