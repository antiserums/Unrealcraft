/** The pixel art pack (UCSourceArt/pixel-v3) as the website sees it.
 *
 *  tools/sync_art.py copies the pack's exports into web/public/art/ and writes web/public/art/manifest.json.
 *  Characters are pre-rendered sprite sheets per body x set x equipment style (24 frames of 128 px);
 *  creatures are sheets too (enemies 64 px, bosses 128 px). Without the manifest every figure falls back to the
 *  flat SVG silhouettes in components/Figure.tsx, so the site never breaks. Draw at integer scales, pixelated. */
import { promises as fs } from "fs";
import path from "path";

export type Anim = { id: string; row: number; frames: number | number[]; fps: number; loop: boolean };
export type SheetSpec = { sheet: string; frame: number; columns: number; animations: Anim[]; kind?: string; name?: string };
export type Manifest = {
  version: number; frame: number;
  characterAnimations: Anim[];
  styles: Record<string, { weapon: string; offhand: string }>;
  /** body -> set -> style -> sheet */
  presets: Record<string, Record<string, Record<string, SheetSpec>>>;
  creatures: Record<string, SheetSpec>;
  sets: Record<string, { name: string; kind: string }>;
  /** set id -> icon path (the chest piece stands for the set) */
  icons: Record<string, string>;
  badges: { id: string; name: string; file: string }[];
  rarity: Record<string, { color: string; label: string; frame: string | null }>;
  environments: Record<string, { path: string; large?: string | null; width: number; height: number; groundY: number }>;
  appearance: Record<string, string[]>;
  banners?: Record<string, string>;
  living_town?: { script: string; stills: Record<string, string>; seasons: string[] };
  /** website-art: "<group>" or "<group>/<frame>" -> path, plus the extra fight arenas */
  website_art?: { images: Record<string, string>; arenas: Record<string, { path: string; width: number; height: number; groundY: number }> };
  decorations?: { avatar: Record<string, string>; card: Record<string, string>; inset?: number; anim?: Record<"avatar" | "card", Record<string, { frames: string[]; fps: number }>> };
};
export type DecoAnim = { frames: string[]; fps: number };

let cache: { at: number; m: Manifest | null } | null = null;

export async function loadManifest(): Promise<Manifest | null> {
  if (cache && Date.now() - cache.at < 10_000) return cache.m;
  try {
    const raw = await fs.readFile(path.join(process.cwd(), "public", "art", "manifest.json"), "utf-8");
    const m = JSON.parse(raw) as Manifest;
    cache = { at: Date.now(), m: m.version === 3 ? m : null };
  } catch {
    cache = { at: Date.now(), m: null };
  }
  return cache.m;
}

export const art = (rel: string) => `/art/${rel}`;

/** The pre-rendered sheet for a body, outfit set and equipment style; falls back across styles and bodies. */
export function presetSheet(m: Manifest | null, body: string, set: string, style: string): SheetSpec | null {
  if (!m) return null;
  const b = m.presets[body] ?? m.presets.body_a ?? Object.values(m.presets)[0];
  const s = b?.[set];
  const spec = s?.[style] ?? s?.melee ?? (s && Object.values(s)[0]);
  return spec ? { ...spec, sheet: art(spec.sheet) } : null;
}

export function creatureSheet(m: Manifest | null, id: string): SheetSpec | null {
  const c = m?.creatures[id];
  return c ? { ...c, sheet: art(c.sheet) } : null;
}

export function iconImage(m: Manifest | null, set: string): string | null {
  const f = m?.icons[set];
  return f ? art(f) : null;
}

/** Achievement badge by the pack's 1-based index. */
export function badgeImage(m: Manifest | null, n: number | undefined): string | null {
  const b = n ? m?.badges[n - 1] : null;
  return b ? art(b.file) : null;
}

/** The fight background. With a quest id the room is picked from every arena the pack has, always the same room
 *  for the same quest; without one it is the training chamber. */
export function arenaBackground(m: Manifest | null, questId?: string): { small: string; large: string | null; groundY: number } | null {
  if (!m) return null;
  const rooms = [
    ...Object.values(m.environments).map((e) => ({ small: art(e.path), large: e.large ? art(e.large) : null, groundY: e.groundY })),
    ...Object.values(m.website_art?.arenas ?? {}).map((e) => ({ small: art(e.path), large: null, groundY: e.groundY })),
  ];
  if (!rooms.length) return null;
  if (!questId) return rooms[0];
  let h = 0;
  for (const ch of questId) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return rooms[h % rooms.length];
}

/** One website-art image by id: "header-quests", "rank-crests/novice", "spots"… null when the pack lacks it. */
export function siteArt(m: Manifest | null, id: string): string | null {
  const f = m?.website_art?.images[id];
  return f ? art(f) : null;
}

