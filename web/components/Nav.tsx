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
          <Link href="/leaderboard" className="link">Leaderboard</Link>
        </nav>
        <div className="nav-user">
          {me ? (
            <>
              <Link href="/me" className="who">
                {me.avatar && <img className="avatar" src={me.avatar} alt="" />}
                <span>{me.name}</span>
                <span className={`pill ${me.staff ? "staff-title" : ""}`} style={{ borderColor: me.rank_color, color: me.rank_color }}>{me.rank_title}</span>
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
