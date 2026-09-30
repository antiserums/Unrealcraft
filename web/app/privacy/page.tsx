import Link from "next/link";
import { DISCORD_INVITE } from "@/lib/mission";

export const metadata = { title: "Privacy policy" };
const UPDATED = "30 September 2026";

export default function Privacy() {
  return (
    <>
      <div className="eyebrow">Unrealcraft</div>
      <h1>Privacy policy</h1>
      <p className="muted small">Effective {UPDATED}</p>

      <div className="card legal">
        <p>This Privacy Policy describes the information Unrealcraft collects when you use this website and the Unrealcraft Discord bot (together, the &quot;Service&quot;), how that information is used, and the choices available to you. By using the Service you acknowledge the practices described in this policy.</p>

        <h2>1. Information we collect</h2>
        <p><b>Account information.</b> The Service uses Discord to sign you in. When you authorise the login, Discord provides your Discord user ID, display name and avatar, and confirms your membership and roles in the Unrealcraft Discord server. Unrealcraft does not receive your Discord password, email address or private messages.</p>
        <p><b>Activity information.</b> The Service records your use of it: quests started and completed, quiz and boss fight attempts and results, experience points, rank, daily streak, achievements and other entitlements, and the specializations you select.</p>
        <p><b>Submissions.</b> When you turn in work for a quest, the Service stores the text and images you submit, the engine version you state, and the reviewer&apos;s decision and notes.</p>
        <p><b>Profile information.</b> The Service stores the choices you make for your player card, including your motto, title, colours, frames, outfit, featured achievements and visibility setting.</p>
        <p><b>Administrative records.</b> Actions taken by staff on an account, such as granting a quest or changing a rank, are recorded in an administrative log.</p>

        <h2>2. Cookies and local storage</h2>
        <p>The Service sets a session cookie to keep you signed in. It expires after 30 days or when you log out. A second, short-lived cookie is used only while the Discord login is in progress. The Service also stores display preferences in your browser&apos;s local storage, such as the season, time of day and pause setting of the home page banner. These preferences remain on your device and are not transmitted to Unrealcraft.</p>
        <p>The Service does not use advertising cookies, third-party analytics or tracking technologies.</p>

        <h2>3. How we use information</h2>
        <p>Information is used to operate the Service: to authenticate you, to record and display your progress, to determine ranks and entitlements, to review submitted work, to show player cards and the leaderboard, to keep the Discord server in step with the website, and to investigate misuse. Unrealcraft does not sell personal information and does not use it for advertising.</p>

        <h2>4. How information is disclosed</h2>
        <p><b>Other members.</b> Your player card is visible to signed-in members. It is visible to people who are not signed in only if you set it to Public.</p>
        <p><b>The public.</b> The leaderboard is publicly accessible and displays your display name, avatar, rank, title, primary specialization and experience points.</p>
        <p><b>Staff.</b> Mentors, administrators and developers can view submissions in order to review them. Administrators and developers can view account data in order to operate the Service.</p>
        <p><b>Discord.</b> The Unrealcraft bot mirrors certain activity into the Discord server, including roles, rank announcements and submitted work posted to review or showcase channels. Information posted in Discord is also subject to Discord&apos;s own privacy policy.</p>
        <p>Unrealcraft does not otherwise disclose personal information to third parties, except where required by law.</p>

        <h2>5. Retention</h2>
        <p>Information is retained for as long as your account exists. On a verified deletion request, Unrealcraft removes your progress, experience points, submissions, uploaded images, player card and stored display name. Content previously posted by the bot in Discord is removed on request.</p>

        <h2>6. Your choices and rights</h2>
        <p>You may set your player card to Private or Public, change or remove your motto, title and featured achievements, and change your specializations at any time from <Link href="/me">your player card page</Link>. You may request a copy of the information held about you, the correction of inaccurate information, or the deletion of your account by contacting staff through the <a href={DISCORD_INVITE}>Unrealcraft Discord server</a>. Depending on where you live, you may have additional rights under local data protection law, and Unrealcraft will honour valid requests made under those laws.</p>

        <h2>7. Security</h2>
        <p>Unrealcraft takes reasonable measures to protect the information it holds, including signed session cookies and restricted staff access. No system is completely secure, and Unrealcraft cannot guarantee the security of information.</p>

        <h2>8. Children</h2>
        <p>The Service requires a Discord account and is therefore subject to Discord&apos;s minimum age requirements. The Service is not directed to children under 13, and Unrealcraft does not knowingly collect information from them.</p>

        <h2>9. Changes to this policy</h2>
        <p>Unrealcraft may update this policy from time to time. Material changes are announced in the <Link href="/changelog">changelog</Link> and on the Discord server, and the effective date above is revised. Continued use of the Service after a change takes effect constitutes acceptance of the updated policy.</p>

        <h2>10. Contact</h2>
        <p>Questions about this policy and requests concerning your information may be directed to staff on the <a href={DISCORD_INVITE}>Unrealcraft Discord server</a>.</p>
      </div>
    </>
  );
}
