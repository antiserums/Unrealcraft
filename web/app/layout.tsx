import type { Metadata } from "next";
import { Cinzel, Cinzel_Decorative, IBM_Plex_Sans } from "next/font/google";
import Nav from "@/components/Nav";
import "./globals.css";

const plex = IBM_Plex_Sans({ variable: "--font-plex", subsets: ["latin"], weight: ["400", "500", "600"] });
const cinzel = Cinzel({ variable: "--font-cinzel", subsets: ["latin"], weight: ["600", "700"] });
const cinzelDeco = Cinzel_Decorative({ variable: "--font-cinzel-deco", subsets: ["latin"], weight: ["700"] });

export const metadata: Metadata = {
  title: { default: "Unrealcraft", template: "%s · Unrealcraft" },
  description: "Learn Unreal Engine 5 by doing quests. Read, build, pass the quiz, show your work.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plex.variable} ${cinzel.variable} ${cinzelDeco.variable}`}>
      <body>
        <Nav />
        <div className="banner" aria-hidden="true"><span className="crest">❖</span></div>
        <main className="wrap tome">{children}</main>
        <footer className="foot">
          <span className="rule" /><span className="crest">❖</span><span className="rule" />
          <div className="small muted">Unrealcraft · a learning guild for Unreal Engine 5 · ranks come only from quests</div>
        </footer>
      </body>
    </html>
  );
}
