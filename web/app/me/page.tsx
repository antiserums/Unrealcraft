import { redirect } from "next/navigation";
import CardStudio from "@/components/CardStudio";
import type { ArtProps, Char } from "@/components/CharacterSheet";
import MeNav from "@/components/MeNav";
import { badgeImage, decorationImages, iconImage, loadManifest, presetSheet, presetSheets } from "@/lib/art";
import { api, type Card } from "@/lib/api";

export const metadata = { title: "Player card" };

export default async function Profile() {
  const [c, ch, manifest] = await Promise.all([api<Card>("/me/card"), api<Char>("/me/character"), loadManifest()]);
  if (!c) redirect("/api/auth/discord?next=/me");
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.earned_achievements.map((a) => [a.key, badgeImage(manifest, a.badge)]));
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
      <div className="eyebrow">Profile</div>
      <h1>{c.name}</h1>
      <MeNav active="/me" />
      {c.known === false && <div className="note small" style={{ marginBottom: 12 }}>The Quartermaster has not seen you yet. Press <b>Start Questing</b> in #welcome on Discord to begin Orientation.</div>}
      <CardStudio initial={c} sheet={sheet} badges={badges} deco={decorationImages(manifest)} shareUrl={shareUrl} wardrobe={wardrobe} />
      {c.next_rank && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="eyebrow">Next rank: {c.next_rank.title}</div>
          <ul className="plain small" style={{ marginTop: 6 }}>
            <li>{c.next_rank.xp_to_go} XP to go</li>
            <li>{c.next_rank.required_left > 0 ? `${c.next_rank.required_left} required quests left` : "Core path done"}</li>
            {c.tier_progress && <li>{c.tier_progress.emoji} {c.tier_progress.name} quests: {c.tier_progress.done}/{c.tier_progress.need}</li>}
            {c.next_rank.human_review && <li>Staff approval needed for this rank</li>}
          </ul>
        </div>
      )}
    </>
  );
}
