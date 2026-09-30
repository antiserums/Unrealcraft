"use client";
import { useT } from "@/components/I18n";

/** Shown when a page throws, most often because the API is down. The illustration is a plain URL, since a client
 *  component cannot read the manifest; it hides itself when the pack is not there. */
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  const t = useT();
  return (
    <>
      <h1>{t("The connection was lost")}</h1>
      <div className="card spot">
        <img className="px" src="/art/website-art/spots/connection-lost.png" width={160} height={120} alt="" onError={(e) => { e.currentTarget.style.display = "none"; }} />
        <div>
          <p style={{ marginTop: 0 }}>{t("The site could not reach the game server. It may be restarting. Try again in a moment.")}</p>
          <button type="button" className="btn primary" onClick={reset}>{t("Try again")}</button>
        </div>
      </div>
    </>
  );
}
