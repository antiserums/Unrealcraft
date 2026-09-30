"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useT } from "./I18n";
import Ico from "./Ico";
import { CATEGORY, STATUS, type Ticket } from "@/lib/tickets";


async function call(path: string, body?: unknown) {
  const r = await fetch(`/api${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail ?? `Request failed (${r.status})`);
  return j;
}

/** The form that opens a ticket (members only). */
export function TicketForm({ categories }: { categories: string[] }) {
  const t = useT();
  const router = useRouter();
  const [category, setCategory] = useState("other");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const j = await call("/me/tickets", { category, subject, body });
      router.push(`/support/${j.id}`);
    } catch (x) {
      setErr((x as Error).message); setBusy(false);
    }
  }

  return (
    <form className="ticket-form" onSubmit={send}>
      <label className="small eyebrow" htmlFor="ticket-category">{t("What is it about?")}</label>
      <select id="ticket-category" value={category} onChange={(e) => setCategory(e.target.value)}>
        {categories.map((c) => <option key={c} value={c}>{t(CATEGORY[c] ?? c)}</option>)}
      </select>
      <label className="small eyebrow" htmlFor="ticket-subject">{t("Subject")}</label>
      <input id="ticket-subject" type="text" value={subject} onChange={(e) => setSubject(e.target.value)} maxLength={120} required minLength={3} placeholder={t("One line that says what you need")} />
      <label className="small eyebrow" htmlFor="ticket-body">{t("Tell us what happened")}</label>
      <textarea id="ticket-body" value={body} onChange={(e) => setBody(e.target.value)} rows={6} maxLength={4000} required minLength={10}
        placeholder={t("What you were doing, what you expected, what happened instead. Quest ids and screenshots links help.")} />
      {err && <div className="note small" data-tone="error">{err}</div>}
      <div className="row">
        <button type="submit" className="btn primary" disabled={busy}>{busy ? t("Sending…") : t("Open ticket")}</button>
      </div>
    </form>
  );
}

/** One ticket's messages with a reply box. Members reply and close; staff reply (marks it answered) and set the status. */
export function TicketThread({ ticket, staff = false }: { ticket: Ticket; staff?: boolean }) {
  const t = useT();
  const router = useRouter();
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const base = staff ? `/admin/tickets/${ticket.id}` : `/me/tickets/${ticket.id}`;
  const messages = Array.isArray(ticket.messages) ? ticket.messages : [];

  async function act(path: string, payload?: unknown) {
    setBusy(true); setErr(null);
    try {
      await call(path, payload);
      setBody("");
      router.refresh();
    } catch (x) {
      setErr((x as Error).message);
    }
    setBusy(false);
  }

  return (
    <div className="ticket">
      <div className="ticket-msgs">
        {messages.map((m) => (
          <div key={m.id} className={`ticket-msg ${m.staff ? "staff" : "member"}`}>
            <div className="small muted">{m.staff ? t("Staff") : (ticket.name ?? t("Member"))} · {m.created_at.slice(0, 16).replace("T", " ")}</div>
            <p>{m.body}</p>
          </div>
        ))}
      </div>
      {ticket.status !== "closed" || staff ? (
        <form className="ticket-reply" onSubmit={(e) => { e.preventDefault(); act(`${base}/reply`, { body }); }}>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} maxLength={4000} required placeholder={staff ? t("Write to the member…") : t("Write a reply…")} />
          {err && <div className="note small" data-tone="error">{err}</div>}
          <div className="row">
            <button type="submit" className="btn primary" disabled={busy || !body.trim()}>{staff ? t("Reply and mark answered") : t("Reply")}</button>
            {staff ? (
              <>
                {ticket.status !== "closed" && <button type="button" className="btn" disabled={busy} onClick={() => act(`${base}/status`, { status: "closed" })}>{t("Close ticket")}</button>}
                {ticket.status !== "open" && <button type="button" className="btn" disabled={busy} onClick={() => act(`${base}/status`, { status: "open" })}>{t("Reopen")}</button>}
              </>
            ) : (
              <button type="button" className="btn" disabled={busy} onClick={() => act(`${base}/close`)}>{t("Close ticket")}</button>
            )}
          </div>
        </form>
      ) : (
        <div className="note small">{t("This ticket is closed. If you need more help, open a new one.")} <Link href="/support">{t("Support")}</Link></div>
      )}
    </div>
  );
}

/** A compact list row. */
export function TicketRow({ tk, href }: { tk: Ticket; href: string }) {
  const t = useT();
  return (
    <Link href={href} className="card ticket-row" style={{ color: "inherit", textDecoration: "none" }}>
      <div className="row" style={{ justifyContent: "space-between", gap: 10 }}>
        <b>#{tk.id} · {tk.subject}</b>
        <span className={`pill ticket-${tk.status}`}><Ico group="quest-state" id={tk.status === "answered" ? "done" : tk.status === "closed" ? "skipped" : "pending"} className="pill-ico" />{t(STATUS[tk.status])}</span>
      </div>
      <div className="small muted">{t(CATEGORY[tk.category] ?? tk.category)}{tk.name ? ` · ${tk.name}` : ""} · {tk.updated_at.slice(0, 10)}{typeof tk.messages === "number" ? ` · ${t("{n} messages", { n: tk.messages })}` : ""}</div>
      {tk.last && <div className="small ticket-last">{tk.last.length > 140 ? tk.last.slice(0, 140) + "…" : tk.last}</div>}
    </Link>
  );
}
