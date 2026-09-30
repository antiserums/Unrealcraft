import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import FightScreen from "@/components/Fight";
import type { GearMap } from "@/components/Figure";
import { api, type Me, type QuestFull } from "@/lib/api";

type Char = { equipped: Record<string, { rarity: string }>; cosmetics: { nameplate?: string } };

export default async function FightPage({ params }: PageProps<"/quests/[id]/fight">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/quests/${id}/fight`);
  const [data, ch] = await Promise.all([api<{ quest: QuestFull }>(`/catalog/quests/${id}`), api<Char>("/me/character")]);
  if (!data) notFound();
  const gear: GearMap = Object.fromEntries(Object.entries(ch?.equipped ?? {}).map(([k, v]) => [k, { rarity: v.rarity }]));
  return (
    <>
      <div className="eyebrow"><Link href={`/quests/${id}`}>← {id} · {data.quest.title}</Link></div>
      <h1>Boss fight</h1>
      <FightScreen questId={id} gear={gear} color={ch?.cosmetics?.nameplate ?? me.rank_color} />
    </>
  );
}
