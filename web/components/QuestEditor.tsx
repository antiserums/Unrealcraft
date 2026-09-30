"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Curriculum } from "./QuestList";

type Quiz = { q: string; choices: string[]; answer_index: number; explain: string };
type Form = {
  id: string; title: string; rank: string; difficulty: string; track: string; subjects: string; required_for_majors: string; taster_for_majors: string;
  adjacent_for: string; required_spine: boolean; elective: boolean; capstone: boolean; needs_others: boolean; time_min: string; xp: string; verify_type: string;
  official_url: string; backup_url: string; extra_urls: string; community_urls: string; checklist: string; done_when: string; action_key: string; next_hint: string;
  quiz: Quiz[]; flavors: string;
};

const NEW_YAML = `id: LDQ99
rank: 1
difficulty: apprentice
track: level-design
subjects: [blockout]
required_for_majors: []
taster_for_majors: []
adjacent_for: []
required_spine: false
elective: true
title: A short imperative title
time_min: 30
official_url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/"
checklist:
  - "First thing to do in the editor."
  - "Second thing."
done_when: "What the turn-in must show."
xp: 40
verify_type: screenshot
quiz:
  - q: "A question?"
    choices: ["A", "B", "C", "D"]
    answer_index: 0
    explain: "Why A is right."
flavors:
  _default: {why: "Why this matters."}
`;

const lines = (v: unknown) => Array.isArray(v) ? v.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join("\n") : "";
const str = (v: unknown) => (v === null || v === undefined ? "" : String(v));

function toYamlish(o: Record<string, unknown> | undefined): string {
  // flavors as YAML text the admin can edit; the API parses it back (majors -> {why, do})
  if (!o) return "_default: {why: \"\"}";
  return Object.entries(o).map(([k, v]) => {
    const inner = v && typeof v === "object" ? Object.entries(v as Record<string, string>).map(([a, b]) => `${a}: ${JSON.stringify(b ?? "")}`).join(", ") : "";
    return `${k}: {${inner}}`;
  }).join("\n");
}

function fromRaw(raw: Record<string, unknown> | null, cur: Curriculum): Form {
  const r = raw ?? {};
  return {
    id: str(r.id), title: str(r.title), rank: str(r.rank ?? 1), difficulty: str(r.difficulty ?? "apprentice"), track: str(r.track ?? cur.tracks[0] ?? ""),
    subjects: (r.subjects as string[] | undefined)?.join(", ") ?? "", required_for_majors: (r.required_for_majors as string[] | undefined)?.join(", ") ?? "",
    taster_for_majors: (r.taster_for_majors as string[] | undefined)?.join(", ") ?? "", adjacent_for: (r.adjacent_for as string[] | undefined)?.join(", ") ?? "",
    required_spine: !!r.required_spine, elective: raw ? !!r.elective : true, capstone: !!r.capstone, needs_others: !!r.needs_others,
    time_min: str(r.time_min ?? 30), xp: str(r.xp ?? 40), verify_type: str(r.verify_type ?? "screenshot"),
    official_url: str(r.official_url), backup_url: str(r.backup_url), extra_urls: lines(r.extra_urls), community_urls: lines(r.community_urls),
    checklist: lines(r.checklist), done_when: str(r.done_when), action_key: str(r.action_key), next_hint: str(r.next_hint),
    quiz: ((r.quiz as Quiz[] | undefined) ?? []).map((x) => ({ q: x.q ?? "", choices: [...(x.choices ?? [])], answer_index: Number(x.answer_index ?? 0), explain: x.explain ?? "" })),
    flavors: toYamlish(r.flavors as Record<string, unknown> | undefined),
  };
}

