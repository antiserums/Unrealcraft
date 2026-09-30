import Link from "next/link";
import type { Majors } from "@/lib/api";

const MAJOR_BLURB: Record<string, string> = {
  level_design: "Spaces, flow and encounters. Build places people want to move through.",
  programming: "Blueprints first, then C++. Make the engine do what you mean.",
  lookdev: "Materials, lighting and Lumen. Make it look the way it feels.",
  tech_art: "Shaders, Niagara, tools. The bridge between art and code.",
  gameplay_design: "Rules, loops and feel. Turn ideas into things worth playing.",
  animation: "Rigs, blends and state machines. Make characters move with intent.",
  cinematics: "Sequencer, cameras and cuts. Tell it like a film.",
};
const MAJOR_GLYPH: Record<string, string> = { level_design: "🗺️", programming: "⚙️", lookdev: "🎨", tech_art: "🔮", gameplay_design: "🎲", animation: "🏃", cinematics: "🎬" };

/** The explainer: how a quest works, the seven majors, the ladder, what you keep. Shown to guests on the home
 *  page and on /how-it-works for everyone. */
export default function HowItWorks({ majors }: { majors: Majors | null }) {
  const list = majors ? Object.values(majors.majors).filter((m) => m.key !== "undecided") : [];
  return (
    <>
      <section>
        <div className="section-h"><h2>How a quest works</h2></div>
        <div className="steps4">
          <Step n="I" title="Read" text="Every dungeon starts with a short guide from the Unreal docs or a trusted source. Open it, and you learn the boss's next move." />
          <Step n="II" title="Build" text="Do the thing in the engine. A checklist tells you exactly what done looks like." />
          <Step n="III" title="Fight the boss" text="A quiz, turn by turn. Right answers hit. Wrong ones wound you and leave a debuff. Beat it with 80% or better." />
          <Step n="IV" title="Open the chest" text="Show your work: a few lines and a screenshot. Auto, honor or a mentor accepts it. XP, outfits and ranks follow." />
        </div>
      </section>

      <section>
        <div className="section-h"><h2>Seven majors</h2><span className="muted small">{majors?.quest_count ?? 700}+ quests. Pick one, cross-train in the rest.</span></div>
        <div className="majors">
          {list.map((m) => (
            <Link key={m.key} href={`/quests?major=${m.key}`} className="major-banner">
              <span className="major-glyph">{MAJOR_GLYPH[m.key] ?? "❖"}</span>
              <b>{m.title}</b>
              <span className="small muted">{MAJOR_BLURB[m.key] ?? ""}</span>
              <span className="small" style={{ color: "var(--gold)" }}>{m.prefix} quests · {Object.keys(m.capstones ?? {}).length} capstone dungeons</span>
            </Link>
          ))}
        </div>
      </section>

      {majors && (
        <section>
          <div className="section-h"><h2>The ladder</h2><span className="muted small">Five ranks. Each one opens a harder tier of dungeons.</span></div>
          <ol className="ladder">
            {majors.ranks.filter((r) => r.n <= 4).map((r) => (
              <li key={r.n} style={{ "--rank": r.color ?? "var(--gold)" } as React.CSSProperties}>
                <span className="ladder-dot" />
                <div>
                  <b style={{ color: r.color ?? "inherit" }}>{r.title}</b>
                  <div className="small muted">{r.n === 0 ? "Where everyone starts. Orientation, then the Starter Quests." : `${r.xp} XP and ${r.quests_to_leave ?? ""} ${majors.tiers[r.tier]?.name ?? ""} quests to move on`}{r.n >= 3 ? " · your major joins your title" : ""}</div>
                </div>
              </li>
            ))}
          </ol>
          <p className="small muted" style={{ marginTop: 12 }}>Beyond Master sit Senior and Lead: guild roles for those who review work and write quests.</p>
        </section>
      )}

      <section>
        <div className="section-h"><h2>What you keep</h2></div>
        <div className="grid">
          <div className="card"><div className="eyebrow">Outfits</div><p className="small" style={{ margin: "6px 0 0" }}>Whole sets for ranking up, clearing capstone dungeons and hitting milestones. Looks only. Nothing but your answers decides a fight.</p></div>
          <div className="card"><div className="eyebrow">Achievements</div><p className="small" style={{ margin: "6px 0 0" }}>Fourteen to earn, from First Blood to Dragonslayer. Feature three on your player card.</p></div>
          <div className="card"><div className="eyebrow">A player card</div><p className="small" style={{ margin: "6px 0 0" }}>Your rank, major, motto and streak on one card, with decorations you unlock. Share the link with anyone.</p></div>
        </div>
      </section>

    </>
  );
}

function Step({ n, title, text }: { n: string; title: string; text: string }) {
  return (
    <div className="card step">
      <span className="step-n">{n}</span>
      <h3 style={{ margin: "6px 0 4px" }}>{title}</h3>
      <p className="small muted" style={{ margin: 0 }}>{text}</p>
    </div>
  );
}
