import HowItWorks from "@/components/HowItWorks";
import { api, type Specializations } from "@/lib/api";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("How it works") };
}

export default async function HowItWorksPage() {
  const t = await getT();
  const specs = await api<Specializations>("/catalog/specializations");
  return (
    <>
      <PageHeader art="header-library" eyebrow="Unrealcraft" title={t("How it works")} />
      <p className="lead" style={{ marginBottom: 6 }}>{t("Every quest is a dungeon. Read the guide, build it in the engine, then fight the boss: a short quiz where right answers land hits. Show your work, open the chest, rank up. Ranks come only from quests.")}</p>
      <HowItWorks specs={specs} />
    </>
  );
}
