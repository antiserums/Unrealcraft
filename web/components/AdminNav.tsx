import Link from "next/link";

const TABS = [["/admin", "Members"], ["/admin/quests", "Quests"], ["/admin/entitlements", "Entitlements"], ["/review", "Review inbox"]] as const;

/** The admin panel's sections. */
export default function AdminNav({ active }: { active: string }) {
  return (
    <nav className="subnav" aria-label="Admin sections">
      {TABS.map(([href, label]) => <Link key={href} href={href} className={href === active ? "on" : ""}>{label}</Link>)}
    </nav>
  );
}
