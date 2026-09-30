import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { TicketThread } from "@/components/Tickets";
import { CATEGORY, STATUS, type Ticket } from "@/lib/tickets";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";

export async function generateMetadata({ params }: PageProps<"/support/[id]">) {
  const { id } = await params;
  const t = await getT();
  return { title: `${t("Ticket")} #${id}` };
}

export default async function TicketPage({ params }: PageProps<"/support/[id]">) {
  const t = await getT();
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/support/${id}`);
  const tk = await api<Ticket>(`/me/tickets/${id}`);
  if (!tk) notFound();
  return (
    <>
      <div className="eyebrow"><Link href="/support">← {t("Support")}</Link></div>
      <h1>#{tk.id} · {tk.subject}</h1>
      <p className="muted small">{t(CATEGORY[tk.category] ?? tk.category)} · {t(STATUS[tk.status])} · {t("opened {date}", { date: tk.created_at.slice(0, 10) })}</p>
      <TicketThread ticket={tk} />
    </>
  );
}
