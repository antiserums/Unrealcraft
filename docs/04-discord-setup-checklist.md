# 04 — Discord setup checklist

Do these steps in order. They take about 20 minutes.

## A. Bot application
- [ ] discord.com/developers → your **Quartermaster** application → Bot tab.
- [ ] Reset Token if you are not sure the one in `bot/.env` is current, and paste it there as `DISCORD_TOKEN`. Never commit it.
- [ ] Privileged Gateway Intents: **Server Members ON**. Presence OFF. Message Content OFF (the bot never reads messages).
- [ ] OAuth2 → URL Generator: scopes `bot` + `applications.commands`. Bot permissions: Manage Roles, Manage Channels,
      Manage Threads, Send Messages, Send Messages in Threads, Create Public Threads, Embed Links, Attach Files,
      Read Message History, Move Members, Use Application Commands. Invite it to the server.

## B. Server settings
- [ ] Server Settings → Community: enable it. Forums and announcement channels need it.
- [ ] Server Settings → Roles: drag the **Quartermaster** role above every rank and specialization role, or role swaps fail.
- [ ] Default notifications: Only @mentions.
- [ ] Invite link (https://discord.gg/Y2yDDNQQw): never expire, no max uses.

## C. `bot/.env`
- [ ] `SITE_URL` = the address members use for the site. Pins, `/site` and `/card` link there. While testing on this
      machine it is `http://localhost:3000`; change it when the site has a public address, then run `/setup sync-pins`.

## D. Build the server
- [ ] From `bot/`: `.venv/Scripts/python.exe -m registrar --bootstrap` (or `/setup bootstrap` in Discord once the bot is online).
      It builds roles, categories, channels, forums, pins, Rules Screening, the welcome screen and AutoMod, writes the IDs
      to `bot/config/unlocks.yaml`, and syncs everyone's roles from the site. Safe to re-run.
- [ ] On a server built by the older bot it renames what carries over (Major roles → specialization roles, the old
      categories) and removes the quest log, the mentor queue and the gate roles. A channel that members posted in is
      never deleted: it is renamed to `…-archive` for you to decide.
- [ ] The only manual step is the **Server Guide** (Server Settings → Onboarding → Server Guide); Discord blocks bots from it.

## E. The site side
- [ ] `api/.env`: your Discord ID in `ADMIN_IDS` or `DEVELOPER_IDS`; `DEV_LOGIN_ID` **empty** before real members arrive
      (the dev login is a developer account with no password).
- [ ] Restart the API after changing `api/.env`.

## F. Smoke test
- [ ] Fresh alt account: join the server, accept the rules, follow the #welcome button, log in on the site.
- [ ] The alt is Novice at once and gets the **Novice** role in Discord within 20 seconds. Do the first steps on the site (O1–O5).
- [ ] Pick a primary specialization and one extra on the player card page. Both roles appear in Discord.
- [ ] In the admin panel set the alt to Apprentice. The role swaps, not stacks.
- [ ] `/card` on the alt shows the same rank and specializations as the site.
- [ ] Join **➕ Join to create** in Town Hall: a room is made for you and removed five minutes after it empties.
