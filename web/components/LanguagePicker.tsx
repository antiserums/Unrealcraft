"use client";
import { useRouter } from "next/navigation";
import { LOCALES, LOCALE_COOKIE } from "@/lib/i18n-config";
import { useLocale, useT } from "./I18n";

/** The language menu in the footer. The choice is a cookie, so the server renders the next page in that language. */
export default function LanguagePicker() {
  const router = useRouter();
  const locale = useLocale();
  const t = useT();
  function pick(code: string) {
    document.cookie = `${LOCALE_COOKIE}=${code}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`;
    router.refresh();
  }
  return (
    <label className="lang-picker">
      <span aria-hidden="true">🌐</span>
      <span className="sr-only">{t("Language")}</span>
      <select value={locale} onChange={(e) => pick(e.target.value)} aria-label={t("Language")}>
        {LOCALES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
      </select>
    </label>
  );
}
