import Link from "next/link";
import { DISCORD_INVITE } from "@/lib/mission";

export const metadata = { title: "Terms of service" };
const UPDATED = "30 September 2026";

export default function Terms() {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Terms of service</h1>
      <p className="muted small">Last updated {UPDATED}. By using Unrealcraft you agree to these terms.</p>

      <div className="card legal">
        <h2>What Unrealcraft is</h2>
        <p>Unrealcraft is a free community for learning Unreal Engine, built as a game: quests, boss fights, ranks and rewards. It is a community project. It is not affiliated with, endorsed by or sponsored by Epic Games. Unreal Engine is a trademark of Epic Games, Inc.</p>

        <h2>Your account</h2>
        <ul>
          <li>You log in with Discord and must be a member of the Unrealcraft Discord server. Discord&apos;s own terms apply to your Discord account.</li>
          <li>One account per person. Do not share an account or play on someone else&apos;s.</li>
          <li>You are responsible for what is done with your account.</li>
        </ul>

        <h2>Fair play</h2>
        <ul>
          <li><b>Do your own work.</b> Turn in things you built yourself. Do not submit someone else&apos;s work, a marketplace asset passed off as yours, or a screenshot that is not from your project.</li>
          <li><b>No cheating.</b> Do not share quiz answers, script the site, or look for ways to grant yourself XP, ranks or entitlements.</li>
          <li><b>Be decent.</b> No harassment, hate, threats, spam or sexual content, in turn-ins, mottos, names or anywhere else. The Discord server&apos;s rules apply here too.</li>
          <li><b>Do not break the site.</b> No attacks, scraping at volume, or attempts to reach data that is not yours. If you find a security problem, tell staff privately.</li>
        </ul>

        <h2>What you turn in</h2>
        <p>Your work stays yours. By turning it in, you let us store it, show it to reviewers, and show it in the Discord server&apos;s review and showcase channels. Only upload things you have the right to share. We may remove a turn-in that breaks these terms.</p>

        <h2>Ranks, XP and entitlements</h2>
        <p>Ranks, XP, titles, outfits, frames and other entitlements are part of the game. They have no cash value, cannot be sold or traded, and are not a certificate or qualification. We may rebalance, rename, add or remove them as the game changes. Staff may correct or remove progress that was earned by breaking these terms.</p>

        <h2>Learning content</h2>
        <p>Quests link to Epic&apos;s documentation and to other guides. Those sites belong to their owners, and we are not responsible for them. We try hard to keep quests correct for the engine version they name, but we cannot promise every quest is right or current. Tell us when one is wrong.</p>

        <h2>Staff decisions</h2>
        <p>Mentors, admins and developers review work and keep the community healthy. They may ask for changes, fail a turn-in, remove content, reset progress, or suspend or remove an account that breaks these terms. If you think a decision was wrong, raise it with staff on Discord.</p>

        <h2>No warranty</h2>
        <p>Unrealcraft is provided as it is, for free, by volunteers. It may be slow, wrong or offline at times, and data can be lost. To the extent the law allows, we are not liable for losses that come from using it. Keep your own copies of your work.</p>

        <h2>Leaving</h2>
        <p>You can stop at any time. To have your account and data deleted, message staff on the <a href={DISCORD_INVITE}>Discord server</a>. See the <Link href="/privacy">privacy page</Link> for what we store.</p>

        <h2>Changes</h2>
        <p>We may update these terms. Changes that matter are announced in the <Link href="/changelog">changelog</Link> and on Discord. Using Unrealcraft after a change means you accept it.</p>
      </div>
    </>
  );
}
