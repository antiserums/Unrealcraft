"""Copy the pixel art pack (UCSourceArt/pixel-v3) into the website and write web/public/art/manifest.json.

Usage (from the repo root):  py -3 tools/sync_art.py [path-to-UCSourceArt]
Default pack path: ../UCSourceArt next to this repo. The pixel-v3 folder inside it is what gets read.

What it copies (see pixel-v3/INTEGRATION.txt):
  characters/presets/<body>/<set>_<style>/sheet.png   24-frame character sheets, 4 x 6 frames of 128 px
  atlases/<creature>.png                               enemies 4 x 4 frames of 64 px; bosses 4 x 6 frames of 128 px
  gear/icons/set_<set>_<slot>.png                      32 px inventory icons
  ui/badges/badge_<n>.png, ui/rarity/<r>.svg           achievement badges, rarity frames
  environments/dungeon-training-chamber-*.png          the arena background (480 x 270, and the 4x version)
  banners/*.webp|png                                   the home banner (3:1, no text baked in)
  profile-decorations/{avatar,card}/NN-<theme>.png     avatar rings (96 px) and card borders (256 x 200), transparent
  metadata/pack.json, metadata/character-presets.json  frame rectangles, animation rows, fps
Nothing in the pack is modified. Only PNG/SVG/JSON files are copied.
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO.parent / "UCSourceArt"
PACK = ROOT / "pixel-v3" if (ROOT / "pixel-v3").is_dir() else ROOT
OUT = REPO / "web" / "public" / "art"
SET_ICON_SLOT = "chest"          # the one icon that stands for a whole set in the wardrobe


def png_alpha(path: Path):
    """(width, height, alpha(x, y)) for an 8-bit RGBA or RGB PNG, no third-party libraries."""
    data = path.read_bytes(); pos = 8; idat = b""; w = h = 0; ct = 6
    while pos < len(data):
        ln, = struct.unpack(">I", data[pos:pos + 4]); t = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + ln]
        if t == b"IHDR":
            w, h, _bd, ct = struct.unpack(">IIBB", body[:10])
        elif t == b"IDAT":
            idat += body
        pos += 12 + ln
    bpp = 4 if ct == 6 else 3
    raw = zlib.decompress(idat); stride = w * bpp; rows = []; prev = bytearray(stride); i = 0
    for _y in range(h):
        f = raw[i]; i += 1; line = bytearray(raw[i:i + stride]); i += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pr = a + b - c; pa, pb, pc = abs(pr - a), abs(pr - b), abs(pr - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line)); prev = line
    return w, h, (lambda x, y: rows[y][x * 4 + 3] if bpp == 4 else 255)


def border_inset(path: Path) -> dict:
    """Inner edge of the border band on each side, in source pixels. Sampled on many lines across the middle
    60 percent of each edge and taking the smallest reading, so corner and centre ornaments (which only add
    to a reading) drop out and the band itself is measured. The site pads the card's gutter by this."""
    w, h, alpha = png_alpha(path)
    xs = range(int(w * 0.2), int(w * 0.8), 3)
    ys = range(int(h * 0.2), int(h * 0.8), 3)
    def edge(samples, along, half, inner):
        vals = []
        for s_ in samples:
            hits = [k for k in half if alpha(*(along(s_, k))) > 20]
            if hits:
                vals.append(inner(hits))
        return min(vals) if vals else 0
    top = edge(xs, lambda x, y: (x, y), range(h // 2), lambda hits: max(hits) + 1)
    bottom = edge(xs, lambda x, y: (x, y), range(h // 2, h), lambda hits: h - min(hits))
    left = edge(ys, lambda y, x: (x, y), range(w // 2), lambda hits: max(hits) + 1)
    right = edge(ys, lambda y, x: (x, y), range(w // 2, w), lambda hits: w - min(hits))
    return {"top": top, "bottom": bottom, "left": left, "right": right}


def main() -> None:
    if not (PACK / "metadata" / "pack.json").is_file():
        sys.exit(f"pixel pack not found at {PACK} (no metadata/pack.json)")
    OUT.mkdir(parents=True, exist_ok=True)
    copied = 0

    def put(rel: str) -> str | None:
        nonlocal copied
        src = PACK / rel
        if not src.is_file():
            return None
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)
            copied += 1
        return rel

    pack = json.loads((PACK / "metadata" / "pack.json").read_text(encoding="utf-8"))
    presets = json.loads((PACK / pack["presetManifest"]).read_text(encoding="utf-8"))
    put("metadata/pack.json")
    put(pack["presetManifest"])

    m: dict = {"version": 3, "frame": 128, "pixelated": True,
               "characterAnimations": pack["characterAnimations"], "styles": pack["equipmentStyles"],
               "presets": {}, "creatures": {}, "sets": {}, "icons": {}, "badges": [], "rarity": {}, "environments": {},
               "appearance": {"body": [b["id"] for b in pack["bodies"]], "style": list(pack["equipmentStyles"].keys())}}
    for p in presets:
        if put(p["sheet"]):
            m["presets"].setdefault(p["body"], {}).setdefault(p["set"], {})[p["style"]] = {
                "sheet": p["sheet"], "frame": p["frameWidth"], "columns": p["columns"], "animations": p["animations"]}
    for c in pack["creatures"]:
        if put(c["atlas"]):
            m["creatures"][c["id"]] = {"sheet": c["atlas"], "kind": c["kind"], "frame": c["frameSize"], "columns": 4,
                                       "animations": c["animations"], "name": c["name"]}
    for s in pack["sets"]:
        m["sets"][s["id"]] = {"name": s["name"], "kind": s["kind"]}
    for it in pack["items"]:
        put(it["icon"])
        if it["slot"] == SET_ICON_SLOT:
            m["icons"][it["theme"]] = it["icon"]
    for b in pack["badges"]:
        if put(b["file"]):
            m["badges"].append({"id": b["id"], "name": b["name"], "file": b["file"]})
    for r in pack["rarity"]:
        f = put(f"ui/rarity/{r['id']}.svg")
        m["rarity"][r["id"]] = {"color": r["color"], "label": r["label"], "frame": f}
    for e in pack.get("environments", []):
        if put(e["path"]):
            big = e["path"].replace("480x270", "1920x1080")
            m["environments"][e["id"]] = {**{k: e[k] for k in ("path", "width", "height", "groundY", "hero", "enemy") if k in e},
                                          "large": put(big)}
    m["banners"] = {}
    for f in sorted((PACK / "banners").glob("*.webp")) + sorted((PACK / "banners").glob("*.png")):
        if "source" in f.name:
            continue
        key = "town" if "town" in f.name else f.stem
        rel = put(f.relative_to(PACK).as_posix())
        if rel and (key not in m["banners"] or f.suffix == ".webp"):
            m["banners"][key] = rel
    m["decorations"] = {"avatar": {}, "card": {}, "inset": {}}
    for kind in ("avatar", "card"):
        for f in sorted((PACK / "profile-decorations" / kind).glob("*.png")):
            key = re.sub(r"^\d+-", "", f.stem)                      # 06-thornwood.png -> thornwood
            rel = put(f.relative_to(PACK).as_posix())
            if rel:
                m["decorations"][kind][key] = rel
                if kind == "card":
                    m["decorations"]["inset"][key] = border_inset(f)
    (OUT / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    print(f"pack: {PACK}\ncopied {copied} files; {sum(len(v) for b in m['presets'].values() for v in b.values())} preset sheets, "
          f"{len(m['creatures'])} creatures, {len(m['icons'])} set icons, {len(m['badges'])} badges -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
