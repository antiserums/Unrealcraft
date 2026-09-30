import { redirect } from "next/navigation";
import Letters, { type Letter } from "@/components/Letters";
import { PageHeader, Spot } from "@/components/SiteArt";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Letters") };
}

/** The mailbox: announcements, letters from staff, and the site's own notes (tickets, reviews, ranks). */
export default async function LettersPage() {
  const t = await getT();
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/letters");
  const data = await api<{ letters: Letter[]; unread: number }>("/me/letters");
  const letters = data?.letters ?? [];
  return (
    <>
      <PageHeader art="header-player" eyebrow={t("Profile")} title={t("Letters")} />
      {letters.length === 0
        ? <Spot art="sleeping-dragon">{t("No letters yet. Announcements, answers to your tickets, review results and rank-ups will land here.")}</Spot>
        : <Letters letters={letters} />}
    </>
  );
}
