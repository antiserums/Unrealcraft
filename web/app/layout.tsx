import type { Metadata } from "next";
import { IBM_Plex_Sans, Sora } from "next/font/google";
import Nav from "@/components/Nav";
import "./globals.css";

const plex = IBM_Plex_Sans({ variable: "--font-plex", subsets: ["latin"], weight: ["400", "500", "600"] });
const sora = Sora({ variable: "--font-sora", subsets: ["latin"], weight: ["600", "700"] });

export const metadata: Metadata = {
  title: { default: "Unrealcraft", template: "%s · Unrealcraft" },
  description: "Learn Unreal Engine 5 by doing quests. Read, build, pass the quiz, show your work.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plex.variable} ${sora.variable}`}>
      <body>
        <Nav />
        <main className="wrap">{children}</main>
      </body>
    </html>
  );
}
