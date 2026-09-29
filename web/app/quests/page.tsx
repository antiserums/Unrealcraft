import QuestCard from "@/components/QuestCard";
import { api, type Majors, type QuestSummary } from "@/lib/api";

const TIERS = ["novice", "apprentice", "adept", "expert", "master"];

export const metadata = { title: "Quests" };

export default async function Quests({ searchParams }: PageProps<"/quests">) {
  const sp = await searchParams;
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
      <h1>Quests</h1>
      <p className="muted">
        {majorTitle ? `${quests.length} ${majorTitle} quests` : `${quests.length} of ${majors?.quest_count ?? 0} quests`}
        {cross.length > 0 && `, plus ${cross.length} cross-training`}. Browse freely; log in to earn.
      </p>
      <form className="filters" method="get">
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
