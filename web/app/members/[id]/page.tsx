import Link from "next/link";
import { notFound } from "next/navigation";
import PlayerCard from "@/components/PlayerCard";
import { achievementBadge, decorationImage, loadManifest, presetSheet } from "@/lib/art";
import { CardDeco } from "@/components/DecoAnim";
import { api, type Card } from "@/lib/api";
import { getT } from "@/lib/i18n";

export default async function Member({ params }: PageProps<"/members/[id]">) {
  const { id } = await params;
  const t = await getT();
  const [c, manifest] = await Promise.all([api<Card>(`/members/${id}`), loadManifest()]);
  if (!c) notFound();      // unknown member, or a private card seen while logged out
  const sheet = presetSheet(manifest, c.body, c.worn.art_id, c.style);
  const badges = Object.fromEntries(c.featured.map((a) => [a.key, achievementBadge(manifest, a)]));
  const deco = { avatar: decorationImage(manifest, "avatar", c.avatar_frame_art ?? undefined), card: decorationImage(manifest, "card", c.card_frame_art ?? undefined) };
  return (
    <>
      <div className="eyebrow">{t("Player card")}</div>
      <h1>{c.name ?? t("A guild member")}{c.title && <span className="muted" style={{ fontWeight: 400 }}>, {t(c.title)}</span>}</h1>
      <div className="studio">
        <div className={`studio-card ${deco.card ? "framed" : ""}`}>
          <CardDeco src={deco.card} theme={c.card_frame} />
          <PlayerCard c={c} sheet={sheet} badges={badges} deco={{ avatar: deco.avatar, card: null, avatarTheme: c.avatar_frame }} />
        </div>
        <div className="studio-panel">
          {c.mine ? (
            <div className="card"><p className="small muted" style={{ margin: 0 }}>{t("This is how others see your card.")}</p><Link className="btn" href="/me" style={{ marginTop: 10 }}>{t("Edit it")}</Link></div>
          ) : (
            <div className="card"><p className="small muted" style={{ margin: 0 }}>{c.public ? t("This member shares their card with anyone who has the link.") : t("Only guild members can see this card.")}</p></div>
          )}
        </div>
      </div>
    </>
  );
}
