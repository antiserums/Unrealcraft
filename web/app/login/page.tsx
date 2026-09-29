const MESSAGES: Record<string, string> = {
  cancelled: "Login was cancelled. Try again when you are ready.",
  token: "Discord did not accept the login. Try again.",
  not_member: "You are not a member of the Unrealcraft Discord server yet. Join it first, then log in.",
};

export default async function Login({ searchParams }: PageProps<"/login">) {
  const { error } = await searchParams;
  const msg = typeof error === "string" ? MESSAGES[error] : null;
  return (
    <>
      <h1>Log in</h1>
      {msg && <div className="note" style={{ marginBottom: 14 }}>{msg}</div>}
      <p>Unrealcraft uses your Discord account. Nothing else to remember.</p>
      <a className="btn primary" href="/api/auth/discord">Log in with Discord</a>
    </>
  );
}
