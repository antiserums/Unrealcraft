import Link from "next/link";
import { DISCORD_INVITE, MISSION } from "@/lib/mission";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Mission statement") };
}

/** The long form of the mission statement. The short one (lib/mission.ts) opens it and is the one shown on the
 *  guest home page; the rest says why Unrealcraft is free, who it is for, and what we promise. */
export default async function Mission() {
  const t = await getT();
  return (
    <>
      <PageHeader art="header-guild" eyebrow="Unrealcraft" title={t("Our mission statement")} />
      <div className="card legal mission">
        <p className="lead" style={{ maxWidth: "none", fontSize: 17 }}>{t(MISSION)}</p>

        <h2>{t("Free, for everyone")}</h2>
        <p>{t("Unrealcraft is free. There is no price, no paid tier, no locked chapter and nothing to buy later. Every quest, every boss fight, every guide and every reward is open to every member from the first day, and it will stay that way.")}</p>
        <p>{t("We built it this way on purpose. Learning to make games should not depend on what you can afford. Some of the best people in this industry started with a borrowed laptop and a free engine, and a lot of talent never gets a chance because a course costs a month's rent. If you have Unreal Engine installed and a little time, you have everything Unrealcraft asks for.")}</p>
        <p>{t("Free also means free of the usual tricks. We do not sell your data, we do not show ads, and we will never put a paywall between you and your next rank. The only currency here is XP, and the only way to earn it is to do the work.")}</p>

        <h2>{t("Learn it the way you would play it")}</h2>
        <p>{t("Most tutorials are a wall of video. You watch, you nod, you forget. Unrealcraft turns learning into a game you can actually play. Every quest is a dungeon with four rooms: read the guide, build the thing in the engine, beat the boss, open the chest. The boss is a quiz that fights back, so you find out at once whether the idea really landed. The chest is where you show your work.")}</p>
        <p>{t("Ranks come only from quests. Nobody outranks you for chatting more or for being here longer. When you see a Master on the leaderboard, you know exactly what they did to get there, because you can open the same quests and do it yourself.")}</p>

        <h2>{t("A home for beginners and veterans alike")}</h2>
        <p>{t("If you have never opened Unreal Engine, start at Orientation. The Starter Quests begin with installing the engine and opening your first project, and every step tells you what done looks like. Nobody is expected to know anything on day one.")}</p>
        <p>{t("If you have shipped games already, skip ahead. The harder tiers, the capstone dungeons and the cross-specialization achievements are there to be conquered, and the ranks above Master are earned by helping others climb. There is always a harder boss.")}</p>
        <p>{t("Pick a primary specialization to set your path, and add as many others as you like. Level Design, Programming, Environment Art, Tech Art, Gameplay Design, Animation and Cinematics are all here, and quests in any of them count as yours.")}</p>

        <h2>{t("A guild, not a classroom")}</h2>
        <p>{t("The Discord server is our guild hall. It is where you ask questions, show off what you built, watch others rank up and find people to build with. Mentors, admins and developers are members who earned their place and give their time freely. Reviews of your work happen on this site, so what you get back is a considered answer, not a hurried reply in a chat.")}</p>
        <p>{t("Everyone is welcome and everyone is treated the same: any age the platform allows, any country, any language, any background, any level of skill. Be kind, do your own work, and help the person behind you on the ladder. That is the whole code.")}</p>

        <h2>{t("What we promise")}</h2>
        <ul>
          <li>{t("Unrealcraft stays free. If that ever changes, it will not be for the people already here.")}</li>
          <li>{t("Your progress is yours. Ranks, XP, titles and outfits are earned, never bought, and staff will never sell or grant them for anything but the work.")}</li>
          <li>{t("Quests stay honest. Each one names the engine version it was written for, links to the real guide, and gets fixed when it is wrong.")}</li>
          <li>{t("The site speaks your language. Unrealcraft is translated into fifteen languages, and the guides link to the best sources we can find.")}</li>
          <li>{t("Nothing is hidden. How ranks work, how reviews work and what we store about you are all written down where anyone can read them.")}</li>
        </ul>

        <h2>{t("Why we do this")}</h2>
        <p>{t("Because a lot of us learned Unreal the hard way, alone, from scattered videos and half-finished forum threads, and we remember how much faster it would have gone with a map, a party and someone to say \"that is done, well done, here is the next one\". Unrealcraft is that map. The bosses are there to make you prove it, the rewards are there to make it fun, and the guild is there so you never learn alone.")}</p>
        <p>{t("Learn Unreal Engine the way you would play it. That is the mission, and it is for everyone.")}</p>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <Link className="btn primary" href="/quests">{t("Quest board")}</Link>
        <Link className="btn" href="/how-it-works">{t("How it works")}</Link>
        <a className="btn" href={DISCORD_INVITE}>{t("Join the Discord")}</a>
      </div>
    </>
  );
}
