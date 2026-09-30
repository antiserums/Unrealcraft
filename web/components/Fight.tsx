"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { SheetSpec } from "@/lib/art";
import { rich } from "@/lib/i18n-config";
import { Boss, Character } from "./Figure";
import Ico from "./Ico";
import { useT } from "./I18n";

type Ev = { kind: string; text: string; damage?: number; bonus_xp?: number; explain?: string; correct?: number; debuff?: string };
type Q = { index: number; total: number; q: string; choices: string[]; hint: string | null; debuff: string | null };
type Fight = {
  fight_id: number; quest: { id: string; title: string; xp: number; verify_type: string };
  boss: { name: string; short: string; look: string; color: string; hits_to_win: number; questions: number; wounds_allowed: number; verb: string; intro: string; tier: string };
  you: { vitality: number; wounds: number; wounds_allowed: number; steady_available: boolean; craft: number; focus: number; crit_pct: number; outfit: string; style?: string };
  hits: number; hits_to_win: number; turn: number; total: number; first_try: boolean; log: Ev[]; question: Q | null;
  result: string | null; events?: Ev[]; resumed?: boolean;
  outcome?: { passed: boolean; score: number; total: number; first_try_bonus?: number; crit_xp?: number; completed?: boolean; quest_xp?: number; loot?: { name: string; tier: string; flavour?: string; color: string; id: string } | null; tested_out?: boolean; next?: string } | null;
};

const DEBUFF: Record<string, string> = { dazed: "Dazed: the choices are shuffled.", weakened: "Weakened: your next hit does half damage.", blinded: "Blinded: no hint this turn." };
/** The pack's scene: 480 x 270 logical pixels, drawn at 2x. Feet land on the ground line (y = 232). */
const STAGE_W = 960, STAGE_H = 540, GROUND = 464;

