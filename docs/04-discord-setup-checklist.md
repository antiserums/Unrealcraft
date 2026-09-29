# 04 — Human Discord setup checklist (test server first)

Do these steps in order. They take about 45 minutes. Check each box as you go.

## A. Bot application
- [ ] discord.com/developers → New Application → name it **Quartermaster**. Give it a dark avatar with a gold "UC" crest.
- [ ] Bot tab → Reset Token → paste the token into `bot/.env` as `DISCORD_TOKEN`. Never commit it.
- [ ] Bot tab → Privileged Gateway Intents: **Server Members ON**. Presence OFF. **Message Content OFF**; the help-desk modal makes it unnecessary.
- [ ] OAuth2 → URL Generator: scopes `bot` + `applications.commands`. Bot permissions: Manage Roles, Manage Channels,
      Manage Threads, Send Messages, Send Messages in Threads, Create Public Threads, Embed Links, Attach Files,
      Read Message History, Add Reactions, Use Application Commands. Invite it to the **test server**.

## B. Server settings
- [ ] Server Settings → Community: enable it. Forums, announcement channels and Stage need Community.
- [ ] Rules screening / Onboarding: **off** for now. /start is the onboarding.
- [ ] Default notifications: Only @mentions.
- [ ] Verification level: Low (test) / Medium (live).
- [ ] AutoMod: enable the "Block mention spam" and "Commonly flagged words" presets, logging to #mod-log.

## C–E. Roles, channels, IDs: automated
The bot builds all of this itself. Run `python -m registrar --bootstrap` (or `/setup bootstrap` in Discord):
roles, categories, forums, permissions, Rules Screening, Onboarding questions, welcome screen, AutoMod, pins,
and it writes every ID into `bot/config/unlocks.yaml`. It is safe to re-run; it never deletes anything a member posted in.

The only manual step is the **Server Guide** (Server Settings → Onboarding → Server Guide); Discord blocks bots from it.

## F. Pins
Pinned guides are created and updated in place by the bot (`/setup sync-pins`). Nothing to post by hand.

## F2. Old checklist (kept for reference)
- [x] Pins are posted by bootstrap. Only the Server Guide is manual.
- [ ] #welcome: 5 posts. (1) The loop. (2) Ranks and what they unlock. (3) Majors and tasters. (4) The five commands. (5) Help-desk format.
- [ ] #quest-board: "How quests work" pin. Its **Clocked in** button is posted by `/admin post-pins` (Phase 2).
- [ ] #help-desk: pin the **New help post** button (also `/admin post-pins`) and one "bad vs good" example (used by R0-META-03).
- [ ] #showcase: pin "How to give WIP feedback: one thing that works, one specific issue, one next step."
- [ ] #epic-games-resources: Epic Get Started, Your First Hour, Level Designer Quick Start, Programming Quick Start, Materials, Blueprints.
- [ ] Add a link to the sample Behavior Tree that R3-DZ-02 refers to in the #epic-games-resources pin (Phase 4).

## G. Smoke test (Phase 2 exit criteria)
- [ ] Fresh alt account: /start → O1 quiz → /major → /rank + /quest → Clocked in → /submit O5 READY → help post → voice 60s → react.
- [ ] It receives Oriented + Greenlit, and the DM names S1.
- [ ] /path matches docs/05 for that major.
- [ ] Completing S1–S11 plus reaching 650 XP promotes to Blockout Artist. The card appears in #rank-ups, the world-lighting channels appear, and the rank role is swapped, not stacked.

## H. Invite link
- [ ] Server invite: https://discord.gg/Y2yDDNQQw. Make sure it is set to **never expire** with **no max uses** (Server Settings → Invites), because it goes on pins and in the README.
- [ ] Post it in #welcome only after the smoke test passes. Until then, test on a separate private server or with the bot invited to this server and all non-GATE categories hidden.
