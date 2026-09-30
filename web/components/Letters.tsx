"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CATEGORY, STATUS, type Ticket } from "@/lib/tickets";
import { TicketThread } from "./Tickets";
import { useT } from "./I18n";
import Ico from "./Ico";

export type Letter = {
  id: number; member_id: number; kind: string; title: string; body: string; link: string | null; sender_id: number | null;
  sender?: string | null; sender_avatar?: string | null; created_at: string; read: boolean;
};

/** Each kind of mail: its label, colour, icon, and what the action button says. */
const KIND: Record<string, { label: string; color: string; group: "quest-state" | "rewards" | "utility" | "statistics"; icon: string; action: string }> = {
  letter: { label: "Letter", color: "var(--gold-2)", group: "utility", icon: "edit", action: "Open" },
  announcement: { label: "Announcement", color: "var(--teal-2)", group: "statistics", icon: "members", action: "Open" },
  ticket: { label: "Ticket", color: "var(--warn)", group: "quest-state", icon: "pending", action: "Open the ticket" },
  review: { label: "Review", color: "var(--ok)", group: "quest-state", icon: "done", action: "Open the quest" },
  rank: { label: "Rank", color: "var(--gold-2)", group: "rewards", icon: "rank-up", action: "Open the wardrobe" },
  donation: { label: "Thank you", color: "#e07b8a", group: "rewards", icon: "outfit", action: "Open the wardrobe" },
};
/** The folders in the sidebar. */
const FOLDERS: { key: string; label: string; group: "utility" | "statistics" | "quest-state" | "rewards"; icon: string; match: (l: Letter, read: boolean) => boolean }[] = [
  { key: "inbox", label: "Inbox", group: "utility", icon: "link", match: () => true },
  { key: "unread", label: "Unread", group: "quest-state", icon: "now", match: (_, read) => !read },
  { key: "announcement", label: "Announcements", group: "statistics", icon: "members", match: (l) => l.kind === "announcement" || l.kind === "letter" },
  { key: "ticket", label: "Tickets", group: "quest-state", icon: "pending", match: (l) => l.kind === "ticket" },
  { key: "review", label: "Reviews", group: "quest-state", icon: "done", match: (l) => l.kind === "review" },
  { key: "rewards", label: "Ranks and rewards", group: "rewards", icon: "rank-up", match: (l) => l.kind === "rank" || l.kind === "donation" },
];

async function post(path: string) {
  await fetch(`/api${path}`, { method: "POST" }).catch(() => null);
}

function when(iso: string, long = false): string {
  const d = new Date(iso.replace(" ", "T") + "Z");
  if (long) return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  const now = new Date();
  return d.toDateString() === now.toDateString()
    ? d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** The inbox: folders down the left, the message list beside them. Mail rows say what they are with a coloured
 *  type tag; the Tickets folder lists the member's own tickets. Clicking a row opens it in place of the list (the
 *  folders stay): a mail shows its text, a ticket shows the whole thread with a reply box. */
