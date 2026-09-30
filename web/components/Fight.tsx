"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Boss, Character } from "./Figure";

type Ev = { kind: string; text: string; damage?: number; bonus_xp?: number; explain?: string; correct?: number; debuff?: string };
type Q = { index: number; total: number; q: string; choices: string[]; hint: string | null; debuff: string | null };
type Fight = {
  fight_id: number; quest: { id: string; title: string; xp: number; verify_type: string };
  boss: { name: string; short: string; look: string; color: string; hits_to_win: number; questions: number; wounds_allowed: number; verb: string; intro: string; tier: string };
  you: { vitality: number; wounds: number; wounds_allowed: number; steady_available: boolean; craft: number; focus: number; crit_pct: number; outfit: string };
  hits: number; hits_to_win: number; turn: number; total: number; first_try: boolean; log: Ev[]; question: Q | null;
  result: string | null; events?: Ev[];
  outcome?: { passed: boolean; score: number; total: number; first_try_bonus?: number; crit_xp?: number; completed?: boolean; quest_xp?: number; loot?: { name: string; tier: string; flavour?: string; color: string; id: string } | null; tested_out?: boolean; next?: string } | null;
};

const DEBUFF: Record<string, string> = { dazed: "Dazed: the choices are shuffled.", weakened: "Weakened: your next hit does half damage.", blinded: "Blinded: no hint this turn." };

