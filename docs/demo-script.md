# Demo Script: Maintenance Triage

Script for a recorded screen walkthrough, published to YouTube, aimed at US residential
property management owners and operations leads.

**Target length: 6:49.** That is 789 words of narration at an unhurried 130 words a
minute, plus 12 percent for pauses and screen actions. The arithmetic is below, per
scene, so the timestamps can't drift from what's said.

**Tone:** calm, plain, unhurried. Incident-report register. Describing how a piece of
office work was automated, not selling software.

---

## The framing this script exists to protect

**This is custom automation built inside a property management company's existing
inbox, not a product.** There is no login to show, no seat, no subscription, and no
second customer sharing this instance. It runs on infrastructure the client owns, reads
a mailbox they already use, and they own it when the work is done.

Three rules keep that honest on camera:

1. **Lead with the automations, not the board.** Scene 2 opens on the n8n workflow list
   before anything that looks like a dashboard.
2. **Name the responsible workflow every time something happens.** A named workflow is
   a component someone can own. "The system" is a product someone rents.
3. **Never say "it does X" without saying which part.** Say "the intake workflow does
   X."

Never say: my platform, my tool, my product, the app, users, sign up, subscribers.

Say: the intake workflow, the alert dispatch workflow, the mailbox, the database, the
board, the office.

---

## Workflows on screen

| Workflow, as named in n8n | Responsible for | Triggered by |
|---|---|---|
| Maintenance Triage Fixture Fire | Injecting the six weekend-style demo messages, staggered | Manual trigger |
| Maintenance Triage Core | Normalizing, classifying, applying the safety-keyword rules, drafting | Called by every ingestion workflow |
| Maintenance Triage Email Ingest | Picking up the one real live email sent on camera | IMAP trigger on the demo mailbox |
| Maintenance Triage Alert Dispatch | Deciding whether the phone buzzes, and sending the Telegram alert | Called after every new ticket |
| Maintenance Triage Telegram Callback | Receiving the approve tap | Telegram button press |
| Maintenance Triage Approval Action | Sending the approved reply, and guaranteeing a second tap can't send twice | Called by the callback workflow |
| Maintenance Triage Form Ingest | The live "break it" submission | Web form trigger |
| Maintenance Triage Board | Rendering everything shown on screen | Loaded on request |

**Two workflows run and never appear on screen:** Maintenance Triage Post Ingest
matches the unit against the demo roster in the background after every ticket, and
Maintenance Triage Emergency Escalation is a 15-minute schedule that stays irrelevant
for an eight-minute recording. **Two more stay disabled throughout:** Maintenance
Triage Daily Digest and Maintenance Triage Operator Heartbeat both default to off in
config, and staying off is confirmed before recording (see the checklist).

---

## YouTube package

### Title

**Recommended:** `How AI Maintenance Triage Works Inside a Property Management Inbox`

66 characters, comfortably inside the roughly 70 that stay visible before truncation.
Names the mechanism and the audience.

**Alternatives:**
- `A Property Management Inbox, Triaged Live by AI and a Fixed Rule` (67)
- `Maintenance Triage Automation: A Full Walkthrough` (51)

### Description

The first 95 characters stand alone before "Show more," so the opening line has to
carry the whole idea.

> A gas-smell message lands in a demo inbox, and a fixed rule flags it before the model finishes.
>
> This is not a product and there's nothing to log into. It's custom automation built inside a property management company's existing mailbox and phone. Thirteen workflows do the work, and this video names which one is responsible for each thing you see.
>
> What it does: reads an incoming message, classifies its priority and trade, and checks the same text against a fixed list of safety keywords that can only raise the priority, never lower it. Drafts a tenant reply and a vendor note. Alerts the manager by Telegram on anything urgent, and sends nothing to a tenant until a person taps approve.
>
> What it refuses to do, and what it genuinely can't do yet, explained near the end.
>
> All fixture messages and unit numbers shown are synthetic. One message is sent live during the recording, from a personal account, to a dedicated demo mailbox.
>
> Chapters below. If you run a property management company and want to see this against your own week, the last thirty seconds explain how.

