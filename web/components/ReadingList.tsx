"use client";
import type { Reading } from "@/lib/api";
import { useT } from "./I18n";

/** Reading links that tell the API "I opened the guide" (feeds the Lore stat). Fire-and-forget; guests just get the link. */
export default function ReadingList({ questId, reading, loggedIn }: { questId: string; reading: Reading[]; loggedIn: boolean }) {
  const t = useT();
  const ping = () => { if (loggedIn) fetch(`/api/me/quests/${questId}/read`, { method: "POST", keepalive: true }).catch(() => {}); };
  return (
    <ol className="steps">
      {reading.map((r) => (
        <li key={r.url}>
          <a href={r.url} target="_blank" rel="noreferrer" onClick={ping}>{r.label}</a>
          {r.kind === "community" && <span className="tag"> · {t("community")}</span>}
        </li>
      ))}
    </ol>
  );
}
