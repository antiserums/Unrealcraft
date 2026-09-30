import Link from "next/link";
import { MISSION } from "@/lib/mission";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Mission statement") };
}

export default async function Mission() {
  const t = await getT();
  return (
    <>
      <PageHeader art="header-guild" eyebrow="Unrealcraft" title={t("Our mission statement")} />
      <div className="card">
        <p className="lead" style={{ margin: 0, maxWidth: "none", fontSize: 17 }}>{t(MISSION)}</p>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <Link className="btn primary" href="/quests">{t("Quest board")}</Link>
        <Link className="btn" href="/how-it-works">{t("How it works")}</Link>
      </div>
    </>
  );
}