### Chapters

```
0:00 A quiet Monday morning inbox
0:22 What this actually is
1:20 Firing six weekend messages
2:41 A real one: gas smell, real alert, real approve
3:45 Breaking it on purpose
4:33 The one it won't draft a reply for
5:06 What it refuses to do, and what it can't do yet
6:02 If you want your own week sorted
```

### Hashtags

`#PropertyManagement #AIAutomation #MaintenanceTriage`

---

## Timing arithmetic

789 words of narration, at 130 words per minute unhurried delivery, is 6.07 minutes of
speech. Add 12 percent for pauses and on-screen actions: 6.07 x 1.12 = 6.80 minutes,
which is 6 minutes 49 seconds. That is the target length above, and the chapter
timestamps below are this same arithmetic run scene by scene, at roughly 0.517 seconds
per word (130 wpm x 1.12 overhead = 116.1 effective words per minute), not estimated
separately.

| Scene | Words | Scene duration | Starts at |
|---|---|---|---|
| 1. Cold open | 43 | 0:22 | 0:00 |
| 2. What this actually is | 113 | 0:58 | 0:22 |
| 3. Firing six weekend messages | 156 | 1:21 | 1:20 |
| 4. The real one | 124 | 1:04 | 2:41 |
| 5. Breaking it on purpose | 92 | 0:48 | 3:45 |
| 6. The accommodation example | 63 | 0:33 | 4:33 |
| 7. What it refuses / can't do | 108 | 0:56 | 5:06 |
| 8. The close | 90 | 0:47 | 6:02 |
| **Total** | **789** | **6:49** | |

If a later edit pushes the total outside 6-10 minutes, cut words from the longest
scene and recompute this table. Do not relabel the chapter timestamps without rerunning
the arithmetic.

---

## Before You Hit Record

All staging happens through the same screens used in the recording. No terminal is on
camera.

**1. Reset to clean state.**
```
.\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean
```
Confirms the board loads empty before anything else.

**2. Start a fresh tunnel and point the board at it.** A stale tunnel URL from a prior
session is the most likely reason a Telegram board-link button fails on camera.
```
.\scripts\start-cloudflare-tunnel.ps1
```
Then set the fresh URL as the board's public base:
```sql
update triage.config
set value = jsonb_set(value, '{public_base_url}', to_jsonb('https://your-current-tunnel.trycloudflare.com'::text), true)
where key = 'board';
```

**3. Confirm the live prerequisites.**
```
.\scripts\check-stage-7-live-prereqs.ps1
```
This fails loudly if the mailbox credentials, outbound mode, or the three live
ingestion workflows (`mt-email-ingest-stage-7`, `mt-form-ingest-stage-7`,
`mt-import-bridge-stage-7`) aren't active. Fix whatever it names before continuing.

**4. Confirm the phone will buzz.** `triage.config.contacts.primary_chat_id`
must be the real chat id for the phone used in the recording, not a placeholder.

**5. Confirm digest and heartbeat stay off.** `triage.config.digest.enabled` and
`triage.config.heartbeat.enabled` should both read `false`, so nothing extra fires or
emails during the recording.

**6. Check n8n's workflow list is presentable.** This screen is Scene 2. All thirteen
active workflows should show Active, sorted so nothing half-built is visible.

Tabs to have open, in this order:
1. n8n workflow list: `http://localhost:5678/home/workflows`
2. The board: `http://localhost:5678/webhook/board?t=<board-token>`
3. The intake form: `http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue`
4. A personal email account, ready to send one message to the demo mailbox
5. Telegram, open and unmuted, on the phone used for recording

Close everything else. Silence notifications other than Telegram.

---

## Scene 1: A quiet Monday morning inbox (0:00-0:22)

**Workflow on screen:** none yet, the board only.

**Screen:** the board, empty. Let it sit for two seconds before speaking.

> "This is a maintenance inbox at seven on a Monday morning. Nothing waiting. Over the
> next few minutes I'm going to put six weekend messages through it, then send one
> myself, live, and show you exactly which piece of automation did each part."

