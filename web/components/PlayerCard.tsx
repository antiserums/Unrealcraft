"use client";
import type { Card } from "@/lib/api";
import type { SheetSpec } from "@/lib/art";
import { AvatarDeco } from "./DecoAnim";
import { Character } from "./Figure";
import { useT } from "./I18n";

export type Deco = { avatar: string | null; card: string | null; avatarTheme?: string };

/** The shareable player card. Pure display: the owner edits it with CardEditor next to it.
 *  The avatar ring is drawn here; the card border is drawn by the page around the card (see .studio-card). */
export default function PlayerCard({ c, sheet, badges, deco }: { c: Card; sheet: SheetSpec | null; badges: Record<string, string | null>; deco?: Deco }) {
  const t = useT();
  const pct = c.xp_next ? Math.min(100, Math.round(((c.xp - c.xp_floor) / (c.xp_next - c.xp_floor)) * 100)) : 100;
  return (
    <article className="pcard" style={{ "--plate": c.nameplate } as React.CSSProperties}>
      <div className="pcard-banner">
        <span className={`pcard-rank ${c.staff ? "staff-title" : ""}`} style={{ color: c.rank_color, borderColor: c.rank_color }}>{t(c.rank_title)}</span>
        <span className="pcard-specs">
          <span className="pcard-spec">{t(c.specialization_title)}</span>
          {c.specializations.filter((s) => !s.primary).length > 0 && (
            <span className="pcard-spec-extra">{c.specializations.filter((s) => !s.primary).map((s) => t(s.title)).join(" · ")}</span>
          )}
        </span>
      </div>
      <div className="pcard-body">
        <div className="pcard-id">
          <div className="pcard-avatar-wrap">
            <div className="pcard-avatar">{c.avatar ? <img src={c.avatar} alt="" /> : <span>{(c.name ?? "?").slice(0, 1)}</span>}</div>
            <AvatarDeco src={deco?.avatar ?? null} theme={deco?.avatarTheme} />
          </div>
          <div>
            <div className="pcard-name">{c.name ?? t("A guild member")}{c.title && <span className="pcard-title">, {t(c.title)}</span>}</div>
            {c.motto ? <div className="pcard-motto">“{c.motto}”</div> : <div className="pcard-motto muted">{t("No motto yet.")}</div>}
          </div>
        </div>
        <div className="pcard-xp">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <span className="eyebrow">{t("{xp} XP", { xp: c.xp })}</span>
            {c.next_rank && <span className="small muted">{t("{xp} to {rank}", { xp: c.next_rank.xp_to_go, rank: t(c.next_rank.title) })}</span>}
          </div>
          <div className="bar"><span style={{ width: `${pct}%`, background: c.nameplate }} /></div>
        </div>
        <div className="pcard-stats">
          <div className="stat"><b>{c.done_count}</b><span className="muted small">{t("quests")}</span></div>
          <div className="stat"><b>{c.streak_days}</b><span className="muted small">{t("day streak")}</span></div>
          <div className="stat"><b>{c.achievements_earned}<span className="muted" style={{ fontSize: 13 }}>/{c.achievements_total}</span></b><span className="muted small">{t("achievements")}</span></div>
        </div>
        <div className={`pcard-figure ${c.staff ? "staff-glow" : ""}`} style={c.staff ? { "--glow": c.rank_color } as React.CSSProperties : undefined}>
          <Character outfit={c.worn.id} sheet={sheet} weapon={c.style} color={c.nameplate} size={140} scale={2} crop={{ x: 20, y: 8, w: 88, h: 104 }} still />
          <div className="small" style={{ textAlign: "center" }}><span className="muted">{t("Wearing")}</span> <b style={{ color: c.worn.color }}>{c.worn.name}</b></div>
        </div>
        <div className="pcard-feats">
          {c.featured.length ? c.featured.map((a) => (
            <div key={a.key} className="feat" title={t(a.desc)}>
              {badges[a.key] ? <img className="px feat-badge" src={badges[a.key]!} alt="" /> : <span className="feat-icon">{a.icon}</span>}
              <span>{t(a.name)}</span>
            </div>
          )) : <div className="small muted">{t("No achievements to show yet. The first one comes with the first finished quest.")}</div>}
        </div>
      </div>
      <div className="pcard-foot">
        <span>Unrealcraft</span>
        {c.member_since && <span className="muted">{t("member since {date}", { date: c.member_since.slice(0, 10) })}</span>}
      </div>
    </article>
  );
}
