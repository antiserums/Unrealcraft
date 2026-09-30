import HowItWorks from "@/components/HowItWorks";
import { api, type Specializations } from "@/lib/api";

export const metadata = { title: "How it works" };

export default async function HowItWorksPage() {
  const specs = await api<Specializations>("/catalog/specializations");
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>How it works</h1>
      <p className="lead" style={{ marginBottom: 6 }}>Every quest is a dungeon. Read the guide, build it in the engine, then fight the boss: a short quiz where right answers land hits. Show your work, open the chest, rank up. Ranks come only from quests.</p>
      <HowItWorks specs={specs} />
    </>
  );
}
