import Link from "next/link";
import type { Specializations } from "@/lib/api";
import { loadManifest, rankCrest, siteArtGroup, specArtId } from "@/lib/art";
import { getT } from "@/lib/i18n";
import { Px } from "./SiteArt";

const SPEC_BLURB: Record<string, string> = {
  level_design: "Spaces, flow and encounters. Build places people want to move through.",
  programming: "Blueprints first, then C++. Make the engine do what you mean.",
  lookdev: "Materials, lighting and Lumen. Make it look the way it feels.",
  tech_art: "Shaders, Niagara, tools. The bridge between art and code.",
  gameplay_design: "Rules, loops and feel. Turn ideas into things worth playing.",
  animation: "Rigs, blends and state machines. Make characters move with intent.",
  cinematics: "Sequencer, cameras and cuts. Tell it like a film.",
};
const SPEC_GLYPH: Record<string, string> = { level_design: "🗺️", programming: "⚙️", lookdev: "🎨", tech_art: "🔮", gameplay_design: "🎲", animation: "🏃", cinematics: "🎬" };

/** The explainer: how a quest works, the seven specializations, the ladder, what you keep. Shown to guests on the
 *  home page and on /how-it-works for everyone. */
export default async function HowItWorks({ specs }: { specs: Specializations | null }) {
  const [t, m] = await Promise.all([getT(), loadManifest()]);
  const stepArt = siteArtGroup(m, "quest-steps"), specArt = siteArtGroup(m, "specializations");
  const list = specs ? Object.values(specs.specializations).filter((m) => m.key !== "undecided") : [];
  return (
    <>
      <section>
        <div className="section-h"><h2>{t("How a quest works")}</h2></div>
        <div className="steps4">
          <Step art={stepArt["read"]} n="I" title={t("Read")} text={t("Every dungeon starts with a short guide from the Unreal docs or a trusted source. Open it, and you learn the boss's next move.")} />
          <Step art={stepArt["build"]} n="II" title={t("Build")} text={t("Do the thing in the engine. A checklist tells you exactly what done looks like.")} />
          <Step art={stepArt["boss"]} n="III" title={t("Fight the boss")} text={t("A quiz, turn by turn. Right answers hit. Wrong ones wound you and leave a debuff. Beat it with 80% or better.")} />
          <Step art={stepArt["turn-in"]} n="IV" title={t("Open the chest")} text={t("Show your work: a few lines and a screenshot. Auto, honor or a mentor accepts it. XP, outfits and ranks follow.")} />
        </div>
      </section>

      <section>
        <div className="section-h"><h2>{t("Seven specializations")}</h2><span className="muted small">{t("{n}+ quests. Pick a primary, add as many others as you like.", { n: specs?.quest_count ?? 700 })}</span></div>
        <div className="specs">
          {list.map((m) => (
            <Link key={m.key} href={`/quests?specialization=${m.key}`} className="spec-banner">
              {specArt[specArtId(m.key)] ? <Px src={specArt[specArtId(m.key)]} scale={2} /> : <span className="spec-glyph">{SPEC_GLYPH[m.key] ?? "❖"}</span>}
              <b>{t(m.title)}</b>
              <span className="small muted">{SPEC_BLURB[m.key] ? t(SPEC_BLURB[m.key]) : ""}</span>
              <span className="small" style={{ color: "var(--gold)" }}>{t("{prefix} quests · {n} capstone dungeons", { prefix: m.prefix ?? "", n: Object.keys(m.capstones ?? {}).length })}</span>
            </Link>
          ))}
        </div>
      </section>

      {specs && (
        <section>
          <div className="section-h"><h2>{t("The ladder")}</h2><span className="muted small">{t("Five ranks. Each one opens a harder tier of dungeons.")}</span></div>
          <ol className="ladder">
            {specs.ranks.filter((r) => r.n <= 4).map((r) => (
              <li key={r.n} style={{ "--rank": r.color ?? "var(--gold)" } as React.CSSProperties}>
                {rankCrest(m, r.n) ? <Px src={rankCrest(m, r.n)} className="ladder-crest" /> : <span className="ladder-dot" />}
                <div>
                  <b style={{ color: r.color ?? "inherit" }}>{t(r.title)}</b>
                  <div className="small muted">{r.n === 0
                    ? t("Where everyone starts. Orientation, then the Starter Quests.")
                    : r.n >= 3
                      ? t("{xp} XP and {n} {tier} quests to move on · your primary specialization joins your title", { xp: r.xp, n: r.quests_to_leave ?? "", tier: specs.tiers[r.tier]?.name ? t(specs.tiers[r.tier].name) : "" })
                      : t("{xp} XP and {n} {tier} quests to move on", { xp: r.xp, n: r.quests_to_leave ?? "", tier: specs.tiers[r.tier]?.name ? t(specs.tiers[r.tier].name) : "" })}</div>
                </div>
              </li>
            ))}
          </ol>
          <p className="small muted" style={{ marginTop: 12 }}>{t("Beyond Master sit Senior and Lead: guild roles for those who review work and write quests.")}</p>
        </section>
      )}

      <section>
        <div className="section-h"><h2>{t("What you keep")}</h2></div>
        <div className="grid">
          <div className="card"><div className="eyebrow">{t("Outfits")}</div><p className="small" style={{ margin: "6px 0 0" }}>{t("Whole sets for ranking up, clearing capstone dungeons and hitting milestones. Looks only. Nothing but your answers decides a fight.")}</p></div>
          <div className="card"><div className="eyebrow">{t("Entitlements")}</div><p className="small" style={{ margin: "6px 0 0" }}>{t("Achievements, titles, colours and frames, earned by ranks, milestones and working across specializations. Feature three achievements on your player card.")}</p></div>
          <div className="card"><div className="eyebrow">{t("A player card")}</div><p className="small" style={{ margin: "6px 0 0" }}>{t("Your rank, specializations, title, motto and streak on one card, with decorations you unlock. Share the link with anyone.")}</p></div>
        </div>
      </section>

    </>
  );
}

function Step({ n, title, text, art }: { n: string; title: string; text: string; art?: string }) {
  return (
    <div className="card step">
      {art ? <span className="step-art"><Px src={art} scale={2} /><span className="step-n">{n}</span></span> : <span className="step-n">{n}</span>}
      <h3 style={{ margin: "6px 0 4px" }}>{title}</h3>
      <p className="small muted" style={{ margin: 0 }}>{text}</p>
    </div>
  );
}
