import Markdown from "@/components/Markdown";
import { api } from "@/lib/api";

type Entry = { version: string; date: string; title: string; body: string };
export const metadata = { title: "Changelog" };

export default async function Changelog() {
  const data = await api<{ current: string | null; entries: Entry[] }>("/changelog");
  return (
    <>
      <h1>Changelog</h1>
      <p className="muted">Current version: <b>{data?.current ?? "—"}</b>. Only pushed releases are posted to #patch-notes on Discord.</p>
      {data?.entries.map((e) => (
        <section key={e.version} className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>{e.version}</h3>
            <span className="muted small">{e.date}</span>
          </div>
          <div style={{ marginTop: 8 }}><Markdown text={e.body} /></div>
        </section>
      ))}
    </>
  );
}
