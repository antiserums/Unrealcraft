"use client";
import { createContext, useContext, useMemo, type ReactNode } from "react";
import { type Dict, type Locale, type TFn, makeT } from "@/lib/i18n-config";

const Ctx = createContext<{ locale: Locale; t: TFn }>({ locale: "en", t: (s, v) => makeT({})(s, v) });

/** Hands the current dictionary to client components. The layout renders it once with the visitor's language. */
export function I18nProvider({ locale, dict, children }: { locale: Locale; dict: Dict; children: ReactNode }) {
  const value = useMemo(() => ({ locale, t: makeT(dict) }), [locale, dict]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

/** For client components: `const t = useT();` then `t("Save")` or `t("{n} quests", { n })`. */
export function useT(): TFn {
  return useContext(Ctx).t;
}

export function useLocale(): Locale {
  return useContext(Ctx).locale;
}
