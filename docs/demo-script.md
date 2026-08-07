# Demo Script: Maintenance Triage

A recorded screen walkthrough for YouTube, aimed at the owner or operations lead of a US
residential property management company.

**Target length: 7:31.** Computed from the narration, scene by scene, in the timing table
below. Not estimated.

**How to talk.** You are talking to one person, not an audience. They run a property
management company, they are watching this on a phone between other jobs, and they have
seen software demos before. Say "you" and "your inbox," never "users" or "viewers." Never
say "in this video" or "as you can see" or "let's take a look." Short sentences. Say the
thing, then stop. If a sentence sounds like a slide, cut it.

---

## The framing this protects

**This is not a product.** No login, no seats, no subscription, nothing for their tenants
to join. It is automation built inside a company's existing mailbox and phone, running on
infrastructure they own.

Three rules hold that on camera:

1. **Show the workflows before the board.** Scene 2 opens on the n8n workflow list. A nice
   dashboard looks like a product; a list of named automations looks like a build.
2. **Name the piece doing the work.** "The intake workflow read that," not "the system read
   that." A named workflow is something they can own.
3. **Never say "it does X" without saying which part.**

Never say: my platform, my tool, my product, the app, users, sign up, subscribers.

---

## Workflows on screen

| Workflow, as named in n8n | What it does in this recording |
|---|---|
| Maintenance Triage Fixture Fire | Injects the six test messages in scene 3 |
| Maintenance Triage Core | Normalizes, classifies, applies the safety rules, writes the drafts |
| Maintenance Triage Email Ingest | Picks up the one real email you send in scene 6 |
| Maintenance Triage Post Ingest | Matches the unit against the roster, decides whether to alert |
| Maintenance Triage Alert Dispatch | Sends the Telegram alert in scene 7 |
| Maintenance Triage Telegram Callback | Receives your approve tap |
| Maintenance Triage Approval Action | Sends the approved reply, and refuses to send twice |
| Maintenance Triage Board | Renders everything you point at |

Three run and never appear: Emergency Escalation (a 15-minute schedule, irrelevant over
seven minutes), Daily Digest and Operator Heartbeat (both gated off in config, confirmed in
staging).

---

## Flow facts that constrain these scenes

Read this before recording. Each one is a real behavior of the build, and getting it wrong
on camera either breaks the take or makes you say something untrue.

1. **Firing fixtures does not ring your phone.** Fixture Fire passes `mock_telegram: true`,
   deliberately, so a rehearsal never sends real alerts. Do not gesture at your phone during
   scene 3, and do not promise a buzz that will not come. The phone buzz comes from the real
   email in scene 6, which is the only path in this recording that uses real alert dispatch.
2. **Six fixtures take about 75 seconds, not 12.** Each one is a real classification call and
   a real drafting call, run one at a time. Cards land roughly 11 seconds apart. Scene 3 is
   written to fill that time. Do not click Execute twice because nothing appeared yet.
3. **The live message must trip a keyword rule.** Use wording that matches the flood rule
   exactly, "water is pouring," so the emergency is guaranteed rather than left to model
   variance on camera.
4. **The approved reply goes back to whoever sent the message.** Outbound is in live mode, so
   for an emailed ticket the reply goes to the sending address. Send scene 6 from a personal
   account you are happy to show, and the reply lands there for you to display.
5. **Quiet hours do not affect an emergency.** An EMERGENCY alerts audibly at any hour. An
   URGENT ticket would be held between 20:00 and 07:00 Chicago time, so do not build a scene
   on an urgent alert firing.
6. **The Telegram alert needs a live tunnel.** Its board button must be a public HTTPS URL. A
   stale or missing `board.public_base_url` makes the whole alert fail, not just the button.
7. **The demo mailbox must have zero unread mail.** The IMAP trigger ingests anything unread
   the moment it is active, and those become tickets on your clean board.
8. **The unit in your live message should exist in the roster.** Use `4C`, which is Maple
   Court 4C, so the card shows a real property rather than "not found."

---

## Timing

910 words of narration at an unhurried 130 words a minute, plus 12 percent for pauses and
screen actions, gives 145.6 effective words a minute. Speech time is words divided by that.
Where the build takes longer than the words, the scene runs at the build's pace instead, and
that floor is what goes in the table.

