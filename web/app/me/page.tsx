import { redirect } from "next/navigation";
import CardStudio from "@/components/CardStudio";
import MeNav from "@/components/MeNav";
import { badgeImage, decorationImages, loadManifest, presetSheet } from "@/lib/art";
import { api, type Card } from "@/lib/api";

export const metadata = { title: "Player card" };

export default async function Profile() {
  const [c, manifest] = await Promise.all([api<Card>("/me/card"), loadManifest()]);
  if (!c) redirect("/api/auth/discord?next=/me");
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.earned_achievements.map((a) => [a.key, badgeImage(manifest, a.badge)]));
  const shareUrl = `${process.env.WEB_ORIGIN ?? "http://localhost:3000"}/members/${c.id}`;
  return (
    <>
      <div className="eyebrow">Profile</div>
      <h1>{c.name}</h1>
      <MeNav active="/me" />
      {c.known === false && <div className="note small" style={{ marginBottom: 12 }}>The Quartermaster has not seen you yet. Press <b>Start Questing</b> in #welcome on Discord to begin Orientation.</div>}
      <CardStudio initial={c} sheet={sheet} badges={badges} deco={decorationImages(manifest)} shareUrl={shareUrl} />
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