export default function Letters({ letters, tickets = [], staffTickets = [], openTicket = null, openMail = null }:
  { letters: Letter[]; tickets?: Ticket[]; staffTickets?: Ticket[]; openTicket?: number | null; openMail?: number | null }) {
  const t = useT();
  const router = useRouter();
  const [readIds, setReadIds] = useState<Set<number>>(new Set(letters.filter((l) => l.read).map((l) => l.id)));
  const [folder, setFolder] = useState(openTicket ? "ticket" : "inbox");
  const [openId, setOpenId] = useState<number | null>(openMail);
  const [ticketId, setTicketId] = useState<number | null>(openTicket);
  const [asStaff, setAsStaff] = useState(false);            // reading a ticket another member opened (staff only)
  const [thread, setThread] = useState<Ticket | null>(null);
  const isRead = (l: Letter) => readIds.has(l.id);
  const from = (l: Letter) => l.sender ?? (l.kind === "announcement" || l.kind === "letter" ? t("Staff") : "Unrealcraft");
  const current = FOLDERS.find((f) => f.key === folder) ?? FOLDERS[0];
  const shown = useMemo(() => letters.filter((l) => current.match(l, isRead(l))), [letters, current, readIds]);   // eslint-disable-line react-hooks/exhaustive-deps
  const open = letters.find((l) => l.id === openId) ?? null;
  const unread = letters.filter((l) => !isRead(l)).length;
  const openTickets = tickets.filter((k) => k.status !== "closed").length + staffTickets.filter((k) => k.status === "open").length;

  // the ticket being read: fetched fresh each time it opens or changes
  useEffect(() => {
    if (ticketId === null) { setThread(null); return; }
    let live = true;
    fetch(asStaff ? `/api/admin/tickets/${ticketId}` : `/api/me/tickets/${ticketId}`).then((r) => (r.ok ? r.json() : null)).then((j) => { if (live) setThread(j); }).catch(() => { if (live) setThread(null); });
    return () => { live = false; };
  }, [ticketId, asStaff]);

  async function show(l: Letter) {
    if (!readIds.has(l.id)) {
      setReadIds(new Set([...readIds, l.id]));
      await post(`/me/letters/${l.id}/read`);
      router.refresh();
    }
    const mine = l.kind === "ticket" && l.link ? /ticket=(\d+)|\/support\/(\d+)/.exec(l.link) : null;
    const theirs = l.kind === "ticket" && l.link ? /\/admin\/tickets\/(\d+)/.exec(l.link) : null;
    if (mine) { setAsStaff(false); setTicketId(Number(mine[1] ?? mine[2])); setOpenId(null); return; }   // a note about a ticket opens the ticket itself
    if (theirs) { setAsStaff(true); setTicketId(Number(theirs[1])); setOpenId(null); return; }
    setOpenId(l.id);
  }
  async function toggleRead(l: Letter) {
    const next = new Set(readIds);
    if (next.has(l.id)) { next.delete(l.id); await post(`/me/letters/${l.id}/unread`); } else { next.add(l.id); await post(`/me/letters/${l.id}/read`); }
    setReadIds(next);
    router.refresh();
  }
  async function readAll() {
    setReadIds(new Set(letters.map((l) => l.id)));
    await post("/me/letters/read-all");
    router.refresh();
  }
  function step(dir: 1 | -1) {
    if (!open) return;
    const i = shown.findIndex((l) => l.id === open.id);
    const next = shown[i + dir];
    if (next) show(next);
  }
  function back() { setOpenId(null); setTicketId(null); setAsStaff(false); }
  function refetchThread() { const id = ticketId; setTicketId(null); setTimeout(() => setTicketId(id), 0); }

  const Tag = ({ kind }: { kind: string }) => { const k = KIND[kind] ?? KIND.letter; return <span className="mail-tag" style={{ color: k.color, borderColor: k.color }}>{t(k.label)}</span>; };
  const StatusTag = ({ status }: { status: Ticket["status"] }) => {
    const color = status === "open" ? "var(--gold-2)" : status === "answered" ? "var(--ok)" : "var(--muted)";
    return <span className="mail-tag" style={{ color, borderColor: color }}>{t(STATUS[status])}</span>;
  };
  const Sender = ({ l, big = false }: { l: Letter; big?: boolean }) => (
    <span className={`mail-sender ${big ? "big" : ""}`}>
      {l.sender_avatar ? <img className="avatar" src={l.sender_avatar} alt="" /> : <span className="mail-seal" aria-hidden="true">{l.sender ? l.sender.slice(0, 1) : "U"}</span>}
      <span>{from(l)}</span>
    </span>
  );

  const side = (
    <aside className="mail-side">
      {FOLDERS.map((f) => {
        const n = f.key === "ticket" ? openTickets : letters.filter((l) => f.match(l, isRead(l)) && !isRead(l)).length;
        return (
          <button key={f.key} type="button" className={`bare mail-folder ${folder === f.key ? "on" : ""}`} onClick={() => { setFolder(f.key); back(); }} aria-current={folder === f.key ? "true" : undefined}>
            <Ico group={f.group} id={f.icon} className="mail-folder-ico" />
            <span className="mail-folder-name">{t(f.label)}</span>
            {n > 0 && <span className="count">{n}</span>}
          </button>
        );
      })}
      {unread > 0 && <button type="button" className="btn mail-readall" onClick={readAll}>{t("Mark all read")}</button>}
    </aside>
  );

  // a ticket, read and answered right here
  if (ticketId !== null) {
    return (
      <div className="mailbox-page">
        {side}
        <div className="mail-main">
          <div className="mail-tools">
            <button type="button" className="btn" onClick={back}>← {t("Back to the inbox")}</button>
          </div>
          <article className="card mail-read">
            {thread ? (
              <>
                <div className="mail-read-top"><Tag kind="ticket" /><StatusTag status={thread.status} /><span className="spacer" /></div>
                <h2 className="mail-read-title">#{thread.id} · {thread.subject}</h2>
                <div className="mail-read-meta">
                  <span className="small muted">{t(CATEGORY[thread.category] ?? thread.category)} · {t("opened {date}", { date: thread.created_at.slice(0, 10) })}{asStaff && thread.author ? <> · {t("From {who}", { who: `${thread.author.name}, ${t(thread.author.rank_title)}` })}</> : null}</span>
                </div>
                <TicketThread ticket={thread} staff={asStaff} onChanged={refetchThread} />
              </>
            ) : <div className="muted small">{t("Loading…")}</div>}
          </article>
        </div>
      </div>
    );
  }

  if (open) {
    const i = shown.findIndex((l) => l.id === open.id);
    return (
      <div className="mailbox-page">
        {side}
        <div className="mail-main">
        <div className="mail-tools">
          <button type="button" className="btn" onClick={back}>← {t("Back to the inbox")}</button>
          <span className="spacer" />
          <span className="small muted">{i + 1} / {shown.length}</span>
          <button type="button" className="btn" disabled={i <= 0} onClick={() => step(-1)} aria-label={t("Newer")}>‹</button>
          <button type="button" className="btn" disabled={i >= shown.length - 1} onClick={() => step(1)} aria-label={t("Older")}>›</button>
        </div>
        <article className="card mail-read">
          <div className="mail-read-top">
            <Tag kind={open.kind} />
            <span className="spacer" />
            <button type="button" className="btn" onClick={() => toggleRead(open)}>{isRead(open) ? t("Mark unread") : t("Mark read")}</button>
          </div>
          <h2 className="mail-read-title">{open.title}</h2>
          <div className="mail-read-meta">
            <Sender l={open} big />
            <span className="muted small">{when(open.created_at, true)}</span>
          </div>
          <p className="letter-text">{open.body}</p>
          {open.link && <Link className="btn primary" href={open.link}>{t((KIND[open.kind] ?? KIND.letter).action)}</Link>}
        </article>
        </div>
      </div>
    );
  }

  // the Tickets folder lists the tickets themselves
  if (folder === "ticket") {
    return (
      <div className="mailbox-page">
        {side}
        <div className="mail-main">
          <div className="mail-tools">
            <b className="mail-folder-title">{t("Tickets")}</b>
            <span className="small muted">{t("{n} in all", { n: tickets.length })}</span>
            <span className="spacer" />
            <Link className="btn" href="/support">{t("Open a ticket")}</Link>
          </div>
          <section className="card mail-list" aria-label={t("Tickets")}>
            {tickets.length === 0 && staffTickets.length === 0 && <div className="muted small" style={{ padding: "18px 12px" }}>{t("No tickets yet. When you open one, it shows here with its answers.")}</div>}
            {staffTickets.length > 0 && <div className="mail-list-head">{t("Waiting for staff")}</div>}
            {staffTickets.map((k) => (
              <button key={`s${k.id}`} type="button" className={`bare mail-row ${k.status === "open" ? "unread" : ""}`} onClick={() => { setAsStaff(true); setTicketId(k.id); }}>
                <span className="mail-dot" aria-hidden="true" />
                <span className="mail-row-main">
                  <span className="mail-row-top"><span className="mail-sender"><span className="mail-seal" aria-hidden="true">{(k.name ?? "?").slice(0, 1)}</span><span>{k.name ?? t("Member")} · #{k.id}</span></span><span className="mail-when">{when(k.updated_at)}</span></span>
                  <span className="mail-subject">{k.subject}</span>
                  <span className="mail-row-bottom"><StatusTag status={k.status} /><span className="mail-preview">{(k.last ?? "").replace(/\s+/g, " ").slice(0, 140)}</span></span>
                </span>
              </button>
            ))}
            {staffTickets.length > 0 && tickets.length > 0 && <div className="mail-list-head">{t("Your tickets")}</div>}
            {tickets.map((k) => (
              <button key={k.id} type="button" className={`bare mail-row ${k.status === "answered" ? "unread" : ""}`} onClick={() => { setAsStaff(false); setTicketId(k.id); }}>
                <span className="mail-dot" aria-hidden="true" />
                <span className="mail-row-main">
                  <span className="mail-row-top"><span className="mail-sender"><span className="mail-seal" aria-hidden="true">#</span><span>#{k.id}</span></span><span className="mail-when">{when(k.updated_at)}</span></span>
                  <span className="mail-subject">{k.subject}</span>
                  <span className="mail-row-bottom"><StatusTag status={k.status} /><span className="mail-preview">{(k.last ?? "").replace(/\s+/g, " ").slice(0, 140)}</span></span>
                </span>
              </button>
            ))}
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="mailbox-page">
      {side}
      <div className="mail-main">
      <div className="mail-tools">
        <b className="mail-folder-title">{t(current.label)}</b>
        <span className="small muted">{t("{n} messages", { n: shown.length })}</span>
      </div>
      <section className="card mail-list" aria-label={t(current.label)}>
        {shown.length === 0 && <div className="muted small" style={{ padding: "18px 12px" }}>{t("Nothing here.")}</div>}
        {shown.map((l) => (
          <button key={l.id} type="button" className={`bare mail-row ${isRead(l) ? "" : "unread"}`} onClick={() => show(l)}>
            <span className="mail-dot" aria-hidden="true" />
            <span className="mail-row-main">
              <span className="mail-row-top"><Sender l={l} /><span className="mail-when">{when(l.created_at)}</span></span>
              <span className="mail-subject">{l.title}</span>
              <span className="mail-row-bottom"><Tag kind={l.kind} /><span className="mail-preview">{l.body.replace(/\s+/g, " ").slice(0, 140)}</span></span>
            </span>
          </button>
        ))}
      </section>
      </div>
    </div>
  );
}

/** Admin: write a letter to everyone, to staff, or to one member. */
export function Compose() {
  const [to, setTo] = useState("all");
  const [uid, setUid] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [link, setLink] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const router = useRouter();

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setMsg(null);
    const r = await fetch("/api/admin/letters", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ to: to === "member" ? uid.trim() : to, title, body, link }) });
    const j = await r.json().catch(() => ({}));
    setBusy(false);
    if (!r.ok) { setMsg(j.detail ?? "Could not send."); return; }
    setMsg(`Sent (#${j.id}).`); setTitle(""); setBody(""); setLink("");
    router.refresh();
  }

  return (
    <form className="ticket-form" onSubmit={send}>
      <label className="small eyebrow">To</label>
      <div className="row" style={{ gap: 6 }}>
        <select value={to} onChange={(e) => setTo(e.target.value)} style={{ width: "auto" }}>
          <option value="all">Everyone (announcement)</option>
          <option value="staff">Staff only</option>
          <option value="member">One member</option>
        </select>
        {to === "member" && <input type="text" value={uid} onChange={(e) => setUid(e.target.value)} placeholder="Discord id" style={{ width: 220 }} required />}
      </div>
      <label className="small eyebrow" htmlFor="letter-title">Subject</label>
      <input id="letter-title" type="text" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} required minLength={2} />
      <label className="small eyebrow" htmlFor="letter-body">Message</label>
      <textarea id="letter-body" value={body} onChange={(e) => setBody(e.target.value)} rows={7} maxLength={6000} required minLength={2} placeholder="Plain text. Line breaks are kept." />
      <label className="small eyebrow" htmlFor="letter-link">Link (optional, /page or https://…)</label>
      <input id="letter-link" type="text" value={link} onChange={(e) => setLink(e.target.value)} placeholder="/changelog" />
      {msg && <div className="note small" data-tone={msg.startsWith("Sent") ? "success" : "error"}>{msg}</div>}
      <div className="row"><button type="submit" className="btn primary" disabled={busy}>{busy ? "Sending…" : "Send"}</button></div>
    </form>
  );
}

