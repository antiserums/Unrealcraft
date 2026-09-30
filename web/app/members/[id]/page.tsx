import Link from "next/link";
import { notFound } from "next/navigation";
import PlayerCard from "@/components/PlayerCard";
import { characterLayers, loadManifest } from "@/lib/art";
import { api, type Card } from "@/lib/api";

export default async function Member({ params }: PageProps<"/members/[id]">) {
  const { id } = await params;
  const [c, manifest] = await Promise.all([api<Card>(`/members/${id}`), loadManifest()]);
  if (!c) notFound();      // unknown member, or a private card seen while logged out
  const layers = characterLayers(manifest, c.cosmetics.appearance?.body ?? "body-a", [c.worn.art_id]);
  return (
    <>
      <div className="eyebrow">Player card</div>
      <h1>{c.name ?? "A guild member"}</h1>
      <div className="two">
        <PlayerCard c={c} layers={layers} />
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
