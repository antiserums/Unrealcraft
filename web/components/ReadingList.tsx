"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Ico from "./Ico";
import type { Reading } from "@/lib/api";
import { useT } from "./I18n";

/** Reading links that tell the API "I opened the guide": each link gets a tick, and the first one of a quest feeds
 *  the Lore stat. Fire-and-forget; guests just get the link. */
export default function ReadingList({ questId, reading, loggedIn, opened = [] }: { questId: string; reading: Reading[]; loggedIn: boolean; opened?: string[] }) {
  const t = useT();
  const router = useRouter();
  const [seen, setSeen] = useState<string[]>(opened);
  const ping = (url: string) => {
    if (!loggedIn || seen.includes(url)) return;
    setSeen((s) => [...s, url]);
    fetch(`/api/me/quests/${questId}/read`, { method: "POST", keepalive: true, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) })
      .then(() => router.refresh()).catch(() => {});                 // the step's marker turns green once every link is opened
  };
  const n = reading.filter((r) => seen.includes(r.url)).length;
  return (
    <>
      <ol className="reading-list">
        {reading.map((r) => {
          const ok = seen.includes(r.url);
          return (
            <li key={r.url} className={ok ? "opened" : ""}>
              <a href={r.url} target="_blank" rel="noreferrer" onClick={() => ping(r.url)} onAuxClick={() => ping(r.url)}>
                <span className="reading-label">{r.label}</span>
                {r.kind === "official" && reading.length > 1 && <span className="pill">{t("official")}</span>}
                {r.kind === "community" && <span className="pill">{t("community")}</span>}
                {r.kind === "backup" && <span className="pill">{t("backup")}</span>}
                {ok && <span className="reading-tick">✔ {t("Opened")}</span>}
                <Ico group="utility" id="external" size={16} />
              </a>
            </li>
          );
        })}
      </ol>
      {loggedIn && reading.length > 1 && <p className="small muted reading-count">{t("{n} of {total} opened", { n, total: reading.length })}</p>}
    </>
  );
}
