import Link from "next/link";
import PathView from "@/components/PathView";
import QuestCard from "@/components/QuestCard";
import { api, type Me, type PathData, type QuestSummary, type Specializations } from "@/lib/api";

const TIERS = ["novice", "apprentice", "adept", "expert", "master"];

export const metadata = { title: "Quest board" };

export default async function Quests({ searchParams }: PageProps<"/quests">) {
  const sp = await searchParams;
  const pick = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : "");
  const me = await api<Me>("/me");
  const view = pick("view") === "path" || (!pick("view") && !pick("specialization") && !pick("tier") && !pick("q") && !pick("subject") && me) ? "path" : "all";
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
        <p style={{ margin: 0 }}>Your path is the road through your primary specialization: what is next, what is done, what the next rank opens.</p>
        <div className="row" style={{ marginTop: 12 }}>
          <a className="btn primary" href="/api/auth/discord?next=/quests">Enter with Discord</a>
          <Link className="btn" href="/quests?view=all">Browse all quests</Link>
        </div>
      </div>
    );
  }
  const p = await api<PathData>("/me/path");
  if (!p) return <div className="card">Your path could not be loaded. Log out and back in, then try again.</div>;
  return <PathView p={p} />;
}

async function All({ sp }: { sp: Record<string, string | string[] | undefined> }) {
  const pick = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : "");
  const spec = pick("specialization"), tier = pick("tier"), q = pick("q"), subject = pick("subject");
  const qs = new URLSearchParams();
  if (spec) qs.set("specialization", spec);
  if (tier) qs.set("tier", tier);
  if (q) qs.set("q", q);
  if (subject) qs.set("subject", subject);
  const [specs, data, subjects] = await Promise.all([
    api<Specializations>("/catalog/specializations"),
    api<{ count: number; quests: QuestSummary[] }>(`/catalog/quests?${qs}`),
    api<{ subjects: [string, number][] }>("/catalog/subjects"),
  ]);
  const quests = data?.quests ?? [];
  const byTier = TIERS.map((t) => ({ t, list: quests.filter((x) => x.difficulty === t) })).filter((g) => g.list.length);
  const specTitle = spec && specs ? specs.specializations[spec]?.title : null;
  return (
    <>
      <p className="muted">
        {specTitle ? `${quests.length} ${specTitle} quests` : `${quests.length} of ${specs?.quest_count ?? 0} quests`}. Browse freely; log in to earn.
      </p>
      <form className="filters" method="get">
        <input type="hidden" name="view" value="all" />
        <select name="specialization" defaultValue={spec}>
          <option value="">All specializations</option>
          {specs && Object.values(specs.specializations).filter((m) => m.key !== "undecided").map((m) => <option key={m.key} value={m.key}>{m.title}</option>)}
        </select>
        <select name="tier" defaultValue={tier}>
          <option value="">All tiers</option>
          {specs && TIERS.map((t) => <option key={t} value={t}>{specs.tiers[t].emoji} {specs.tiers[t].name}</option>)}
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
            <h2>{specs?.tiers[t].emoji} {specs?.tiers[t].name}</h2>
            <span className="muted small">{list.length} quests</span>
          </div>
          <div className="grid">{list.map((x) => <QuestCard key={x.id} q={x} />)}</div>
        </section>
      ))}
      {quests.length === 0 && <div className="card">No quests match. Clear a filter.</div>}
    </>
  );
}