export default function FightScreen({ questId, outfit, weaponStyle = "melee", color, heroSheet, bossSheet, background, winArt, loseArt, icons = {} }:
  { questId: string; outfit: string; weaponStyle?: string; color: string; heroSheet?: SheetSpec | null; bossSheet?: SheetSpec | null; background?: { small: string; large: string | null } | null; winArt?: string | null; loseArt?: string | null; icons?: Record<string, string> }) {
  const t = useT();
  const router = useRouter();
  const [f, setF] = useState<Fight | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [bossPose, setBossPose] = useState<"idle" | "attack" | "hit" | "dead">("idle");
  const [youPose, setYouPose] = useState<"idle" | "strike" | "hurt" | "down" | "win">("idle");
  const [float, setFloat] = useState<{ text: string; side: "boss" | "you"; kind: string } | null>(null);
  const [last, setLast] = useState<Ev[]>([]);
  const [picked, setPicked] = useState<{ i: number; ok: boolean } | null>(null);   // the answer just given, until the next turn shows
  const [k, setK] = useState(1);
  const asked = useRef<number>(Date.now());
  const started = useRef(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (started.current) return;            // React dev mode runs effects twice; one fight is enough
    started.current = true;
    (async () => {
      const r = await fetch(`/api/me/quests/${questId}/fight`, { method: "POST" });
      const j = await r.json();
      if (!r.ok) { setErr(j.detail ?? t("Could not start the fight.")); return; }
      setF(j); asked.current = Date.now();
    })();
  }, [questId]);

  // The stage is a fixed 960 x 540 scene scaled down to the column it sits in, so sprites stay at integer scales.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setK(Math.min(1, el.clientWidth / STAGE_W)));
    ro.observe(el);
    return () => ro.disconnect();
  }, [f]);

  async function answer(pos: number) {
    if (!f || busy) return;
    setBusy(true);
    const seconds = (Date.now() - asked.current) / 1000;
    const r = await fetch(`/api/fights/${f.fight_id}/turn`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ answer: pos, seconds }) });
    const j: Fight = await r.json();
    if (!r.ok) { setErr((j as unknown as { detail: string }).detail); setBusy(false); return; }
    const evs = j.events ?? [];
    const main = evs.find((e) => ["hit", "crit", "wound", "steady"].includes(e.kind));
    if (main && (main.kind === "hit" || main.kind === "crit")) {
      setYouPose("strike"); setBossPose("hit");
      setFloat({ text: main.kind === "crit" ? t("-{damage} CRIT", { damage: main.damage ?? 0 }) : `-${main.damage}`, side: "boss", kind: main.kind });
    } else if (main) {
      setYouPose("hurt"); setBossPose("attack");
      setFloat({ text: main.kind === "steady" ? "-½" : "-1", side: "you", kind: main.kind });
    }
    setLast(evs);
    setPicked({ i: pos, ok: !!main && (main.kind === "hit" || main.kind === "crit") });
    setTimeout(() => {
      setF(j); asked.current = Date.now(); setBusy(false); setFloat(null); setPicked(null);
      if (j.result === "win") { setBossPose("dead"); setYouPose("win"); }
      else if (j.result === "lose") { setYouPose("down"); setBossPose("idle"); }
      else { setYouPose("idle"); setBossPose("idle"); }
    }, 700);
  }

  // Leaving by the Retreat link ends the fight. Leaving any other way (reload, closing the tab) keeps it, and the
  // next visit picks it up at the same question.
  async function retreat() {
    if (!f || busy) return;
    setBusy(true);
    await fetch(`/api/fights/${f.fight_id}/retreat`, { method: "POST" }).catch(() => null);
    router.push(`/quests/${questId}`);
  }

  if (err) return <div className="card"><b>{err}</b><p style={{ margin: "8px 0 0" }}><Link href={`/quests/${questId}`}>← {t("Back to the dungeon")}</Link></p></div>;
  if (!f) return <div className="card muted">{t("Entering the dungeon…")}</div>;

  const bossHp = Math.max(0, f.hits_to_win - f.hits) / f.hits_to_win;
  const youHp = Math.max(0, (f.you.wounds_allowed + 1 - f.you.wounds)) / (f.you.wounds_allowed + 1);
  const q = f.question;
  const bossScale = bossSheet ? (bossSheet.frame <= 64 ? 3 : 2) : 2;
  const bossSize = bossSheet ? bossSheet.frame * bossScale : 240;
  const bg = background?.large ?? background?.small;

  return (
    <div className="fight">
      <div ref={box} className="arena-box" style={{ height: STAGE_H * k }}>
        <div className={`arena-stage ${bg ? "dungeon" : ""}`} style={{ width: STAGE_W, height: STAGE_H, transform: `scale(${k})`, backgroundImage: bg ? `url("${bg}")` : undefined }}>
          <div className="hpbox you">
            <div className="eyebrow">{icons.vitality && <img className="px pxi pill-ico" src={icons.vitality} width={32} height={32} alt="" />}{t("You")}</div>
            <div className="bar big"><span style={{ width: `${youHp * 100}%`, background: "#4FA36C" }} /></div>
            <div className="small">{f.you.steady_available
              ? t("Wounds: {wounds} · {more} more before you fall · steady ready", { wounds: f.you.wounds, more: Math.max(0, f.you.wounds_allowed - Math.floor(f.you.wounds)) })
              : t("Wounds: {wounds} · {more} more before you fall", { wounds: f.you.wounds, more: Math.max(0, f.you.wounds_allowed - Math.floor(f.you.wounds)) })}</div>
          </div>
          <div className="hpbox boss">
            <div className="eyebrow" style={{ color: f.boss.color }}>{f.boss.name}</div>
            <div className="bar big"><span style={{ width: `${bossHp * 100}%`, background: f.boss.color }} /></div>
            <div className="small">{f.hits > f.hits_to_win
              ? t("{hits}/{total} hits · victory lap · {questions} questions", { hits: Math.min(f.hits, f.hits_to_win), total: f.hits_to_win, questions: f.boss.questions })
              : t("{hits}/{total} hits · {questions} questions", { hits: Math.min(f.hits, f.hits_to_win), total: f.hits_to_win, questions: f.boss.questions })}</div>
          </div>

          <div className="fighter" style={{ left: 96, top: GROUND - 208 - 8 }}>
            {float?.side === "you" && <span className={`float ${float.kind}`}>{float.text}</span>}
            {heroSheet ? <Character sheet={heroSheet} weapon={weaponStyle} pose={youPose} scale={2} crop={null} /> : <Character outfit={outfit} color={color} pose={youPose} size={170} />}
          </div>
          <div className="fighter" style={{ left: STAGE_W - 96 - bossSize, top: GROUND - bossSize + (bossSheet ? (bossSheet.frame <= 64 ? 16 : 20) : 0) }}>
            {float?.side === "boss" && <span className={`float ${float.kind}`}>{float.text}</span>}
            <Boss look={f.boss.look} sheet={bossSheet} color={f.boss.color} pose={bossPose} size={200} />
          </div>
        </div>
      </div>

      {f.resumed && last.length === 0 && !f.result && (
        <div className="log card"><div className="ev"><b>{t("You are back in the fight, right where you left it.")}</b></div></div>
      )}

      {last.length > 0 && (
        <div className="log card">
          {last.map((e, i) => (
            <div key={i} className={`ev ${e.kind}`}>
              <b>{e.text}</b>
              {e.kind === "crit" && e.bonus_xp ? <span className="pill" style={{ marginLeft: 8 }}>{t("+{xp} XP", { xp: e.bonus_xp })}</span> : null}
              {e.explain && <div className="small" style={{ marginTop: 4 }}>{["hit", "crit"].includes(e.kind) ? t("You saw through it: {why}", { why: e.explain }) : t("It got you because: {why}", { why: e.explain })}</div>}
            </div>
          ))}
        </div>
      )}

      {q && !f.result && (
        <div className="card question">
          <div className="eyebrow">{t("Turn {turn} of {total}", { turn: f.turn, total: f.total })}{q.debuff && <span className="pill" style={{ marginLeft: 8, color: "var(--bad)", borderColor: "var(--bad)" }}>{icons[q.debuff] && <img className="px pxi pill-ico" src={icons[q.debuff]} width={32} height={32} alt="" />}{DEBUFF[q.debuff] ? t(DEBUFF[q.debuff]) : q.debuff}</span>}</div>
          {q.hint && <p className="muted small" style={{ margin: "6px 0 0" }}>{icons.hint && <img className="px pxi pill-ico" src={icons.hint} width={32} height={32} alt="" />}{q.hint}</p>}
          <h2 style={{ marginTop: 8 }}>{q.q}</h2>
          <div className="choices">
            {q.choices.map((c, i) => (
              <button key={i} onClick={() => answer(i)} disabled={busy} className={`choice ${picked?.i === i ? (picked.ok ? "correct" : "incorrect") : ""}`}>
                <span className="letter">{"ABCD"[i]}</span> {c}
              </button>
            ))}
          </div>
          <div className="row small muted" style={{ marginTop: 8 }}>
            <span>{t("Answer fast for a better crit chance.")}</span>
            <span className="spacer" />
            <button type="button" className="linklike muted" onClick={retreat} disabled={busy}>{t("Retreat (nothing is recorded)")}</button>
          </div>
        </div>
      )}

      {f.result && (
        <div className="card result">
          {f.result === "win" ? (
            <>
              {winArt && <img className="px result-art" src={winArt} width={160} height={120} alt="" />}
              <h2 style={{ marginTop: 0 }}>{icons.victory ? <img className="px pxi h-ico" src={icons.victory} width={32} height={32} alt="" /> : "🏆 "}{t("{boss} is beaten · {score}/{total}", { boss: f.boss.short, score: f.outcome?.score ?? 0, total: f.outcome?.total ?? 0 })}</h2>
              <ul className="plain">
                {f.outcome?.first_try_bonus ? <li><Ico group="rewards" id="xp" />{t("Flawless first try: +{xp} XP", { xp: f.outcome.first_try_bonus })}</li> : null}
                {f.outcome?.crit_xp ? <li>{icons.critical && <img className="px pxi pill-ico" src={icons.critical} width={32} height={32} alt="" />}{t("Crits: +{xp} XP", { xp: f.outcome.crit_xp })}</li> : null}
                {f.outcome?.completed ? <li><Ico group="rewards" id="xp" />{f.outcome.tested_out ? t("Quest complete: +{xp} XP (tested out, no turn-in needed)", { xp: f.outcome.quest_xp ?? 0 }) : t("Quest complete: +{xp} XP", { xp: f.outcome.quest_xp ?? 0 })}</li> : null}
                {f.outcome?.loot ? <li><Ico group="rewards" id="outfit" />{rich(t("New outfit: {name}. {flavour}"), { name: <b style={{ color: f.outcome.loot.color }}>{f.outcome.loot.name}</b>, flavour: <i>{f.outcome.loot.flavour}</i> })}</li> : null}
              </ul>
              <div className="row">
                {f.outcome?.next === "submit" && <Link className="btn primary" href={`/quests/${questId}#claim`}>{t("Claim the chest: send your work")}</Link>}
                {f.outcome?.next === "next" && <Link className="btn primary" href="/">{t("Next dungeon")}</Link>}
                {f.outcome?.next === "action" && <Link className="btn primary" href={`/quests/${questId}`}>{t("Back to the dungeon")}</Link>}
                <Link className="btn" href="/me/wardrobe">{f.outcome?.loot ? t("Wear it") : t("Wardrobe")}</Link>
              </div>
            </>
          ) : (
            <>
              {loseArt && <img className="px result-art" src={loseArt} width={160} height={120} alt="" />}
              <h2 style={{ marginTop: 0 }}>{t("You are knocked down · {score}/{total}", { score: f.outcome?.score ?? 0, total: f.outcome?.total ?? 0 })}</h2>
              <p>{t("You need {n} right. Read the guide again and come back whenever you are ready.", { n: f.hits_to_win })}</p>
              <div className="row">
                <a className="btn primary" href={`/quests/${questId}/fight`}>{t("Fight again")}</a>
                <Link className="btn" href={`/quests/${questId}`}>{t("Back to the reading")}</Link>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
