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
  const body = ch.cosmetics.appearance?.body ?? "body-a";
  const art: ArtProps = {
    layersBy: Object.fromEntries(ch.outfits.map((o) => [o.art_id, characterLayers(manifest, body, [o.art_id])]).filter(([, v]) => v) as [string, string[]][]),
    icons: Object.fromEntries(ch.outfits.map((o) => [o.art_id, iconImage(manifest, o.art_id)]).filter(([, v]) => v) as [string, string][]),
    appearance: manifest?.appearance ?? {},
  };
  return (
    <>
      <div className="eyebrow">Profile</div>
      <h1>Wardrobe</h1>
      <MeNav active="/me/wardrobe" />
      <CharacterSheet initial={ch} fallbackColor={ch.cosmetics.nameplate ?? me.rank_color} art={art} />
    </>
  );
}
