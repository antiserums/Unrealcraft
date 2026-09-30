import Link from "next/link";
import { DISCORD_INVITE } from "@/lib/mission";

export const metadata = { title: "Privacy" };
const UPDATED = "30 September 2026";

export default function Privacy() {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Privacy</h1>
      <p className="muted small">Last updated {UPDATED}. Written in plain English on purpose.</p>

      <div className="card legal">
        <h2>The short version</h2>
        <p>We keep what the game needs to work: who you are on Discord, what you have done here, and what you chose to show. We do not sell it, we do not run ads, and we do not use trackers or analytics.</p>

        <h2>What we collect</h2>
        <ul>
          <li><b>From Discord, when you log in:</b> your Discord ID, your display name and your avatar. We also check that you are a member of the Unrealcraft server and which of its roles you hold. We never see your Discord password, your email or your messages.</li>
          <li><b>What you do here:</b> quests you start and finish, quiz and boss fight attempts, XP, rank, streak, achievements and other entitlements, and the specializations you chose.</li>
          <li><b>What you turn in:</b> the text and screenshots you submit for a quest, the engine version you state, and the reviewer&apos;s decision and notes.</li>
          <li><b>What you put on your player card:</b> your motto, title, colours, frames, outfit and featured achievements.</li>
          <li><b>Staff actions:</b> when an admin changes an account, the action is written to an admin log.</li>
        </ul>

        <h2>Cookies and browser storage</h2>
        <ul>
          <li>One login cookie keeps you signed in. It lasts up to 30 days and is removed when you log out. A short-lived cookie is used during the Discord login itself.</li>
          <li>Your browser remembers small display choices, such as the home banner&apos;s season, time of day and pause. These stay on your device and are never sent to us.</li>
          <li>There are no advertising or tracking cookies.</li>
        </ul>

        <h2>Who can see what</h2>
        <ul>
          <li><b>Your player card</b> is visible to logged-in members. It is only visible to people who are not logged in if you set it to Public on your card page.</li>
          <li><b>The leaderboard</b> is public. It shows your display name, avatar, rank, title, primary specialization and XP.</li>
          <li><b>Your turn-ins</b> are seen by you and by the mentors, admins and developers who review them. The Discord bot may also post a turn-in to the server&apos;s review or showcase channels.</li>
          <li><b>Admins and developers</b> can see your account data in order to run the site.</li>
        </ul>

        <h2>Who we share it with</h2>
        <p>Nobody, beyond what is described above. Discord is involved because you log in with it and because the bot mirrors progress into the server (roles, rank-up posts, turn-ins). Discord&apos;s own privacy policy covers what Discord does.</p>

        <h2>How long we keep it</h2>
        <p>For as long as you have an account. If you ask us to delete your account, we remove your progress, XP, turn-ins, uploaded screenshots, player card and saved name. Posts the bot already made in Discord are removed on request as well.</p>

        <h2>Your choices</h2>
        <ul>
          <li>Set your player card to Private or Public on <Link href="/me">your card page</Link>.</li>
          <li>Hide your title, change your motto, or remove featured achievements at any time.</li>
          <li>Ask for a copy of your data, a correction, or deletion of your account by messaging staff on the <a href={DISCORD_INVITE}>Unrealcraft Discord server</a>.</li>
        </ul>

        <h2>Age</h2>
        <p>You need a Discord account to use Unrealcraft, so Discord&apos;s minimum age applies here too. Unrealcraft is not aimed at children under 13.</p>

        <h2>Changes</h2>
        <p>If this page changes in a way that matters, we will say so in the <Link href="/changelog">changelog</Link> and on the Discord server.</p>
      </div>
    </>
  );
}
