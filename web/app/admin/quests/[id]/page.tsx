import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import AdminNav from "@/components/AdminNav";
import QuestEditor from "@/components/QuestEditor";
import type { Curriculum } from "@/components/QuestList";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Admin · Quest" };

type Loaded = { quest: Record<string, unknown>; file: string; yaml: string };

export default async function AdminQuest({ params }: PageProps<"/admin/quests/[id]">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/admin/quests/${id}`);
  const cur = await api<Curriculum>("/admin/curriculum");
  if (!cur) return <><h1>Quest</h1><div className="card">Admins and developers only.</div></>;
  const isNew = id === "new";
  const loaded = isNew ? null : await api<Loaded>(`/admin/curriculum/quests/${id}`);
  if (!isNew && !loaded) notFound();
  return (
    <>
      <div className="eyebrow"><Link href="/admin/quests">← Quests</Link></div>
      <h1>{isNew ? "New quest" : `${id} · ${String(loaded!.quest.title ?? "")}`}</h1>
      <AdminNav active="/admin/quests" />
      <QuestEditor cur={cur} initial={loaded?.quest ?? null} file={loaded?.file ?? cur.default_file} yamlText={loaded?.yaml ?? null} />
    </>
  );
}