/** Every image of one group, keyed by frame id: siteArtGroup(m, "specializations")["level-design"]. */
export function siteArtGroup(m: Manifest | null, group: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(m?.website_art?.images ?? {})) if (k.startsWith(group + "/")) out[k.slice(group.length + 1)] = art(v);
  return out;
}

/** Achievement keys that have their own named badge in website-art (the older badges are picked by index). */
const NAMED_BADGE: Record<string, string> = {
  rooms_50: "dungeons-50", rooms_150: "dungeons-150", focus_50: "first-try-wins-50", craft_10: "works-accepted-10", lore_50: "readings-50",
  streak_30: "streak-30", capstone_4: "capstones-4", specs_7: "all-specializations", cross_25: "outside-field-25",
};
/** The badge for an achievement: its named website-art badge when there is one, else the pack badge by index. */
export function achievementBadge(m: Manifest | null, a: { key: string; badge?: number }): string | null {
  const named = NAMED_BADGE[a.key] ? siteArt(m, `achievement-badges/${NAMED_BADGE[a.key]}`) : null;
  return named ?? badgeImage(m, a.badge);
}

/** Art ids use hyphens and the older "lookdev" key is Environment Art. */
export const specArtId = (key: string) => (key === "lookdev" ? "environment-art" : key.replace(/_/g, "-"));
const TIER_ORDER = ["novice", "apprentice", "adept", "expert", "master"];
/** Difficulty mark (1 to 5) for a tier name such as "Adept". */
export function difficultyArt(m: Manifest | null, tierName: string): string | null {
  const i = TIER_ORDER.indexOf(tierName.toLowerCase());
  return i < 0 ? null : siteArt(m, `difficulty/difficulty-${i + 1}`);
}
/** Rank crest for a rank number: -1 Orientation, 0 Novice … 4 Master. Staff ranks beyond that use the Master crest. */
export function rankCrest(m: Manifest | null, n: number): string | null {
  const ids = ["orientation", ...TIER_ORDER];
  return siteArt(m, `rank-crests/${ids[Math.max(0, Math.min(n + 1, ids.length - 1))]}`);
}

/** Sheets for every set (for the wardrobe's try-on mirror), keyed by set id. */
export function presetSheets(m: Manifest | null, body: string, style: string): Record<string, SheetSpec> {
  if (!m) return {};
  const out: Record<string, SheetSpec> = {};
  for (const set of Object.keys(m.sets)) {
    const s = presetSheet(m, body, set, style);
    if (s) out[set] = s;
  }
  return out;
}

/** The home banner (3:1, title goes in the upper central sky). */
export function bannerImage(m: Manifest | null, key = "town"): string | null {
  const f = m?.banners?.[key];
  return f ? art(f) : null;
}

/** The home banner as a pair: the looping animated version (when the pack has one) and a still for reduced
 *  motion and the pause control. Without an animation both point at the still banner. */
export function bannerSet(m: Manifest | null): { animated: string | null; still: string; living: LivingTownArt | null } | null {
  const still = bannerImage(m, "town_still") ?? bannerImage(m, "town");
  if (!still) return null;
  const lt = m?.living_town;
  const living = lt?.script ? { script: art(lt.script), stills: Object.fromEntries(Object.entries(lt.stills).map(([k, v]) => [k, art(v)])), seasons: lt.seasons } : null;
  return { animated: bannerImage(m, "town_animated"), still, living };
}

/** The living-town banner: a canvas component with seasons and time-of-day lighting, plus one still per season and
 *  time (e.g. "summer-day") shown before the script runs. */
export type LivingTownArt = { script: string; stills: Record<string, string>; seasons: string[] };

/** Avatar ring or card border for a decoration theme id. */
export function decorationImage(m: Manifest | null, kind: "avatar" | "card", id: string | undefined): string | null {
  const f = id ? m?.decorations?.[kind]?.[id] : null;
  return f ? art(f) : null;
}

/** Every decoration image by kind, for the pickers. */
export function decorationImages(m: Manifest | null): { avatar: Record<string, string>; card: Record<string, string> } {
  const out = { avatar: {} as Record<string, string>, card: {} as Record<string, string> };
  for (const kind of ["avatar", "card"] as const) for (const [k, v] of Object.entries(m?.decorations?.[kind] ?? {})) out[kind][k] = art(v);
  return out;
}

/** The animation (if any) for a decoration theme. */
export function decorationAnim(m: Manifest | null, kind: "avatar" | "card", id: string | undefined): DecoAnim | null {
  const a = id ? m?.decorations?.anim?.[kind]?.[id] : null;
  return a ? { frames: a.frames.map(art), fps: a.fps } : null;
}
