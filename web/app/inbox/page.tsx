import { redirect } from "next/navigation";
import Letters, { type Letter } from "@/components/Letters";
import { PageHeader, Spot } from "@/components/SiteArt";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";
import type { Ticket } from "@/lib/tickets";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Inbox") };
}

/** The inbox: announcements, letters from staff, the site's own notes (reviews, ranks), and the member's tickets,
 *  which are read and answered right here. `?ticket=ID` or `?mail=ID` opens one straight away. */
export default async function InboxPage({ searchParams }: PageProps<"/inbox">) {
  const t = await getT();
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/inbox");
  const sp = await searchParams;
  const [data, tk] = await Promise.all([api<{ letters: Letter[]; unread: number }>("/me/letters"), api<{ tickets: Ticket[] }>("/me/tickets")]);
  const letters = data?.letters ?? [];
  const tickets = tk?.tickets ?? [];
  const openTicket = typeof sp.ticket === "string" && /^\d+$/.test(sp.ticket) ? Number(sp.ticket) : null;
  const openMail = typeof sp.mail === "string" && /^\d+$/.test(sp.mail) ? Number(sp.mail) : null;
  return (
    <>
      <PageHeader art="header-player" eyebrow={t("Profile")} title={t("Inbox")} />
      {letters.length === 0 && tickets.length === 0
        ? <Spot art="sleeping-dragon">{t("No mail yet. Announcements, answers to your tickets, review results and rank-ups will land here.")}</Spot>
        : <Letters letters={letters} tickets={tickets} openTicket={openTicket} openMail={openMail} />}
    </>
  );
}
