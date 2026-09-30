import Link from "next/link";
import { DISCORD_INVITE, MISSION } from "@/lib/mission";
import { PageHeader } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export async function generateMetadata() {
  const t = await getT();
  return { title: t("Mission statement") };
}

/** The long form of the mission statement: what Unrealcraft is for and what it stands for. How the game works
 *  lives on /how-it-works, not here. The short statement (lib/mission.ts) opens the page. */
export default async function Mission() {
  const t = await getT();
  return (
    <>
      <PageHeader art="header-guild" eyebrow="Unrealcraft" title={t("Our mission statement")} />
      <div className="card legal mission">
        <p className="lead" style={{ maxWidth: "none", fontSize: 17 }}>{t(MISSION)}</p>

        <h2>{t("Free, for everyone")}</h2>
        <p>{t("Unrealcraft is free: no price, no paid tier, nothing to buy later. Learning to make games should not depend on what you can afford. Some of the best people in this industry started with a borrowed laptop and a free engine, and a lot of talent never gets a chance because a course costs a month's rent. We want the door open for the next one of them.")}</p>
        <p>{t("Free also means free of the usual tricks: no ads, no selling your data, no paywall between you and what you came here to learn. The only money that ever changes hands is a donation you choose to make, and all it buys is a thank-you: a set of gear and frames that does nothing but look good.")}</p>

        <h2>{t("Learning should feel like playing")}</h2>
        <p>{t("You learn by doing, and doing is easier to start and easier to keep up when it feels like a game. So Unrealcraft is one: something to play, not something to get through. The game is the wrapper, not the point. Behind every boss and every reward is a real skill you can take into a real project.")}</p>

        <h2>{t("A guild, not a classroom")}</h2>
        <p>{t("Nobody should have to learn alone. Unrealcraft is a community first: a place to ask, to show what you made and to find people to build with. It is made for your first day in Unreal Engine and for your tenth shipped game alike, and the people who mentor and run things are members who give their time freely.")}</p>
        <p>{t("Everyone is treated the same: any age the platform allows, any country, any language, any background, any level of skill. Be kind, do your own work, and help the person behind you. That is the whole code.")}</p>

        <h2>{t("What we promise")}</h2>
        <ul>
          <li>{t("Your progress is yours. Nobody stands above anyone else for being here longer, talking more or paying anything.")}</li>
          <li>{t("We stay honest. What we teach is checked against the engine, and when we are wrong we fix it and say so.")}</li>
          <li>{t("We speak your language. The site is translated into fifteen languages, and we will keep adding more.")}</li>
          <li>{t("Nothing is hidden. How things work and what we store about you are written down where anyone can read them.")}</li>
        </ul>

        <h2>{t("Why we do this")}</h2>
        <p>{t("A lot of us learned Unreal the hard way: alone, from scattered videos and half-finished forum threads. We remember how much faster it would have gone with a map, a party and someone to say \"that is done, well done, here is the next one\". Unrealcraft is that map, that party and that voice.")}</p>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <Link className="btn primary" href="/how-it-works">{t("How it works")}</Link>
        <Link className="btn" href="/quests">{t("Quest board")}</Link>
        <a className="btn" href={DISCORD_INVITE}>{t("Join the Discord")}</a>
      </div>
    </>
  );
}
