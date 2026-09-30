"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ReviewItem } from "@/lib/api";

type Result = { final: string | null; quest_xp?: number; message: string };

/** Pass / Changes / Fail with a note. Mentors only; one verdict decides. */
export default function ReviewForm({ s }: { s: ReviewItem }) {
  const router = useRouter();
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [res, setRes] = useState<Result | null>(null);

  async function send(verdict: "pass" | "changes" | "fail") {
    if (verdict !== "pass" && !notes.trim()) { setErr("Say what to change. A note is required for Changes and Fail."); return; }
    setBusy(true); setErr(null);
    const r = await fetch(`/api/review/submissions/${s.id}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ verdict, notes }) });
    const j = await r.json();
    if (!r.ok) setErr(j.detail ?? "Could not record that."); else { setRes(j); router.refresh(); }
    setBusy(false);
  }

  if (s.status !== "pending") {
    return <div className="card"><div className="eyebrow">Decided</div><p style={{ margin: "6px 0 0" }}><b style={{ textTransform: "capitalize" }}>{s.status}</b>{s.decided_at ? ` on ${s.decided_at.slice(0, 10)}` : ""}.{s.notes ? ` Note: “${s.notes}”` : ""}</p></div>;
  }
  if (res) {
    return (
      <div className="card chest open">
        <div className="eyebrow">Recorded</div>
        <p style={{ margin: "6px 0 10px" }}>{res.message}{res.final === "pass" && res.quest_xp ? ` The member gets +${res.quest_xp} XP and their chest opens.` : ""}</p>
        <Link className="btn primary" href="/admin/review">Back to the inbox</Link>
      </div>
    );
  }
  if (s.blocked) return <div className="card"><div className="eyebrow">Not yours to review</div><p style={{ margin: "6px 0 0" }}>{s.blocked}</p></div>;
  if (s.reviewed_by_me) return <div className="card"><div className="eyebrow">Waiting</div><p style={{ margin: "6px 0 0" }}>You already reviewed this one.</p></div>;

  return (
    <div className="card">
      <div className="eyebrow">Your verdict</div>
      <label className="small muted" htmlFor="rv-notes" style={{ display: "block", marginTop: 8 }}>Note to the member (required for Changes and Fail)</label>
      <textarea id="rv-notes" rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What is good, what to fix, where to look." style={{ width: "100%", marginTop: 4 }} />
      {err && <div className="note small" style={{ marginTop: 8, borderColor: "var(--bad)" }}>{err}</div>}
      <div className="verdicts" style={{ marginTop: 10 }}>
        <button className="primary" disabled={busy} onClick={() => send("pass")}>Pass</button>
        <button className="changes" disabled={busy} onClick={() => send("changes")}>Changes</button>
        <button className="fail" disabled={busy} onClick={() => send("fail")}>Fail</button>
      </div>
      <p className="small muted" style={{ margin: "10px 0 0" }}>
        Your verdict decides. Pass gives XP and opens the chest; Changes and Fail send your note to the member.
      </p>
    </div>
  );
}
