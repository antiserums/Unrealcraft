"""Fetch the real page title of every reading link in the curriculum, so quest pages can name each link
instead of saying "Extra reading 1".

  py -3 tools/link_titles.py            fetch titles for links that have none yet
  py -3 tools/link_titles.py --refresh  fetch every title again

Writes curriculum/link_titles.json (url -> title). The API reads that file; a link with no entry is named
from its address instead. Run this after adding links to the curriculum, then restart the API.
"""
from __future__ import annotations

import html
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum"
OUT = CURRICULUM / "link_titles.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
PAUSE = 3.0                                   # seconds between requests; faster than this and the docs site stalls
DEADLINE = 30                                 # seconds one request may take in all
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")
TITLE_RE = re.compile(r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"']([^\"']+)[\"']|<title[^>]*>([^<]+)</title>", re.I)


class Throttled(Exception):
    """The site wants us to slow down: it answered 429, or stopped answering."""


def curriculum_urls() -> list[str]:
    urls: set[str] = set()
    for f in sorted(CURRICULUM.glob("*.yaml")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if "url" in line or line.lstrip().startswith("- "):          # official_url, extra_urls items, community url, backup_url
                urls.update(u.rstrip(".,") for u in URL_RE.findall(line))
    return sorted(urls)


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(400_000).decode("utf-8", "replace")


def get(url: str) -> str:
    """One page, with a hard limit on the whole request: when the docs site has had enough it stops answering
    instead of refusing, and a plain socket timeout never fires."""
    box: dict = {}

    def run() -> None:
        try:
            box["text"] = _get(url)
        except Exception as e:                                           # noqa: BLE001
            box["error"] = e

    th = threading.Thread(target=run, daemon=True)
    th.start()
    th.join(DEADLINE)
    if th.is_alive():
        raise Throttled
    if "error" in box:
        raise box["error"]
    return box["text"]


def clean(title: str) -> str:
    """'Animation Sequences in Unreal Engine | Unreal Engine 5.8 Documentation | Epic…' -> the first part."""
    return re.sub(r"\s+", " ", html.unescape(title).split(" | ")[0]).strip()


def title_of(url: str) -> str | None:
    host = urllib.parse.urlparse(url).netloc.lower()
    try:
        if "youtube.com" in host or "youtu.be" in host:
            d = json.loads(get("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")))
            return f"{d['title']} ({d['author_name']})" if d.get("author_name") else d["title"]
        m = TITLE_RE.search(get(url))
        return (clean(m.group(1) or m.group(2)) if m else "") or None
    except Throttled:
        raise
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Throttled from e
        print(f"  failed: {url}  ({e})", flush=True)
    except Exception as e:                                               # noqa: BLE001  (timeouts, dead links)
        print(f"  failed: {url}  ({e})", flush=True)
    return None


def save(urls: list[str], known: dict[str, str]) -> int:
    kept = {u: known[u] for u in urls if u in known}                    # links no longer in the curriculum drop out
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return len(kept)


def main() -> None:
    """One link at a time with a pause between them: the docs site turns away anything faster. Progress is saved as it
    goes, so a stopped run picks up where it left off."""
    refresh = "--refresh" in sys.argv
    known: dict[str, str] = {} if refresh or not OUT.exists() else json.loads(OUT.read_text(encoding="utf-8"))
    urls = curriculum_urls()
    todo = [u for u in urls if u not in known]
    print(f"{len(urls)} links in the curriculum, {len(todo)} to fetch", flush=True)
    pause, i = PAUSE, 0
    while i < len(todo):
        try:
            if (t := title_of(todo[i])):
                known[todo[i]] = t
            i += 1
            pause = PAUSE
        except Throttled:
            pause = min(max(pause * 2, 60), 300)                         # back off, then try the same link again
            print(f"  slowing down: waiting {pause:.0f}s  ({save(urls, known)} titles saved)", flush=True)
        if i and i % 25 == 0:
            print(f"  {i}/{len(todo)}  ({save(urls, known)} titles saved)", flush=True)
        time.sleep(pause)
    print(f"{save(urls, known)}/{len(urls)} titles -> {OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
