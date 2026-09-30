import Link from "next/link";
import { api, type Me } from "@/lib/api";

export default async function Nav() {
  const me = await api<Me>("/me");
  return (
    <header className="nav">
      <div className="nav-in">
        <Link href="/" className="brand">Unrealcraft</Link>
        <nav className="nav-links" aria-label="Main">
          <Link href="/quests" className="link">Quest Board</Link>
          <Link href="/how-it-works" className="link">How it works</Link>
          {me && <Link href="/leaderboard" className="link">Hall of Fame</Link>}
          {me?.review?.can && <Link href="/review" className="link">Review{me.review.pending > 0 && <span className="count">{me.review.pending}</span>}</Link>}
          {me?.admin && <Link href="/admin" className="link">Admin</Link>}
          <Link href="/changelog" className="link">Changelog</Link>
        </nav>
        <div className="nav-user">
          {me ? (
            <>
              <Link href="/me" className="who">
                {me.avatar && <img className="avatar" src={me.avatar} alt="" />}
                <span>{me.name}</span>
                <span className="pill" style={{ borderColor: me.rank_color, color: me.rank_color }}>{me.rank_title}</span>
              </Link>
              <form action="/api/auth/logout" method="post"><button type="submit">Log out</button></form>
            </>
          ) : (
            <a className="btn primary" href="/api/auth/discord">Enter with Discord</a>
          )}
        </div>
      </div>
    </header>
  );
}
