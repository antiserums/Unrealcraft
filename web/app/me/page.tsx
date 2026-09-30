import { redirect } from "next/navigation";
import CardStudio from "@/components/CardStudio";
import type { ArtProps, Char } from "@/components/CharacterSheet";
import MeNav from "@/components/MeNav";
import SpecializationPicker from "@/components/SpecializationPicker";
import { achievementBadge, decorationImages, iconImage, loadManifest, presetSheet, presetSheets } from "@/lib/art";
import { api, type Card } from "@/lib/api";
import { getT } from "@/lib/i18n";

export async function generateMetadata() { const t = await getT(); return { title: t("Player card") }; }

export default async function Profile() {
  const t = await getT();
  const [c, ch, manifest] = await Promise.all([api<Card>("/me/card"), api<Char>("/me/character"), loadManifest()]);
  if (!c) redirect("/api/auth/discord?next=/me");
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.earned_achievements.map((a) => [a.key, achievementBadge(manifest, a)]));
  const shareUrl = `${process.env.WEB_ORIGIN ?? "http://localhost:3000"}/members/${c.id}`;
  let wardrobe: { char: Char; art: ArtProps } | null = null;
  if (ch) {
    const bodies = manifest?.appearance.body ?? [];
    const sheets: ArtProps["sheets"] = {};
    for (const b of bodies) { sheets[b] = {}; for (const s of ch.styles) sheets[b][s] = presetSheets(manifest, b, s); }
    wardrobe = { char: ch, art: { sheets, bodies, icons: Object.fromEntries(ch.outfits.map((o) => [o.art_id, iconImage(manifest, o.art_id)]).filter(([, v]) => v) as [string, string][]) } };
  }
  return (
    <>
      <div className="eyebrow">{t("Profile")}</div>
      <h1>{c.name}{c.title && <span className="muted" style={{ fontWeight: 400 }}>, {t(c.title)}</span>}</h1>
      <MeNav active="/me" />
      <CardStudio initial={c} sheet={sheet} badges={badges} deco={decorationImages(manifest)} shareUrl={shareUrl} wardrobe={wardrobe} />
      <SpecializationPicker mine={c.specializations} options={c.specialization_options ?? []} />
      {c.next_rank && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="eyebrow">{t("Next rank: {rank}", { rank: t(c.next_rank.title) })}</div>
          <ul className="plain small" style={{ marginTop: 6 }}>
            <li>{t("{xp} XP to go", { xp: c.next_rank.xp_to_go })}</li>
            <li>{c.next_rank.required_left > 0 ? t("{n} required quests left", { n: c.next_rank.required_left }) : t("Core path done")}</li>
            {c.tier_progress && <li>{c.tier_progress.emoji} {t("{tier} quests: {done}/{need}", { tier: t(c.tier_progress.name), done: c.tier_progress.done, need: c.tier_progress.need })}</li>}
            {c.next_rank.human_review && <li>{t("Staff approval needed for this rank")}</li>}
          </ul>
        </div>
      )}
    </>
  );
}
