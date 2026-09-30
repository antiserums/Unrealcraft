import { redirect } from "next/navigation";
import CharacterSheet, { type ArtProps, type Char } from "@/components/CharacterSheet";
import MeNav from "@/components/MeNav";
import { characterLayers, iconImage, loadManifest } from "@/lib/art";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Wardrobe" };

export default async function Wardrobe() {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/me/wardrobe");
  const [ch, manifest] = await Promise.all([api<Char>("/me/character"), loadManifest()]);
  if (!ch) redirect("/me");
  const art: ArtProps = {
    layers: characterLayers(manifest, ch.cosmetics.appearance?.body ?? "body-a", [ch.worn.art_id]),
    icons: Object.fromEntries(ch.outfits.map((o) => [o.art_id, iconImage(manifest, o.art_id)]).filter(([, v]) => v) as [string, string][]),
    appearance: manifest?.appearance ?? {},
  };
  return (
    <>
      <div className="eyebrow">Profile</div>
      <h1>Wardrobe</h1>
      <MeNav active="/me/wardrobe" />
      <p className="muted">Your look and your outfits. Outfits are rewards for quests, ranks and achievements. They change nothing but how you look.</p>
      <CharacterSheet initial={ch} fallbackColor={ch.cosmetics.nameplate ?? me.rank_color} art={art} />
    </>
  );
}
