/** Character and creature figures. Outfits are looks only.
 *  With the pixel pack (see lib/art.ts) a figure is an animated sprite sheet drawn by Sprite.tsx.
 *  Without it, the flat SVG silhouettes below stand in, so the site works while art is missing. */
import type { CSSProperties } from "react";
import type { SheetSpec } from "@/lib/art";
import Sprite from "./Sprite";

const RAR: Record<string, string> = { common: "#4FA36C", uncommon: "#3D7DD8", rare: "#8E6CCF", epic: "#D9824A", legendary: "#D9534F" };
export const RARITY_COLOR = RAR;

type CharPose = "idle" | "strike" | "hurt" | "down" | "win";
type BossPose = "idle" | "attack" | "hit" | "dead";

/** The body occupies x 32..96, y 12..108 of the 128 px frame; this window keeps swings and the shield in view. */
export const HERO_CROP = { x: 20, y: 4, w: 88, h: 116 };
const CHAR_ANIM: Record<CharPose, string> = { idle: "idle", strike: "attack", hurt: "hit", down: "defeat", win: "victory" };
const BOSS_ANIM: Record<BossPose, string> = { idle: "idle", attack: "attack", hit: "hit", dead: "defeat" };

const OUTFIT_TINT: Record<string, string> = { novice: "#3fb6b0", apprentice: "#4FA36C", adept: "#3D7DD8", expert: "#D9824A", master: "#e6c35a", warrior: "#6f7a86", ranger: "#4e8a4a", spellcaster: "#8E6CCF" };

/** The member's figure: the pack's sheet when there is one, otherwise a silhouette tinted by the set.
 *  `size` is the silhouette height; sheets draw at an integer `scale` (2 = 256 px frame) and can be cropped. */
export function Character({ outfit = "novice", sheet, weapon = "melee", color = "#556270", size = 160, pose = "idle", scale = 2, crop = HERO_CROP, still = false, style }:
  { outfit?: string; sheet?: SheetSpec | null; weapon?: string; still?: boolean; color?: string; size?: number; pose?: CharPose; scale?: number; crop?: { x: number; y: number; w: number; h: number } | null; style?: CSSProperties }) {
  if (sheet) {
    const anim = pose === "strike" && weapon === "caster" ? "cast" : CHAR_ANIM[pose];
    return <Sprite spec={sheet} anim={anim} scale={scale} crop={crop ?? undefined} still={still} className={`figure pose-${pose}`} style={style} label="Your character" />;
  }
  const cloth = OUTFIT_TINT[outfit] ?? "#3fb6b0";
  const tf = pose === "strike" ? "translate(14 0) rotate(-6 50 80)" : pose === "hurt" ? "translate(-8 0) rotate(5 50 80)"
    : pose === "down" ? "rotate(80 50 110) translate(0 10)" : pose === "win" ? "translate(0 -6)" : "";
  return (
    <svg viewBox="0 0 100 120" width={size} height={size * 1.2} style={style} className={`figure pose-${pose}`} aria-label="Your character">
      <g transform={tf} style={{ transition: "transform .25s ease" }}>
        <ellipse cx="50" cy="114" rx="26" ry="5" fill="#000" opacity=".18" />
        <path d="M36 44 L30 100 L70 100 L64 44 Z" fill={cloth} opacity=".55" />
        <path d="M40 74 L36 108 L44 108 L48 80 L52 80 L56 108 L64 108 L60 74 Z" fill="#3a3330" />
        <rect x="33" y="103" width="14" height="7" rx="2" fill="#6b4a2e" /><rect x="53" y="103" width="14" height="7" rx="2" fill="#6b4a2e" />
        <path d="M34 42 Q50 34 66 42 L64 78 L36 78 Z" fill={cloth} />
        <path d="M38 62 L62 62 L62 66 L38 66 Z" fill="#6b4a2e" />
        <path d="M34 46 L22 72 L28 75 L40 54 Z" fill={cloth} /><path d="M66 46 L82 66 L77 71 L60 54 Z" fill={cloth} />
        <circle cx="24" cy="74" r="5" fill="#6b4a2e" /><circle cx="80" cy="69" r="5" fill="#6b4a2e" />
        <g transform="rotate(-20 80 69)"><rect x="78" y="30" width="4" height="46" rx="1" fill="#c9ccd2" /><path d="M74 30 L86 30 L80 20 Z" fill="#c9ccd2" /><rect x="75" y="72" width="10" height="4" fill={color} /></g>
        <circle cx="50" cy="26" r="13" fill="#e6c9a8" />
        <path d="M37 24 Q50 8 63 24 L63 20 Q50 4 37 20 Z" fill={cloth} />
        <circle cx="50" cy="50" r="3.5" fill={color} stroke="#fff" strokeWidth=".8" />
      </g>
    </svg>
  );
}

