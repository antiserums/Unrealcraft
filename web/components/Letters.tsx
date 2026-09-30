"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useT } from "./I18n";
import Ico from "./Ico";

export type Letter = { id: number; member_id: number; kind: string; title: string; body: string; link: string | null; sender_id: number | null; created_at: string; read: boolean };

/** What each kind of letter is, for the label and the icon. */
const KIND: Record<string, { label: string; group: "quest-state" | "rewards" | "utility" | "statistics"; icon: string }> = {
  letter: { label: "Letter", group: "utility", icon: "edit" },
  announcement: { label: "Announcement", group: "statistics", icon: "members" },
  ticket: { label: "Ticket", group: "quest-state", icon: "pending" },
  review: { label: "Review", group: "quest-state", icon: "done" },
  rank: { label: "Rank", group: "rewards", icon: "rank-up" },
  donation: { label: "Thank you", group: "rewards", icon: "outfit" },
};
/** The inbox folders: a filter each. */
const FOLDERS: { key: string; label: string; match: (l: Letter, read: boolean) => boolean }[] = [
  { key: "all", label: "Inbox", match: () => true },
  { key: "unread", label: "Unread", match: (_, read) => !read },
  { key: "announcement", label: "Announcements", match: (l) => l.kind === "announcement" },
  { key: "letter", label: "Letters", match: (l) => l.kind === "letter" },
  { key: "ticket", label: "Tickets", match: (l) => l.kind === "ticket" },
  { key: "review", label: "Reviews", match: (l) => l.kind === "review" },
  { key: "rewards", label: "Ranks and rewards", match: (l) => l.kind === "rank" || l.kind === "donation" },
];

async function post(path: string) {
  await fetch(`/api${path}`, { method: "POST" }).catch(() => null);
}

/** The mailbox: folders on the left, the list in the middle, the open letter on the right. Opening a letter marks
 *  it read. On a phone the three stack. */
export default function Letters({ letters }: { letters: Letter[] }) {
  const t = useT();
  const router = useRouter();
  const [folder, setFolder] = useState("all");
  const [readIds, setReadIds] = useState<Set<number>>(new Set(letters.filter((l) => l.read).map((l) => l.id)));
  const [openId, setOpenId] = useState<number | null>(letters.find((l) => !l.read)?.id ?? letters[0]?.id ?? null);
  const isRead = (l: Letter) => readIds.has(l.id);
  const shown = useMemo(() => letters.filter((l) => (FOLDERS.find((f) => f.key === folder) ?? FOLDERS[0]).match(l, isRead(l))), [letters, folder, readIds]);   // eslint-disable-line react-hooks/exhaustive-deps
  const open = letters.find((l) => l.id === openId) ?? null;

  async function show(l: Letter) {
    setOpenId(l.id);
    if (!readIds.has(l.id)) {
      setReadIds(new Set([...readIds, l.id]));
      await post(`/me/letters/${l.id}/read`);
      router.refresh();
    }
  }
  async function readAll() {
    setReadIds(new Set(letters.map((l) => l.id)));
    await post("/me/letters/read-all");
    router.refresh();
  }
  const unread = letters.filter((l) => !isRead(l)).length;

  return (
    <div className="inbox">
      <nav className="inbox-folders" aria-label={t("Folders")}>
        {FOLDERS.map((f) => {
          const n = letters.filter((l) => f.match(l, isRead(l)) && !isRead(l)).length;
          return (
            <button key={f.key} type="button" className={`bare inbox-folder ${folder === f.key ? "on" : ""}`} onClick={() => setFolder(f.key)}>
              <span>{t(f.label)}</span>{n > 0 && <span className="count">{n}</span>}
            </button>
          );
        })}
        {unread > 0 && <button type="button" className="btn inbox-readall" onClick={readAll}>{t("Mark all read")}</button>}
      </nav>

      <div className="inbox-list card">
        {shown.length === 0 && <div className="muted small" style={{ padding: 10 }}>{t("Nothing in this folder.")}</div>}
        {shown.map((l) => {
          const k = KIND[l.kind] ?? KIND.letter;
          return (
            <button key={l.id} type="button" className={`bare inbox-row ${isRead(l) ? "" : "unread"} ${openId === l.id ? "on" : ""}`} onClick={() => show(l)} aria-current={openId === l.id ? "true" : undefined}>
              <Ico group={k.group} id={k.icon} className="pill-ico" />
              <span className="inbox-row-text">
                <span className="inbox-title">{l.title}</span>
                <span className="small muted">{t(k.label)} · {l.created_at.slice(0, 10)}</span>
              </span>
              {!isRead(l) && <span className="inbox-dot" aria-label={t("new")} />}
            </button>
          );
        })}
      </div>

      <article className="inbox-read card">
        {open ? (
          <>
            <div className="eyebrow">{t((KIND[open.kind] ?? KIND.letter).label)} · {open.created_at.slice(0, 16).replace("T", " ")}</div>
            <h2 style={{ marginTop: 6 }}>{open.title}</h2>
            <p className="letter-text">{open.body}</p>
            {open.link && <Link className="btn primary" href={open.link}>{t("Open")}</Link>}
          </>
        ) : (
          <div className="muted small">{t("Pick a letter to read it.")}</div>
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
      <label className="small eyebrow" htmlFor="letter-title">Title</label>
      <input id="letter-title" type="text" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} required minLength={2} />
      <label className="small eyebrow" htmlFor="letter-body">Letter</label>
      <textarea id="letter-body" value={body} onChange={(e) => setBody(e.target.value)} rows={7} maxLength={6000} required minLength={2} placeholder="Plain text. Line breaks are kept." />
      <label className="small eyebrow" htmlFor="letter-link">Link (optional, /page or https://…)</label>
      <input id="letter-link" type="text" value={link} onChange={(e) => setLink(e.target.value)} placeholder="/changelog" />
      {msg && <div className="note small" data-tone={msg.startsWith("Sent") ? "success" : "error"}>{msg}</div>}
      <div className="row"><button type="submit" className="btn primary" disabled={busy}>{busy ? "Sending…" : "Send letter"}</button></div>
    </form>
  );
}

/** Admin: the letters sent so far, with an unsend button. */
export function SentList({ letters }: { letters: (Letter & { reads: number; name?: string | null })[] }) {
  const router = useRouter();
  async function unsend(id: number) {
    if (!confirm(`Unsend letter #${id}? Members who have not opened it will never see it.`)) return;
    await fetch(`/api/admin/letters/${id}`, { method: "DELETE" });
    router.refresh();
  }
  const who = (l: Letter & { name?: string | null }) => l.member_id === 0 ? "everyone" : l.member_id === -1 ? "staff" : (l.name ?? `member ${l.member_id}`);
  return (
    <table className="adm">
      <thead><tr><th>#</th><th>To</th><th>Kind</th><th>Title</th><th>Sent</th><th>Opened</th><th></th></tr></thead>
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
