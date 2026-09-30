import Link from "next/link";
import AdminNav from "@/components/AdminNav";
import { PageHeader } from "@/components/SiteArt";
import { TicketRow } from "@/components/Tickets";
import type { Ticket } from "@/lib/tickets";
import { api } from "@/lib/api";

export const metadata = { title: "Tickets" };

/** Every support ticket, for staff. Open ones first by default; the filter shows one status. */
export default async function AdminTickets({ searchParams }: PageProps<"/admin/tickets">) {
  const { status } = await searchParams;
  const s = typeof status === "string" && ["open", "answered", "closed"].includes(status) ? status : "";
  const data = await api<{ tickets: Ticket[]; open: number }>(`/admin/tickets${s ? `?status=${s}` : ""}`);
  if (!data) return <><h1>Tickets</h1><div className="card">Staff only.</div></>;
  const rows = s ? data.tickets : [...data.tickets].sort((a, b) => (a.status === "open" ? 0 : 1) - (b.status === "open" ? 0 : 1));
  return (
    <>
      <PageHeader art="header-admin" eyebrow="Staff" title="Support tickets" />
      <AdminNav active="/admin/tickets" />
      <div className="row" style={{ marginBottom: 14 }}>
        {[["", "All"], ["open", "Open"], ["answered", "Answered"], ["closed", "Closed"]].map(([k, label]) => (
          <Link key={k} href={`/admin/tickets${k ? `?status=${k}` : ""}`} className={`btn ${s === k ? "primary" : ""}`}>{label}{k === "open" && data.open ? ` (${data.open})` : ""}</Link>
        ))}
      </div>
      {rows.length === 0 ? <div className="card muted">Nothing here.</div> : <div className="grid">{rows.map((tk) => <TicketRow key={tk.id} tk={tk} href={`/admin/tickets/${tk.id}`} />)}</div>}
    </>
  );
}
