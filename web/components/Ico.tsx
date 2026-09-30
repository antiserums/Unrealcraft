/** A 32 px icon from the pack's utility, rewards or navigation groups, by a fixed path, so client components can use
 *  it without the manifest. `html:not(.site-art) .ico` hides it when the pack is missing. */
export default function Ico({ group, id, className = "" }: { group: "utility" | "rewards" | "navigation" | "quest-state"; id: string; className?: string }) {
  return <img className={`px pxi ico ${className}`} src={`/art/website-art/icons/${group}/${id}.png`} width={32} height={32} alt="" />;
}
