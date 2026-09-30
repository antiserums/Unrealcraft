import Link from "next/link";
import { notFound } from "next/navigation";
import { TicketThread } from "@/components/Tickets";
import { CATEGORY, STATUS, type Ticket } from "@/lib/tickets";
import { api } from "@/lib/api";

export async function generateMetadata({ params }: PageProps<"/admin/tickets/[id]">) {
  const { id } = await params;
  return { title: `Ticket #${id}` };
}

export default async function AdminTicket({ params }: PageProps<"/admin/tickets/[id]">) {
  const { id } = await params;
  const tk = await api<Ticket>(`/admin/tickets/${id}`);
  if (!tk) notFound();
  return (
    <>
      <div className="eyebrow"><Link href="/admin/tickets">← Tickets</Link></div>
      <h1>#{tk.id} · {tk.subject}</h1>
      <p className="muted small">
        {CATEGORY[tk.category] ?? tk.category} · {STATUS[tk.status]} · opened {tk.created_at.slice(0, 10)} · from{" "}
        <Link href={`/admin/members/${tk.member_id}`}>{tk.name ?? `member ${tk.member_id}`}</Link>
      </p>
      <TicketThread ticket={tk} staff />
    </>
  );
}
