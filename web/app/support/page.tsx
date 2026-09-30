import Link from "next/link";
import { DISCORD_INVITE, DONATE_URL } from "@/lib/mission";
import { PageHeader, Spot } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Support Unrealcraft") };
}

/** Donations. Nothing on the site is ever paid for; a donation of five dollars or more is thanked with the
 *  Patron set (outfit, avatar frame, card frame). Staff grant the `supporter` medal after a donation, which opens
 *  the whole set. The donation link comes from NEXT_PUBLIC_DONATE_URL. */
export default async function Support() {
  const t = await getT();
  return (
    <>
      <PageHeader art="header-guild" eyebrow="Unrealcraft" title={t("Support Unrealcraft")} />
      <div className="card legal">
        <p className="lead" style={{ maxWidth: "none" }}>{t("Unrealcraft is free and always will be. Nothing here is for sale: not quests, not ranks, not rewards. But the servers, the domain and the art cost money, and if you want to help carry that, you can.")}</p>

        <h2>{t("The Patron set")}</h2>
        <p>{t("Donate five dollars or more, once, and you get the whole Patron set as a thank-you: an outfit, an avatar frame and a player card frame. They are looks only, like every other entitlement, and they are yours for good. It is the same set at five dollars or five hundred, because this is a thank-you, not a shop.")}</p>
        <ul>
          <li>{t("Patron's Regalia: an outfit in deep wine and gold, with the guild's mark on the shoulder.")}</li>
          <li>{t("Patron avatar frame: wine-red enamel and gold, with a small heart at the top.")}</li>
          <li>{t("Patron player card frame: the same enamel and gold around your card.")}</li>
        </ul>

        <h2>{t("How it works")}</h2>
        <ol>
          <li>{t("Donate through the button below. Put your Discord name in the message so we know it is you.")}</li>
          <li>{rich(t("Tell a staff member on the {discord}, or wait: we check donations every few days."), { discord: <a href={DISCORD_INVITE}>{t("Discord server")}</a> })}</li>
          <li>{rich(t("The set appears in your {wardrobe} and in Edit profile as soon as staff mark you as a supporter."), { wardrobe: <Link href="/me/wardrobe">{t("wardrobe")}</Link> })}</li>
        </ol>
        <p className="muted small">{t("Donations are gifts to keep Unrealcraft running. They are not purchases, they are not refundable, and they never affect XP, ranks or reviews.")}</p>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        {DONATE_URL
          ? <a className="btn primary" href={DONATE_URL} target="_blank" rel="noreferrer">{t("Donate")}</a>
          : <span className="btn" aria-disabled="true">{t("Donations open soon")}</span>}
        <Link className="btn" href="/mission">{t("Our mission statement")}</Link>
      </div>
      {!DONATE_URL && <div style={{ marginTop: 14 }}><Spot art="chest-pending">{t("The donation page is not set up yet. Until it is, there is nothing to do here but read.")}</Spot></div>}
    </>
  );
}