| Scene | Words | Speech | Floor | Duration | Starts |
|---|---|---|---|---|---|
| 1. The inbox you already know | 41 | 0:16 | 0:20 | 0:20 | 0:00 |
| 2. What this actually is | 89 | 0:36 | none | 0:36 | 0:20 |
| 3. Putting a weekend through it | 69 | 0:28 | 1:15 | 1:15 | 0:56 |
| 4. What it did with them | 67 | 0:27 | none | 0:27 | 2:11 |
| 5. The rule that overrules the AI | 79 | 0:32 | none | 0:32 | 2:39 |
| 6. Sending one for real | 62 | 0:25 | 0:45 | 0:45 | 3:11 |
| 7. The tap, and the email that follows | 79 | 0:32 | 0:40 | 0:40 | 3:56 |
| 8. The one it refuses to answer | 72 | 0:29 | none | 0:29 | 4:36 |
| 9. What it won't do, and can't do | 95 | 0:39 | none | 0:39 | 5:06 |
| 10. What it takes to run in your business | 176 | 1:12 | none | 1:12 | 5:45 |
| 11. See it against your own week | 81 | 0:33 | none | 0:33 | 6:58 |
| **Total** | **910** | | | **7:31** | |

If an edit changes the words, recompute this table and the chapter list from it. Do not
relabel timestamps by hand.

---

## Before you record

**1. Clean board.**
```
.\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean
```

**2. Empty the demo mailbox.** Every unread message in it becomes a ticket the moment the
IMAP trigger runs. Archive everything.

**3. Fresh tunnel, and point the board at it.**
```
.\scripts\start-cloudflare-tunnel.ps1
```
Then set the new URL:
```sql
update triage.config
set value = jsonb_set(value, '{public_base_url}', to_jsonb('https://your-current-tunnel.trycloudflare.com'::text), true)
where key = 'board';
```

**4. Confirm the live paths.**
```
.\scripts\check-stage-7-live-prereqs.ps1
```

**5. Confirm your phone will actually buzz.** `triage.config.contacts.primary_chat_id` must
be the real chat id for the phone you are filming, not a placeholder.

**6. Confirm nothing extra fires.** `triage.config.digest.enabled` and `heartbeat.enabled`
both read `false`.

**7. Confirm all thirteen workflows show Active** in n8n, and tidy the list. That screen is
scene 2.

**8. Dry-run scene 6 once, then reset.** Send the real email, watch it alert, then run the
snapshot restore again. You want to know it works before the camera is on.

Tabs open, in order:
1. n8n workflows: `http://localhost:5678/home/workflows`
2. The board: `http://localhost:5678/webhook/board?t=<board-token>`
3. Fixture Fire workflow, ready to execute
4. Your phone, on camera, with Telegram open

Silence every notification except Telegram.

---

## Scene 1: The inbox you already know (0:00-0:20)

**On screen:** the board, empty.

**You do:** let it sit for three seconds before speaking.

> "If you run a property management company, you already know what Monday morning looks
> like. Forty messages sat there since Friday. Somewhere in them is the one that actually
> mattered. This is that inbox, except something read it before you did."

---

## Scene 2: What this actually is (0:20-0:56)

**On screen:** the n8n workflow list, all thirteen showing Active.

**You do:** scroll slowly down the names as you talk. Do not click into one.

> "I want to be straight with you about what this is, because it changes how you watch the
> rest. This isn't software. There's nothing to log into, nothing to buy a seat for, no
> portal for your tenants to learn. It's a set of automations that sit on a server, read a
> mailbox, and write to a database. All of it yours. Right now you're looking at the list of
> them. Thirteen pieces, each doing one job. I'll name which one is working every time
> something happens on screen."

**Watch out:** this is the scene that stops the video reading as a product tour. Do not cut
it for time.

---

## Scene 3: Putting a weekend through it (0:56-2:11)

**Responsible:** Maintenance Triage Fixture Fire, then Maintenance Triage Core.

**On screen:** click Execute on Fixture Fire, then switch to the board and stay there.

**You do:** click once. Switch tabs. Then wait, and keep talking while cards appear.

> "So let me put a weekend through it. These six are test messages I wrote, standing in for
> what actually lands between Friday night and Monday. Watch the board, not me."

Let two or three cards land.

> "These take about ten seconds each, because every one is a real call to a real model
> reading real text. It isn't a recording. That's also roughly what it costs you: a fraction
> of a cent per message."

Then stop talking and let the rest land.

**Watch out:** about 75 seconds end to end. No phone buzz here, by design. If the silence
feels long in the edit, this is the scene to speed up, not the one to cut.

---

## Scene 4: What it did with them (2:11-2:39)

**Responsible:** decisions from Maintenance Triage Core, rendered by Maintenance Triage Board.

**On screen:** the full board. Point at the buried-lede card, then the squeaky-door card.

> "Look at what it did with them. Somebody wrote three paragraphs about a barking dog and a
> parking space, and buried in the middle of it, their ceiling is dripping into a bucket.
> That's the one it put near the top. Somebody else typed urgent in capital letters about a
> squeaking door, and it left that at the bottom, because it reads what's described, not how
> loudly."

---

## Scene 5: The rule that overrules the AI (2:39-3:11)

