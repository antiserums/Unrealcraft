"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
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

/** Mail, laid out like a desktop mail client: folders on the left, the message list in the middle, the open mail
 *  in a reading pane on the right that never hides the list. Every row says what it is (a coloured type tag),
 *  who it is from, the subject and a preview. */
export default function Letters({ letters }: { letters: Letter[] }) {
  const t = useT();
  const router = useRouter();
  const [folder, setFolder] = useState("inbox");
  const [readIds, setReadIds] = useState<Set<number>>(new Set(letters.filter((l) => l.read).map((l) => l.id)));
  const [openId, setOpenId] = useState<number | null>(letters.find((l) => !l.read)?.id ?? letters[0]?.id ?? null);
  const isRead = (l: Letter) => readIds.has(l.id);
  const from = (l: Letter) => l.sender ?? (l.kind === "announcement" || l.kind === "letter" ? t("Staff") : "Unrealcraft");
  const current = FOLDERS.find((f) => f.key === folder) ?? FOLDERS[0];
  const shown = useMemo(() => letters.filter((l) => current.match(l, isRead(l))), [letters, current, readIds]);   // eslint-disable-line react-hooks/exhaustive-deps
  const open = letters.find((l) => l.id === openId) ?? null;
  const unread = letters.filter((l) => !isRead(l)).length;

  async function show(l: Letter) {
    setOpenId(l.id);
    if (!readIds.has(l.id)) {
      setReadIds(new Set([...readIds, l.id]));
      await post(`/me/letters/${l.id}/read`);
      router.refresh();
    }
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

  const Tag = ({ kind }: { kind: string }) => { const k = KIND[kind] ?? KIND.letter; return <span className="mail-tag" style={{ color: k.color, borderColor: k.color }}>{t(k.label)}</span>; };
  const Sender = ({ l, big = false }: { l: Letter; big?: boolean }) => (
    <span className={`mail-sender ${big ? "big" : ""}`}>
      {l.sender_avatar ? <img className="avatar" src={l.sender_avatar} alt="" /> : <span className="mail-seal" aria-hidden="true">{l.sender ? l.sender.slice(0, 1) : "U"}</span>}
      <span>{from(l)}</span>
    </span>
  );

  return (
    <div className="mailbox-page">
      <aside className="mail-side">
        <div className="eyebrow" style={{ marginBottom: 6 }}>{t("Folders")}</div>
        {FOLDERS.map((f) => {
          const n = letters.filter((l) => f.match(l, isRead(l)) && !isRead(l)).length;
          return (
            <button key={f.key} type="button" className={`bare mail-folder ${folder === f.key ? "on" : ""}`} onClick={() => setFolder(f.key)} aria-current={folder === f.key ? "true" : undefined}>
              <Ico group={f.group} id={f.icon} className="mail-folder-ico" />
              <span className="mail-folder-name">{t(f.label)}</span>
              {n > 0 && <span className="count">{n}</span>}
            </button>
          );
        })}
        {unread > 0 && <button type="button" className="btn mail-readall" onClick={readAll}>{t("Mark all read")}</button>}
      </aside>

      <section className="card mail-list" aria-label={t(current.label)}>
        <div className="mail-list-head"><b>{t(current.label)}</b><span className="muted small">{t("{n} messages", { n: shown.length })}</span></div>
        {shown.length === 0 && <div className="muted small" style={{ padding: "18px 12px" }}>{t("Nothing here.")}</div>}
        {shown.map((l) => (
          <button key={l.id} type="button" className={`bare mail-row ${isRead(l) ? "" : "unread"} ${openId === l.id ? "on" : ""}`} onClick={() => show(l)} aria-current={openId === l.id ? "true" : undefined}>
            <span className="mail-dot" aria-hidden="true" />
            <span className="mail-row-main">
              <span className="mail-row-top"><Sender l={l} /><span className="mail-when">{when(l.created_at)}</span></span>
              <span className="mail-subject">{l.title}</span>
              <span className="mail-row-bottom"><Tag kind={l.kind} /><span className="mail-preview">{l.body.replace(/\s+/g, " ").slice(0, 90)}</span></span>
            </span>
          </button>
        ))}
      </section>

      <article className="card mail-read" aria-live="polite">
        {open ? (
          <>
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
          </>
        ) : (
          <div className="mail-empty"><span className="mail-glyph big" aria-hidden="true" /><p className="muted">{t("Pick a message to read it here.")}</p></div>
        )}
      </article>
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
