import Link from "next/link";
import { TicketForm, TicketRow } from "@/components/Tickets";
import type { Ticket } from "@/lib/tickets";
import { PageHeader, Spot } from "@/components/SiteArt";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";
import { DISCORD_INVITE } from "@/lib/mission";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Support") };
}

/** The help centre: where to look first, then a ticket to staff. Tickets are answered in the admin panel. */
export default async function Support() {
  const t = await getT();
  const me = await api<Me>("/me");
  const data = me ? await api<{ tickets: Ticket[]; categories: string[] }>("/me/tickets") : null;
  const tickets = data?.tickets ?? [];
  return (
    <>
      <PageHeader art="header-review" eyebrow="Unrealcraft" title={t("Support")} />
      <div className="grid">
        <div className="card">
          <div className="eyebrow">{t("Quick answers")}</div>
          <p className="small" style={{ margin: "6px 0 0" }}>{rich(t("The {faq} covers joining, quests, boss fights, ranks, specializations and your player card."), { faq: <Link href="/faq">{t("FAQ")}</Link> })}</p>
        </div>
        <div className="card">
          <div className="eyebrow">{t("Ask the guild")}</div>
          <p className="small" style={{ margin: "6px 0 0" }}>{rich(t("For quick questions and help with the engine, the {discord} is the fastest place. Other members are usually around."), { discord: <a href={DISCORD_INVITE}>{t("Discord server")}</a> })}</p>
        </div>
        <div className="card">
          <div className="eyebrow">{t("Write to staff")}</div>
          <p className="small" style={{ margin: "6px 0 0" }}>{t("For anything about your account, a review, a broken quest or a donation, open a ticket below. Staff answer here, and you get the reply on this page.")}</p>
        </div>
      </div>

      <div className="section-h"><h2>{t("Open a ticket")}</h2></div>
      {me ? (
        <div className="card"><TicketForm categories={data?.categories ?? ["account", "quest", "review", "bug", "donation", "other"]} /></div>
      ) : (
        <Spot art="guild-entry">
          <p style={{ marginTop: 0 }}>{t("Log in to open a ticket. Staff need to know which account they are helping.")}</p>
          <a className="btn primary" href="/api/auth/discord?next=/support">{t("Log in with Discord")}</a>
        </Spot>
      )}

      {me && (
        <>
          <div className="section-h"><h2>{t("Your tickets")}</h2><span className="muted small">{t("{n} in all", { n: tickets.length })}</span></div>
          {tickets.length === 0
            ? <Spot art="sleeping-dragon">{t("No tickets yet. When you open one, it shows here with its answers.")}</Spot>
            : <div className="grid">{tickets.map((tk) => <TicketRow key={tk.id} tk={tk} href={`/support/${tk.id}`} />)}</div>}
        </>
      )}
    </>
  );
}
