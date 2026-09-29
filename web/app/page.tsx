import Link from "next/link";
import QuestCard from "@/components/QuestCard";
import { api, type Majors, type Me, type Next } from "@/lib/api";

export default async function Home() {
  const [me, majors] = await Promise.all([api<Me>("/me"), api<Majors>("/catalog/majors")]);
  if (!me) return <Guest majors={majors} />;
  const next = await api<Next>("/me/next");
  const pct = me.xp_next ? Math.min(100, Math.round(((me.xp - me.xp_floor) / (me.xp_next - me.xp_floor)) * 100)) : 100;
  return (
    <>
      <div className="eyebrow">Welcome back</div>
      <h1>{me.name} · <span style={{ color: me.rank_color }}>{me.rank_title}</span> · {me.major_title}</h1>
      <div className="two">
        <div>
          <h2 style={{ marginTop: 8 }}>Continue questing</h2>
          {next?.main ? (
            <>
              <p className="muted small">Why this one: {next.reason}</p>
              <QuestCard q={next.main} />
            </>
          ) : (
            <div className="card"><b>{next?.reason ?? "Nothing required right now."}</b><p className="muted">Pick any quest you like from the browser.</p></div>
          )}
          {next && next.electives.length > 0 && (
            <>
              <h3 style={{ marginTop: 20 }}>Or pick an elective</h3>
              <div className="grid">{next.electives.map((q) => <QuestCard key={q.id} q={q} />)}{next.adjacent && <QuestCard q={next.adjacent} />}</div>
            </>
          )}
        </div>
        <div className="card">
          <div className="eyebrow">Progress</div>
          <div className="stat" style={{ margin: "8px 0" }}>
            <b>{me.xp} XP</b>
            {me.next_rank && <span className="muted small">{me.next_rank.xp_to_go} XP to {me.next_rank.title}</span>}
          </div>
          <div className="bar"><span style={{ width: `${pct}%`, background: me.rank_color }} /></div>
          <div className="row" style={{ marginTop: 14, gap: 24 }}>
            <div className="stat"><b>{me.done_count}</b><span className="muted small">quests done</span></div>
            <div className="stat"><b>{me.streak_days}</b><span className="muted small">day streak</span></div>
            {me.tier_progress && <div className="stat"><b>{me.tier_progress.done}/{me.tier_progress.need}</b><span className="muted small">{me.tier_progress.emoji} {me.tier_progress.name} quests</span></div>}
          </div>
          {me.next_rank && (
            <p className="small muted" style={{ marginTop: 12 }}>
              Next: <b>{me.next_rank.title}</b>. {me.next_rank.required_left > 0 ? `${me.next_rank.required_left} required quests left.` : "Core path done."}
              {me.next_rank.tier_left > 0 && ` ${me.next_rank.tier_left} more ${me.tier_progress?.name} quests, your choice.`}
            </p>
          )}
          <div className="row" style={{ marginTop: 10 }}>
            <Link className="btn" href="/path">My path</Link>
            <Link className="btn" href="/me">Profile</Link>
          </div>
        </div>
      </div>
    </>
  );
}

function Guest({ majors }: { majors: Majors | null }) {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Learn Unreal Engine 5 by doing quests.</h1>
      <p style={{ fontSize: 17 }}>Read the guide, build it in Unreal, pass a short quiz, show your work. Ranks come only from quests.</p>
      <div className="row" style={{ margin: "14px 0 24px" }}>
        <a className="btn primary" href="/api/auth/discord">Log in with Discord</a>
        <Link className="btn" href="/quests">Browse the quests first</Link>
      </div>
      <h2>Seven majors</h2>
      <div className="grid">
        {majors && Object.values(majors.majors).filter((m) => m.key !== "undecided").map((m) => (
          <Link key={m.key} href={`/quests?major=${m.key}`} className="card" style={{ color: "inherit" }}>
            <b>{m.title}</b>
            <div className="muted small">{m.prefix} quests · capstones at every rank</div>
          </Link>
        ))}
      </div>
      <h2>Ranks</h2>
      <div className="card">
        {majors && majors.ranks.map((r) => (
          <div key={r.n} className="row" style={{ padding: "6px 0", borderBottom: "1px solid var(--line)" }}>
            <b style={{ width: 110, color: r.color ?? "inherit" }}>{r.title}</b>
            <span className="muted small">{r.xp} XP{r.quests_to_leave ? ` · ${r.quests_to_leave} ${majors.tiers[r.tier]?.name} quests to leave` : ""}</span>
          </div>
        ))}
        <p className="muted small" style={{ marginTop: 10 }}>You need to be a member of the Unrealcraft Discord server to log in.</p>
      </div>
    </>
  );
}
