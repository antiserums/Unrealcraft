import Link from "next/link";
import { api, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";
import LanguagePicker from "./LanguagePicker";

/** Site footer: the crest, the quiet links (FAQ, changelog, legal, and for staff the review inbox and admin panel)
 *  and the language menu. */
export default async function Foot() {
  const [me, t] = await Promise.all([api<Me>("/me"), getT()]);
  return (
    <footer className="foot">
      <span className="rule" /><span className="crest">❖</span><span className="rule" />
      <nav className="foot-links" aria-label={t("Site")}>
        <Link href="/faq">{t("FAQ")}</Link>
        <Link href="/changelog">{t("Changelog")}</Link>
        <Link href="/privacy">{t("Privacy policy")}</Link>
        <Link href="/terms">{t("Terms of service")}</Link>
        {me?.review?.can && <Link href="/review">{t("Review")}{me.review.pending > 0 ? ` (${me.review.pending})` : ""}</Link>}
        {me?.admin && <Link href="/admin">{t("Admin")}</Link>}
        <LanguagePicker />
      </nav>
      <div className="small muted">{t("Unrealcraft · an RPG learning experience for Unreal Engine")}</div>
    </footer>
  );
}
