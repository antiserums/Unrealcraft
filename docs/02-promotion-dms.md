# 02 — Promotion templates

Every promotion does five things, in this order (see `bot/cogs/ranks.py → promote()`):
1. Swap the visible rank role. Never stack them.
2. Unlock the new category or categories so the channels appear.
3. DM the 6-line briefing below.
4. Post the card in #rank-ups.
5. Grant the jump medal (`jump_<old>_<new>`), shown on /rank.

A DM has six lines, always in this order: **what you are · what you owe · next quest · who to ping · one new power · sign-off**.
`{placeholders}` are filled by the bot. `{next_quest}` comes from the same picker /quest uses, so it's already major-weighted.

---

### Oriented → Novice (Rank −1 → 0)
```
You're Novice. You have a desk but no badge yet.
You owe the Starter Quests: 11 short quests, each one sitting.
Next: {next_quest_id} · {next_quest_title} (~{time_min} min). Run /quest.
Stuck? #help-desk with the template. Mentors answer formatted posts first.
New power: #starter-quests and the major forums are open (post in your major's).
— Quartermaster · Unrealcraft
```

### Novice → Apprentice (0 → 1)
```
Apprentice. You can build a space and light it without getting lost.
You owe the {major_title} Rank 1 path, ending in: {capstone_title}.
Next: {next_quest_id} · {next_quest_title}. /path shows the whole rank.
Ask in your major's forum when a blockout feels wrong and you can't say why.
New power: World & Lighting track and the Blockout showcase tag.
— Quartermaster · Unrealcraft
```

### Apprentice → Adept (1 → 2)
```
Adept. You make things play.
You owe your side of Rank 2 ({major_side}) + {taster_count} taster(s), ending in: {capstone_title}.
Next: {next_quest_id} · {next_quest_title}.
Want a partner? Join ➕ Join to create and invite someone. Post graphs in your major's forum for reviews.
New power: you can peer-approve Rank 0–1 turn-ins (3 a day) for +15 XP each.
— Quartermaster · Unrealcraft
```
(If the major is still Undecided: add a line before the sign-off: `Pick a major now: /major. Undecided ends at this rank.`)

### Adept → Expert · {Specialty} (2 → 3)
```
Expert · {seal_title}. People can @ you for {seal_title} work now.
You owe your {seal_title} Specialty quests + the shared character basics, ending in: {capstone_title}.
Next: {next_quest_id} · {next_quest_title}.
For feedback, post in #showcase with the Critique-wanted tag.
New power: 1.25× XP on {seal_title} quests, /critique, and you can apply for Mentor-in-Training.
— Quartermaster · Unrealcraft
```
(The Specialty is picked before this DM is sent. Promotion opens a Specialty picker that only offers the Specialties allowed for the member's major, listed in `majors.yaml → seals`.)

### Expert → Master (3 → 4)
```
Master · {seal_title}. You own a system now, not just a scene.
You owe one capstone: {capstone_title}. {capstone_brief}
Next: {next_quest_id} · {next_quest_title}. Your 30-day workshop thread is open: {workshop_thread}.
Your mentor from here on is whoever reviewed your R3 capstone ({last_reviewer}). Ping them there.
New power: {track_unlock} opens, you can review Rank 2 turn-ins, and your name is hoisted.
— Quartermaster · Unrealcraft
```
`{track_unlock}` = "the C++ systems track" for code-leaning majors or "the art-systems track" for art-leaning ones.

### Master → Senior (4 → 5)
```
Senior. Your work holds up when other people touch it.
You owe: {capstone_title}, plus one weekly raid hosted this quarter.
Next: {next_quest_id} · {next_quest_title}.
Staff channel for questions: ping @Curriculum. Your promotion was human-reviewed by {reviewer}.
New power: /curriculum-propose, Stage lectures, and you can read the mentor queue.
— Quartermaster · Unrealcraft
```

### Senior → Lead (5 → 6)
```
Lead. You shipped. Vouched by {voucher_1} and {voucher_2}.
You owe the server your judgment. Review in #mentor-queue when you can.
Next: the Optimization shelf is open. /path shows it. Nothing is required.
Staff and Curriculum sit with you in #curriculum-wip.
New power: full mentor buttons, /commend, /title from the approved list, and the gold nameplate.
— Quartermaster · Unrealcraft
```

---

## #rank-ups card (embed)

```
┌───────────────────────────────────────────────┐
│  {avatar}  {display_name}                      │  accent = new rank or Specialty color
│  Apprentice  →  Adept       │  old title struck through in gray
│  Major · Level Design                          │
│  Capstone: Three-route courtyard  [thumbnail]  │  image = capstone submission's first attachment
│  Days at previous rank: 9   ·   Streak: 6      │
│  Reviewed by: honor system / @peer / @mentor   │
│  🎖 Jump medal: Novice → Blockout            │
└───────────────────────────────────────────────┘
Buttons: [ 🔥 Congrats ]  (counts as a reaction and gives no XP)
```

Nothing is posted when someone just has a lot of XP. A card only appears when a capstone passes and the XP threshold is met.

---

## Respec DM (major change)

```
Major changed: {old_major} → {new_major}.
{if rank < 3: "Free respec used. {n} missing taster(s) were added to /quest."}
{if rank >= 3: "Finish 4 required {new_major} quests at your current rank to move your Specialty. Your old {old_seal} Specialty is now a medal."}
Next: {next_quest_id} · {next_quest_title}.
— Quartermaster · Unrealcraft
```
