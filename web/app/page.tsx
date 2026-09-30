import Link from "next/link";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type Next } from "@/lib/api";
import { bannerImage, loadManifest } from "@/lib/art";

type MemberStats = { fights: number; fights_won: number; bosses_first_try: number; crit_xp: number; xp_week: number; reads: number; turnins: number; turnins_passed: number; turnins_pending: number };
type GuildStats = { members: number; quests_done: number; quests_done_week: number; fights_week: number; xp_week: number; masters: number };

export default async function Home() {
  const [me, manifest] = await Promise.all([api<Me>("/me"), loadManifest()]);
  const [next, stats, guild] = await Promise.all([
    me ? api<Next>("/me/next") : null,
    me ? api<{ me: MemberStats; guild: GuildStats }>("/me/stats") : null,
    me ? null : api<GuildStats>("/catalog/stats"),
  ]);
  const banner = bannerImage(manifest);
  const g = stats?.guild ?? guild;
  const pct = me?.xp_next ? Math.min(100, Math.round(((me.xp - me.xp_floor) / (me.xp_next - me.xp_floor)) * 100)) : 100;

  return (
    <>
      <section className={`hero ${banner ? "px banner-hero" : ""}`} style={banner ? { backgroundImage: `url("${banner}")` } : undefined}>
        {me ? (
          <div className="ribbon">
            <div className="ribbon-who">
              {me.avatar && <img className="avatar big" src={me.avatar} alt="" />}
              <div>
                <div className="eyebrow">Welcome back</div>
                <h1>{me.name}</h1>
                <div className="small"><span style={{ color: me.rank_color, fontWeight: 600 }}>{me.rank_title}</span><span className="muted"> · {me.major_title} · {me.xp} XP</span></div>
              </div>
            </div>
            {next?.main ? (
              <Link href={`/quests/${next.main.id}`} className="ribbon-next">
                <div className="eyebrow">Next room</div>
                <div className="ribbon-next-title"><TierBadge tier={next.main.tier} /><b>{next.main.id} · {next.main.title}</b></div>
                <div className="small muted">{next.main.xp} XP{next.main.time_min ? ` · ~${next.main.time_min} min` : ""}{next.main.has_quiz ? ` · boss with ${next.main.quiz_len} questions` : ""} · {next.reason}</div>
              </Link>
            ) : (
              <div className="ribbon-next"><div className="eyebrow">Next room</div><div className="small muted">{next?.reason ?? "Nothing is required right now. Pick any quest you like."}</div></div>
            )}
            <div className="ribbon-actions">
              {next?.main && <Link className="btn primary" href={`/quests/${next.main.id}`}>Enter {next.main.id}</Link>}
              <Link className="btn" href="/quests">Quest board</Link>
            </div>
          </div>
        ) : (
          <div className="ribbon guest">
            <div>
              <div className="eyebrow">A learning guild for Unreal Engine 5</div>
              <h1>Learn Unreal by clearing dungeons.</h1>
              <p className="lead">Every quest is a room: read, build, fight the boss, open the chest. Ranks come only from quests.</p>
            </div>
            <div className="ribbon-actions">
              <a className="btn primary" href="/api/auth/discord">Enter with Discord</a>
              <Link className="btn" href="/how-it-works">How it works</Link>
            </div>
          </div>
        )}
      </section>

      {me && stats && (
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
      )}

      {g && (
        <section>
          <div className="section-h"><h2>Player statistics</h2><span className="muted small">everyone, this week</span><Link href="/leaderboard" className="small" style={{ marginLeft: "auto" }}>Leaderboard →</Link></div>
          <div className="stats-grid">
            <Stat n={g.members} label="players" />
            <Stat n={g.quests_done_week} label="rooms cleared this week" />
            <Stat n={g.fights_week} label="boss fights fought" />
            <Stat n={g.xp_week} label="XP earned by players" />
            <Stat n={g.quests_done} label="rooms cleared all time" />
            <Stat n={g.masters} label="players at Master or above" />
          </div>
          {!me && <p className="small muted" style={{ marginTop: 12 }}>New here? Read <Link href="/how-it-works">how it works</Link>, or browse the <Link href="/quests">quest board</Link> before logging in.</p>}
        </section>
      )}
    </>
  );
}

function Stat({ n, label }: { n: number | string; label: string }) {
  return <div className="card stat"><b>{n}</b><span className="muted small">{label}</span></div>;
}
