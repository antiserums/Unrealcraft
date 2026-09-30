import Link from "next/link";

const TABS = [["/me", "Player card"], ["/me/achievements", "Achievements"]] as const;

export default function MeNav({ active }: { active: string }) {
  return (
    <nav className="subnav" aria-label="Profile sections">
      {TABS.map(([href, label]) => <Link key={href} href={href} className={href === active ? "on" : ""}>{label}</Link>)}
    </nav>
  );
}
