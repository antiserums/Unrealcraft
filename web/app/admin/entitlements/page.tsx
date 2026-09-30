import { redirect } from "next/navigation";
import AdminNav from "@/components/AdminNav";
import EntitlementManager, { type EntitlementData } from "@/components/EntitlementManager";
import { loadManifest } from "@/lib/art";
import { api, type Me } from "@/lib/api";

export const metadata = { title: "Admin · Entitlements" };

export default async function AdminEntitlements() {
  const me = await api<Me>("/me");
  if (!me) redirect("/api/auth/discord?next=/admin/entitlements");
  const [data, manifest] = await Promise.all([api<EntitlementData>("/admin/entitlements"), loadManifest()]);
  if (!data) return <><h1>Entitlements</h1><div className="card">Admins and developers only.</div></>;
  const art = {
    sets: Object.entries(manifest?.sets ?? {}).map(([id, s]) => ({ id, name: s.name })),
    avatar: Object.keys(manifest?.decorations?.avatar ?? {}), card: Object.keys(manifest?.decorations?.card ?? {}),
    badges: (manifest?.badges ?? []).map((b, i) => ({ n: i + 1, name: b.name })),
  };
  return (
    <>
      <div className="eyebrow">Staff</div>
      <h1>Entitlements</h1>
      <AdminNav active="/admin/entitlements" />
      <p className="muted small">Every unlock an account can hold: outfits, nameplate colours, avatar and player card frames, titles and achievements. Built-in rows come from the art pack; you can edit or switch them off, and add your own. The art itself comes only from the synced art pack.</p>
      <EntitlementManager data={data} art={art} />
    </>
  );
}