**Responsible:** the `Apply Safety Rules` step inside Maintenance Triage Core.

**On screen:** the gas card, with its override stamp. Open the detail view if the stamp is
hard to read.

> "Now this one is the reason I built it this way. A tenant writes that they can probably
> smell gas, and it's probably nothing. The model on its own called that urgent. Not an
> emergency. A separate rule overruled it, because the word gas is in the message. That rule
> is ordinary code sitting after the model. It can't be talked out of it, it can't have a bad
> day, and it only ever moves things up, never down."

**Watch out:** the strongest thirty seconds in the video. Slow down here.

---

## Scene 6: Sending one for real (3:11-3:56)

**Responsible:** Maintenance Triage Email Ingest, then Core, then Post Ingest.

**On screen:** your phone composing an email, then the board.

**You do:** send from a personal account, not the demo mailbox.

> "Here's what I'd want to see if I were you. Everything so far came from my own test set. So
> let me send one for real, from my phone, to the actual mailbox this thing reads."

Send: *"Water is pouring out from under the kitchen sink and I can't stop it. Unit 4C."*

> "Nothing on my end after this. No clicking, no helping it along."

Put the phone down. Watch the board. Roughly 20 seconds.

> "There it is. Read, sorted, and the same water rule pushed it to emergency."

**Watch out:** the wording matters. "Water is pouring" trips the flood rule, so the emergency
is guaranteed rather than left to the model. `4C` is a real roster unit, so the card shows
Maple Court rather than "not found."

---

## Scene 7: The tap, and the email that follows (3:56-4:36)

**Responsible:** Maintenance Triage Alert Dispatch, then Telegram Callback, then Approval Action.

**On screen:** your phone as the alert lands, then the board, then your inbox.

> "And that's my phone. Not a notification I built to look good in a video. That's the real
> thing, with three buttons on it, and I could be anywhere when it arrives."

Hold the phone still so the buttons are readable.

> "Watch the board when I press approve."

Tap approve. Cut to the board; the card moves to reply sent.

> "That email just went to the tenant, because I pressed a button. There is no path through
> any of this where a message reaches your tenant without somebody's thumb. Not a setting I
> switched on. There's no code for it."

Show the reply arriving in the personal account you sent from.

**Watch out:** the reply goes back to the address that sent the message, which is why scene 6
comes from an account you can show. Tap approve once. A second tap is correctly refused, and
explaining that on camera costs you the moment.

---

## Scene 8: The one it refuses to answer (4:36-5:06)

**Responsible:** the human-only decision in Maintenance Triage Core.

**On screen:** open the accommodation card from scene 3. Scroll to where the draft would be.

> "And here's the one I'd point at if you only had thirty seconds. A tenant asks for grab
> bars in the bathroom for their mother, who uses a walker. It read that, flagged it, and
> wrote nothing at all. No draft, not even a weak one. That's a fair housing conversation, and
> it belongs to a person who knows your properties and your obligations. A machine having an
> opinion there helps nobody."

---

## Scene 9: What it won't do, and can't do (5:06-5:45)

**On screen:** the board, still.

> "Let me be honest about the rest of it. It won't create the work order in your software. It
> won't call a vendor. It'll miss things, and some days it'll wake you for something that
> turns out to be nothing, which costs you a phone call. It can't read a photo, only tell you
> one is attached. And the only accuracy number I'll give you is the one I measured: six test
> messages, six correct priorities, no missed safety signals, on that set. I'm not going to
> hand you a bigger number I haven't earned."

**Watch out:** do not soften this. It is the scene that makes everything before it credible.

---

## Scene 10: What it takes to run in your business (5:45-6:58)

**On screen:** the board, or your face if you have a camera. This is the part they are
actually deciding on.

> "So what would it actually take to put this in your business. Less than you'd think. You
> add a forwarding rule to your maintenance inbox, which takes about five minutes. You send me
> your unit list, one export out of whatever software you already use. You tell me who gets
> woken up, what response times you promise your owners, and how you want replies to sound."

> "That's it. I don't touch your property management software. I don't need a login to it.
> Your tenants carry on emailing exactly where they email now, and they never know anything
> changed."

> "And the first week, it doesn't send anything. It just reads, sorts, and drafts, and at the
> end of the week you compare what it flagged against what your team actually did. If it's
> reading your mail wrong, you find out that week, for the price of a forwarding rule."

> "If you ever want it gone, you delete the forwarding rule. Five minutes, and you're back to
> exactly the inbox you have today. Nothing's moved, nothing's trapped anywhere."

---

## Scene 11: See it against your own week (6:58-7:31)

**On screen:** the board.

> "If you want to see this against your own week rather than mine, send me twenty real
> maintenance emails from last month. Black out the names and addresses, I don't need them.
> I'll run them through what you just watched and send you back your own week, sorted, with
> the ones it got wrong listed first. Costs you nothing, and there's nothing to install. The
> link's in the description, and I delete your files the day I send the page back."

