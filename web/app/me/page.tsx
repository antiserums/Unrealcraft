import { redirect } from "next/navigation";
import CharacterSheet, { type Char } from "@/components/CharacterSheet";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Profile" };

export default async function Profile() {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/me");
  const ch = await api<Char>("/me/character");
  const pct = me.xp_next ? Math.min(100, Math.round(((me.xp - me.xp_floor) / (me.xp_next - me.xp_floor)) * 100)) : 100;
  return (
    <>
      <div className="row" style={{ marginBottom: 10 }}>
        {me.avatar && <img src={me.avatar} alt="" style={{ width: 64, height: 64, borderRadius: "50%" }} />}
        <div>
          <h1 style={{ margin: 0 }}>{me.name}</h1>
          <div className="row small">
            <span className="pill" style={{ borderColor: me.rank_color, color: me.rank_color, fontWeight: 600 }}>{me.rank_title}</span>
            <span className="muted">{me.major_title}{me.minor ? ` · minor ${me.minor}` : ""}</span>
            {me.member_since && <span className="muted">· member since {me.member_since.slice(0, 10)}</span>}
          </div>
        </div>
      </div>
      {ch && <div style={{ marginBottom: 20 }}><CharacterSheet initial={ch} fallbackColor={me.rank_color} /></div>}
      <h2 style={{ marginTop: 0 }}>Progress</h2>
      {me.known === false && <div className="note small" style={{ marginBottom: 12 }}>The Quartermaster has not seen you yet. Press <b>Start Questing</b> in #welcome on Discord to begin Orientation.</div>}
      <div className="two">
        <div className="card">
          <div className="eyebrow">XP</div>
          <div className="stat" style={{ margin: "6px 0" }}><b>{me.xp}{me.xp_next ? ` / ${me.xp_next}` : ""}</b></div>
          <div className="bar"><span style={{ width: `${pct}%`, background: me.rank_color }} /></div>
          <div className="row" style={{ marginTop: 14, gap: 24 }}>
            <div className="stat"><b>{me.done_count}</b><span className="muted small">quests done</span></div>
            <div className="stat"><b>{me.streak_days}</b><span className="muted small">day streak</span></div>
            <div className="stat"><b>{me.ue_version ?? "—"}</b><span className="muted small">engine version</span></div>
          </div>
          {me.next_rank && (
            <div style={{ marginTop: 14 }}>
              <div className="eyebrow">Next rank: {me.next_rank.title}</div>
              <ul className="plain small">
                <li>{me.next_rank.xp_to_go} XP to go</li>
                <li>{me.next_rank.required_left > 0 ? `${me.next_rank.required_left} required quests left` : "Core path done"}</li>
                {me.tier_progress && <li>{me.tier_progress.emoji} {me.tier_progress.name} quests: {me.tier_progress.done}/{me.tier_progress.need}</li>}
                {me.next_rank.human_review && <li>Staff approval needed for this rank</li>}
                {me.next_rank.opens && <li className="muted">Opens: {me.next_rank.opens}</li>}
              </ul>
            </div>
          )}
        </div>
        <div>
          <div className="card">
            <div className="eyebrow">Medals</div>
            {me.medals.length ? (
              <ul className="plain small">{me.medals.map((m) => <li key={m.medal_key}>{m.medal_key} <span className="muted">· {m.earned_at.slice(0, 10)}</span></li>)}</ul>
            ) : <p className="muted small" style={{ margin: "6px 0 0" }}>None yet.</p>}
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="eyebrow">Recent XP</div>
            {me.recent_xp?.length ? (
              <ul className="plain small">{me.recent_xp.map((x, i) => <li key={i}><b>+{x.amount}</b> {x.reason} <span className="muted">· {x.created_at.slice(0, 10)}</span></li>)}</ul>
            ) : <p className="muted small" style={{ margin: "6px 0 0" }}>Nothing yet. Finish a quest.</p>}
          </div>
        </div>
      </div>
    </>
  );
}
