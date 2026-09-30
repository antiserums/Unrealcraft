import Link from "next/link";
import type { SheetSpec } from "@/lib/art";
import { getT } from "@/lib/i18n";
import { Boss } from "./Figure";

export type BossInfo = { name: string; short: string; look: string; color: string; hits_to_win: number; questions: number; wounds_allowed: number; intro: string; tier: string; hint_topics: string[]; creature: string; kind: "enemy" | "boss" };

export default async function BossCard({ boss, questId, canFight, reason, sheet }: { boss: BossInfo; questId: string; canFight: boolean; reason?: string; sheet?: SheetSpec | null }) {
  const t = await getT();
  const vars = { questions: boss.questions, hits: boss.hits_to_win, wounds: boss.wounds_allowed, topics: boss.hint_topics.join(", ") };
  return (
    <div className="card" style={{ display: "flex", gap: 14, alignItems: "center", borderColor: boss.color }}>
      <Boss look={boss.look} sheet={sheet} color={boss.color} size={92} scale={sheet && sheet.frame <= 64 ? 2 : 1} />
      <div style={{ flex: 1, minWidth: 180 }}>
        <div className="eyebrow" style={{ color: boss.color }}>{boss.kind === "boss" ? t("Boss of this dungeon") : t("Guardian of this dungeon")}</div>
        <b style={{ fontSize: 16 }}>{boss.name}</b>
        <div className="small muted" style={{ margin: "2px 0 6px" }}>{boss.hint_topics.length
          ? t("{questions} questions · {hits} hits to win · wounds allowed: {wounds} · asks about {topics}", vars)
          : t("{questions} questions · {hits} hits to win · wounds allowed: {wounds}", vars)}</div>
        {canFight ? (
          <Link className="btn primary" href={`/quests/${questId}/fight`}>⚔️ {t("Enter the fight")}</Link>
        ) : (
          <span className="small muted">{reason ?? t("Log in to fight.")}</span>
        )}
      </div>
    </div>
  );
}
