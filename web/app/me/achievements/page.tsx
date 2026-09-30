import { redirect } from "next/navigation";
import MeNav from "@/components/MeNav";
import { badgeImage, loadManifest } from "@/lib/art";
import { api, type Achievement, type Me } from "@/lib/api";
import { getT } from "@/lib/i18n";

export async function generateMetadata() { const t = await getT(); return { title: t("Achievements") }; }

export default async function Achievements() {
  const t = await getT();
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/me/achievements");
  const [data, manifest] = await Promise.all([api<{ achievements: Achievement[] }>("/me/achievements"), loadManifest()]);
  const all = data?.achievements ?? [];
  const earned = all.filter((a) => a.earned);
  const todo = all.filter((a) => !a.earned);
  const badge = (a: Achievement) => badgeImage(manifest, a.badge);
  return (
    <>
      <div className="eyebrow">{t("Profile")}</div>
      <h1>{t("Achievements")}</h1>
      <MeNav active="/me/achievements" />
      <p className="muted">{t("{earned} of {total} earned. Achievements are entitlements: some unlock an outfit, a frame, a colour or a title. Pick up to three to show on your card.", { earned: earned.length, total: all.length })}</p>
      {earned.length > 0 && (
        <>
          <div className="section-h"><h2>{t("Earned")}</h2></div>
          <div className="grid">{earned.map((a) => <Badge key={a.key} a={a} img={badge(a)} />)}</div>
        </>
      )}
      <div className="section-h"><h2>{t("Still to earn")}</h2><span className="muted small">{t("{n} left", { n: todo.length })}</span></div>
      <div className="grid">{todo.map((a) => <Badge key={a.key} a={a} img={badge(a)} />)}</div>
    </>
  );
}

async function Badge({ a, img }: { a: Achievement; img: string | null }) {
  const t = await getT();
  const pct = Math.round((a.have / a.need) * 100);
  return (
    <div className={`card ach ${a.earned ? "earned" : ""}`}>
      <div className="row" style={{ gap: 12, alignItems: "flex-start" }}>
        <span className="ach-icon">{img ? <img className="px" src={img} alt="" /> : a.icon}</span>
        <div style={{ flex: 1 }}>
          <div className="title" style={{ fontWeight: 600 }}>{t(a.name)}</div>
          <div className="small muted">{t(a.desc)}</div>
          {a.outfit && <div className="small" style={{ color: "var(--gold-2)", marginTop: 2 }}>{t("Unlocks an outfit")}</div>}
        </div>
      </div>
      {a.earned ? (
        <div className="small" style={{ color: "var(--ok)", marginTop: 8 }}>✔ {a.earned_at ? t("Earned · {date}", { date: a.earned_at.slice(0, 10) }) : t("Earned")}</div>
      ) : (
        <div style={{ marginTop: 10 }}>
          <div className="bar"><span style={{ width: `${pct}%`, background: "var(--teal)" }} /></div>
          <div className="small muted" style={{ marginTop: 4 }}>{a.have} / {a.need}</div>
        </div>
      )}
    </div>
  );
}
