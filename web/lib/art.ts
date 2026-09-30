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
  decorations?: { avatar: Record<string, string>; card: Record<string, string> };
};

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

export function arenaBackground(m: Manifest | null): { small: string; large: string | null; groundY: number } | null {
  const e = m?.environments.dungeon_training_chamber ?? (m && Object.values(m.environments)[0]);
  return e ? { small: art(e.path), large: e.large ? art(e.large) : null, groundY: e.groundY } : null;
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
