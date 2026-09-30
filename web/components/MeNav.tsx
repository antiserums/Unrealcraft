import Link from "next/link";
import { getT } from "@/lib/i18n";

const TABS = [["/me", "Player card"], ["/me/achievements", "Achievements"]] as const;

export default async function MeNav({ active }: { active: string }) {
  const t = await getT();
  return (
    <nav className="subnav" aria-label={t("Profile sections")}>
      {TABS.map(([href, label]) => <Link key={href} href={href} className={href === active ? "on" : ""}>{t(label)}</Link>)}
    </nav>
  );
}
