import Link from "next/link";
import { Boss } from "./Figure";

export type BossInfo = { name: string; short: string; look: string; color: string; hits_to_win: number; questions: number; wounds_allowed: number; intro: string; tier: string; hint_topics: string[]; creature: string; kind: "enemy" | "boss" };

export default function BossCard({ boss, questId, canFight, reason, image }: { boss: BossInfo; questId: string; canFight: boolean; reason?: string; image?: string | null }) {
  return (
    <div className="card" style={{ display: "flex", gap: 14, alignItems: "center", borderColor: boss.color }}>
      <Boss look={boss.look} image={image} color={boss.color} size={92} />
      <div style={{ flex: 1, minWidth: 180 }}>
        <div className="eyebrow" style={{ color: boss.color }}>{boss.kind === "boss" ? "Boss of this dungeon" : "Guardian of this room"}</div>
        <b style={{ fontSize: 16 }}>{boss.name}</b>
        <div className="small muted" style={{ margin: "2px 0 6px" }}>{boss.questions} questions · {boss.hits_to_win} hits to win · {boss.wounds_allowed} wound{boss.wounds_allowed === 1 ? "" : "s"} allowed{boss.hint_topics.length ? ` · asks about ${boss.hint_topics.join(", ")}` : ""}</div>
        {canFight ? (
          <Link className="btn primary" href={`/quests/${questId}/fight`}>⚔️ Enter the fight</Link>
        ) : (
          <span className="small muted">{reason ?? "Log in to fight."}</span>
        )}
      </div>
    </div>
  );
}
