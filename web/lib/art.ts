/** The art pack (UCSourceArt) as the website sees it.
 *
 *  tools/sync_art.py copies the pack's exports into web/public/art/ and writes web/public/art/manifest.json.
 *  Until an id has exports, components fall back to the built-in SVG silhouettes, so the site never breaks
 *  while the artist AI is still producing. IDs, slots, canvas and draw order follow art-and-overlay-spec.txt. */
import { promises as fs } from "fs";
import path from "path";

export type Manifest = {
  version: number;
  canvas: { width: number; height: number };
  /** id -> files. Paths are relative to /art/. */
  assets: Record<string, { icon?: string; full?: string; portrait?: string; layers?: { z: number; file: string; body?: string }[] }>;
  /** Appearance options the pack ships, e.g. {"body": ["body-a","body-b"], "skin": [...], "hair": [...]} */
  appearance?: Record<string, string[]>;
  /** Character base layers by body id, in draw order. */
  bodies?: Record<string, { z: number; file: string }[]>;
};

let cache: { at: number; m: Manifest | null } | null = null;

export async function loadManifest(): Promise<Manifest | null> {
  if (cache && Date.now() - cache.at < 10_000) return cache.m;
  try {
    const raw = await fs.readFile(path.join(process.cwd(), "public", "art", "manifest.json"), "utf-8");
    cache = { at: Date.now(), m: JSON.parse(raw) as Manifest };
  } catch {
    cache = { at: Date.now(), m: null };
  }
  return cache.m;
}

/** Layers (URLs, back to front) for a character with the given body and equipped art ids. */
export function characterLayers(m: Manifest | null, body: string, artIds: string[]): string[] | null {
  if (!m?.bodies?.[body]) return null;
  const layers: { z: number; file: string }[] = [...m.bodies[body]];
  for (const id of artIds) {
    const a = m.assets[id];
    for (const l of a?.layers ?? []) if (!l.body || l.body === body) layers.push(l);
  }
  return layers.sort((a, b) => a.z - b.z).map((l) => `/art/${l.file}`);
}

export function creatureImage(m: Manifest | null, id: string, kind: "full" | "portrait" = "full"): string | null {
  const f = m?.assets[id]?.[kind] ?? m?.assets[id]?.full;
  return f ? `/art/${f}` : null;
}

export function iconImage(m: Manifest | null, id: string): string | null {
  const f = m?.assets[id]?.icon;
  return f ? `/art/${f}` : null;
}
