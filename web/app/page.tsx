import Link from "next/link";
import HowItWorks from "@/components/HowItWorks";
import Ico from "@/components/Ico";
import StatsBoard, { type Tile } from "@/components/StatsBoard";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type Next, type Specializations } from "@/lib/api";
import HeroBanner from "@/components/HeroBanner";
import { AvatarDeco } from "@/components/DecoAnim";
import { arenaBackground, bannerSet, creatureSheet, decorationImage, loadManifest, rankCrest, siteArtGroup } from "@/lib/art";
import type { BossInfo } from "@/components/BossCard";
import { Boss } from "@/components/Figure";
import { Px } from "@/components/SiteArt";
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
  const boss = next?.main?.has_quiz ? await api<BossInfo>(`/catalog/quests/${next.main.id}/boss`) : null;   // the ribbon shows who waits inside
  const banner = bannerSet(manifest);
  const pct = me?.xp_next ? Math.min(100, Math.round(((me.xp - me.xp_floor) / (me.xp_next - me.xp_floor)) * 100)) : 100;
  const arena = next?.main ? arenaBackground(manifest, next.main.id) : null;
  const bossSheet = boss ? creatureSheet(manifest, boss.creature) : null;
  const crest = me ? rankCrest(manifest, me.rank) : null;
  const nextCrest = me?.next_rank ? rankCrest(manifest, me.next_rank.n) : null;
  // the tiles' corner icons (logged-in only: the guest board has none) and the guild's tiles, shared by both boards
  const ico = (id: string) => <Ico group="statistics" id={id} size={16} className="stat-ico" />;
  const guildTiles = (g: GuildStats, ic: (id: string) => React.ReactNode): Tile[] => [
    { key: "members", icon: ic("members"), n: g.members, label: t("players"), mode: "total" },
    { key: "quests", icon: ic("quests"), n: g.quests_done_week, label: t("dungeons cleared this week") },
    { key: "fights", icon: ic("fights"), n: g.fights_week, label: t("boss fights fought") },
    { key: "xp", icon: ic("xp"), n: g.xp_week, label: t("XP earned by players") },
    { key: "quests", id: "quests_all", icon: ic("all-time"), n: g.quests_done, label: t("dungeons cleared all time"), mode: "total" },
    { key: "masters", icon: ic("masters"), n: g.masters, label: t("players at Master or above"), mode: "total" },
  ];
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
                <div className="ribbon-name">
                  <h1>{me.name}</h1>
                  <span className={`pill ${me.staff ? "staff-title" : ""}`} data-role={me.staff ?? undefined} style={{ borderColor: me.rank_color, color: me.rank_color }}>{t(me.rank_title)}</span>
                </div>
                {me.title && <div className="ribbon-title">{t(me.title)}</div>}
                {/* the road to the next rank: this crest, the bar, the next crest */}
                <div className="ribbon-xp">
                  <div className="ribbon-xp-row">
                    {crest ? <Px src={crest} className="ribbon-crest" /> : null}
                    <div className="bar" title={`${pct}%`}><span style={{ width: `${pct}%` }} /></div>
                    {nextCrest ? <Px src={nextCrest} className="ribbon-crest next" /> : null}
                  </div>
                  <div className="ribbon-xp-line small">
                    <b>{t("{xp} XP", { xp: me.xp })}</b>
                    {me.next_rank && <span className="muted"> · {t("{n} to {rank}", { n: me.next_rank.xp_to_go, rank: t(me.next_rank.title) })}</span>}
                    {me.tier_progress && <span className="muted"> · {t("{tier} quests {done}/{need}", { tier: t(me.tier_progress.name), done: me.tier_progress.done, need: me.tier_progress.need })}</span>}
                  </div>
                </div>
                {me.specializations.length > 0 && (
                  <div className="ribbon-specs">
                    {me.specializations.map((s) => <span key={s.key} className={`pill spec-chip ${s.primary ? "primary" : ""}`}>{t(s.title)}</span>)}
                  </div>
                )}
              </div>
            </Link>
            {next?.main ? (
              <Link href={`/quests/${next.main.id}`} className="ribbon-next" title={t("Open this dungeon")}>
                {/* a window into the dungeon: its arena, with the boss waiting in it */}
                <div className="ribbon-boss" style={arena ? ({ "--arena": `url("${arena.small}")` } as React.CSSProperties) : undefined}>
                  {boss && <Boss look={boss.look} sheet={bossSheet} color={boss.color} size={70} scale={bossSheet && bossSheet.frame <= 64 ? 2 : 1} />}
                </div>
                <div className="ribbon-next-text">
                  <div className="eyebrow">{t("Next dungeon")}</div>
                  <div className="ribbon-next-title"><TierBadge tier={next.main.tier} /><b>{next.main.id} · {next.main.title}</b></div>
                  {boss && <div className="ribbon-boss-name" style={{ color: boss.color }}>{boss.kind === "boss" ? t("Boss: {name}", { name: boss.name }) : t("Guardian: {name}", { name: boss.name })}</div>}
                  <div className="small muted">{[t("{xp} XP", { xp: next.main.xp }), next.main.time_min ? t("~{n} min", { n: next.main.time_min }) : null, boss ? t("{n} questions", { n: boss.questions }) : next.main.has_quiz ? t("{n} questions", { n: next.main.quiz_len }) : t("no boss"), boss ? t("{n} hits to win", { n: boss.hits_to_win }) : null].filter(Boolean).join(" · ")}</div>
                </div>
                <span className="ribbon-go" aria-hidden="true">→</span>
              </Link>
            ) : (
              <Link href="/quests" className="ribbon-next" title={t("Quest board")}>
                <div className="ribbon-boss" />
                <div className="ribbon-next-text">
                  <div className="eyebrow">{t("Next dungeon")}</div>
                  <b>{t("Nothing is required right now")}</b>
                  <div className="small muted">{next?.reason ?? t("Pick any quest you like from the board.")}</div>
                </div>
                <span className="ribbon-go" aria-hidden="true">→</span>
              </Link>
            )}
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
            <StatsBoard scope="me" endpoint="/me/stats/series" tiles={[
              { key: "quests", icon: ico("quests"), n: me.done_count, label: t("quests done"), mode: "total" },
              { key: "streak", icon: ico("streak"), n: me.streak_days, label: t("day streak") },
              { key: "xp", icon: ico("xp"), n: stats.me.xp_week, label: t("XP this week") },
              { key: "fights_won", icon: ico("fights"), n: `${stats.me.fights_won}/${stats.me.fights}`, label: t("bosses beaten"), mode: "total" },
              { key: "first_try", icon: ico("flawless"), n: stats.me.bosses_first_try, label: t("beaten first try"), mode: "total" },
              { key: "crit_xp", icon: ico("critical"), n: stats.me.crit_xp, label: t("XP from crits") },
              { key: "reads", icon: ico("reading"), n: stats.me.reads, label: t("guides opened"), mode: "total" },
              { key: "turnins_passed", icon: ico(stats.me.turnins_pending ? "pending" : "accepted"), n: `${stats.me.turnins_passed}/${stats.me.turnins}`, label: stats.me.turnins_pending ? t("work accepted · {n} waiting", { n: stats.me.turnins_pending }) : t("work accepted"), mode: "total" },
            ]} />
          </section>
          <section>
            <div className="section-h"><h2>{t("Player statistics")}</h2><span className="muted small">{t("everyone, this week")}</span><Link href="/leaderboard" className="small" style={{ marginLeft: "auto" }}>{t("Leaderboard →")}</Link></div>
            <StatsBoard scope="guild" endpoint="/me/stats/series" tiles={guildTiles(stats.guild, ico)} />
          </section>
        </>
      ) : (
        <>
          <HowItWorks specs={specs} />
          {guild && (
            <section>
              <div className="section-h"><h2>{t("Player statistics")}</h2><span className="muted small">{t("everyone, this week")}</span></div>
              <StatsBoard scope="guild" endpoint="/catalog/stats/series" tiles={guildTiles(guild, () => null)} />
            </section>
          )}
        </>
      )}
    </>
  );
}
