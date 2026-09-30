import Link from "next/link";
import { redirect } from "next/navigation";
import { Spot } from "@/components/SiteArt";
import { api, type Me, type ReviewAccess, type ReviewItem } from "@/lib/api";

export const metadata = { title: "Review inbox" };

const ROUTE: Record<string, string> = { peer: "rank 2", mentor: "rank 3–4", human: "rank 5+", honor: "honor · accepted on trust", auto: "auto" };

export default async function ReviewInbox() {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/review");
  const data = await api<{ access: ReviewAccess; pending: ReviewItem[]; recent: ReviewItem[] }>("/review/queue");
  if (!data) {
    return (
      <>
        <h1>Review inbox</h1>
        <div className="card">Only mentors, admins and devs review work.</div>
      </>
    );
  }
  const { access, pending, recent } = data;
  const mine = pending.filter((s) => !s.blocked && !s.reviewed_by_me);
  const rest = pending.filter((s) => s.blocked || s.reviewed_by_me);
  return (
    <>
      <div className="eyebrow">Mentor</div>
      <h1>Review inbox</h1>
      <p className="muted">{pending.length} waiting. Pass gives the member their XP and opens their chest. Changes sends it back with your note. Fail is for work that is not an honest attempt; they can try again in two hours. Honor-route work (rank 0 and 1) was accepted on trust and needs nothing from you.</p>

      <div className="section-h"><h2>For you</h2><span className="muted small">{mine.length} you can act on</span></div>
      {mine.length === 0 && <Spot art="sleeping-dragon">Nothing waiting for you right now.</Spot>}
      <div className="grid">{mine.map((s) => <Row key={s.id} s={s} />)}</div>

      {rest.length > 0 && (
        <>
          <div className="section-h"><h2>Not yours</h2><span className="muted small">{rest.length} · your own work, or already reviewed</span></div>
          <div className="grid lock">{rest.map((s) => <Row key={s.id} s={s} />)}</div>
        </>
      )}

      {recent.length > 0 && (
        <>
          <div className="section-h"><h2>Recently decided</h2></div>
          <div className="grid">{recent.map((s) => <Row key={s.id} s={s} />)}</div>
        </>
      )}
    </>
  );
}

function Row({ s }: { s: ReviewItem }) {
  const age = Math.max(0, Math.round((Date.now() - new Date(s.created_at + "Z").getTime()) / 3600000));
  const status = s.status === "pending" ? (s.reviewed_by_me ? "you reviewed" : s.blocked ?? "waiting")
    : `${s.status}${s.decided_at ? ` · ${s.decided_at.slice(0, 10)}` : ""}`;
  return (
    <Link href={`/review/${s.id}`} className="card rv-row" style={{ color: "inherit" }}>
      <div className="pcard-avatar">{s.member.avatar ? <img src={s.member.avatar} alt="" /> : <span>{(s.member.name ?? "?").slice(0, 1)}</span>}</div>
      <div style={{ minWidth: 0 }}>
        <div><b>{s.member.name ?? `Member ${s.member.id}`}</b> <span className="muted small">· #{s.id} · {s.quest.id} {s.quest.title}</span></div>
        <div className="small muted" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.payload.text?.slice(0, 140) || "(no text)"}</div>
        <div className="row small" style={{ gap: 8, marginTop: 4 }}>
          <span className="route">{ROUTE[s.route] ?? s.route}</span>
          <span className="muted">{age < 1 ? "just now" : age < 48 ? `${age} h ago` : `${Math.round(age / 24)} d ago`}</span>
          {s.payload.attachments?.length ? <span className="muted">· {s.payload.attachments.length} image{s.payload.attachments.length === 1 ? "" : "s"}</span> : null}
        </div>
      </div>
      <span className={`status ${s.status === "pass" ? "done" : s.status === "pending" ? "now" : "skipped"}`} style={{ textAlign: "right" }}>{status}</span>
    </Link>
  );
}
