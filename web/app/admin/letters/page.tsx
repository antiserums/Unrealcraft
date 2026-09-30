import AdminNav from "@/components/AdminNav";
import { Compose, SentList, type Letter } from "@/components/Letters";
import { PageHeader } from "@/components/SiteArt";
import { api } from "@/lib/api";

export const metadata = { title: "Mail" };

/** Admins write announcements and letters here and see what was sent and how many opened it. */
export default async function AdminLetters() {
  const data = await api<{ letters: (Letter & { reads: number; name?: string | null })[] }>("/admin/letters");
  if (!data) return <><h1>Letters</h1><div className="card">Admins and developers only.</div></>;
  return (
    <>
      <PageHeader art="header-admin" eyebrow="Staff" title="Mail" />
      <AdminNav active="/admin/letters" />
      <div className="section-h"><h2>Write mail</h2><span className="muted small">to everyone, to staff, or to one member</span></div>
      <div className="card"><Compose /></div>
      <div className="section-h"><h2>Sent</h2><span className="muted small">{data.letters.length} letters</span></div>
      <div className="card"><SentList letters={data.letters} /></div>
    </>
  );
}