function toRaw(f: Form): Record<string, unknown> {
  const list = (s: string) => s.split(/[\n,]/).map((x) => x.trim()).filter(Boolean);
  const nl = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);
  return {
    id: f.id.trim().toUpperCase(), rank: Number(f.rank), difficulty: f.difficulty, track: f.track.trim(), subjects: list(f.subjects),
    required_for_majors: list(f.required_for_majors), taster_for_majors: list(f.taster_for_majors), adjacent_for: list(f.adjacent_for),
    required_spine: f.required_spine, elective: f.elective, capstone: f.capstone, ...(f.needs_others ? { needs_others: true } : {}),
    title: f.title.trim(), time_min: f.time_min ? Number(f.time_min) : null, official_url: f.official_url.trim() || "TODO_URL", backup_url: f.backup_url.trim() || null,
    extra_urls: nl(f.extra_urls), community_urls: nl(f.community_urls), checklist: nl(f.checklist), done_when: f.done_when.trim(), xp: Number(f.xp),
    verify_type: f.verify_type, action_key: f.action_key.trim() || null, next_hint: f.next_hint.trim() || null,
    quiz: f.quiz.map((x) => ({ q: x.q, choices: x.choices, answer_index: Number(x.answer_index), explain: x.explain })), flavors: f.flavors,
  };
}

