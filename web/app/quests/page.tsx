import Link from "next/link";
import PathView from "@/components/PathView";
import QuestCard from "@/components/QuestCard";
import { api, type Majors, type Me, type PathData, type QuestSummary } from "@/lib/api";

const TIERS = ["novice", "apprentice", "adept", "expert", "master"];

export const metadata = { title: "Quest board" };

export default async function Quests({ searchParams }: PageProps<"/quests">) {
  const sp = await searchParams;
  const pick = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : "");
  const me = await api<Me>("/me");
  const view = pick("view") === "path" || (!pick("view") && !pick("major") && !pick("tier") && !pick("q") && !pick("subject") && me) ? "path" : "all";
  return (
    <>
      <h1>Quest board</h1>
      <nav className="subnav" aria-label="Quest board views">
        <Link href="/quests?view=path" className={view === "path" ? "on" : ""}>My path</Link>
        <Link href="/quests?view=all" className={view === "all" ? "on" : ""}>All quests</Link>
      </nav>
      {view === "path" ? <Path me={me} /> : <All sp={sp} />}
    </>
  );
}

async function Path({ me }: { me: Me | null }) {
  if (!me) {
    return (
      <div className="card">
        <p style={{ margin: 0 }}>Your path is the road through your major: what is next, what is done, what the next rank opens.</p>
        <div className="row" style={{ marginTop: 12 }}>
          <a className="btn primary" href="/api/auth/discord?next=/quests">Enter with Discord</a>
          <Link className="btn" href="/quests?view=all">Browse all quests</Link>
        </div>
      </div>
    );
  }
  const p = await api<PathData>("/me/path");
  if (!p) return <div className="card">The Quartermaster has not seen you yet. Press <b>Start Questing</b> in #welcome on Discord to begin Orientation.</div>;
  return <PathView p={p} />;
}

async function All({ sp }: { sp: Record<string, string | string[] | undefined> }) {
  const pick = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : "");
  const major = pick("major"), tier = pick("tier"), q = pick("q"), subject = pick("subject");
  const qs = new URLSearchParams();
  if (major) qs.set("major", major);
  if (tier) qs.set("tier", tier);
  if (q) qs.set("q", q);
  if (subject) qs.set("subject", subject);
  const [majors, data, subjects] = await Promise.all([
    api<Majors>("/catalog/majors"),
    api<{ count: number; quests: QuestSummary[] }>(`/catalog/quests?${qs}`),
    api<{ subjects: [string, number][] }>("/catalog/subjects"),
  ]);
  const all = data?.quests ?? [];
  const quests = all.filter((x) => !x.cross);
  const cross = all.filter((x) => x.cross);
  const byTier = TIERS.map((t) => ({ t, list: quests.filter((x) => x.difficulty === t) })).filter((g) => g.list.length);
  const majorTitle = major && majors ? majors.majors[major]?.title : null;
  return (
    <>
      <p className="muted">
        {majorTitle ? `${quests.length} ${majorTitle} quests` : `${quests.length} of ${majors?.quest_count ?? 0} quests`}
        {cross.length > 0 && `, plus ${cross.length} cross-training`}. Browse freely; log in to earn.
      </p>
      <form className="filters" method="get">
        <input type="hidden" name="view" value="all" />
        <select name="major" defaultValue={major}>
          <option value="">All majors</option>
          {majors && Object.values(majors.majors).map((m) => <option key={m.key} value={m.key}>{m.title}</option>)}
        </select>
        <select name="tier" defaultValue={tier}>
          <option value="">All tiers</option>
          {majors && TIERS.map((t) => <option key={t} value={t}>{majors.tiers[t].emoji} {majors.tiers[t].name}</option>)}
        </select>
        <select name="subject" defaultValue={subject}>
          <option value="">All subjects</option>
          {subjects?.subjects.slice(0, 60).map(([s, n]) => <option key={s} value={s}>{s} ({n})</option>)}
        </select>
        <input name="q" placeholder="Search title or ID" defaultValue={q} />
        <button type="submit" className="primary">Filter</button>
      </form>
      {byTier.map(({ t, list }) => (
        <section key={t}>
          <div className="section-h">
            <h2>{majors?.tiers[t].emoji} {majors?.tiers[t].name}</h2>
            <span className="muted small">{list.length} quests</span>
          </div>
          <div className="grid">{list.map((x) => <QuestCard key={x.id} q={x} />)}</div>
        </section>
      ))}
      {cross.length > 0 && (
        <section className="lock">
          <div className="section-h">
            <h2>Cross-training from other majors</h2>
            <span className="muted small">{cross.length} quests · optional, do not count toward {majorTitle} rank-ups</span>
          </div>
          <div className="grid">{cross.map((x) => <QuestCard key={x.id} q={x} />)}</div>
        </section>
      )}
      {all.length === 0 && <div className="card">No quests match. Clear a filter.</div>}
    </>
  );
}
