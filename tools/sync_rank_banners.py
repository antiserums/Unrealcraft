"""Optional integration helper for Unrealcraft/tools/sync_art.py.

Call m['rank_banners'] = sync_rank_banners(PACK, OUT) before writing m.
This copies only manifest-listed runtime files, not sources or review material.
"""
import json
import shutil
from pathlib import Path


def sync_rank_banners(pack, out):
    pack, out = Path(pack).resolve(), Path(out).resolve()
    relative = Path('banners/rank-banners')
    root = pack / relative
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    for file in manifest['runtimeFiles']:
        source = (root / file).resolve()
        source.relative_to(root)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = out / relative / file
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    scenes = {}
    for rank, scene in manifest['scenes'].items():
        prefix = relative.as_posix() + '/'
        scenes[rank] = {
            'id': rank, 'name': scene['name'], 'unlockRank': scene['unlockRank'], 'minRank': scene['minRank'],
            'script': prefix + scene['script'],
            'stills': {key: prefix + value for key, value in scene['stills'].items()},
            'loops': {key: prefix + value for key, value in scene['loops'].items()},
            'seasons': manifest['seasons'], 'alt': scene['alt'],
            'width': manifest['width'], 'height': manifest['height'],
        }
    return scenes