/** A creature: enemy sheets are 64 px frames (draw at 3x), boss sheets 128 px (draw at 2x). */
export function Boss({ look, sheet, color = "#8E6CCF", size = 200, pose = "idle", scale, style }:
  { look: string; sheet?: SheetSpec | null; color?: string; size?: number; pose?: BossPose; scale?: number; style?: CSSProperties }) {
  if (sheet) {
    const k = scale ?? (sheet.frame <= 64 ? 3 : 2);
    return <Sprite spec={sheet} anim={BOSS_ANIM[pose]} scale={k} className={`figure boss pose-${pose}`} style={style} label="The boss" />;
  }
  const tf = pose === "attack" ? "translate(-12 0) scale(1.04)" : pose === "hit" ? "translate(8 0)" : pose === "dead" ? "translate(0 30) scale(1 .3)" : "";
  const op = pose === "dead" ? 0.35 : 1;
  const body = BOSS_SHAPES[look] ?? BOSS_SHAPES.knight;
  return (
    <svg viewBox="0 0 100 120" width={size} height={size * 1.2} style={style} className={`figure boss pose-${pose}`} aria-label="The boss">
      <g transform={tf} opacity={op} style={{ transition: "transform .25s ease, opacity .6s ease", transformOrigin: "50px 110px" }}>
        <ellipse cx="50" cy="114" rx="34" ry="6" fill="#000" opacity=".2" />
        {body(color)}
      </g>
    </svg>
  );
}

