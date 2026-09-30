/** A pixel icon from the pack by a fixed path, so client components can use it without the manifest.
 *  `size` 16 picks the sets drawn on a 16 px grid (utility-16, statistics, selection-controls); 32 the
 *  larger sets. `html:not(.site-art) .ico` hides it when the pack is missing. */
type Group = "utility" | "rewards" | "navigation" | "quest-state" | "quest-steps" | "banner-controls" | "combat-status" | "statistics";

export default function Ico({ group, id, size = 32, className = "" }: { group: Group; id: string; size?: 16 | 32; className?: string }) {
  const dir = size === 16 && group === "utility" ? "utility-16" : group;
  return <img className={`px pxi ico ico-${size} ${className}`} src={`/art/website-art/icons/${dir}/${id}.png`} width={size} height={size} alt="" />;
}