export default function FightScreen({ questId, outfit, color, layers, bossImage }: { questId: string; outfit: string; color: string; layers?: string[] | null; bossImage?: string | null }) {
  const [f, setF] = useState<Fight | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [bossPose, setBossPose] = useState<"idle" | "attack" | "hit" | "dead">("idle");
  const [youPose, setYouPose] = useState<"idle" | "strike" | "hurt" | "down" | "win">("idle");
  const [float, setFloat] = useState<{ text: string; side: "boss" | "you"; kind: string } | null>(null);
  const [last, setLast] = useState<Ev[]>([]);
  const asked = useRef<number>(Date.now());
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;            // React dev mode runs effects twice; one fight is enough
    started.current = true;
    (async () => {
      const r = await fetch(`/api/me/quests/${questId}/fight`, { method: "POST" });
      const j = await r.json();
      if (!r.ok) { setErr(j.detail ?? "Could not start the fight."); return; }
      setF(j); asked.current = Date.now();
    })();
  }, [questId]);

  async function answer(pos: number) {
    if (!f || busy) return;
    setBusy(true);
    setBossPose("attack");
    const seconds = (Date.now() - asked.current) / 1000;
    const r = await fetch(`/api/fights/${f.fight_id}/turn`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ answer: pos, seconds }) });
    const j: Fight = await r.json();
    if (!r.ok) { setErr((j as unknown as { detail: string }).detail); setBusy(false); return; }
    const evs = j.events ?? [];
    const main = evs.find((e) => ["hit", "crit", "wound", "steady"].includes(e.kind));
    if (main && (main.kind === "hit" || main.kind === "crit")) {
      setYouPose("strike"); setBossPose("hit");
      setFloat({ text: `-${main.damage}${main.kind === "crit" ? " CRIT" : ""}`, side: "boss", kind: main.kind });
    } else if (main) {
      setYouPose("hurt"); setBossPose("attack");
      setFloat({ text: main.kind === "steady" ? "-½" : "-1", side: "you", kind: main.kind });
    }
    setLast(evs);
    setTimeout(() => {
      setF(j); asked.current = Date.now(); setBusy(false); setFloat(null);
      if (j.result === "win") { setBossPose("dead"); setYouPose("win"); }
      else if (j.result === "lose") { setYouPose("down"); setBossPose("idle"); }
      else { setYouPose("idle"); setBossPose("idle"); }
    }, 650);
  }

  if (err) return <div className="card"><b>{err}</b><p style={{ margin: "8px 0 0" }}><Link href={`/quests/${questId}`}>← Back to the room</Link></p></div>;
  if (!f) return <div className="card muted">Entering the boss room…</div>;

  const bossHp = Math.max(0, f.hits_to_win - f.hits) / f.hits_to_win;
  const youHp = Math.max(0, (f.you.wounds_allowed + 1 - f.you.wounds)) / (f.you.wounds_allowed + 1);
  const q = f.question;

  return (
    <div className="fight">
      <div className="arena">
        <div className="side you">
          <div className="hpbox">
            <div className="eyebrow">You · Vitality {f.you.vitality}</div>
            <div className="bar big"><span style={{ width: `${youHp * 100}%`, background: "#4FA36C" }} /></div>
            <div className="small muted">{f.you.wounds} wound{f.you.wounds === 1 ? "" : "s"} · {Math.max(0, f.you.wounds_allowed - Math.floor(f.you.wounds))} more before you fall
              {f.you.steady_available && <> · steady ready</>}
            </div>
          </div>
          <div className="stage">{float?.side === "you" && <span className={`float ${float.kind}`}>{float.text}</span>}<Character outfit={outfit} layers={layers} color={color} pose={youPose} size={150} /></div>
        </div>
        <div className="side boss">
          <div className="hpbox">
            <div className="eyebrow" style={{ color: f.boss.color }}>{f.boss.name}</div>
            <div className="bar big"><span style={{ width: `${bossHp * 100}%`, background: f.boss.color }} /></div>
            <div className="small muted">{Math.min(f.hits, f.hits_to_win)}/{f.hits_to_win} hits{f.hits > f.hits_to_win ? " · victory lap" : ""} · {f.boss.questions} questions in the room</div>
          </div>
          <div className="stage">{float?.side === "boss" && <span className={`float ${float.kind}`}>{float.text}</span>}<Boss look={f.boss.look} image={bossImage} color={f.boss.color} pose={bossPose} size={170} /></div>
        </div>
      </div>

      {last.length > 0 && (
        <div className="log card">
          {last.map((e, i) => (
            <div key={i} className={`ev ${e.kind}`}>
              <b>{e.text}</b>
              {e.kind === "crit" && e.bonus_xp ? <span className="pill" style={{ marginLeft: 8 }}>+{e.bonus_xp} XP</span> : null}
              {e.explain && <div className="small" style={{ marginTop: 4 }}>{["hit", "crit"].includes(e.kind) ? "You saw through it: " : "It got you because: "}{e.explain}</div>}
            </div>
          ))}
        </div>
      )}

      {q && !f.result && (
        <div className="card question">
          <div className="eyebrow">Turn {f.turn} of {f.total}{q.debuff && <span className="pill" style={{ marginLeft: 8, color: "var(--bad)", borderColor: "var(--bad)" }}>{DEBUFF[q.debuff]}</span>}</div>
          {q.hint && <p className="muted small" style={{ margin: "6px 0 0" }}>{q.hint}</p>}
          <h2 style={{ marginTop: 8 }}>{q.q}</h2>
          <div className="choices">
            {q.choices.map((c, i) => (
              <button key={i} onClick={() => answer(i)} disabled={busy} className="choice">
                <span className="letter">{"ABCD"[i]}</span> {c}
              </button>
            ))}
          </div>
          <div className="row small muted" style={{ marginTop: 8 }}>
            <span>Answer fast for a better crit chance ({f.you.crit_pct}% base).</span>
            <span className="spacer" />
            <Link href={`/quests/${questId}`} className="muted">Retreat (nothing is recorded)</Link>
          </div>
        </div>
      )}

      {f.result && (
        <div className="card result">
          {f.result === "win" ? (
            <>
              <h2 style={{ marginTop: 0 }}>🏆 {f.boss.short} is beaten · {f.outcome?.score}/{f.outcome?.total}</h2>
              <ul className="plain">
                {f.outcome?.first_try_bonus ? <li>⭐ Flawless first try: +{f.outcome.first_try_bonus} XP</li> : null}
                {f.outcome?.crit_xp ? <li>Crits: +{f.outcome.crit_xp} XP</li> : null}
                {f.outcome?.completed ? <li>✅ Quest complete: +{f.outcome.quest_xp} XP{f.outcome.tested_out ? " (tested out, no turn-in needed)" : ""}</li> : null}
                {f.outcome?.loot ? <li>🎁 New outfit: <b style={{ color: f.outcome.loot.color }}>{f.outcome.loot.name}</b>. <i>{f.outcome.loot.flavour}</i></li> : null}
              </ul>
              <div className="row">
                {f.outcome?.next === "submit" && <Link className="btn primary" href={`/quests/${questId}#claim`}>Claim the chest: send your work</Link>}
                {f.outcome?.next === "next" && <Link className="btn primary" href="/">Next room</Link>}
                {f.outcome?.next === "action" && <Link className="btn primary" href={`/quests/${questId}`}>Back to the room</Link>}
                <Link className="btn" href="/me">{f.outcome?.loot ? "Wear it" : "Character sheet"}</Link>
              </div>
            </>
          ) : (
            <>
              <h2 style={{ marginTop: 0 }}>You are knocked down · {f.outcome?.score}/{f.outcome?.total}</h2>
              <p>You need {f.hits_to_win} right. Read the guide again and come back whenever you are ready.</p>
              <div className="row">
                <a className="btn primary" href={`/quests/${questId}/fight`}>Fight again</a>
                <Link className="btn" href={`/quests/${questId}`}>Back to the reading</Link>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
