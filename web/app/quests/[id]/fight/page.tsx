import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import FightScreen from "@/components/Fight";
import type { GearMap } from "@/components/Figure";
import { api, type Me, type QuestFull } from "@/lib/api";
import { characterLayers, creatureImage, loadManifest } from "@/lib/art";

type Char = { equipped: Record<string, { rarity: string; art_id?: string; item_key: string; slot: string }>; cosmetics: { nameplate?: string; appearance?: Record<string, string> } };

export default async function FightPage({ params }: PageProps<"/quests/[id]/fight">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/quests/${id}/fight`);
  const [data, ch, boss, manifest] = await Promise.all([
    api<{ quest: QuestFull }>(`/catalog/quests/${id}`), api<Char>("/me/character"), api<{ creature: string }>(`/catalog/quests/${id}/boss`), loadManifest(),
  ]);
  if (!data) notFound();
  const equipped = Object.values(ch?.equipped ?? {});
  const gear: GearMap = Object.fromEntries(equipped.map((v) => [v.slot, { rarity: v.rarity }]));
  const body = ch?.cosmetics?.appearance?.body ?? "body-a";
  const layers = characterLayers(manifest, body, equipped.map((v) => v.art_id ?? `gear_${v.item_key.split(":")[0]}_${v.slot}`));
  const bossImage = boss ? creatureImage(manifest, boss.creature) : null;
  return (
    <>
      <div className="eyebrow"><Link href={`/quests/${id}`}>← {id} · {data.quest.title}</Link></div>
      <h1>Boss fight</h1>
      <FightScreen questId={id} gear={gear} layers={layers} bossImage={bossImage} color={ch?.cosmetics?.nameplate ?? me.rank_color} />
    </>
  );
}
