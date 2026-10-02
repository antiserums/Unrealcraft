import Link from "next/link";
import type { QuestSummary } from "@/lib/api";
import { difficultyArt, loadManifest, siteArt, type Manifest } from "@/lib/art";
import { Px } from "./SiteArt";
import { getT } from "@/lib/i18n";
import type { TFn } from "@/lib/i18n-config";

/** The words and the art pack, loaded once by the page and handed to every card. The quest board draws hundreds of
 *  cards; when each one fetched these for itself, the page took many seconds to render. */
export type CardCtx = { t: TFn; m: Manifest | null };

export async function cardCtx(): Promise<CardCtx> {
  const [t, m] = await Promise.all([getT(), loadManifest()]);
  return { t, m };
}

export function TierBadgeView({ tier, ctx }: { tier: QuestSummary["tier"]; ctx: CardCtx }) {
  const mark = difficultyArt(ctx.m, tier.name);
  return <span className={`tier tier-${tier.name.toLowerCase()} ${mark ? "has-mark" : ""}`} style={{ background: tier.color }}>{mark ? <img className="px" src={mark} width={32} height={32} alt="" /> : tier.emoji} {ctx.t(tier.name)}</span>;
}

/** One badge on a page: loads what it needs itself. */
export async function TierBadge({ tier }: { tier: QuestSummary["tier"] }) {
  return <TierBadgeView tier={tier} ctx={await cardCtx()} />;
}

/** A quest on the board or on a path. Give it the page's `ctx` (see `cardCtx`). */
export default function QuestCard({ q, ctx, showStatus = false }: { q: QuestSummary; ctx: CardCtx; showStatus?: boolean }) {
  const { t, m } = ctx;
  const mark = q.status && ["done", "now", "skipped"].includes(q.status) ? siteArt(m, `quest-state/${q.status}`) : null;
  const cls = ["card", "qcard", q.status ?? ""].join(" ");
  const kind = q.kind === "capstone" ? `★ ${t("Capstone")}` : q.kind === "elective" ? t("Elective") : t("Required");
  return (
    <Link href={`/quests/${q.id}`} prefetch={false} className={cls} style={{ color: "inherit", textDecoration: "none", "--tier": q.tier.color } as React.CSSProperties}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <TierBadgeView tier={q.tier} ctx={ctx} />
        {showStatus && q.status && (
          <span className={`status ${q.status}`}>
            {mark ? <Px src={mark} /> : q.status === "done" ? "✔ " : q.status === "now" ? "▶ " : ""}
            {q.status === "done" ? t("Done") : q.status === "now" ? t("Up next") : q.status === "skipped" ? t("Skipped") : ""}
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
      <div className="meta"><span className="pill">{t(q.owner)}</span>{q.subjects.slice(0, 3).map((s) => <span key={s} className="pill muted-chip">{s}</span>)}</div>
    </Link>
  );
}