/** Admin: the mail sent so far, with an unsend button. */
export function SentList({ letters }: { letters: (Letter & { reads: number; name?: string | null })[] }) {
  const router = useRouter();
  async function unsend(id: number) {
    if (!confirm(`Unsend #${id}? Members who have not opened it will never see it.`)) return;
    await fetch(`/api/admin/letters/${id}`, { method: "DELETE" });
    router.refresh();
  }
  const who = (l: Letter & { name?: string | null }) => l.member_id === 0 ? "everyone" : l.member_id === -1 ? "staff" : (l.name ?? `member ${l.member_id}`);
  return (
    <table className="adm">
      <thead><tr><th>#</th><th>To</th><th>Kind</th><th>Subject</th><th>Sent</th><th>Opened</th><th></th></tr></thead>
      <tbody>
        {letters.map((l) => (
          <tr key={l.id}>
            <td>{l.id}</td><td>{who(l)}</td><td>{l.kind}</td><td>{l.title}</td><td>{l.created_at.slice(0, 16)}</td><td>{l.reads}</td>
            <td><button type="button" className="btn" onClick={() => unsend(l.id)}>Unsend</button></td>
          </tr>
        ))}
        {letters.length === 0 && <tr><td colSpan={7} className="muted">Nothing sent yet.</td></tr>}
      </tbody>
    </table>
  );
}
