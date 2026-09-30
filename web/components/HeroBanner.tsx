"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { LivingTownArt } from "@/lib/art";

/** The artist's canvas component (art/banners/living-town/living-town.js), loaded as a browser module. */
type LivingTown = {
  ready: Promise<void>; season: string; timeMode: "local" | "manual"; hour: number; playing: boolean; seconds: number;
  setSeason(s: string): void; setTime(mode: "local" | "manual", hour?: number): void; render(t: number): unknown; destroy(): void;
};
type Prefs = { season: string; timeMode: "local" | "manual"; hour: number; paused?: boolean };
const KEY = "uc-living-town-v2";                       // the artist's own storage key, so their preview and the site agree
const SEASON_LABEL: Record<string, string> = { spring: "Spring", summer: "Summer", autumn: "Autumn", winter: "Winter" };
const TIMES: { label: string; mode: "local" | "manual"; hour?: number }[] = [
  { label: "My time", mode: "local" }, { label: "Dawn", mode: "manual", hour: 6.5 }, { label: "Day", mode: "manual", hour: 12 },
  { label: "Dusk", mode: "manual", hour: 18.5 }, { label: "Night", mode: "manual", hour: 22 },
];

function loadPrefs(): Prefs {
  try { return { season: "summer", timeMode: "local", hour: 12, ...JSON.parse(localStorage.getItem(KEY) || "{}") }; } catch { return { season: "summer", timeMode: "local", hour: 12 }; }
}
function savePrefs(p: Prefs) { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* storage may be blocked */ } }

/** The home hero. With the living-town pack: a canvas that follows the visitor's clock, with a small ⚙ that opens
 *  season and time-of-day choices and a pause. Otherwise the looping WebP with a pause, or the still. */
export default function HeroBanner({ animated, still, living, children }: { animated: string | null; still: string; living: LivingTownArt | null; children: ReactNode }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const townRef = useRef<LivingTown | null>(null);
  const [prefs, setPrefs] = useState<Prefs>({ season: "summer", timeMode: "local", hour: 12 });
  const [live, setLive] = useState(false);
  const [open, setOpen] = useState(false);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const p = loadPrefs();
    setPrefs(p);
    setPaused(!!p.paused);
    if (!living || !canvasRef.current) return;
    let town: LivingTown | null = null;
    let cancelled = false;
    // a plain dynamic import by URL, kept away from the bundler: the module lives in public/art and finds its own assets
    (new Function("u", "return import(u)")(living.script) as Promise<{ LivingTown: new (c: HTMLCanvasElement, o: object) => LivingTown }>)
      .then(async (mod) => {
        if (cancelled) return;
        town = new mod.LivingTown(canvasRef.current!, { season: p.season, timeMode: p.timeMode, hour: p.hour });
        await town.ready;
        if (cancelled) { town.destroy(); return; }
        if (p.paused) { town.playing = false; town.render(town.seconds); }
        townRef.current = town;
        setLive(true);
      })
      .catch(() => { /* the still stays */ });
    return () => { cancelled = true; town?.destroy(); townRef.current = null; };
  }, [living]);

  function apply(next: Prefs) {
    setPrefs(next); savePrefs(next);
    const t = townRef.current;
    if (!t) return;
    if (t.season !== next.season) t.setSeason(next.season);
    t.setTime(next.timeMode, next.hour);
  }
  function togglePause() {
    const next = !paused;
    setPaused(next);
    const p = { ...prefs, paused: next };
    setPrefs(p); savePrefs(p);
    const t = townRef.current;
    if (t) { t.playing = !next; t.render(t.seconds); }
  }
  const stillFor = living ? (living.stills[`${prefs.season}-${prefs.timeMode === "manual" && (prefs.hour < 6 || prefs.hour >= 20) ? "night" : "day"}`] ?? still) : still;
  const style = { "--banner": `url("${living ? stillFor : animated ?? still}")`, "--banner-still": `url("${stillFor}")` } as React.CSSProperties;
  const canPause = !!living || !!animated;

  return (
    <section className={`hero px banner-hero ${living ? "living" : ""} ${live ? "live" : ""} ${paused || (!animated && !living) ? "paused" : ""}`} style={style}>
      {living && <canvas ref={canvasRef} className="banner-canvas" role="img" aria-label="A pixel-art town by a river: water, foliage, clouds, a waterwheel and villagers, lit for the time of day" />}
      {canPause && (
        <div className={`banner-tools ${open ? "open" : ""}`}>
          {living && open && (
            <div className="banner-menu">
              <div className="row" style={{ gap: 4 }}>
                {living.seasons.map((s) => <button key={s} type="button" className={prefs.season === s ? "on" : ""} onClick={() => apply({ ...prefs, season: s })}>{SEASON_LABEL[s] ?? s}</button>)}
              </div>
              <div className="row" style={{ gap: 4 }}>
                {TIMES.map((t) => {
                  const on = t.mode === "local" ? prefs.timeMode === "local" : prefs.timeMode === "manual" && prefs.hour === t.hour;
                  return <button key={t.label} type="button" className={on ? "on" : ""} onClick={() => apply({ ...prefs, timeMode: t.mode, hour: t.hour ?? prefs.hour })}>{t.label}</button>;
                })}
              </div>
            </div>
          )}
          {living && <button type="button" className="banner-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open} title="Season and time of day">⚙</button>}
          <button type="button" className="banner-btn" onClick={togglePause} aria-pressed={paused} title={paused ? "Play the banner" : "Pause the banner"}>{paused ? "▶" : "❚❚"}</button>
        </div>
      )}
      {children}
    </section>
  );
}
