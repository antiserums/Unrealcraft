import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import ReviewForm from "@/components/ReviewForm";
import { TierBadge } from "@/components/QuestCard";
import { api, type Me, type ReviewItem } from "@/lib/api";

export default async function ReviewDetail({ params }: PageProps<"/review/[id]">) {
  const { id } = await params;
  const me = await api<Me>("/me");
  if (!me) redirect(`/api/auth/discord?next=/review/${id}`);
  const s = await api<ReviewItem>(`/review/submissions/${id}`);
  if (!s) notFound();
  const d = s.quest_detail!;
  return (
    <>
      <div className="eyebrow"><Link href="/review">← Review inbox</Link></div>
      <h1>#{s.id} · {s.quest.id} · {s.quest.title}</h1>
      <div className="two">
        <div>
          <div className="card">
            <div className="rv-row" style={{ gridTemplateColumns: "44px 1fr" }}>
              <div className="pcard-avatar">{s.member.avatar ? <img src={s.member.avatar} alt="" /> : <span>{(s.member.name ?? "?").slice(0, 1)}</span>}</div>
              <div>
                <b>{s.member.name ?? `Member ${s.member.id}`}</b>
                <div className="small muted">rank {s.member.rank ?? "?"} · {s.member.major ?? "undecided"} · sent {s.created_at.slice(0, 16).replace("T", " ")} · engine {s.payload.ue_version || "not stated ⚠"} · <Link href={`/members/${s.member.id}`}>player card</Link></div>
              </div>
            </div>
            <div className="eyebrow" style={{ marginTop: 14 }}>What they sent</div>
            <pre className="rv-text" style={{ marginTop: 6 }}>{s.payload.text || "(no text)"}</pre>
            {s.payload.attachments?.length ? (
              <div className="rv-shots">{s.payload.attachments.map((u) => <a key={u} href={u} target="_blank" rel="noreferrer"><img src={u} alt="" /></a>)}</div>
            ) : null}
          </div>

          {s.previous && s.previous.length > 0 && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="eyebrow">Earlier attempts</div>
              <ul className="plain small" style={{ marginTop: 6 }}>
                {s.previous.map((p) => <li key={p.id}>#{p.id} · <b>{p.status}</b> · {p.created_at.slice(0, 10)}{p.notes ? ` · “${p.notes}”` : ""}</li>)}
              </ul>
            </div>
          )}

          {s.actions && s.actions.length > 0 && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="eyebrow">Reviews so far</div>
              <ul className="plain small" style={{ marginTop: 6 }}>
                {s.actions.map((a, i) => <li key={i}><b>{a.verdict}</b> by {a.name ?? a.reviewer_id}{a.is_peer ? " (peer)" : " (mentor)"} · {a.created_at.slice(0, 16).replace("T", " ")}{a.notes ? ` · “${a.notes}”` : ""}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div>
          <ReviewForm s={s} />
          <div className="card" style={{ marginTop: 12 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="eyebrow">What the quest asks</div>
              <TierBadge tier={s.quest.tier} />
            </div>
            {d.do && <p className="small" style={{ marginTop: 8 }}>{d.do}</p>}
            {d.done_when && <p className="small"><b>Done when:</b> {d.done_when}</p>}
            {d.checklist.length > 0 && (
              <ul className="check small">{d.checklist.map((c, i) => <li key={i}><span className="mark">{c.kind === "submit" ? "📎" : "☐"}</span><span>{c.text}</span></li>)}</ul>
            )}
            <p className="small muted" style={{ margin: "8px 0 0" }}>Route: <b>{s.route}</b> · verify by {d.verify_type ?? "?"} · <Link href={`/quests/${s.quest.id}`}>open the quest</Link></p>
          </div>
        </div>
      </div>
    </>
  );
}
