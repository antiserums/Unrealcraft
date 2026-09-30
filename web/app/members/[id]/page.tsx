import Link from "next/link";
import { notFound } from "next/navigation";
import PlayerCard from "@/components/PlayerCard";
import { badgeImage, loadManifest, presetSheet } from "@/lib/art";
import { api, type Card } from "@/lib/api";

export default async function Member({ params }: PageProps<"/members/[id]">) {
  const { id } = await params;
  const [c, manifest] = await Promise.all([api<Card>(`/members/${id}`), loadManifest()]);
  if (!c) notFound();      // unknown member, or a private card seen while logged out
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.featured.map((a) => [a.key, badgeImage(manifest, a.badge)]));
  return (
    <>
      <div className="eyebrow">Player card</div>
      <h1>{c.name ?? "A guild member"}</h1>
      <div className="two">
        <PlayerCard c={c} sheet={sheet} badges={badges} />
        <div>
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
