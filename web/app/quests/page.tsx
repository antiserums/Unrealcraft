import Link from "next/link";
import PathView from "@/components/PathView";
import QuestCard, { cardCtx } from "@/components/QuestCard";
import { api, type Me, type PathData, type QuestSummary, type Specializations } from "@/lib/api";
import Ico from "@/components/Ico";
import { PageHeader, Spot } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

const TIERS = ["novice", "apprentice", "adept", "expert", "master"];
// Hundreds of cards on one page are slow to build and to scroll: each tier shows a first few with a link to the rest,
// and a single tier is shown one page at a time.
const PREVIEW = 12, PER_PAGE = 48;

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Quest board") };
}

export default async function Quests({ searchParams }: PageProps<"/quests">) {
  const t = await getT();
  const sp = await searchParams;
  const pick = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : "");
  const me = await api<Me>("/me");
  const view = pick("view") === "path" || (!pick("view") && !pick("specialization") && !pick("tier") && !pick("q") && !pick("subject") && me) ? "path" : "all";
  return (
    <>
      <PageHeader art={view === "path" ? "header-path" : "header-quests"} title={t("Quest board")} />
      <nav className="subnav" aria-label={t("Quest board views")}>
        <Link href="/quests?view=path" className={view === "path" ? "on" : ""}><Ico group="navigation" id="path" />{t("My path")}</Link>
        <Link href="/quests?view=all" className={view === "all" ? "on" : ""}><Ico group="navigation" id="quest-board" />{t("All quests")}</Link>
      </nav>
      {view === "path" ? <Path me={me} /> : <All sp={sp} />}
    </>
  );
}

async function Path({ me }: { me: Me | null }) {
  const t = await getT();
  if (!me) {
    return (
      <div className="card">
        <p style={{ margin: 0 }}>{t("Your path is the road through your primary specialization: what is next, what is done, what the next rank opens.")}</p>
        <div className="row" style={{ marginTop: 12 }}>
          <a className="btn primary" href="/api/auth/discord?next=/quests">{t("Enter with Discord")}</a>
          <Link className="btn" href="/quests?view=all">{t("Browse all quests")}</Link>
        </div>
      </div>
    );
  }
  const p = await api<PathData>("/me/path");
  if (!p) return <div className="card">{t("Your path could not be loaded. Log out and back in, then try again.")}</div>;
  return <PathView p={p} />;
}

async function All({ sp }: { sp: Record<string, string | string[] | undefined> }) {
  const t = await getT();
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
  const ctx = await cardCtx();                      // one lookup of the words and the art for all the cards
  const byTier = TIERS.map((k) => ({ k, list: quests.filter((x) => x.difficulty === k) })).filter((g) => g.list.length);
  const href = (extra: Record<string, string>) => {
    const u = new URLSearchParams(qs);
    u.set("view", "all");
    for (const [k, v] of Object.entries(extra)) u.set(k, v);
    return `/quests?${u}`;
  };
  const pages = Math.max(1, Math.ceil(quests.length / PER_PAGE));
  const page = Math.min(pages, Math.max(1, parseInt(pick("page"), 10) || 1));
  const preview = !tier && quests.length > PER_PAGE;      // a short list (a search, a small filter) is shown whole
  const specTitle = spec && specs ? specs.specializations[spec]?.title : null;
  return (
    <>
      <p className="muted">
        {specTitle
          ? t("{n} {spec} quests. Browse freely; log in to earn.", { n: quests.length, spec: t(specTitle) })
          : t("{n} of {total} quests. Browse freely; log in to earn.", { n: quests.length, total: specs?.quest_count ?? 0 })}
      </p>
      <form className="filters" method="get">
        <input type="hidden" name="view" value="all" />
        <select name="specialization" defaultValue={spec}>
          <option value="">{t("All specializations")}</option>
          {specs && Object.values(specs.specializations).filter((m) => m.key !== "undecided").map((m) => <option key={m.key} value={m.key}>{t(m.title)}</option>)}
        </select>
        <select name="tier" defaultValue={tier}>
          <option value="">{t("All tiers")}</option>
          {specs && TIERS.map((k) => <option key={k} value={k}>{specs.tiers[k].emoji} {t(specs.tiers[k].name)}</option>)}
        </select>
        <select name="subject" defaultValue={subject}>
          <option value="">{t("All subjects")}</option>
          {subjects?.subjects.slice(0, 60).map(([s, n]) => <option key={s} value={s}>{s} ({n})</option>)}
        </select>
        <input name="q" placeholder={t("Search title or ID")} defaultValue={q} />
        <button type="submit" className="primary"><Ico group="utility" id="filter" />{t("Filter")}</button>
      </form>
      {byTier.map(({ k, list }) => {
        const shown = tier ? list.slice((page - 1) * PER_PAGE, page * PER_PAGE) : preview ? list.slice(0, PREVIEW) : list;
        return (
          <section key={k}>
            <div className="section-h">
              <h2>{specs?.tiers[k].emoji} {specs ? t(specs.tiers[k].name) : ""}</h2>
              <span className="muted small">{t("{n} quests", { n: list.length })}</span>
            </div>
            <div className="grid">{shown.map((x) => <QuestCard key={x.id} q={x} ctx={ctx} />)}</div>
            {preview && list.length > PREVIEW && (
              <p className="more"><Link className="btn" href={href({ tier: k })}>{t("Show all {n} {tier} quests", { n: list.length, tier: specs ? t(specs.tiers[k].name) : k })}</Link></p>
            )}
            {tier && pages > 1 && (
              <nav className="pager" aria-label={t("Pages")}>
                {page > 1 ? <Link className="btn" href={href({ page: String(page - 1) })}>← {t("Previous")}</Link> : <span />}
                <span className="muted small">{t("Showing {from} to {to} of {total}", { from: (page - 1) * PER_PAGE + 1, to: Math.min(page * PER_PAGE, list.length), total: list.length })}</span>
                {page < pages ? <Link className="btn" href={href({ page: String(page + 1) })}>{t("Next")} →</Link> : <span />}
              </nav>
            )}
          </section>
        );
      })}
      {quests.length === 0 && <Spot art="empty-notice-board">{t("No quests match. Clear a filter.")}</Spot>}
    </>
  );
}
