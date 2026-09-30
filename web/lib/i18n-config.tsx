import type { ReactNode } from "react";

/** Languages the site offers. English is the source: every key in the dictionaries IS the English sentence, so a
 *  missing translation falls back to readable English instead of a code. `dir` is the writing direction. */
export const LOCALES = [
  { code: "en", name: "English", dir: "ltr" },
  { code: "es", name: "Español", dir: "ltr" },
  { code: "pt", name: "Português", dir: "ltr" },
  { code: "fr", name: "Français", dir: "ltr" },
  { code: "de", name: "Deutsch", dir: "ltr" },
  { code: "it", name: "Italiano", dir: "ltr" },
  { code: "pl", name: "Polski", dir: "ltr" },
  { code: "tr", name: "Türkçe", dir: "ltr" },
  { code: "ru", name: "Русский", dir: "ltr" },
  { code: "ar", name: "العربية", dir: "rtl" },
  { code: "hi", name: "हिन्दी", dir: "ltr" },
  { code: "id", name: "Bahasa Indonesia", dir: "ltr" },
  { code: "zh", name: "简体中文", dir: "ltr" },
  { code: "ja", name: "日本語", dir: "ltr" },
  { code: "ko", name: "한국어", dir: "ltr" },
] as const;
export type Locale = (typeof LOCALES)[number]["code"];
export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "uc_lang";
export type Dict = Record<string, string>;
export type Vars = Record<string, string | number>;
export type TFn = (text: string, vars?: Vars) => string;

export function isLocale(x: string | undefined | null): x is Locale {
  return !!x && LOCALES.some((l) => l.code === x);
}

/** Best match for an Accept-Language header, e.g. "pt-BR,pt;q=0.9,en;q=0.8" -> "pt". */
export function matchLocale(header: string | null | undefined): Locale {
  for (const part of (header ?? "").split(",")) {
    const base = part.split(";")[0].trim().toLowerCase().split("-")[0];
    if (isLocale(base)) return base;
  }
  return DEFAULT_LOCALE;
}

/** Look the English sentence up in the dictionary and fill `{name}` placeholders. */
export function translate(dict: Dict, text: string, vars?: Vars): string {
  const s = dict[text] ?? text;
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s;
}

export function makeT(dict: Dict): TFn {
  return (text, vars) => translate(dict, text, vars);
}

/** Put React nodes into a translated sentence: rich(t("Read the {link} first."), { link: <a …>…</a> }).
 *  The translator keeps `{link}` where it belongs in their language. */
export function rich(text: string, parts: Record<string, ReactNode>): ReactNode[] {
  return text.split(/(\{\w+\})/g).filter(Boolean).map((chunk, i) => {
    const m = /^\{(\w+)\}$/.exec(chunk);
    return m && m[1] in parts ? <span key={i}>{parts[m[1]]}</span> : chunk;
  });
}
