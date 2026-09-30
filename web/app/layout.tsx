import type { Metadata } from "next";
import { Cinzel, Cinzel_Decorative, IBM_Plex_Sans } from "next/font/google";
import Foot from "@/components/Foot";
import { I18nProvider } from "@/components/I18n";
import Nav from "@/components/Nav";
import { loadManifest, siteArt } from "@/lib/art";
import { getDict, getLocale, getT } from "@/lib/i18n";
import { LOCALES } from "@/lib/i18n-config";
import "./globals.css";

// Latin, extended Latin and Cyrillic come from the web fonts; other scripts fall back to the system's own fonts.
const plex = IBM_Plex_Sans({ variable: "--font-plex", subsets: ["latin", "latin-ext", "cyrillic"], weight: ["400", "500", "600"] });
const cinzel = Cinzel({ variable: "--font-cinzel", subsets: ["latin", "latin-ext"], weight: ["600", "700"] });
const cinzelDeco = Cinzel_Decorative({ variable: "--font-cinzel-deco", subsets: ["latin"], weight: ["700"] });

export async function generateMetadata(): Promise<Metadata> {
  const [t, m] = await Promise.all([getT(), loadManifest()]);
  const emblem = siteArt(m, "site-emblem/emblem-32");
  return {
    ...(emblem ? { icons: { icon: emblem } } : {}),
    title: { default: "Unrealcraft", template: "%s · Unrealcraft" },
    description: t("An RPG learning experience for Unreal Engine. Every quest is a dungeon: read, build, beat the boss, open the chest."),
  };
}

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const locale = await getLocale();
  const dict = await getDict(locale);
  const dir = LOCALES.find((l) => l.code === locale)?.dir ?? "ltr";
  const siteArtOn = !!(await loadManifest())?.website_art;      // the pack's interface art: see "site-art" in globals.css
  return (
    <html lang={locale} dir={dir} className={`${plex.variable} ${cinzel.variable} ${cinzelDeco.variable} ${siteArtOn ? "site-art" : ""}`}>
      <body>
        <I18nProvider locale={locale} dict={dict}>
          <Nav />
          <div className="banner" aria-hidden="true"><span className="crest">❖</span></div>
          <main className="wrap tome">{children}</main>
          <Foot />
        </I18nProvider>
      </body>
    </html>
  );
}
