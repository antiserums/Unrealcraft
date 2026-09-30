import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import FightScreen from "@/components/Fight";
import { api, type Me, type QuestFull } from "@/lib/api";
import { characterLayers, creatureImage, loadManifest } from "@/lib/art";

type Char = { worn: { id: string; art_id: string }; cosmetics: { nameplate?: string; appearance?: Record<string, string> } };

export default async function FightPage({ params }: PageProps<"/quests/[id]/fight">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/quests/${id}/fight`);
  const [data, ch, boss, manifest] = await Promise.all([
    api<{ quest: QuestFull }>(`/catalog/quests/${id}`), api<Char>("/me/character"), api<{ creature: string }>(`/catalog/quests/${id}/boss`), loadManifest(),
  ]);
  if (!data) notFound();
  const body = ch?.cosmetics?.appearance?.body ?? "body-a";
  const layers = ch ? characterLayers(manifest, body, [ch.worn.art_id]) : null;
  const bossImage = boss ? creatureImage(manifest, boss.creature) : null;
  return (
    <>
      <div className="eyebrow"><Link href={`/quests/${id}`}>← {id} · {data.quest.title}</Link></div>
      <h1>Boss fight</h1>
      <FightScreen questId={id} outfit={ch?.worn.id ?? "wayfarer"} layers={layers} bossImage={bossImage} color={ch?.cosmetics?.nameplate ?? me.rank_color} />
    </>
  );
}
