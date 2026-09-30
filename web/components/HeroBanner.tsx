"use client";
import { useEffect, useState, type ReactNode } from "react";

/** The home hero: the pack's town banner, looping when the pack ships the animated version. Reduced-motion users
 *  get the still through CSS; everyone gets a pause control (the choice is remembered in this browser). */
export default function HeroBanner({ animated, still, children }: { animated: string | null; still: string; children: ReactNode }) {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    try { setPaused(localStorage.getItem("banner.paused") === "1"); } catch { /* storage may be blocked */ }
  }, []);
  function toggle() {
    const next = !paused;
    setPaused(next);
    try { localStorage.setItem("banner.paused", next ? "1" : "0"); } catch { /* ignore */ }
  }
  const style = { "--banner": `url("${animated ?? still}")`, "--banner-still": `url("${still}")` } as React.CSSProperties;
  return (
    <section className={`hero px banner-hero ${paused || !animated ? "paused" : ""}`} style={style}>
      {animated && (
        <button type="button" className="banner-pause" onClick={toggle} aria-pressed={paused} title={paused ? "Play the banner" : "Pause the banner"}>
          {paused ? "▶" : "❚❚"}
        </button>
      )}
      {children}
    </section>
  );
}
