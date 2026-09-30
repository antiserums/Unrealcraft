import Link from "next/link";
import HowItWorks from "@/components/HowItWorks";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type Next, type Specializations } from "@/lib/api";
import HeroBanner from "@/components/HeroBanner";
import { bannerSet, loadManifest } from "@/lib/art";

type MemberStats = { fights: number; fights_won: number; bosses_first_try: number; crit_xp: number; xp_week: number; reads: number; turnins: number; turnins_passed: number; turnins_pending: number };
type GuildStats = { members: number; quests_done: number; quests_done_week: number; fights_week: number; xp_week: number; masters: number };

export default async function Home() {
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
            <div className="ribbon-who">
              {me.avatar && <img className="avatar big" src={me.avatar} alt="" />}
              <div>
                <div className="eyebrow">Welcome back</div>
                <h1>{me.name}</h1>
                <div className="small"><span className={me.staff ? "staff-title" : ""} style={{ color: me.rank_color, fontWeight: 600 }}>{me.rank_title}</span><span className="muted"> · {me.specializations.length ? me.specializations.map((s) => s.title).join(" · ") : "Undecided"} · {me.xp} XP</span></div>
              </div>
            </div>
            {next?.main ? (
              <Link href={`/quests/${next.main.id}`} className="ribbon-next">
                <div className="eyebrow">Next dungeon</div>
                <div className="ribbon-next-title"><TierBadge tier={next.main.tier} /><b>{next.main.id} · {next.main.title}</b></div>
                <div className="small muted">{next.main.xp} XP{next.main.time_min ? ` · ~${next.main.time_min} min` : ""}{next.main.has_quiz ? ` · boss with ${next.main.quiz_len} questions` : ""} · {next.reason}</div>
              </Link>
            ) : (
              <div className="ribbon-next"><div className="eyebrow">Next dungeon</div><div className="small muted">{next?.reason ?? "Nothing is required right now. Pick any quest you like."}</div></div>
            )}
            <div className="ribbon-actions">
              {next?.main && <Link className="btn primary" href={`/quests/${next.main.id}`}>Enter {next.main.id}</Link>}
              <Link className="btn" href="/quests">Quest board</Link>
            </div>
          </div>
        ) : (
          <div className="ribbon guest">
            <div>
              <h1>Our mission statement</h1>
              <p className="lead">Unrealcraft is an RPG learning experience for Unreal Engine so you can learn the way you would play it. Read the guides, build it in Unreal, beat the bosses, claim your rewards. Whether you are here to learn the basics or to prove yourself against the hardest of challenges, Unrealcraft is a home for you.</p>
            </div>
            <div className="ribbon-actions">
              <a className="btn primary" href="/api/auth/discord">Enter with Discord</a>
              <Link className="btn" href="/quests">Browse the quests</Link>
            </div>
          </div>
        )}
    </>
  );

  return (
    <>
      {banner ? <HeroBanner animated={banner.animated} still={banner.still} living={banner.living}>{hero}</HeroBanner> : <section className="hero">{hero}</section>}

      {me && stats ? (
        <>
          <section>
            <div className="section-h"><h2>Your statistics</h2><Link href="/me" className="small">Player card →</Link></div>
            <div className="card" style={{ marginBottom: 12 }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="eyebrow">{me.next_rank ? `${me.next_rank.xp_to_go} XP to ${me.next_rank.title}` : "Top of the ladder"}</span>
                {me.tier_progress && <span className="small muted">{me.tier_progress.emoji} {me.tier_progress.name} quests {me.tier_progress.done}/{me.tier_progress.need}{me.next_rank && me.next_rank.required_left > 0 ? ` · ${me.next_rank.required_left} required left` : ""}</span>}
              </div>
              <div className="bar" style={{ marginTop: 8 }}><span style={{ width: `${pct}%`, background: me.rank_color }} /></div>
            </div>
            <div className="stats-grid">
              <Stat n={me.done_count} label="quests done" />
              <Stat n={me.streak_days} label="day streak" />
              <Stat n={stats.me.xp_week} label="XP this week" />
              <Stat n={`${stats.me.fights_won}/${stats.me.fights}`} label="bosses beaten" />
              <Stat n={stats.me.bosses_first_try} label="beaten first try" />
              <Stat n={stats.me.crit_xp} label="XP from crits" />
              <Stat n={stats.me.reads} label="guides opened" />
              <Stat n={`${stats.me.turnins_passed}/${stats.me.turnins}`} label={`work accepted${stats.me.turnins_pending ? ` · ${stats.me.turnins_pending} waiting` : ""}`} />
            </div>
          </section>
          <section>
            <div className="section-h"><h2>Player statistics</h2><span className="muted small">everyone, this week</span><Link href="/leaderboard" className="small" style={{ marginLeft: "auto" }}>Leaderboard →</Link></div>
            <div className="stats-grid">
              <Stat n={stats.guild.members} label="players" />
              <Stat n={stats.guild.quests_done_week} label="dungeons cleared this week" />
              <Stat n={stats.guild.fights_week} label="boss fights fought" />
              <Stat n={stats.guild.xp_week} label="XP earned by players" />
              <Stat n={stats.guild.quests_done} label="dungeons cleared all time" />
              <Stat n={stats.guild.masters} label="players at Master or above" />
            </div>
          </section>
        </>
      ) : (
        <>
          <HowItWorks specs={specs} />
          {guild && (
            <section>
              <div className="section-h"><h2>Player statistics</h2><span className="muted small">everyone, this week</span></div>
              <div className="stats-grid">
                <Stat n={guild.members} label="players" />
                <Stat n={guild.quests_done_week} label="dungeons cleared this week" />
                <Stat n={guild.fights_week} label="boss fights fought" />
                <Stat n={guild.xp_week} label="XP earned by players" />
                <Stat n={guild.quests_done} label="dungeons cleared all time" />
                <Stat n={guild.masters} label="players at Master or above" />
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}

function Stat({ n, label }: { n: number | string; label: string }) {
  return <div className="card stat"><b>{n}</b><span className="muted small">{label}</span></div>;
}
