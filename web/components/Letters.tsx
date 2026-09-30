"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useT } from "./I18n";
import Ico from "./Ico";

export type Letter = { id: number; member_id: number; kind: string; title: string; body: string; link: string | null; sender_id: number | null; sender?: string | null; created_at: string; read: boolean };

/** What each kind of letter is: the label, the icon and who it reads as being from. */
const KIND: Record<string, { label: string; group: "quest-state" | "rewards" | "utility" | "statistics"; icon: string }> = {
  letter: { label: "Letter", group: "utility", icon: "edit" },
  announcement: { label: "Announcement", group: "statistics", icon: "members" },
  ticket: { label: "Ticket", group: "quest-state", icon: "pending" },
  review: { label: "Review", group: "quest-state", icon: "done" },
  rank: { label: "Rank", group: "rewards", icon: "rank-up" },
  donation: { label: "Thank you", group: "rewards", icon: "outfit" },
};
/** The filter tabs across the top. */
const TABS: { key: string; label: string; match: (l: Letter, read: boolean) => boolean }[] = [
  { key: "all", label: "All", match: () => true },
  { key: "unread", label: "Unread", match: (_, read) => !read },
  { key: "announcement", label: "Announcements", match: (l) => l.kind === "announcement" || l.kind === "letter" },
  { key: "ticket", label: "Tickets", match: (l) => l.kind === "ticket" },
  { key: "review", label: "Reviews", match: (l) => l.kind === "review" },
  { key: "rewards", label: "Ranks and rewards", match: (l) => l.kind === "rank" || l.kind === "donation" },
];

async function post(path: string) {
  await fetch(`/api${path}`, { method: "POST" }).catch(() => null);
}

/** Relative date for the list: today's time, else the day. */
function when(iso: string): string {
  const d = new Date(iso.replace(" ", "T") + "Z");
  const now = new Date();
  const same = d.toDateString() === now.toDateString();
  return same ? d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) : d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** The inbox. A list of letters like any mail app: who it is from, the subject and a preview, the date on the
 *  right, unread rows in bold. Click a row to read it full width; Back returns to the list. Tabs filter. */
export default function Letters({ letters }: { letters: Letter[] }) {
  const t = useT();
  const router = useRouter();
  const [tab, setTab] = useState("all");
  const [readIds, setReadIds] = useState<Set<number>>(new Set(letters.filter((l) => l.read).map((l) => l.id)));
  const [openId, setOpenId] = useState<number | null>(null);
  const isRead = (l: Letter) => readIds.has(l.id);
  const from = (l: Letter) => l.sender ?? (l.kind === "announcement" || l.kind === "letter" ? t("Staff") : "Unrealcraft");
  const shown = useMemo(() => letters.filter((l) => (TABS.find((f) => f.key === tab) ?? TABS[0]).match(l, isRead(l))), [letters, tab, readIds]);   // eslint-disable-line react-hooks/exhaustive-deps
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

  if (open) {
    const k = KIND[open.kind] ?? KIND.letter;
    const i = shown.findIndex((l) => l.id === open.id);
    return (
      <div className="mail">
        <div className="mail-bar">
          <button type="button" className="btn" onClick={() => setOpenId(null)}>← {t("Back")}</button>
          <span className="spacer" />
          <span className="small muted">{i + 1} / {shown.length}</span>
          <button type="button" className="btn" disabled={i <= 0} onClick={() => step(-1)} aria-label={t("Newer")}>‹</button>
          <button type="button" className="btn" disabled={i >= shown.length - 1} onClick={() => step(1)} aria-label={t("Older")}>›</button>
        </div>
        <article className="card mail-read">
          <div className="mail-read-head">
            <Ico group={k.group} id={k.icon} className="pill-ico" />
            <div style={{ flex: 1, minWidth: 0 }}>
              <h2 style={{ margin: 0 }}>{open.title}</h2>
              <div className="small muted">{t("From {who}", { who: from(open) })} · {t(k.label)} · {open.created_at.slice(0, 16).replace("T", " ")}</div>
            </div>
          </div>
          <p className="letter-text">{open.body}</p>
          {open.link && <Link className="btn primary" href={open.link}>{t("Open")}</Link>}
        </article>
      </div>
    );
  }

  return (
    <div className="mail">
      <div className="mail-bar">
        <nav className="mail-tabs" aria-label={t("Folders")}>
          {TABS.map((f) => {
            const n = letters.filter((l) => f.match(l, isRead(l)) && !isRead(l)).length;
            return (
              <button key={f.key} type="button" className={`bare mail-tab ${tab === f.key ? "on" : ""}`} onClick={() => setTab(f.key)} aria-pressed={tab === f.key}>
                {t(f.label)}{n > 0 && <span className="count">{n}</span>}
              </button>
            );
          })}
        </nav>
        <span className="spacer" />
        {unread > 0 && <button type="button" className="btn" onClick={readAll}>{t("Mark all read")}</button>}
      </div>
      <div className="card mail-list">
        {shown.length === 0 && <div className="muted small" style={{ padding: "18px 12px" }}>{t("Nothing here.")}</div>}
        {shown.map((l) => {
          const k = KIND[l.kind] ?? KIND.letter;
          const unreadRow = !isRead(l);
          return (
            <button key={l.id} type="button" className={`bare mail-row ${unreadRow ? "unread" : ""}`} onClick={() => show(l)}>
              <span className="mail-dot" aria-hidden="true" />
              <Ico group={k.group} id={k.icon} className="mail-ico" />
              <span className="mail-from">{from(l)}</span>
              <span className="mail-subject"><b>{l.title}</b><span className="mail-preview"> — {l.body.replace(/\s+/g, " ").slice(0, 120)}</span></span>
              <span className="mail-when">{when(l.created_at)}</span>
            </button>
          );
        })}
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