const eye = (x: number, y: number) => <circle cx={x} cy={y} r="2.6" fill="#fff" />;
const BOSS_SHAPES: Record<string, (c: string) => React.ReactNode> = {
  wisp: (c) => <><path d="M50 12 C78 30 84 66 60 96 C52 106 48 106 40 96 C16 66 22 30 50 12 Z" fill={c} opacity=".9" /><circle cx="50" cy="50" r="14" fill="#fff" opacity=".35" />{eye(44, 48)}{eye(56, 48)}</>,
  golem: (c) => <><rect x="22" y="40" width="56" height="52" rx="8" fill={c} /><rect x="30" y="18" width="40" height="28" rx="6" fill={c} /><rect x="8" y="46" width="16" height="36" rx="6" fill={c} /><rect x="76" y="46" width="16" height="36" rx="6" fill={c} /><rect x="28" y="92" width="18" height="18" fill={c} /><rect x="54" y="92" width="18" height="18" fill={c} />{eye(42, 32)}{eye(58, 32)}</>,
  serpent: (c) => <><path d="M14 100 C30 60 70 120 86 70 C96 40 70 20 50 30 C34 38 40 60 56 54" fill="none" stroke={c} strokeWidth="14" strokeLinecap="round" /><circle cx="52" cy="30" r="13" fill={c} />{eye(47, 27)}{eye(58, 27)}</>,
  spectre: (c) => <><path d="M28 110 L28 40 Q50 6 72 40 L72 110 L64 98 L56 110 L50 98 L44 110 L36 98 Z" fill={c} opacity=".85" />{eye(42, 44)}{eye(58, 44)}</>,
  beast: (c) => <><ellipse cx="50" cy="70" rx="34" ry="24" fill={c} /><circle cx="76" cy="46" r="16" fill={c} /><path d="M66 32 L70 16 L78 30 Z M84 32 L90 16 L92 32 Z" fill={c} /><rect x="24" y="86" width="10" height="24" fill={c} /><rect x="42" y="88" width="10" height="22" fill={c} /><rect x="60" y="88" width="10" height="22" fill={c} /><path d="M18 62 C4 52 6 40 14 34" stroke={c} strokeWidth="8" fill="none" strokeLinecap="round" />{eye(80, 44)}</>,
  swarm: (c) => <>{[[20, 40, 6], [34, 24, 8], [52, 18, 10], [70, 28, 7], [82, 48, 9], [64, 56, 12], [40, 60, 9], [26, 80, 7], [50, 84, 11], [74, 82, 8], [58, 100, 6], [36, 100, 5]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} fill={c} opacity={0.6 + (i % 3) * 0.13} />)}</>,
  sentinel: (c) => <><path d="M50 8 L82 26 L82 70 L50 112 L18 70 L18 26 Z" fill={c} /><circle cx="50" cy="52" r="16" fill="#111" opacity=".4" /><circle cx="50" cy="52" r="7" fill="#fff" /></>,
  treant: (c) => <><rect x="40" y="56" width="20" height="54" fill={c} /><path d="M50 10 C20 20 12 50 30 62 C20 70 40 80 50 66 C60 80 80 70 70 62 C88 50 80 20 50 10 Z" fill={c} /><path d="M30 110 L20 100 M70 110 L80 100" stroke={c} strokeWidth="8" strokeLinecap="round" />{eye(44, 74)}{eye(56, 74)}</>,
  construct: (c) => <><circle cx="50" cy="58" r="30" fill="none" stroke={c} strokeWidth="10" />{[0, 45, 90, 135, 180, 225, 270, 315].map((a) => <rect key={a} x="46" y="18" width="8" height="12" fill={c} transform={`rotate(${a} 50 58)`} />)}<circle cx="50" cy="58" r="10" fill={c} />{eye(50, 58)}</>,
  wraith: (c) => <><path d="M50 14 C74 14 82 44 72 70 C66 86 70 100 80 110 C60 100 40 100 20 110 C30 100 34 86 28 70 C18 44 26 14 50 14 Z" fill={c} opacity=".8" />{eye(42, 40)}{eye(58, 40)}</>,
  knight: (c) => <><rect x="36" y="14" width="28" height="24" rx="6" fill={c} /><rect x="30" y="40" width="40" height="44" rx="6" fill={c} /><rect x="16" y="44" width="12" height="34" rx="5" fill={c} /><rect x="72" y="44" width="12" height="34" rx="5" fill={c} /><rect x="34" y="84" width="12" height="26" fill={c} /><rect x="54" y="84" width="12" height="26" fill={c} /><rect x="40" y="24" width="20" height="4" fill="#fff" /></>,
  drake: (c) => <><path d="M30 100 C10 80 14 50 40 46 C50 26 70 22 84 34 C96 44 90 60 78 62 L92 70 L74 72 C80 90 60 106 30 100 Z" fill={c} /><path d="M40 46 C20 30 8 40 6 60 C18 52 30 54 40 60 Z" fill={c} opacity=".8" /><path d="M64 56 C70 40 86 36 96 44" stroke={c} strokeWidth="6" fill="none" /><rect x="30" y="98" width="10" height="14" fill={c} /><rect x="56" y="100" width="10" height="12" fill={c} />{eye(78, 40)}</>,
};

export function GearDot({ rarity }: { rarity: string }) {
  return <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: RAR[rarity] ?? "#888", marginRight: 6 }} />;
}

/** Inventory tile: the pack's icon inside a rarity frame, or a rarity swatch until the icon exists. */
export function ItemIcon({ icon, rarity, size = 44 }: { icon?: string | null; rarity: string; size?: number }) {
  const c = RAR[rarity] ?? "#888";
  return (
    <span className="item-icon" style={{ width: size, height: size, borderColor: c, boxShadow: `inset 0 0 0 1px ${c}55, 0 0 8px ${c}33` }}>
      {icon ? <img className="px" src={icon} alt="" style={{ width: "100%", height: "100%", objectFit: "contain" }} /> : <span style={{ background: c, opacity: .35, position: "absolute", inset: 6, borderRadius: 3 }} />}
    </span>
  );
}
