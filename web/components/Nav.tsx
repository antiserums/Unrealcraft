import Link from "next/link";
import { api, type Me } from "@/lib/api";
import { loadManifest, siteArt } from "@/lib/art";
import { getT } from "@/lib/i18n";
import { Px } from "./SiteArt";

export default async function Nav() {
  const [me, t, m] = await Promise.all([api<Me>("/me"), getT(), loadManifest()]);
  const emblem = siteArt(m, "site-emblem/emblem-32");
  return (
    <header className="nav">
      <div className="nav-in">
        <Link href="/" className={`brand ${emblem ? "has-emblem" : ""}`}><Px src={emblem} />Unrealcraft</Link>
        <nav className="nav-links" aria-label={t("Main")}>
          <Link href="/quests" className="link">{t("Quest Board")}</Link>
          <Link href="/how-it-works" className="link">{t("How it works")}</Link>
          <Link href="/leaderboard" className="link">{t("Leaderboard")}</Link>
          <Link href="/mission" className="link">{t("Mission statement")}</Link>
        </nav>
        <div className="nav-user">
          {me ? (
            <>
              <Link href="/me" className="who">
                {me.avatar && <img className="avatar" src={me.avatar} alt="" />}
                <span>{me.name}</span>
                <span className={`pill ${me.staff ? "staff-title" : ""}`} style={{ borderColor: me.rank_color, color: me.rank_color }}>{t(me.rank_title)}</span>
              </Link>
              <form action="/api/auth/logout" method="post"><button type="submit">{t("Log out")}</button></form>
            </>
          ) : (
            <a className="btn primary" href="/api/auth/discord">{t("Enter with Discord")}</a>
          )}
        </div>
      </div>
    </header>
  );
}
