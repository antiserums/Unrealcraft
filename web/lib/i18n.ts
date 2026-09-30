import { cookies, headers } from "next/headers";
import { DEFAULT_LOCALE, LOCALE_COOKIE, type Dict, type Locale, type TFn, isLocale, makeT, matchLocale } from "./i18n-config";

/** Server side of localization. The visitor's language is the `uc_lang` cookie (set by the footer picker), else the
 *  browser's Accept-Language, else English. Dictionaries live in web/locales/<code>.json, keyed by the English text. */
const LOADERS: Record<Exclude<Locale, "en">, () => Promise<Dict>> = {
  es: () => import("@/locales/es.json").then((m) => m.default as Dict),
  pt: () => import("@/locales/pt.json").then((m) => m.default as Dict),
  fr: () => import("@/locales/fr.json").then((m) => m.default as Dict),
  de: () => import("@/locales/de.json").then((m) => m.default as Dict),
  it: () => import("@/locales/it.json").then((m) => m.default as Dict),
  pl: () => import("@/locales/pl.json").then((m) => m.default as Dict),
  tr: () => import("@/locales/tr.json").then((m) => m.default as Dict),
  ru: () => import("@/locales/ru.json").then((m) => m.default as Dict),
  ar: () => import("@/locales/ar.json").then((m) => m.default as Dict),
  hi: () => import("@/locales/hi.json").then((m) => m.default as Dict),
  id: () => import("@/locales/id.json").then((m) => m.default as Dict),
  zh: () => import("@/locales/zh.json").then((m) => m.default as Dict),
  ja: () => import("@/locales/ja.json").then((m) => m.default as Dict),
  ko: () => import("@/locales/ko.json").then((m) => m.default as Dict),
};

export async function getLocale(): Promise<Locale> {
  const saved = (await cookies()).get(LOCALE_COOKIE)?.value;
  if (isLocale(saved)) return saved;
  return matchLocale((await headers()).get("accept-language"));
}

export async function getDict(locale?: Locale): Promise<Dict> {
  const l = locale ?? (await getLocale());
  if (l === "en" || l === DEFAULT_LOCALE) return {};          // English is the source text: nothing to look up
  return LOADERS[l]();
}

/** For server components and pages: `const t = await getT();` then `t("Quest board")` or `t("{n} quests", { n })`. */
export async function getT(): Promise<TFn> {
  return makeT(await getDict());
}
