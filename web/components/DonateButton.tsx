"use client";
import { useState } from "react";
import { useT } from "./I18n";

/** Pick an amount and go to Stripe Checkout. The API makes the session; Stripe hosts the payment page. */
export default function DonateButton({ loggedIn, minimum, currency }: { loggedIn: boolean; minimum: number; currency: string }) {
  const t = useT();
  const presets = [minimum, minimum * 2, minimum * 5];
  const [amount, setAmount] = useState<number>(minimum);
  const [custom, setCustom] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const unit = currency.toUpperCase();

  async function go() {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/donate/checkout", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ amount }) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || !j.url) { setErr(j.detail ?? t("Could not start the donation. Try again in a moment.")); setBusy(false); return; }
    window.location.href = j.url;
  }

  if (!loggedIn) return <a className="btn primary" href="/api/auth/discord?next=/donate">{t("Log in to donate")}</a>;
  return (
    <div className="donate">
      <div className="row" style={{ gap: 6 }}>
        {presets.map((p) => <button key={p} type="button" className={`btn ${amount === p && !custom ? "primary" : ""}`} onClick={() => { setAmount(p); setCustom(""); }}>{p} {unit}</button>)}
        <input type="text" inputMode="numeric" value={custom} placeholder={t("Other")} style={{ width: 90 }} aria-label={t("Other amount")}
          onChange={(e) => { const v = e.target.value.replace(/[^0-9]/g, ""); setCustom(v); if (v) setAmount(Math.max(minimum, parseInt(v, 10))); }} />
      </div>
      <p className="small muted" style={{ margin: "8px 0" }}>{t("Minimum {min} {unit}. Payment happens on Stripe; we never see your card.", { min: minimum, unit })}</p>
      {err && <div className="note small" data-tone="error" style={{ marginBottom: 8 }}>{err}</div>}
      <button type="button" className="btn primary" disabled={busy || amount < minimum} onClick={go}>{busy ? t("Opening Stripe…") : t("Donate {n} {unit}", { n: amount, unit })}</button>
    </div>
  );
}
