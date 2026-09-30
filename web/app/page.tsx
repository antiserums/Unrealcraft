import Link from "next/link";
import HowItWorks from "@/components/HowItWorks";
import Ico from "@/components/Ico";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type Next, type Specializations } from "@/lib/api";
import HeroBanner from "@/components/HeroBanner";
import { AvatarDeco } from "@/components/DecoAnim";
import { bannerSet, decorationImage, loadManifest, siteArtGroup } from "@/lib/art";
import { MISSION } from "@/lib/mission";
import { getT } from "@/lib/i18n";

type MemberStats = { fights: number; fights_won: number; bosses_first_try: number; crit_xp: number; xp_week: number; reads: number; turnins: number; turnins_passed: number; turnins_pending: number };
type GuildStats = { members: number; quests_done: number; quests_done_week: number; fights_week: number; xp_week: number; masters: number };

export default async function Home() {
  const t = await getT();
  const [me, manifest] = await Promise.all([api<Me>("/me"), loadManifest()]);
  const [next, stats, guild, specs] = await Promise.all([
    me ? api<Next>("/me/next") : null,
    me ? api<{ me: MemberStats; guild: GuildStats }>("/me/stats") : null,
    me ? null : api<GuildStats>("/catalog/stats"),
    me ? null : api<Specializations>("/catalog/specializations"),
  ]);
  const banner = bannerSet(manifest);
  const pct = me?.xp_next ? Math.min(100, Math.round(((me.xp - me.xp_floor) / (me.xp_next - me.xp_floor)) * 100)) : 100;
  const hero = (
    <>
        {me ? (
          <div className="ribbon">
            <Link href="/me" className="ribbon-who" title={t("Your player card")}>
              <div className="pcard-avatar-wrap">
                <div className="pcard-avatar" style={{ "--plate": me.nameplate ?? me.rank_color } as React.CSSProperties}>{me.avatar ? <img src={me.avatar} alt="" /> : <span>{(me.name ?? "?").slice(0, 1)}</span>}</div>
                <AvatarDeco src={decorationImage(manifest, "avatar", me.avatar_frame_art ?? undefined)} theme={me.avatar_frame} />
              </div>
              <div className="ribbon-id">
                <div className="eyebrow">{t("Welcome back")}</div>
                <h1>{me.name}</h1>
                {me.title && <div className="ribbon-title">{t(me.title)}</div>}
                <div className="ribbon-meta">
                  <span className={`pill ${me.staff ? "staff-title" : ""}`} style={{ borderColor: me.rank_color, color: me.rank_color }}>{t(me.rank_title)}</span>
                  <span className="muted small">{me.next_rank ? t("{xp} XP · {n} to {rank}", { xp: me.xp, n: me.next_rank.xp_to_go, rank: t(me.next_rank.title) }) : t("{xp} XP", { xp: me.xp })}</span>
                </div>
                <div className="ribbon-specs">
                  {me.specializations.length
                    ? me.specializations.map((s) => <span key={s.key} className={s.primary ? "primary" : ""}>{t(s.title)}</span>)
                    : <span>{t("Undecided")}</span>}
                </div>
              </div>
            </Link>
            {next?.main ? (
              <Link href={`/quests/${next.main.id}`} className="ribbon-next">
                <div className="eyebrow">{t("Next dungeon")}</div>
                <div className="ribbon-next-title"><TierBadge tier={next.main.tier} /><b>{next.main.id} · {next.main.title}</b></div>
                <div className="small muted">{[t("{xp} XP", { xp: next.main.xp }), next.main.time_min ? t("~{n} min", { n: next.main.time_min }) : null, next.main.has_quiz ? t("boss with {n} questions", { n: next.main.quiz_len }) : null, next.reason].filter(Boolean).join(" · ")}</div>
              </Link>
            ) : (
              <div className="ribbon-next"><div className="eyebrow">{t("Next dungeon")}</div><div className="small muted">{next?.reason ?? t("Nothing is required right now. Pick any quest you like.")}</div></div>
            )}
            <div className="ribbon-actions">
              {next?.main && <Link className="btn primary" href={`/quests/${next.main.id}`}>{t("Enter {id}", { id: next.main.id })}</Link>}
              <Link className="btn" href="/quests">{t("Quest board")}</Link>
            </div>
          </div>
        ) : (
          <div className="ribbon guest">
            <div>
              <h1>{t("Our mission statement")}</h1>
              <p className="lead">{t(MISSION)}</p>
            </div>
            <div className="ribbon-actions">
              <a className="btn primary" href="/api/auth/discord">{t("Enter with Discord")}</a>
              <Link className="btn" href="/quests">{t("Browse the quests")}</Link>
            </div>
          </div>
        )}
    </>
  );

  return (
    <>
      {banner ? <HeroBanner icons={siteArtGroup(manifest, "banner-controls")} animated={banner.animated} still={banner.still} living={banner.living}>{hero}</HeroBanner> : <section className="hero">{hero}</section>}

      {me && stats ? (
        <>
          <section>
            <div className="section-h"><h2>{t("Your statistics")}</h2><Link href="/me" className="small">{t("Player card →")}</Link></div>
            <div className="card" style={{ marginBottom: 12 }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="eyebrow">{me.next_rank ? t("{n} XP to {rank}", { n: me.next_rank.xp_to_go, rank: t(me.next_rank.title) }) : t("Top of the ladder")}</span>
                {me.tier_progress && <span className="small muted">{me.tier_progress.emoji} {[t("{tier} quests {done}/{need}", { tier: t(me.tier_progress.name), done: me.tier_progress.done, need: me.tier_progress.need }), me.next_rank && me.next_rank.required_left > 0 ? t("{n} required left", { n: me.next_rank.required_left }) : null].filter(Boolean).join(" · ")}</span>}
              </div>
              <div className="bar" style={{ marginTop: 8 }}><span style={{ width: `${pct}%`, background: me.rank_color }} /></div>
            </div>
            <div className="stats-grid">
              <Stat icon="quests" n={me.done_count} label={t("quests done")} />
              <Stat icon="streak" n={me.streak_days} label={t("day streak")} />
              <Stat icon="xp" n={stats.me.xp_week} label={t("XP this week")} />
              <Stat icon="fights" n={`${stats.me.fights_won}/${stats.me.fights}`} label={t("bosses beaten")} />
              <Stat icon="flawless" n={stats.me.bosses_first_try} label={t("beaten first try")} />
              <Stat icon="critical" n={stats.me.crit_xp} label={t("XP from crits")} />
              <Stat icon="reading" n={stats.me.reads} label={t("guides opened")} />
              <Stat icon={stats.me.turnins_pending ? "pending" : "accepted"} n={`${stats.me.turnins_passed}/${stats.me.turnins}`} label={stats.me.turnins_pending ? t("work accepted · {n} waiting", { n: stats.me.turnins_pending }) : t("work accepted")} />
            </div>
          </section>
          <section>
            <div className="section-h"><h2>{t("Player statistics")}</h2><span className="muted small">{t("everyone, this week")}</span><Link href="/leaderboard" className="small" style={{ marginLeft: "auto" }}>{t("Leaderboard →")}</Link></div>
            <div className="stats-grid">
              <Stat icon="members" n={stats.guild.members} label={t("players")} />
              <Stat icon="quests" n={stats.guild.quests_done_week} label={t("dungeons cleared this week")} />
              <Stat icon="fights" n={stats.guild.fights_week} label={t("boss fights fought")} />
              <Stat icon="xp" n={stats.guild.xp_week} label={t("XP earned by players")} />
              <Stat icon="all-time" n={stats.guild.quests_done} label={t("dungeons cleared all time")} />
              <Stat icon="masters" n={stats.guild.masters} label={t("players at Master or above")} />
            </div>
          </section>
        </>
      ) : (
        <>
          <HowItWorks specs={specs} />
          {guild && (
            <section>
              <div className="section-h"><h2>{t("Player statistics")}</h2><span className="muted small">{t("everyone, this week")}</span></div>
              <div className="stats-grid">
                <Stat n={guild.members} label={t("players")} />
                <Stat n={guild.quests_done_week} label={t("dungeons cleared this week")} />
                <Stat n={guild.fights_week} label={t("boss fights fought")} />
                <Stat n={guild.xp_week} label={t("XP earned by players")} />
                <Stat n={guild.quests_done} label={t("dungeons cleared all time")} />
                <Stat n={guild.masters} label={t("players at Master or above")} />
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}

function Stat({ n, label, icon }: { n: number | string; label: string; icon?: string }) {
  return <div className="card stat">{icon && <Ico group="statistics" id={icon} size={16} className="stat-ico" />}<b>{n}</b><span className="muted small">{label}</span></div>;
}
