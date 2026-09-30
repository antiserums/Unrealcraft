import Link from "next/link";
import { api, type Me } from "@/lib/api";

export default async function Nav() {
  const me = await api<Me>("/me");
  return (
    <header className="nav">
      <div className="nav-in">
        <Link href="/" className="brand">Unrealcraft</Link>
        <Link href="/quests" className="link">Quest Board</Link>
        {me && <Link href="/path" className="link">My Path</Link>}
        {me && <Link href="/leaderboard" className="link">Hall of Fame</Link>}
        <Link href="/changelog" className="link">Changelog</Link>
        <span className="spacer" />
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
    </header>
  );
}
