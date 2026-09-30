import Link from "next/link";
import { api, type Me } from "@/lib/api";

/** Site footer: the crest, the quiet links (changelog, and for staff the review inbox and admin panel). */
export default async function Foot() {
  const me = await api<Me>("/me");
  return (
    <footer className="foot">
      <span className="rule" /><span className="crest">❖</span><span className="rule" />
      <nav className="foot-links" aria-label="Site">
        <Link href="/faq">FAQ</Link>
        <Link href="/changelog">Changelog</Link>
        <Link href="/privacy">Privacy</Link>
        <Link href="/terms">Terms of service</Link>
        {me?.review?.can && <Link href="/review">Review{me.review.pending > 0 ? ` (${me.review.pending})` : ""}</Link>}
        {me?.admin && <Link href="/admin">Admin</Link>}
      </nav>
      <div className="small muted">Unrealcraft · an RPG learning experience for Unreal Engine</div>
    </footer>
  );
}
