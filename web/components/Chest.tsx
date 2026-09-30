"use client";
import Link from "next/link";
import { useState } from "react";
import { rich } from "@/lib/i18n-config";
import { useT } from "./I18n";
import Ico from "./Ico";

type Result = { status: "accepted" | "pending" | "practice"; message: string; xp?: number; loot?: { name: string; tier: string; flavour?: string; color: string } | null; route?: string };
type Prev = { id: number; status: string; route: string; notes: string | null; created_at: string; decided_at: string | null; payload: Record<string, unknown> };

export default function Chest({ questId, verifyType, ueVersion, previous, isO5, pendingArt }:
  { pendingArt?: string | null; questId: string; verifyType: string; ueVersion: string | null; previous: Prev[]; isO5: boolean }) {
  const t = useT();
  const [text, setText] = useState("");
  const [ue, setUe] = useState(ueVersion ?? "");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [res, setRes] = useState<Result | null>(null);
  const pending = previous.find((p) => p.status === "pending");

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    const fd = new FormData();
    fd.set("text", text); fd.set("ue_version", ue);
    files.forEach((f) => fd.append("files", f));
    const r = await fetch(`/api/me/quests/${questId}/submit`, { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) setErr(j.detail ?? t("Could not send.")); else setRes(j);
    setBusy(false);
  }

  if (res) {
    return (
      <div className="chest open">
        {res.status === "pending" && pendingArt && <img className="px result-art" src={pendingArt} width={160} height={120} alt="" />}
        <h3 style={{ marginTop: 0 }}>{res.status === "accepted" ? <><Ico group="quest-steps" id="turn-in" className="h-ico" />{t("Chest opened")}</> : res.status === "pending" ? <><Ico group="quest-state" id="pending" className="h-ico" />{t("Sent to the reviewers")}</> : <><Ico group="quest-state" id="done" className="h-ico" />{t("Practice done")}</>}</h3>
        <p>{res.message}</p>
        {res.loot && <p>{rich(t("New outfit: {name} {flavour}"), { name: <b style={{ color: res.loot.color }}>{res.loot.name}</b>, flavour: <i>{res.loot.flavour}</i> })}</p>}
        <div className="row">
          <Link className="btn primary" href="/">{t("Next dungeon")}</Link>
          {res.loot && <Link className="btn" href="/me">{t("Wear it")}</Link>}
        </div>
      </div>
    );
  }
  if (pending) {
    return <div className="chest"><p className="muted">{t("You sent this on {date}. The chest opens when a reviewer accepts it ({route}).", { date: pending.created_at.slice(0, 10), route: pending.route })}</p></div>;
  }
  return (
    <form className="chest" onSubmit={send}>
      {previous.length > 0 && previous[0].status !== "pass" && (
        <div className="note small" style={{ marginBottom: 10 }}>
          {rich(t("Last time: {status}. Fix it and send again."), { status: <><b>{previous[0].status}</b>{previous[0].notes ? ` · ${previous[0].notes}` : ""}</> })}
        </div>
      )}
      <label className="small eyebrow" htmlFor="chest-text">{isO5 ? t("Type READY") : verifyType === "writeup" ? t("Your writeup") : t("What you did, in a few lines")}</label>
      <textarea id="chest-text" value={text} onChange={(e) => setText(e.target.value)} rows={verifyType === "writeup" ? 8 : 4} required
        placeholder={isO5 ? "READY" : t("What you built, what you changed, what you learned. Paste links here too.")} />
      {!isO5 && (
        <div className="row" style={{ marginTop: 10 }}>
          <div className="upload" style={{ flex: 1, minWidth: 200 }}>
            <label className="small eyebrow" htmlFor="chest-files">{verifyType === "screenshot" ? t("Screenshots (required)") : t("Screenshots (optional)")}</label>
            <input id="chest-files" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 4))} />
            {files.length > 0 && <div className="small muted">{files.map((f) => f.name).join(", ")}</div>}
          </div>
          <div style={{ width: 140 }}>
            <label className="small eyebrow" htmlFor="chest-ue">{t("Unreal version")}</label>
            <input id="chest-ue" value={ue} onChange={(e) => setUe(e.target.value)} placeholder="5.8" style={{ width: "100%" }} />
          </div>
        </div>
      )}
      {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
      <div className="row" style={{ marginTop: 12 }}>
        <button type="submit" className="primary" disabled={busy}>{busy ? t("Sending…") : t("Open the chest")}</button>
        <span className="small muted">{t("Up to 4 images, 8 MB each.")}</span>
      </div>
    </form>
  );
}