**Watch out:** no deadline, no bonus, no limited spots. The offer works because it is small
and checkable. Two details carry it: listing the misses first, and saying out loud that the
files get deleted. Someone deciding whether to email you their tenants' messages is thinking
about both.

**Put the link in the description before you publish.** The narration promises it.

---

## YouTube package

### Title

**Recommended:** `I built something that reads your maintenance inbox before you do`

65 characters, inside the roughly 70 that stay visible. Second person, and it describes what
happens to them rather than what the thing is.

**Alternatives:**
- `What happens to your maintenance inbox before you open it Monday` (64)
- `Your weekend maintenance inbox, already sorted by Monday morning` (64)

### Description

The first line has to stand alone before "Show more." This one is exactly 100 characters.

> A tenant writes that they can probably smell gas. A fixed rule overrules the AI and flags it anyway.
>
> If you run a property management company, this is the part of the job that lives in an inbox and somebody's memory: reading every message, working out which one can't wait, and drafting the reply. This reads them first and sorts them. It never answers anyone on its own.
>
> There's nothing to log into and nothing to buy. It's automation built inside a mailbox and a phone that already exist, running on a server the client owns. Thirteen workflows do the work, and the video names which one is responsible for each thing on screen.
>
> Near the end: what it refuses to do, what it genuinely can't do yet, and exactly what it would take to run inside your own business. That last part is about five minutes of setup on your side.
>
> All test messages, unit numbers and tenants shown are synthetic. One message is sent live during the recording, from a personal account, to a dedicated demo mailbox.
>
> Chapters below. The last thirty seconds explain how to see this against your own week.

### Chapters

```
0:00 The inbox you already know
0:20 What this actually is
0:56 Putting a weekend through it
2:11 What it did with them
2:39 The rule that overrules the AI
3:11 Sending one for real
3:56 The tap, and the email that follows
4:36 The one it refuses to answer
5:06 What it won't do, and can't do
5:45 What it takes to run in your business
6:58 See it against your own week
```

### Hashtags

`#PropertyManagement #AIAutomation #MaintenanceTriage`

---

## If something stalls

Say one of these and keep moving. Do not troubleshoot on camera for more than a few seconds.

**Cards are slow to appear in scene 3**
> "Each one of these is a real classification call, so it's doing the work rather than
> replaying it."

**The model is slow or errors**
> "That's the failure I actually want. When it can't read something it says so loudly instead
> of dropping it quietly."

**The Telegram alert doesn't arrive**
> "The alert is the second channel, not the record. The ticket's already on the board either
> way, and that's the bit that matters."

**The board link fails**
> "The page is down. The request is still stored, so let me show you the run itself instead."

**The whole thing is down**
> "I'm not going to debug this while you watch. I'll cut to a version of this I recorded
> earlier and tell you that's what I've done."

**It classifies your live message wrong**
> "That's wrong, and I'd rather you see it than not. That message becomes a test case today,
> and this is exactly how it gets safer."

---

## Language rules

**Never say:**
- That it catches every emergency.
- That it verifies, confirms, or checks anything about a tenant's situation.
- That it replaces anyone's judgment.
- Anything implying a legal obligation, a deadline, or a compliance guarantee.
- My platform, my tool, my product, the app, users, sign up, subscribers.

**Say instead:**
- "It flags it and you decide."
- "It only ever adds information. It never removes any."
- "That's a response target, not a deadline."
- The name of the workflow doing the work.

**On accuracy.** The only number in this script is the measured six-fixture result: six of
six priorities correct, no missed safety signals, on that set. Do not turn it into a
percentage and do not extend it to messages it has not seen. The wider 30-fixture run has
not passed.

**On the word approve.** It means one thing: a human pressing a button that releases an
email. Never use it for anything the model decided.

---

## Pre-recording checklist

- [ ] Docker services up
- [ ] `restore-stage-8-demo-snapshot.ps1 -Name clean` run, board confirmed empty
- [ ] Demo mailbox has zero unread messages
- [ ] Fresh tunnel running, URL written into `triage.config.board.public_base_url`
- [ ] `check-stage-7-live-prereqs.ps1` passes
- [ ] `contacts.primary_chat_id` is the phone you are filming
- [ ] `digest.enabled` and `heartbeat.enabled` both false
- [ ] All thirteen workflows Active, list tidied for scene 2
- [ ] Scene 6 dry-run done, then board reset again
- [ ] Personal sending account open and ready, and one you are happy to show
- [ ] Phone framed, Telegram open, notifications otherwise silenced
- [ ] No day counts or ticket ages spoken aloud, they drift after recording
- [ ] "Synthetic test data" note ready for the description
