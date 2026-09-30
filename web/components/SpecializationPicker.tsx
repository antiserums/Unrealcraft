"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { MySpecialization, SpecializationOption } from "@/lib/api";

/** Primary plus extras. The primary drives ranks, the next quest and the nameplate; extras make those quests
 *  count as yours (XP bonus at Expert and up, "yours" on the Quest Board) and feed cross-specialization rewards. */
export default function SpecializationPicker({ mine, options }: { mine: MySpecialization[]; options: SpecializationOption[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [primary, setPrimary] = useState(mine.find((s) => s.primary)?.key ?? "undecided");
  const [extras, setExtras] = useState<string[]>(mine.filter((s) => !s.primary).map((s) => s.key));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const startPrimary = mine.find((s) => s.primary)?.key ?? "undecided";
  const startExtras = mine.filter((s) => !s.primary).map((s) => s.key).sort().join(",");
  const dirty = primary !== startPrimary || [...extras].sort().join(",") !== startExtras;

  async function save() {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/specializations", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ primary, extras: extras.filter((e) => e !== primary) }) });
    setBusy(false);
    if (!r.ok) { setErr((await r.json()).detail ?? "Could not save."); return; }
    setOpen(false); router.refresh();
  }
  function toggle(k: string) { setExtras((x) => (x.includes(k) ? x.filter((e) => e !== k) : [...x, k])); }

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="eyebrow">Specializations</div>
          <div style={{ marginTop: 4 }}>
            {mine.length ? mine.map((s) => <span key={s.key} className="pill" style={{ marginRight: 6, borderColor: s.primary ? "var(--gold)" : undefined }}>{s.title}{s.primary ? " · primary" : ""}</span>) : <span className="muted">Undecided. Pick one to get a path.</span>}
          </div>
        </div>
        {!open && <button onClick={() => setOpen(true)}>Change</button>}
      </div>
      {open && (
        <div style={{ marginTop: 12 }}>
          <div className="small muted">Your primary sets your path, your rank requirements and your nameplate. Extras make their quests count as yours too. Finishing quests across specializations earns its own entitlements.</div>
          <div className="adm-grid" style={{ marginTop: 8 }}>
            <div>
              <label>Primary</label>
              <select value={primary} onChange={(e) => setPrimary(e.target.value)}>
                <option value="undecided">Undecided</option>
                {options.map((o) => <option key={o.key} value={o.key}>{o.title}</option>)}
              </select>
            </div>
            <div className="wide" style={{ marginTop: 0 }}>
              <label>Extras</label>
              <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
                {options.filter((o) => o.key !== primary).map((o) => (
                  <label key={o.key} className="row small" style={{ gap: 5, textTransform: "none", letterSpacing: 0, color: "var(--ink)", cursor: "pointer" }} title={o.blurb}>
                    <input type="checkbox" checked={extras.includes(o.key)} onChange={() => toggle(o.key)} /> {o.title}
                  </label>
                ))}
              </div>
            </div>
          </div>
          {primary !== startPrimary && startPrimary !== "undecided" && <div className="note small" style={{ marginTop: 8 }}>Changing your primary changes which quests your next rank needs. Your finished quests stay finished.</div>}
          {err && <div className="note small" style={{ marginTop: 8, borderColor: "var(--bad)" }}>{err}</div>}
          <div className="row" style={{ gap: 6, marginTop: 10 }}>
            <button className="primary" onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save"}</button>
            <button onClick={() => { setOpen(false); setPrimary(startPrimary); setExtras(startExtras ? startExtras.split(",") : []); setErr(null); }} disabled={busy}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