---

## Scene 2: What this actually is (0:22-1:20)

**Workflow on screen:** all thirteen active workflows.

**Screen:** the n8n Workflows page.

> "One thing before anything else, because it changes how you read the rest of this.
> This is not a product. There's no login, no seat, no monthly subscription to a
> dashboard. What you're watching is thirteen automations running on a server, reading
> a mailbox, and writing to a database."

Scroll slowly down a few of the names.

> "Intake reads a message and classifies it. A separate set of fixed rules checks the
> same text for safety keywords, and can only raise the priority, never lower it. Alert
> dispatch decides whether a phone buzzes. Approval action is the only place an email
> ever gets sent, and only after a human taps a button. Every scene from here names
> which one is responsible."

---

## Scene 3: Firing six weekend messages (1:20-2:41)

**Workflow on screen:** Maintenance Triage Fixture Fire, then Maintenance Triage Core.

**Screen:** click Manual Start on the fixture-fire workflow, then the board, refreshing
every five seconds as cards land.

> "These six are fixture messages I wrote to stand in for what actually lands over a
> weekend. Watch the board, not me."

Let the cards land, roughly two seconds apart.

> "There's a burst pipe with no unit number. There's a squeaky door marked 'urgent' in
> all caps, which stays at the bottom, because the rules don't listen to volume.
> There's a three-paragraph complaint about a barking dog and a parking spot, and
> buried in the middle of it, a dripping ceiling with a bucket underneath. That's the
> one the board leads with."

Point at the gas-smell card and its stamp.

> "And there's this one. A message that just says it's probably nothing, but there
> might be a smell of gas. The model on its own read that as urgent, not an emergency.
> A fixed keyword rule overrode it, because the word gas is in the text. That override
> is separate code from the model, and it can't be talked out of firing, because it
> isn't reasoning about anything. It's checking a word."

---

## Scene 4: A real one (2:41-3:45)

**Workflow on screen:** Maintenance Triage Email Ingest, then Maintenance Triage Alert
Dispatch, then Maintenance Triage Approval Action.

**Screen:** a personal email account, compose a message to the demo mailbox; then the
board; then the phone.

> "Everything so far was a fixture. Here's a real one. I'm sending this from my own
> phone right now, to the actual mailbox this project reads."

Send: *"Hi, this is Dana in 2B. I think I smell gas by the front door. Probably
nothing."*

> "That email is on its way over a live inbox connection. Nobody touches a keyboard on
> my end after I hit send."

Wait for the board to update.

> "There it is. Classified, overridden by the same gas rule, and alerted."

Cut to the phone as it buzzes.

> "That's my phone. A real Telegram message, with real buttons: approve, hold, not an
> emergency."

Tap approve.

> "I just approved a reply. Watch the board."

Cut back; the card now shows "Reply sent."

> "That email went out through the real mailbox, to a real inbox, because I tapped a
> button. There's no path in this project from a message to a tenant that skips that
> tap. Not a setting. There's no code for it."

---

## Scene 5: Breaking it on purpose (3:45-4:33)

**Workflow on screen:** Maintenance Triage Form Ingest.

**Screen:** the intake form.

> "Now let me try to break it. I'm going to submit something bad on purpose."

Fill in something deliberately garbled and submit.

> "No unit, barely a sentence, and no photo actually attached even though the message
> says one is."

Board updates.

> "That one landed as needs review, not a priority at all. That's a system state. The
> model can't choose it. A message this thin trips a rule that says don't guess, hand
> it to a person. If it had said the word gas instead of nothing, the safety rule
> still would have fired, no matter how badly it was written."

---

## Scene 6: The one it won't draft a reply for (4:33-5:06)

**Workflow on screen:** decisions made in Maintenance Triage Core, rendered by
Maintenance Triage Board.

**Screen:** open the accommodation-request card from Scene 3's fixture batch.

> "Last one. This message asks for grab bars installed for a tenant's mother, who uses
> a walker."

Scroll to the "human decision required" band.

