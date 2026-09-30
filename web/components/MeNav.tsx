import Link from "next/link";
import { getT } from "@/lib/i18n";
import Ico from "./Ico";

const TABS = [["/me", "Player card", "player-card"], ["/me/achievements", "Achievements", "achievements"], ["/letters", "Letters", "mission-scroll"]] as const;

export default async function MeNav({ active }: { active: string }) {
  const t = await getT();
  return (
    <nav className="subnav" aria-label={t("Profile sections")}>
      {TABS.map(([href, label, icon]) => <Link key={href} href={href} className={href === active ? "on" : ""}><Ico group="navigation" id={icon} />{t(label)}</Link>)}
    </nav>
  );
}
