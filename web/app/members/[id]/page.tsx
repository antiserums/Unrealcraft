import Link from "next/link";
import { notFound } from "next/navigation";
import PlayerCard from "@/components/PlayerCard";
import { badgeImage, decorationImage, loadManifest, presetSheet } from "@/lib/art";
import { api, type Card } from "@/lib/api";

export default async function Member({ params }: PageProps<"/members/[id]">) {
  const { id } = await params;
  const [c, manifest] = await Promise.all([api<Card>(`/members/${id}`), loadManifest()]);
  if (!c) notFound();      // unknown member, or a private card seen while logged out
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.featured.map((a) => [a.key, badgeImage(manifest, a.badge)]));
  const deco = { avatar: decorationImage(manifest, "avatar", c.avatar_frame), card: decorationImage(manifest, "card", c.card_frame) };
  return (
    <>
      <div className="eyebrow">Player card</div>
      <h1>{c.name ?? "A guild member"}</h1>
      <div className="studio">
        <div className="studio-card">
          {deco.card && <div className="px pcard-deco" style={{ borderImageSource: `url("${deco.card}")` }} aria-hidden="true" />}
          <PlayerCard c={c} sheet={sheet} badges={badges} deco={{ avatar: deco.avatar, card: null }} />
        </div>
        <div className="studio-panel">
          {c.mine ? (
            <div className="card"><p className="small muted" style={{ margin: 0 }}>This is how others see your card.</p><Link className="btn" href="/me" style={{ marginTop: 10 }}>Edit it</Link></div>
          ) : (
            <div className="card"><p className="small muted" style={{ margin: 0 }}>{c.public ? "This member shares their card with anyone who has the link." : "Only guild members can see this card."}</p></div>
          )}
        </div>
      </div>
    </>
  );
}
