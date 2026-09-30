"""Localization helper for the website.

Collects every English sentence the site translates: literal `t("…")` / `t('…')` calls in web/app, web/components
and web/lib, plus the data strings listed in web/locales/data-keys.ts. Writes them to web/locales/en.json (the
source list, English = English) and reports, per language, which keys are missing and which are no longer used.

    py -3 tools/i18n_extract.py            # rebuild en.json and print the report
    py -3 tools/i18n_extract.py --prune    # also drop unused keys from every language file
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web"
LOCALES = WEB / "locales"
CALL = re.compile(r"""\bt\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|`((?:[^`\\$]|\\.)*)`)""")
DATA = re.compile(r'"((?:[^"\\]|\\.)*)"')


def unescape(s: str) -> str:
    return json.loads('"' + s.replace('\\"', '"').replace('"', '\\"').replace("\\'", "'") + '"')


def keys() -> list[str]:
    found: dict[str, None] = {}
    for folder in ("app", "components", "lib"):
        for f in sorted((WEB / folder).rglob("*.ts*")):
            for m in CALL.finditer(f.read_text(encoding="utf-8")):
                raw = next(g for g in m.groups() if g is not None)
                found[unescape(raw)] = None
    body = (LOCALES / "data-keys.ts").read_text(encoding="utf-8")
    body = body[body.index("export const DATA_KEYS"):]
    for m in DATA.finditer(re.sub(r"//.*", "", body)):
        found[unescape(m.group(1))] = None
    return list(found)


def main() -> None:
    ks = keys()
    (LOCALES / "en.json").write_text(json.dumps({k: k for k in ks}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(ks)} keys -> web/locales/en.json")
    for f in sorted(LOCALES.glob("*.json")):
        if f.name == "en.json" or f.name.startswith("_") or f.name.endswith("-missing.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8") or "{}")
        missing = [k for k in ks if not d.get(k)]
        unused = [k for k in d if k not in ks]
        if "--prune" in sys.argv and unused:
            d = {k: v for k, v in d.items() if k in ks}
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"{f.stem}: {len(ks) - len(missing)}/{len(ks)} translated, {len(missing)} missing, {len(unused)} unused")


if __name__ == "__main__":
    main()
