"use client";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import type { Anim, SheetSpec } from "@/lib/art";

/** Plays one row of a pixel sprite sheet. Integer scales only; looping rows loop, the rest hold their last frame.
 *  `crop` shows a window of the frame (source pixels) so a 128 px canvas can sit in a tighter box. */
export default function Sprite({ spec, anim = "idle", scale = 2, crop, flip = false, still = false, className = "", style, label }:
  { spec: SheetSpec; anim?: string; scale?: number; still?: boolean; crop?: { x: number; y: number; w: number; h: number }; flip?: boolean; className?: string; style?: CSSProperties; label?: string }) {
  const a: Anim = useMemo(() => spec.animations.find((x) => x.id === anim) ?? spec.animations[0], [spec, anim]);
  const count = Array.isArray(a.frames) ? a.frames.length : a.frames;
  const [i, setI] = useState(0);
  const rows = Math.max(...spec.animations.map((x) => x.row)) + 1;

  useEffect(() => {
    setI(0);
    if (still || count <= 1 || (typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    let n = 0;
    const t = setInterval(() => {
      n += 1;
      if (n >= count) { if (a.loop) n = 0; else { clearInterval(t); return; } }
      setI(n);
    }, 1000 / a.fps);
    return () => clearInterval(t);
  }, [a, count, still]);

  const f = spec.frame, k = scale;
  const col = Array.isArray(a.frames) ? a.frames[i] % spec.columns : i;
  const row = Array.isArray(a.frames) ? Math.floor(a.frames[i] / spec.columns) : a.row;
  const inner: CSSProperties = {
    width: f * k, height: f * k, backgroundImage: `url("${spec.sheet}")`,
    backgroundSize: `${spec.columns * f * k}px ${rows * f * k}px`,
    backgroundPosition: `${-col * f * k}px ${-row * f * k}px`,
    backgroundRepeat: "no-repeat", imageRendering: "pixelated",
    transform: flip ? "scaleX(-1)" : undefined,
  };
  if (!crop) return <div className={`px ${className}`} role="img" aria-label={label} style={{ ...inner, ...style }} />;
  return (
    <div className={`px ${className}`} role="img" aria-label={label} style={{ width: crop.w * k, height: crop.h * k, overflow: "hidden", position: "relative", ...style }}>
      <div style={{ ...inner, position: "absolute", left: -crop.x * k, top: -crop.y * k }} />
    </div>
  );
}
