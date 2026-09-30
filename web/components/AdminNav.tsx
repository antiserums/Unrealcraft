import Link from "next/link";
import { api, type Me } from "@/lib/api";

/** The admin panel's sections. Admins and developers see everything; mentors see only the review inbox and
 *  the tickets. The API enforces the same split, this only hides the tabs. */
const ADMIN_TABS = [["/admin", "Members"], ["/admin/quests", "Quests"], ["/admin/entitlements", "Entitlements"]] as const;
const STAFF_TABS = [["/admin/review", "Review inbox"], ["/admin/tickets", "Tickets"]] as const;

export default async function AdminNav({ active }: { active: string }) {
  const me = await api<Me>("/me");
  const tabs = me?.admin ? [...ADMIN_TABS, ...STAFF_TABS] : [...STAFF_TABS];
  return (
    <nav className="subnav" aria-label="Admin sections">
      {tabs.map(([href, label]) => <Link key={href} href={href} className={href === active ? "on" : ""}>{label}{href === "/admin/review" && me?.review?.pending ? ` (${me.review.pending})` : ""}</Link>)}
    </nav>
  );
}
