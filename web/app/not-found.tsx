import Link from "next/link";
import { Spot } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export default async function NotFound() {
  const t = await getT();
  return (
    <>
      <h1>{t("This page is not on the map")}</h1>
      <Spot art="lantern-signpost">
        <p style={{ marginTop: 0 }}>{t("The road ends here. The page may have moved, or the link is wrong.")}</p>
        <div className="row">
          <Link className="btn primary" href="/">{t("Back to town")}</Link>
          <Link className="btn" href="/quests">{t("Quest board")}</Link>
        </div>
      </Spot>
    </>
  );
}
