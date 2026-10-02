import Markdown from "@/components/Markdown";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

type Entry = { version: string; date: string; title: string; body: string; rev: number | null };
export async function generateMetadata() {
  const t = await getT();
  return { title: t("Changelog") };
}

export default async function Changelog() {
  const t = await getT();
  const data = await api<{ current: string | null; rev: number | null; entries: Entry[] }>("/changelog");
  return (
    <>
      <PageHeader art="header-library" title={t("Changelog")} />
      <p className="muted">{rich(t("Current version: {version}. Only pushed releases are posted to #patch-notes on Discord."), { version: <b>{data?.current ?? "—"}</b> })}{data?.rev != null && <> <span className="pill" title="rev">rev {data.rev}</span></>}</p>
      {data?.entries.map((e) => (
        <section key={e.version} className="card" style={{ marginBottom: 12 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>{e.version}</h3>
            <span className="muted small">{e.rev != null && <span className="pill" style={{ marginRight: 8 }}>rev {e.rev}</span>}{e.date}</span>
          </div>
          <div style={{ marginTop: 8 }}><Markdown text={e.body} /></div>
        </section>
      ))}
    </>
  );
}
