import Link from "next/link";
import DonateButton from "@/components/DonateButton";
import { PageHeader, Spot } from "@/components/SiteArt";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Donate") };
}

/** Donations. Nothing on the site is ever paid for; a donation of the minimum or more is thanked with the Patron
 *  set (outfit, avatar frame, card frame), granted automatically when Stripe confirms the payment. */
export default async function Donate({ searchParams }: PageProps<"/donate">) {
  const t = await getT();
  const sp = await searchParams;
  const [me, status] = await Promise.all([api<Me>("/me"), api<{ open: boolean; currency: string; minimum: number }>("/donate/status")]);
  const open = !!status?.open;
  const min = status?.minimum ?? 5;
  const unit = (status?.currency ?? "usd").toUpperCase();
  return (
    <>
      <PageHeader art="header-guild" eyebrow="Unrealcraft" title={t("Support Unrealcraft")} />
      {sp.thanks && <div className="note" data-tone="success" style={{ marginBottom: 14 }}>{t("Thank you. Your donation went through, and the Patron set is yours. It shows in your wardrobe and in Edit profile within a minute.")}</div>}
      {sp.cancelled && <div className="note" data-tone="warning" style={{ marginBottom: 14 }}>{t("No payment was made. Come back any time.")}</div>}
      <div className="card legal">
        <p className="lead" style={{ maxWidth: "none" }}>{t("Unrealcraft is free and always will be. Nothing here is for sale: not quests, not ranks, not rewards. But the servers, the domain and the art cost money, and if you want to help carry that, you can.")}</p>

        <h2>{t("The Patron set")}</h2>
        <p>{t("Donate {min} {unit} or more, once, and you get the whole Patron set as a thank-you: an outfit, an avatar frame and a player card frame. They are looks only, like every other entitlement, and they are yours for good. It is the same set at the minimum or at a hundred times that, because this is a thank-you, not a shop.", { min, unit })}</p>
        <ul>
          <li>{t("Patron's Regalia: an outfit in deep wine and gold, with the guild's mark on the shoulder.")}</li>
          <li>{t("Patron avatar frame: wine-red enamel and gold, with a small heart at the top.")}</li>
          <li>{t("Patron player card frame: the same enamel and gold around your card.")}</li>
        </ul>

        <h2>{t("How it works")}</h2>
        <p>{rich(t("Pick an amount and press Donate. Stripe takes the payment on its own page, and the set is unlocked the moment Stripe confirms it. If it does not show within a few minutes, open a ticket on the {support} page and staff will fix it."), { support: <Link href="/support">{t("Support")}</Link> })}</p>
        <p className="muted small">{t("Donations are gifts to keep Unrealcraft running. They are not purchases, they are not refundable, and they never affect XP, ranks or reviews.")}</p>

        <div style={{ marginTop: 16 }}>
          {open ? <DonateButton loggedIn={!!me} minimum={min} currency={status?.currency ?? "usd"} /> : <span className="btn" aria-disabled="true">{t("Donations open soon")}</span>}
        </div>
      </div>
      {!open && <div style={{ marginTop: 14 }}><Spot art="chest-pending">{t("The donation page is not set up yet. Until it is, there is nothing to do here but read.")}</Spot></div>}
      <div className="row" style={{ marginTop: 14 }}>
        <Link className="btn" href="/mission">{t("Our mission statement")}</Link>
      </div>
    </>
  );
}
