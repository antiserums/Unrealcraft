import { PageHeader } from "@/components/SiteArt";
import { redirect } from "next/navigation";
import AdminNav from "@/components/AdminNav";
import QuestList, { type Curriculum } from "@/components/QuestList";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Admin · Quests" };

export default async function AdminQuests() {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/admin/quests");
  const cur = await api<Curriculum>("/admin/curriculum");
  if (!cur) return <><h1>Quests</h1><div className="card">Admins and developers only.</div></>;
  return (
    <>
      <PageHeader art="header-admin" eyebrow="Staff" title="Quests" />
      <AdminNav active="/admin/quests" />
      <p className="muted small">{cur.quests.length} quests in <code>{cur.dir}</code>. Saving a quest rewrites its YAML file (comments in that file are dropped) and reloads the site&apos;s catalog. The bot needs <code>/admin reload-curriculum</code> on Discord afterwards.</p>
      <QuestList cur={cur} />
    </>
  );
}
