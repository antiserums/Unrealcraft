"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useT } from "./I18n";
import Ico from "./Ico";
import { type Author, CATEGORY, STATUS, type Ticket } from "@/lib/tickets";


/** POST to the API. Plain objects go as JSON; a FormData (text plus screenshots) goes as it is. */
async function call(path: string, body?: unknown) {
  const form = body instanceof FormData;
  const r = await fetch(`/api${path}`, { method: "POST", headers: form ? undefined : { "content-type": "application/json" }, body: form ? body : body ? JSON.stringify(body) : undefined });
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
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.set("category", category); fd.set("subject", subject); fd.set("body", body);
      files.forEach((f) => fd.append("files", f));
      const j = await call("/me/tickets", fd);
      router.push(`/inbox?ticket=${j.id}`);
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
        placeholder={t("What you were doing, what you expected, what happened instead. Quest ids and screenshots help.")} />
      <ScreenshotPicker files={files} onChange={setFiles} id="ticket-files" />
      {err && <div className="note small" data-tone="error">{err}</div>}
      <div className="row">
        <button type="submit" className="btn primary" disabled={busy}>{busy ? t("Sending…") : t("Open ticket")}</button>
      </div>
    </form>
  );
}

/** One ticket's messages with a reply box. Members reply and close; staff reply (marks it answered) and set the status. */
export function TicketThread({ ticket, staff = false, onChanged }: { ticket: Ticket; staff?: boolean; onChanged?: () => void }) {
  const t = useT();
  const router = useRouter();
  const [body, setBody] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const base = staff ? `/admin/tickets/${ticket.id}` : `/me/tickets/${ticket.id}`;
  const messages = Array.isArray(ticket.messages) ? ticket.messages : [];

  async function act(path: string, payload?: unknown) {
    setBusy(true); setErr(null);
    try {
      await call(path, payload);
      setBody(""); setFiles([]);
      router.refresh();
      onChanged?.();
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
            <span className="ticket-av" aria-hidden="true">
              {m.author?.avatar ? <img className="avatar" src={m.author.avatar} alt="" /> : <span className="mail-seal">{(m.author?.name ?? (m.staff ? "S" : ticket.name ?? "?")).slice(0, 1)}</span>}
            </span>
            <div className="ticket-msg-body">
              <div className="ticket-who">
                {m.author ? <Who a={m.author} /> : <b>{m.staff ? t("Staff") : (ticket.name ?? t("Member"))}</b>}
                {m.staff && <span className="mail-tag ticket-staff-tag">{t("Staff")}</span>}
                <span className="small muted ticket-when">{m.created_at.slice(0, 16).replace("T", " ")}</span>
              </div>
              <p>{m.body}</p>
              {m.attachments && m.attachments.length > 0 && (
                <div className="ticket-shots">{m.attachments.map((u) => <a key={u} href={u} target="_blank" rel="noreferrer"><img src={u} alt="" loading="lazy" /></a>)}</div>
              )}
            </div>
          </div>
        ))}
      </div>
      {ticket.status !== "closed" || staff ? (
        <form className="ticket-reply" onSubmit={(e) => { e.preventDefault(); const fd = new FormData(); fd.set("body", body); files.forEach((f) => fd.append("files", f)); act(`${base}/reply`, fd); }}>
          <div className="eyebrow small" style={{ marginBottom: 6 }}>{staff ? t("Reply to the member") : t("Your reply")}</div>
          {staff && <p className="small muted" style={{ margin: "0 0 8px" }}>{t("A reply marks the ticket answered. Close it when it is done; members cannot close their own.")}</p>}
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} maxLength={4000} required placeholder={staff ? t("Write to the member…") : t("Write a reply…")} />
          <ScreenshotPicker files={files} onChange={setFiles} id={`reply-files-${ticket.id}`} />
          {err && <div className="note small" data-tone="error">{err}</div>}
          <div className="row">
            <button type="submit" className="btn primary" disabled={busy || !body.trim()}>{t("Reply")}</button>
            {staff ? (
              <>
                {ticket.status !== "closed" && <button type="button" className="btn" disabled={busy} onClick={() => act(`${base}/status`, { status: "closed" })}>{t("Close ticket")}</button>}
                {ticket.status !== "open" && <button type="button" className="btn" disabled={busy} onClick={() => act(`${base}/status`, { status: "open" })}>{t("Reopen")}</button>}
              </>
            ) : null}
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

/** Name, avatar and nameplate of whoever wrote a message: the staff role for staff, else the rank title. */
function Who({ a }: { a: Author }) {
  const t = useT();
  return (
    <span className="who" style={{ gap: 6 }}>
      {a.avatar && <img className="avatar" src={a.avatar} alt="" />}
      <b>{a.name}</b>
      <span className={`pill ${a.staff ? "staff-title" : ""}`} data-role={a.staff ?? undefined} style={{ borderColor: a.rank_color, color: a.rank_color }}>{t(a.rank_title)}</span>
    </span>
  );
}

/** Up to four screenshots (PNG, JPG, WEBP or GIF, 8 MB each). The chest also takes video clips; tickets do not. */
function ScreenshotPicker({ files, onChange, id }: { files: File[]; onChange: (f: File[]) => void; id: string }) {
  const t = useT();
  return (
    <div className="upload ticket-upload">
      <label className="small eyebrow" htmlFor={id}>{t("Screenshots (optional)")}</label>
      <input id={id} type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple onChange={(e) => onChange(Array.from(e.target.files ?? []).slice(0, 4))} />
      {files.length > 0 && <div className="small muted">{files.map((f) => f.name).join(", ")}</div>}
    </div>
  );
}
