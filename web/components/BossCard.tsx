import Link from "next/link";
import { getT } from "@/lib/i18n";

export type BossInfo = { name: string; short: string; look: string; color: string; hits_to_win: number; questions: number; wounds_allowed: number; intro: string; tier: string; hint_topics: string[]; creature: string; kind: "enemy" | "boss" };

/** The boss step of a quest: who guards it, what the fight asks, and the way in. The boss itself stands in the page's header. */
export default async function BossCard({ boss, questId, canFight, reason, note }: { boss: BossInfo; questId: string; canFight: boolean; reason?: string; note?: string }) {
  const t = await getT();
  const vars = { questions: boss.questions, hits: boss.hits_to_win, wounds: boss.wounds_allowed, topics: boss.hint_topics.join(", ") };
  return (
    <div className="qboss" style={{ "--boss": boss.color } as React.CSSProperties}>
      <div className="eyebrow" style={{ color: boss.color }}>{boss.kind === "boss" ? t("Boss of this dungeon") : t("Guardian of this dungeon")}</div>
      <b className="qboss-name">{boss.name}</b>
      <div className="small">{boss.hint_topics.length
        ? t("{questions} questions · {hits} hits to win · wounds allowed: {wounds} · asks about {topics}", vars)
        : t("{questions} questions · {hits} hits to win · wounds allowed: {wounds}", vars)}</div>
      {note && <p className="small muted">{note}</p>}
      {canFight ? (
        <Link className="btn primary" href={`/quests/${questId}/fight`}>⚔️ {t("Enter the fight")}</Link>
      ) : (
        <span className="small muted">{reason ?? t("Log in to fight.")}</span>
      )}
    </div>
  );
}
