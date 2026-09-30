"""Copy the art pack's finished exports into the website and write web/public/art/manifest.json.

Usage (from the repo root):  py -3 tools/sync_art.py [path-to-UCSourceArt]
Default pack path: ../UCSourceArt next to this repo.

What it reads (see UCSourceArt/art-and-overlay-spec.txt):
  gear/icons/<id>_icon_v###.png            inventory icons (512x512)
  gear/overlays/<id>_<body>_<part>_v###.png  fitted overlays on the 1024x1024 canvas; <part> names a draw-order layer
  characters/bases/<body>_<part>_v###.png  body base layers
  enemies/<id>_full_v###.png, enemies/<id>_portrait_v###.png
  bosses/<id>_full_v###.png,  bosses/<id>_portrait_v###.png
  metadata/<id>.json                       optional; `layers` there override the filename-derived draw order
The newest version number wins. Only PNGs are copied; nothing in the pack is modified.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO.parent / "UCSourceArt"
OUT = REPO / "web" / "public" / "art"

# Draw order from the spec (art-and-overlay-spec.txt). Overlay filenames name the part after the body id.
Z = {"back": 10, "body": 20, "face": 30, "legs": 40, "feet": 50, "chest": 60, "face-front": 70, "hair-rear": 80,
     "shoulders": 90, "hair-front": 100, "head": 110, "hands": 120, "weapon": 130, "offhand": 130, "straps": 140, "fx": 150}
NAME = re.compile(r"^(?P<id>[a-z0-9_-]+?)_(?P<rest>.+?)_v(?P<v>\d{3})\.png$")


def newest(files: list[Path]) -> dict[str, Path]:
    """key -> newest file, where key is the filename without the version suffix."""
    best: dict[str, tuple[int, Path]] = {}
    for f in files:
        m = NAME.match(f.name)
        if not m:
            continue
        key = f"{m['id']}_{m['rest']}"
        v = int(m["v"])
        if key not in best or v > best[key][0]:
            best[key] = (v, f)
    return {k: p for k, (v, p) in best.items()}


def main() -> None:
    if not PACK.is_dir():
        sys.exit(f"art pack not found at {PACK}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "canvas": {"width": 1024, "height": 1024}, "assets": {}, "bodies": {}, "appearance": {}}
    copied = 0

    def put(src: Path) -> str:
        nonlocal copied
        rel = src.relative_to(PACK).as_posix()
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)
            copied += 1
        return rel

    assets = manifest["assets"]
    for f in newest(list((PACK / "gear" / "icons").glob("*.png"))).values():
        m = NAME.match(f.name)
        assets.setdefault(m["id"], {})["icon"] = put(f)
    for f in newest(list((PACK / "gear" / "overlays").glob("*.png"))).values():
        m = NAME.match(f.name)
        parts = m["rest"].split("_")                     # <body>_<part>
        body, part = (parts[0], "_".join(parts[1:])) if len(parts) > 1 else (None, parts[0])
        z = Z.get(part, Z.get(m["id"].split("_")[-1], 60))
        assets.setdefault(m["id"], {}).setdefault("layers", []).append({"z": z, "file": put(f), "body": body})
    for f in newest(list((PACK / "characters" / "bases").glob("*.png"))).values():
        m = NAME.match(f.name)
        manifest["bodies"].setdefault(m["id"], []).append({"z": Z.get(m["rest"], 20), "file": put(f)})
    for folder in ("enemies", "bosses"):
        for f in newest(list((PACK / folder).glob("*.png"))).values():
            m = NAME.match(f.name)
            kind = "portrait" if m["rest"].startswith("portrait") else "full"
            assets.setdefault(m["id"], {})[kind] = put(f)
    for f in (PACK / "metadata").glob("*.json"):
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(meta, dict) and meta.get("id") in assets and meta.get("layersOverride"):
            assets[meta["id"]]["layers"] = meta["layersOverride"]
        if isinstance(meta, dict) and meta.get("appearance"):
            manifest["appearance"].update(meta["appearance"])
    for body in manifest["bodies"]:
        manifest["appearance"].setdefault("body", [])
        if body not in manifest["appearance"]["body"]:
            manifest["appearance"]["body"].append(body)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"pack: {PACK}\ncopied {copied} files; {len(assets)} assets, {len(manifest['bodies'])} bodies -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
