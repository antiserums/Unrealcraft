import { Spot } from "@/components/SiteArt";
import { getT } from "@/lib/i18n";

export default async function Login({ searchParams }: PageProps<"/login">) {
  const t = await getT();
  const MESSAGES: Record<string, string> = {
    cancelled: t("Login was cancelled. Try again when you are ready."),
    token: t("Discord did not accept the login. Try again."),
    not_member: t("You are not a member of the Unrealcraft Discord server yet. Join it first, then log in."),
  };
  const { error } = await searchParams;
  const msg = typeof error === "string" ? MESSAGES[error] : null;
  return (
    <>
      <h1>{t("Log in")}</h1>
      {msg && <div className="note" style={{ marginBottom: 14 }}>{msg}</div>}
      <Spot art="guild-entry">
        <p style={{ marginTop: 0 }}>{t("Unrealcraft uses your Discord account. Nothing else to remember.")}</p>
        <a className="btn primary" href="/api/auth/discord">{t("Log in with Discord")}</a>
      </Spot>
    </>
  );
}
