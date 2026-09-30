import Link from "next/link";
import type { ReactNode } from "react";
import { DISCORD_INVITE } from "@/lib/mission";

export const metadata = { title: "FAQ" };

const GROUPS: { title: string; items: { q: string; a: ReactNode }[] }[] = [
  {
    title: "Getting started",
    items: [
      { q: "What is Unrealcraft?", a: <>A free community where you learn Unreal Engine by playing an RPG. Every quest is a dungeon: read the guide, build it in the engine, beat the boss, open the chest. See <Link href="/how-it-works">How it works</Link>.</> },
      { q: "How do I join?", a: <>Join the <a href={DISCORD_INVITE}>Unrealcraft Discord server</a>, press Start Questing there, then log in here with Discord.</> },
      { q: "Does it cost anything?", a: "No. Unrealcraft is free. Entitlements are earned, never bought." },
      { q: "Do I need to know Unreal Engine already?", a: "No. Orientation and the Starter Quests begin at installing the engine and opening your first project." },
      { q: "Which engine version do I need?", a: "Unreal Engine 5. Each quest links to the guide it was written against. State your engine version when you turn work in, so reviewers know what they are looking at." },
    ],
  },
  {
    title: "Quests and boss fights",
    items: [
      { q: "What is a boss fight?", a: "A short quiz played as a turn-based fight. Right answers land hits. Wrong answers wound you. You win with 80% or better." },
      { q: "What happens if I lose?", a: "Nothing is lost. Open the reading again and retry whenever you are ready. There is no cooldown on a boss." },
      { q: "What is the chest?", a: "The turn-in. After the boss, you show your work with a few lines and a screenshot. Some quests are accepted at once, and others wait for a mentor." },
      { q: "Why is a dungeon locked?", a: "Each rank opens a harder tier of dungeons. Rank up to open the next tier." },
      { q: "Does my outfit or gear change the fight?", a: "No. Outfits, frames, colours and titles are looks only. Nothing but your answers decides a fight." },
    ],
  },
  {
    title: "Ranks and specializations",
    items: [
      { q: "How do I rank up?", a: "Ranks come only from quests. Each rank needs an XP total, the core path of your primary specialization, and a number of quests of that tier. Chatting earns no XP." },
      { q: "What is a specialization?", a: "One of seven fields: Level Design, Programming, Environment Art, Tech Art, Gameplay Design, Animation and Cinematics. Each has its own quests and capstone dungeons." },
      { q: "Can I pick more than one?", a: <>Yes. Pick a primary, which sets your path, your rank requirements and your nameplate, and add as many others as you like on <Link href="/me">your player card page</Link>. Quests in any of them count as yours.</> },
      { q: "Can I change my primary later?", a: "Yes. Your finished quests stay finished. The quests your next rank needs will change to match the new primary." },
      { q: "Is there a reward for trying other specializations?", a: "Yes. Finishing quests across specializations earns its own achievements and titles." },
    ],
  },
  {
    title: "Entitlements and your player card",
    items: [
      { q: "What are entitlements?", a: "Everything you unlock: outfits, nameplate colours, avatar frames, player card frames, titles and achievements. They come from ranks, milestones and staff grants." },
      { q: "What is a title?", a: "A name shown after yours, like \"Kai, the Learner\". Pick one you have earned in Edit profile, or pick None to hide it." },
      { q: "Who can see my player card?", a: <>Logged-in members. You can also make it Public so anyone with the link can open it. See <Link href="/privacy">Privacy</Link>.</> },
      { q: "Can I change how the home banner looks?", a: "Yes. The small gear on the banner sets the season and time of day, and the button beside it pauses the motion. Your choice stays in your browser." },
    ],
  },
  {
    title: "Reviews and help",
    items: [
      { q: "Who reviews my work, and where?", a: "Mentors, admins and developers, here on the site. A review ends in Pass, Changes or Fail, with notes you can read on the quest page. Nothing is reviewed on Discord." },
      { q: "What is the Discord server for, then?", a: <>It is the guild hall: a place to talk, ask questions and show off your progress. Your roles there follow your rank and specialization here. Join at the <a href={DISCORD_INVITE}>Discord server</a>.</> },
      { q: "How long does a review take?", a: "Reviewers are volunteers, so it varies. You can keep questing while you wait." },
      { q: "A quest is wrong or a link is dead. What do I do?", a: <>Tell staff on the <a href={DISCORD_INVITE}>Discord server</a>. Quests are fixed in the curriculum and the fix shows in the <Link href="/changelog">changelog</Link>.</> },
      { q: "How do I delete my account?", a: <>Message staff on Discord. The <Link href="/privacy">privacy page</Link> lists what is removed.</> },
      { q: "Is Unrealcraft part of Epic Games?", a: "No. It is a community project and is not affiliated with or endorsed by Epic Games." },
    ],
  },
];

export default function Faq() {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Frequently asked questions</h1>
      {GROUPS.map((g) => (
        <section key={g.title}>
          <div className="section-h"><h2>{g.title}</h2></div>
          <div className="faq">
            {g.items.map((it) => (
              <details key={it.q} className="card faq-item">
                <summary>{it.q}</summary>
                <p>{it.a}</p>
              </details>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
