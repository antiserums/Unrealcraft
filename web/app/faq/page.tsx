import Link from "next/link";
import type { ReactNode } from "react";
import { DISCORD_INVITE } from "@/lib/mission";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";
import { rich } from "@/lib/i18n-config";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("FAQ") };
}

export default async function Faq() {
  const t = await getT();

  const groups: { title: string; items: { q: string; a: ReactNode }[] }[] = [
    {
      title: t("Getting started"),
      items: [
        { q: t("What is Unrealcraft?"), a: rich(t("A free community where you learn Unreal Engine by playing an RPG. Every quest is a dungeon: read the guide, build it in the engine, beat the boss, open the chest. See {link}."), { link: <Link href="/how-it-works">{t("How it works")}</Link> }) },
        { q: t("How do I join?"), a: rich(t("Join the {discord}, press Start Questing there, then log in here with Discord."), { discord: <a href={DISCORD_INVITE}>{t("Unrealcraft Discord server")}</a> }) },
        { q: t("Does it cost anything?"), a: t("No. Unrealcraft is free. Entitlements are earned, never bought.") },
        { q: t("Do I need to know Unreal Engine already?"), a: t("No. The first steps and the Starter Quests begin at installing the engine and opening your first project.") },
        { q: t("Which engine version do I need?"), a: t("Unreal Engine 5. Each quest links to the guide it was written against. State your engine version when you turn work in, so reviewers know what they are looking at.") },
      ],
    },
    {
      title: t("Quests and boss fights"),
      items: [
        { q: t("What is a boss fight?"), a: t("A short quiz played as a turn-based fight. Right answers land hits. Wrong answers wound you. You win with 80% or better.") },
        { q: t("What happens if I lose?"), a: t("Nothing is lost. Open the reading again and retry whenever you are ready. There is no cooldown on a boss.") },
        { q: t("What is the chest?"), a: t("The turn-in. After the boss, you show your work with a few lines and a screenshot. Some quests are accepted at once, and others wait for a mentor.") },
        { q: t("Why is a dungeon locked?"), a: t("Each rank opens a harder tier of dungeons. Rank up to open the next tier.") },
        { q: t("Does my outfit or gear change the fight?"), a: t("No. Outfits, frames, colours and titles are looks only. Nothing but your answers decides a fight.") },
      ],
    },
    {
      title: t("Ranks and specializations"),
      items: [
        { q: t("How do I rank up?"), a: t("Ranks come only from quests. Each rank needs an XP total, the core path of your primary specialization, and a number of quests of that tier. Chatting earns no XP.") },
        { q: t("What is a specialization?"), a: t("One of seven fields: Level Design, Programming, Environment Art, Tech Art, Gameplay Design, Animation and Cinematics. Each has its own quests and capstone dungeons.") },
        { q: t("Can I pick more than one?"), a: rich(t("Yes. Pick a primary, which sets your path, your rank requirements and your nameplate, and add as many others as you like on {link}. Quests in any of them count as yours."), { link: <Link href="/me">{t("your player card page")}</Link> }) },
        { q: t("Can I change my primary later?"), a: t("Yes. Your finished quests stay finished. The quests your next rank needs will change to match the new primary.") },
        { q: t("Is there a reward for trying other specializations?"), a: t("Yes. Finishing quests across specializations earns its own achievements and titles.") },
      ],
    },
    {
      title: t("Entitlements and your player card"),
      items: [
        { q: t("What are entitlements?"), a: t("Everything you unlock: outfits, nameplate colours, avatar frames, player card frames, titles and achievements. They come from ranks, milestones and staff grants.") },
        { q: t("What is a title?"), a: t("A name shown after yours, like \"Kai, the Learner\". Pick one you have earned in Edit profile, or pick None to hide it.") },
        { q: t("Who can see my player card?"), a: rich(t("Logged-in members. You can also make it Public so anyone with the link can open it. See {privacy}."), { privacy: <Link href="/privacy">{t("Privacy")}</Link> }) },
        { q: t("Can I change how the home banner looks?"), a: t("Yes. The small gear on the banner sets the season and time of day, and the button beside it pauses the motion. Your choice stays in your browser.") },
      ],
    },
    {
      title: t("Reviews and help"),
      items: [
        { q: t("Who reviews my work, and where?"), a: t("Mentors, admins and developers, here on the site. A review ends in Pass, Changes or Fail, with notes you can read on the quest page. Nothing is reviewed on Discord.") },
        { q: t("What is the Discord server for, then?"), a: rich(t("It is the guild hall: a place to talk, ask questions and show off your progress. Your roles there follow your rank and specialization here. Join at the {discord}."), { discord: <a href={DISCORD_INVITE}>{t("Discord server")}</a> }) },
        { q: t("How long does a review take?"), a: t("Reviewers are volunteers, so it varies. You can keep questing while you wait.") },
        { q: t("A quest is wrong or a link is dead. What do I do?"), a: rich(t("Tell staff on the {discord}. Quests are fixed in the curriculum and the fix shows in the {changelog}."), { discord: <a href={DISCORD_INVITE}>{t("Discord server")}</a>, changelog: <Link href="/changelog">{t("changelog")}</Link> }) },
        { q: t("How do I delete my account?"), a: rich(t("Message staff on Discord. The {privacy} lists what is removed."), { privacy: <Link href="/privacy">{t("privacy page")}</Link> }) },
        { q: t("Is Unrealcraft part of Epic Games?"), a: t("No. It is a community project and is not affiliated with or endorsed by Epic Games.") },
      ],
    },
  ];

  return (
    <>
      <PageHeader art="header-library" eyebrow="Unrealcraft" title={t("Frequently asked questions")} />
      {groups.map((g) => (
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
