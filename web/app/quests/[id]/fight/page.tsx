import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import FightScreen from "@/components/Fight";
import { api, type Me, type QuestFull } from "@/lib/api";
import { arenaBackground, creatureSheet, loadManifest, presetSheet } from "@/lib/art";

type Char = { worn: { id: string; art_id: string }; style: string; body: string; cosmetics: { nameplate?: string } };

export default async function FightPage({ params }: PageProps<"/quests/[id]/fight">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/quests/${id}/fight`);
  const [data, ch, boss, manifest] = await Promise.all([
    api<{ quest: QuestFull }>(`/catalog/quests/${id}`), api<Char>("/me/character"), api<{ creature: string }>(`/catalog/quests/${id}/boss`), loadManifest(),
  ]);
  if (!data) notFound();
  const heroSheet = ch ? presetSheet(manifest, ch.body, ch.worn.art_id, ch.style) : null;
  const bossSheet = boss ? creatureSheet(manifest, boss.creature) : null;
  return (
    <>
      <div className="eyebrow"><Link href={`/quests/${id}`}>← {id} · {data.quest.title}</Link></div>
      <h1>Boss fight</h1>
      <FightScreen questId={id} outfit={ch?.worn.id ?? "novice"} weaponStyle={ch?.style ?? "melee"} heroSheet={heroSheet} bossSheet={bossSheet}
        background={arenaBackground(manifest)} color={ch?.cosmetics?.nameplate ?? me.rank_color} />
    </>
  );
}
