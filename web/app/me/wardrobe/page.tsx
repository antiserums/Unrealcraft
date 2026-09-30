import { redirect } from "next/navigation";
import CharacterSheet, { type ArtProps, type Char } from "@/components/CharacterSheet";
import MeNav from "@/components/MeNav";
import { iconImage, loadManifest, presetSheets } from "@/lib/art";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";

export async function generateMetadata() { const t = await getT(); return { title: t("Wardrobe") }; }

export default async function Wardrobe() {
  const t = await getT();
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/me/wardrobe");
  const [ch, manifest] = await Promise.all([api<Char>("/me/character"), loadManifest()]);
  if (!ch) redirect("/me");
  const bodies = manifest?.appearance.body ?? [];
  const sheets: ArtProps["sheets"] = {};
  for (const b of bodies) {
    sheets[b] = {};
    for (const s of ch.styles) sheets[b][s] = presetSheets(manifest, b, s);
  }
  const art: ArtProps = {
    sheets, bodies,
    icons: Object.fromEntries(ch.outfits.map((o) => [o.art_id, iconImage(manifest, o.art_id)]).filter(([, v]) => v) as [string, string][]),
  };
  return (
    <>
      <div className="eyebrow">{t("Profile")}</div>
      <h1>{t("Wardrobe")}</h1>
      <MeNav active="/me/wardrobe" />
      <CharacterSheet initial={ch} fallbackColor={ch.cosmetics.nameplate ?? me.rank_color} art={art} />
    </>
  );
}
