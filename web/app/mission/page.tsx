import Link from "next/link";
import { MISSION } from "@/lib/mission";

export const metadata = { title: "Mission statement" };

export default function Mission() {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Our mission statement</h1>
      <div className="card">
        <p className="lead" style={{ margin: 0, maxWidth: "none", fontSize: 17 }}>{MISSION}</p>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <Link className="btn primary" href="/quests">Quest board</Link>
        <Link className="btn" href="/how-it-works">How it works</Link>
      </div>
    </>
  );
}