> "No draft was written for this one at all. Not a weak draft. No draft. An
> accommodation request like this gets flagged and routed straight to a person,
> because that's a decision a human has to make, not something a model should have an
> opinion on."

---

## Scene 7: What it refuses to do, and what it can't do yet (5:06-6:02)

**Screen:** the board, static.

> "A few things worth saying plainly. It never dispatches a vendor. It never sends
> anything without a tap. Age alone never sets off a phone alert; an old routine
> request just gets flagged overdue on the board."

> "And a few things it genuinely can't do yet. It doesn't write into a property
> management system. It can't read a photo, only show that one's attached. It hasn't
> been tested past English and Spanish. The only accuracy number I'll give you is
> measured: six test messages, six correct priorities, zero missed safety signals, on
> this exact fixture set. I'm not going to hand you a bigger number I haven't earned."

---

## Scene 8: If you want your own week sorted (6:02-6:49)

**Screen:** the board.

> "So that's the whole thing. A message arrives, it gets read, a fixed rule
> double-checks the dangerous words, a person approves anything that goes out, and the
> board shows all of it, the whole time."

> "If you run a property management company and want to see this against your own
> week, send me twenty real maintenance emails, names and addresses blacked out. I'll
> run them through exactly what you just watched and send back how your week would
> have sorted. No cost, nothing to install, nothing to sign up for."

---

## Fallback Lines

If something stalls mid-recording, say one of these and keep moving. Don't apologize
or troubleshoot live for more than a few seconds.

**OpenAI is slow or fails**
> "That's the failure mode I actually want. When it can't read something, it says so
> loudly instead of dropping it quietly."

**The Telegram alert doesn't arrive**
> "The alert is a second channel, not the source of truth. The ticket is already on the
> board regardless."

**The board link fails**
> "The display link is down right now. The request is still stored; let me show the
> raw execution instead."

**Postgres or the board is down entirely**
> "I'm not going to debug this on camera. I'll cut to a version of this scene recorded
> earlier and say so in the video."

**A live classification comes back wrong**
> "That's wrong, and I'd rather show you that than hide it. I'm saving this exact
> message as a new test case right now."

---

## Language Rules

Stated once here; the whole script obeys them.

**Never say:**
- "This confirms the model is always right."
- "This catches every emergency."
- "This replaces your judgment."
- "This is legal advice" or anything implying a guaranteed compliance outcome.
- My platform, my tool, my product, the app, users, sign up, subscribers.

**Say instead:**
- "This flags it and a person decides."
- "This adds information, it never removes any."
- "This is a response target, not a deadline."
- The name of the responsible workflow, every time.

**On accuracy.** The only number this script uses is the measured six-fixture result
(6 of 6 priority matches, zero missed safety signals). It does not extrapolate that
into a broader percentage, because the wider 30-fixture accuracy run has not passed.

**On the word approve.** Every use of it, in the workflow names and in the narration,
means one specific thing: a human tapping a button that releases an email. Scene 4 is
where it happens on camera. Never use the word to describe anything the model itself
decided.

---

## Pre-Recording Checklist

- [ ] Docker services running (n8n, Postgres)
- [ ] `restore-stage-8-demo-snapshot.ps1 -Name clean` run, board confirmed empty
- [ ] Fresh Cloudflare Tunnel running, URL copied into `triage.config.board.public_base_url`
- [ ] `check-stage-7-live-prereqs.ps1` passes
- [ ] `triage.config.contacts.primary_chat_id` is the real chat id for the recording phone
- [ ] `triage.config.digest.enabled` and `heartbeat.enabled` both `false`
- [ ] Telegram open and unmuted on the recording phone
- [ ] Personal email account open and ready to send the one live message
- [ ] n8n workflow list, board, and intake form tabs all open and tidy
- [ ] Fixture Fire workflow open with Manual Start ready to click
- [ ] No day counts or ages quoted in narration that will drift after this is recorded
- [ ] "Synthetic test data" note ready for the description
- [ ] Notifications silenced except Telegram
- [ ] Screen readable at the recording resolution
