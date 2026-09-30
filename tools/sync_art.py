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
  profile-decorations/{avatar,card}/NN-<theme>.png     avatar rings (48 px) and card borders (352 x 252), transparent
  metadata/pack.json, metadata/character-presets.json  frame rectangles, animation rows, fps
Nothing in the pack is modified. Only PNG/SVG/JSON files are copied.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO.parent / "UCSourceArt"
PACK = ROOT / "pixel-v3" if (ROOT / "pixel-v3").is_dir() else ROOT
OUT = REPO / "web" / "public" / "art"
SET_ICON_SLOT = "chest"          # the one icon that stands for a whole set in the wardrobe


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
    # banners/animated/: a looping animated WebP (48 frames, 8 fps, 6 s) plus a still for reduced motion / pause
    anim = PACK / "banners" / "animated"
    if anim.is_dir():
        moving = anim / "fantasy-town-animated-960x320.webp"
        still = anim / "fantasy-town-still.png"
        if moving.exists() and (rel := put(moving.relative_to(PACK).as_posix())):
            m["banners"]["town_animated"] = rel
        if still.exists() and (rel := put(still.relative_to(PACK).as_posix())):
            m["banners"]["town_still"] = rel
    # Card borders follow docs/09-playercard-art-spec.md: 352 x 252 with the card in the centre 320 x 220, so the
    # band's inner edge is 16 source px from the canvas edge on every side and every theme.
    m["decorations"] = {"avatar": {}, "card": {}, "inset": 16, "anim": {"avatar": {}, "card": {}}}
    for kind in ("avatar", "card"):
        for f in sorted((PACK / "profile-decorations" / kind).glob("*.png")):
            key = re.sub(r"^\d+-", "", f.stem)                      # 06-thornwood.png -> thornwood
            rel = put(f.relative_to(PACK).as_posix())
            if rel:
                m["decorations"][kind][key] = rel
    # Animated decorations: the pack lists per-frame PNGs next to a sheet (profile-decorations/manifest.json).
    deco_meta = PACK / "profile-decorations" / "manifest.json"
    if deco_meta.is_file():
        for a in json.loads(deco_meta.read_text(encoding="utf-8")).get("assets", []):
            anim = a.get("animation")
            if not anim or a.get("type") not in ("avatar", "card"):
                continue
            folder = Path(anim["sheet"]).parent.as_posix()          # animations/<theme>
            frames = [put(f"profile-decorations/{folder}/{a['type']}_{i}.png") for i in range(int(anim.get("frames", 0)))]
            frames = [f for f in frames if f]
            if frames:
                m["decorations"]["anim"][a["type"]][a["theme"]] = {"frames": frames, "fps": int(anim.get("fps", 8))}
    (OUT / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    print(f"pack: {PACK}\ncopied {copied} files; {sum(len(v) for b in m['presets'].values() for v in b.values())} preset sheets, "
          f"{len(m['creatures'])} creatures, {len(m['icons'])} set icons, {len(m['badges'])} badges -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