/** Add or edit one quest. Form mode covers every field the curriculum uses; YAML mode takes the quest as text. */
export default function QuestEditor({ cur, initial, file: file0, yamlText }: { cur: Curriculum; initial: Record<string, unknown> | null; file: string; yamlText: string | null }) {
  const router = useRouter();
  const isNew = initial === null;
  const [tab, setTab] = useState<"form" | "yaml">("form");
  const [f, setF] = useState<Form>(() => fromRaw(initial, cur));
  const [yaml, setYaml] = useState(yamlText ?? NEW_YAML);
  const [file, setFile] = useState(file0);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [confirm, setConfirm] = useState("");
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => ({ ...x, [k]: v }));
  const want = cur.tiers[f.difficulty]?.quiz_len;

  async function save() {
    setBusy(true); setErr(null); setMsg(null);
    const body = tab === "form" ? { quest: toRaw(f), file, replace: isNew ? null : String(initial!.id) } : { yaml, file, replace: isNew ? null : String(initial!.id) };
    const r = await fetch("/api/admin/curriculum/quests", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    setBusy(false);
    if (!r.ok) { setErr(j.detail ?? "Could not save."); return; }
    setMsg(j.message + (j.warnings?.length ? ` Warnings: ${j.warnings.join(" · ")}` : ""));
    if (isNew || j.id !== initial!.id) router.push(`/admin/quests/${j.id}`); else router.refresh();
  }
  async function remove() {
    setBusy(true); setErr(null);
    const r = await fetch(`/api/admin/curriculum/quests/${initial!.id}`, { method: "DELETE" });
    const j = await r.json();
    setBusy(false);
    if (!r.ok) { setErr(j.detail ?? "Could not delete."); return; }
    router.push("/admin/quests");
  }
  function quiz(i: number, patch: Partial<Quiz>) { setF((x) => ({ ...x, quiz: x.quiz.map((q, k) => (k === i ? { ...q, ...patch } : q)) })); }
  function choice(i: number, c: number, v: string) { setF((x) => ({ ...x, quiz: x.quiz.map((q, k) => (k === i ? { ...q, choices: q.choices.map((s, n) => (n === c ? v : s)) } : q)) })); }

  return (
    <div className="card adm">
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
        <div className="subnav" style={{ margin: 0 }}>
          <a href="#" className={tab === "form" ? "on" : ""} onClick={(e) => { e.preventDefault(); setTab("form"); }}>Form</a>
          <a href="#" className={tab === "yaml" ? "on" : ""} onClick={(e) => { e.preventDefault(); setTab("yaml"); }}>YAML</a>
        </div>
        <div className="adm-form" style={{ margin: 0 }}>
          <label className="small muted">file</label>
          <input list="quest-files" value={file} onChange={(e) => setFile(e.target.value)} style={{ width: 170 }} />
          <datalist id="quest-files">{cur.files.map((x) => <option key={x} value={x} />)}{!cur.files.includes(cur.default_file) && <option value={cur.default_file} />}</datalist>
          <button className="primary" onClick={save} disabled={busy}>{busy ? "Saving…" : isNew ? "Add quest" : "Save"}</button>
        </div>
      </div>
      {msg && <div className="note small" style={{ marginTop: 10 }}>{msg}</div>}
      {err && <div className="note small" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}

      {tab === "yaml" ? (
        <div className="adm-field">
          <label>One quest as YAML (no <code>quests:</code> wrapper). The form and this text are separate; whichever tab is open is what gets saved.</label>
          <textarea value={yaml} onChange={(e) => setYaml(e.target.value)} rows={28} spellCheck={false} />
        </div>
      ) : (
        <>
          <div className="adm-grid">
            <div><label>Id</label><input value={f.id} onChange={(e) => set("id", e.target.value)} placeholder="LDQ41" disabled={!isNew && false} /></div>
            <div className="wide" style={{ marginTop: 0 }}><label>Title</label><input value={f.title} onChange={(e) => set("title", e.target.value)} placeholder="Snap every block to the grid" /></div>
            <div><label>Rank</label><select value={f.rank} onChange={(e) => set("rank", e.target.value)}><option value="-1">-1 · Orientation</option>{cur.ranks.map((r) => <option key={r.n} value={r.n}>{r.n} · {r.title}</option>)}</select></div>
            <div><label>Difficulty</label><select value={f.difficulty} onChange={(e) => set("difficulty", e.target.value)}>{Object.entries(cur.tiers).map(([k, t]) => <option key={k} value={k}>{t.name} · {t.quiz_len} questions</option>)}</select></div>
            <div><label>Track</label><input list="quest-tracks" value={f.track} onChange={(e) => set("track", e.target.value)} /><datalist id="quest-tracks">{cur.tracks.map((t) => <option key={t} value={t} />)}</datalist></div>
            <div><label>XP</label><input type="number" value={f.xp} onChange={(e) => set("xp", e.target.value)} /></div>
            <div><label>Minutes</label><input type="number" value={f.time_min} onChange={(e) => set("time_min", e.target.value)} /></div>
            <div><label>Verify by</label><select value={f.verify_type} onChange={(e) => set("verify_type", e.target.value)}>{cur.verify_types.map((v) => <option key={v} value={v}>{v}</option>)}</select></div>
            <div><label>Subjects (comma separated)</label><input value={f.subjects} onChange={(e) => set("subjects", e.target.value)} placeholder="snapping, grid" /></div>
            <div><label>Required for majors</label><input value={f.required_for_majors} onChange={(e) => set("required_for_majors", e.target.value)} placeholder={`all, ${cur.majors.slice(0, 2).join(", ")}`} /></div>
            <div><label>Taster for majors</label><input value={f.taster_for_majors} onChange={(e) => set("taster_for_majors", e.target.value)} /></div>
            <div><label>Adjacent for</label><input value={f.adjacent_for} onChange={(e) => set("adjacent_for", e.target.value)} /></div>
            <div className="wide row" style={{ gap: 16, marginTop: 0 }}>
              <label className="row" style={{ gap: 5, textTransform: "none", letterSpacing: 0, fontSize: 13, color: "var(--ink)" }}><input type="checkbox" checked={f.elective} onChange={(e) => set("elective", e.target.checked)} /> elective</label>
              <label className="row" style={{ gap: 5, textTransform: "none", letterSpacing: 0, fontSize: 13, color: "var(--ink)" }}><input type="checkbox" checked={f.required_spine} onChange={(e) => set("required_spine", e.target.checked)} /> on the spine</label>
              <label className="row" style={{ gap: 5, textTransform: "none", letterSpacing: 0, fontSize: 13, color: "var(--ink)" }}><input type="checkbox" checked={f.capstone} onChange={(e) => set("capstone", e.target.checked)} /> capstone</label>
              <label className="row" style={{ gap: 5, textTransform: "none", letterSpacing: 0, fontSize: 13, color: "var(--ink)" }}><input type="checkbox" checked={f.needs_others} onChange={(e) => set("needs_others", e.target.checked)} /> needs other members</label>
            </div>
            <div className="wide" style={{ marginTop: 0 }}><label>Official URL (https)</label><input value={f.official_url} onChange={(e) => set("official_url", e.target.value)} placeholder="https://dev.epicgames.com/…" /></div>
            <div><label>Backup URL</label><input value={f.backup_url} onChange={(e) => set("backup_url", e.target.value)} /></div>
            <div><label>Action key (verify by action)</label><input value={f.action_key} onChange={(e) => set("action_key", e.target.value)} /></div>
            <div><label>Extra URLs (one per line)</label><textarea value={f.extra_urls} onChange={(e) => set("extra_urls", e.target.value)} rows={3} /></div>
            <div><label>Community URLs (one per line)</label><textarea value={f.community_urls} onChange={(e) => set("community_urls", e.target.value)} rows={3} /></div>
          </div>
          <div className="adm-field"><label>Checklist (one step per line)</label><textarea value={f.checklist} onChange={(e) => set("checklist", e.target.value)} rows={6} /></div>
          <div className="adm-field"><label>Done when (what the turn-in must show)</label><textarea value={f.done_when} onChange={(e) => set("done_when", e.target.value)} rows={3} /></div>
          <div className="adm-field"><label>Next hint (optional)</label><input value={f.next_hint} onChange={(e) => set("next_hint", e.target.value)} /></div>
          <div className="adm-field"><label>Flavors, one line per major: <code>major: {"{"}why: &quot;…&quot;, do: &quot;…&quot;{"}"}</code> (<code>_default</code> is the fallback)</label><textarea value={f.flavors} onChange={(e) => set("flavors", e.target.value)} rows={4} /></div>

          <div className="section-h" style={{ margin: "18px 0 6px" }}><h2 style={{ fontSize: 16 }}>Boss fight · quiz</h2><span className="muted small">{f.quiz.length} questions{want ? ` · ${want} wanted for ${cur.tiers[f.difficulty].name}` : ""}</span></div>
          {f.quiz.map((item, i) => (
            <div key={i} className="quiz-item">
              <div className="row" style={{ justifyContent: "space-between" }}>
                <b className="small">Question {i + 1}</b>
                <div className="row" style={{ gap: 4 }}>
                  <button type="button" onClick={() => setF((x) => ({ ...x, quiz: x.quiz.map((q, k) => (k === i ? { ...q, choices: [...q.choices, ""] } : q)) }))} disabled={item.choices.length >= 6} style={{ padding: "3px 8px", fontSize: 11 }}>+ choice</button>
                  <button type="button" onClick={() => setF((x) => ({ ...x, quiz: x.quiz.filter((_, k) => k !== i) }))} style={{ padding: "3px 8px", fontSize: 11 }}>remove</button>
                </div>
              </div>
              <input value={item.q} onChange={(e) => quiz(i, { q: e.target.value })} placeholder="The question" style={{ width: "100%", marginTop: 6 }} />
              <div className="choices">
                {item.choices.map((c, k) => (
                  <label key={k}><input type="radio" name={`ans${i}`} checked={item.answer_index === k} onChange={() => quiz(i, { answer_index: k })} title="the right answer" /><input value={c} onChange={(e) => choice(i, k, e.target.value)} placeholder={`Choice ${k + 1}`} style={{ flex: 1 }} /></label>
                ))}
              </div>
              <input value={item.explain} onChange={(e) => quiz(i, { explain: e.target.value })} placeholder="Explain why the right answer is right" style={{ width: "100%", marginTop: 6 }} />
            </div>
          ))}
          <button type="button" style={{ marginTop: 8 }} onClick={() => setF((x) => ({ ...x, quiz: [...x.quiz, { q: "", choices: ["", "", "", ""], answer_index: 0, explain: "" }] }))}>+ question</button>
        </>
      )}

      {!isNew && (
        <div style={{ marginTop: 24, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
          <h3 style={{ color: "var(--bad)", margin: 0 }}>Delete this quest</h3>
          <div className="small muted">Removes it from {file0}. Members keep their progress rows. Type the id to confirm.</div>
          <div className="adm-form">
            <input value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder={String(initial!.id)} style={{ width: 160 }} />
            <button className="danger" disabled={busy || confirm !== String(initial!.id)} onClick={remove}>Delete</button>
          </div>
        </div>
      )}
    </div>
  );
}
