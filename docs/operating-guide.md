# Operating And Testing Guide

This is not a script. It is how you run, use, and test every part of the maintenance
triage automation, mostly through the n8n browser interface, your mailbox, and Telegram.
A script or a terminal command is used only where no screen exists for that task, and
each time that happens, it's called out explicitly with the reason why.

For what each piece does and why it's built this way, see
[how-the-system-works.md](how-the-system-works.md). This document assumes you've read
that, and is only concerned with doing and checking things.

Every section below follows the same shape: **Do**, **Expect**, **Verify**.

---

## Quick reference: what's operable where

| Task | Where you do it | UI or command |
|---|---|---|
| Start/stop the local stack | Docker Desktop | Command (no browser control for Docker itself) |
| Check workflows are Active | n8n → Workflows | UI |
| Check credentials | n8n → Credentials | UI |
| View the board | Your browser | UI |
| Submit a test request | The web form, in your browser | UI |
| Submit a test request | Your email client | UI |
| Fire six ready-made test messages | n8n → Fixture Fire workflow | UI |
| Approve, hold, or downgrade an alert | Telegram, on your phone | UI |
| Run the daily summary or the quiet-inbox check on demand | n8n → that workflow | UI |
| Run the unanswered-emergency check on demand | n8n → that workflow | UI |
| Turn the daily summary or quiet-inbox check on/off | n/a | Command (no settings screen exists yet) |
| Change response targets, quiet hours, contacts | n/a | Command (no settings screen exists yet) |
| Import a folder of past emails in bulk | n/a | Command (no upload screen exists for bulk files) |
| Reset the board to empty | n/a | Command (no delete/reset control exists) |
| Save or restore a clean snapshot | n/a | Command (no snapshot control exists) |

The commands referenced throughout are PowerShell scripts already in `scripts/`, or short
database commands where no script exists for a one-off change. Where a command is a
generic database update rather than a saved script, that's stated directly.

---

## Before you start

**Do:** Open Docker Desktop and confirm three containers are running: `n8n`, `postgres`,
and `greenmail`. If they aren't:
```powershell
.\scripts\start-local.ps1
```

**Expect:** All three show a green "Running" status in Docker Desktop within about 30
seconds.

**Verify:** Open `http://localhost:5678` in your browser. The n8n interface loads. This is
the only step here that has no in-browser alternative, because Docker itself has no
browser control beyond Docker Desktop's own application.

---

## One-time checks before any test

Do these once at the start of a session. Both are entirely in n8n's own interface.

### Confirm the automations are switched on

**Do:** Open n8n → **Workflows** in the left sidebar.

**Expect:** A list of names. These should show **Active**: Core, Email Intake, Web Form
Intake, Unit Matching & Routing, Alert Sending, Approval Handling, Unanswered-Emergency
Check, The Board. Daily Summary and Quiet-Inbox Check will also show Active, but sending
is separately switched off by default; see "Turning the daily summary or quiet-inbox check
on" below.

**Verify:** Click the Active toggle if anything shows Inactive that should be on. If a
board or form link 404s right after you do this, restart n8n from Docker Desktop, since a
newly switched-on address needs the running process to notice it.

### Confirm the credentials are in place

**Do:** Open n8n → **Credentials** in the left sidebar.

**Expect:** Five entries: a Postgres connection, an OpenAI connection, a Telegram bot
connection, and two mailbox connections (one for reading mail, one for sending it).

**Verify:** Open each one. None of the fields should read a placeholder value. The Postgres
credential has a **Test** button; use it and expect a success message. The others don't
have a formal test button, so confirming the fields are filled in is the check.

---

## The board: seeing everything that's open

**Do:** Open the board link in your browser:
```
http://localhost:5678/webhook/board?t=<board-token>
```
Ask whoever set this up for the current token if you don't have it.

**Expect:** A list of cards, most urgent first. An empty board says so plainly rather than
showing a blank page. The page refreshes itself every five seconds; you don't need to
reload it.

**Verify:** Click any card's reference number to open its detail page. That page shows the
original message, the drafted reply, the reasoning behind the priority, and the running
history of everything that's happened to that request. If nothing appears in that history,
something upstream didn't run; see Troubleshooting.

---

## Submitting a request through the web form

**Do:** Open:
```
http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue
```
Fill in a name, a unit, a contact method, and a description, then submit.

**Expect:** A confirmation screen showing a reference number, in the shape `MR-0001`.

**Verify:** Open the board. A new card appears within a few seconds, showing your test
message. Open its detail page to see the priority the AI assigned and why. If the priority
looks wrong for what you typed, that's useful information; see how-the-system-works.md for
what the safety check specifically looks for before assuming something is broken.

---

## Submitting a request by email

**Do:** Send an email to the maintenance mailbox from any account. Word anything meant to
trip the safety check exactly, for example "water is pouring out from under the sink,"
since the check matches specific phrases.

**Expect:** Nothing happens immediately. The mailbox is checked periodically, not the
instant a message arrives.

**Verify:** Watch the board. A card should appear within roughly a minute. If it doesn't
appear after several minutes, confirm Email Intake shows Active in n8n, and confirm the
message is still marked unread in the mailbox, since only unread mail is picked up.

---

## Firing six ready-made test messages at once

Useful for a quick end-to-end check without composing anything, or for showing someone
what a busy inbox looks like sorted.

**Do:** Open n8n → **Workflows** → **Maintenance Triage Fixture Fire**. Click **Execute
workflow** at the bottom of the canvas.

**Expect:** Six cards land on the board one at a time over about a minute and a quarter,
not all at once. Each one is a genuine call to the AI reading model, which is why it takes
that long, not a replay of something canned.

**Verify:** All six appear, spanning every state the system produces: an emergency with an
override stamp, one with no unit given, a routine item, an urgent item, and one flagged as
legally sensitive with no draft written. **These do not alert your phone.** That's
deliberate, so a rehearsal never pages anyone by accident. To see a real phone alert, use
the email or web form path instead, described above.

---

## Approving, holding, or downgrading an alert

**Do:** Submit a message that trips the safety check by email or the web form, worded to
guarantee an emergency (see above). Wait for the alert to reach Telegram.

**Expect:** A message on your phone with the tenant's own words, the unit, and three
buttons: **Approve reply**, **Hold**, and **Not emergency**. Tap **Approve reply**.

**Verify:** The Telegram message updates in place to show it's been sent. Open the board;
the card now shows the reply as sent. If you sent the test from a real address, check that
inbox; the drafted reply should have arrived there.

**Also verify the double-send guard:** tap **Approve reply** a second time on the same
alert. Nothing sends again. Telegram shows a small popup saying it was already handled,
and the board still shows exactly one reply sent.

---

## Testing the legally-sensitive path

**Do:** Submit a message through the web form describing something like a disability
accommodation request, for example asking for grab bars to be installed for a family
member who uses a walker.

**Expect:** No alert reaches your phone for this on its own, since it isn't a safety
emergency.

**Verify:** Open the card on the board. It's marked as needing a person's judgment, and no
reply was drafted at all, not even a rough one. That's not a fault; it's the design. A
request like this is never something a machine should have an opinion on.

---

## Testing the "needs a person" safety net

**Do:** Submit something genuinely unreadable through the web form: a couple of words,
garbled text, or a message that references an attachment that isn't actually there.

**Expect:** The card lands on the board flagged as needing your review rather than being
guessed at.

**Verify:** Open its detail page. The reasoning explains that there wasn't enough to work
with, rather than showing a confident-looking answer built on nothing.

---

## Testing duplicate detection

**Do:** Send the identical message twice by email, within the same day.

**Expect:** Only one card on the board.

**Verify:** Open that card's detail page. Its history shows a note that a duplicate arrived
and was folded into the same record, rather than creating a second one.

---

## Testing that a tenant's reply doesn't create a second ticket

**Do:** After a reply has been approved and sent to a real address you control, reply to
that email from that address, the normal way you'd reply to any email.

**Expect:** No new card on the board.

**Verify:** Open the original card. Its history now includes the tenant's reply, appended
to the same request. This confirms replies thread onto the original conversation instead of
looking like a brand-new, unrelated report.

---

## Running the daily summary on demand

**Do:** Open n8n → **Workflows** → **Maintenance Triage Daily Digest**. Click **Execute
workflow**.

**Expect:** By default, nothing is sent. Sending this summary is switched off out of the
box, and running the workflow manually still respects that switch; it doesn't bypass it.

**Verify:** If you want to actually see a summary email land, sending has to be turned on
first, which currently has no screen for it. Run this database command from a terminal:
```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage `
  -c "update triage.config set value = jsonb_set(value, '{enabled}', 'true'::jsonb) where key = 'digest';"
```
Then execute the workflow again. Check the recipient inbox for the summary email. Turn it
back off afterward the same way, replacing `'true'` with `'false'`, unless you intend to
leave it running on its daily schedule.

---

## Running the quiet-inbox check on demand

**Do:** Open n8n → **Workflows** → **Maintenance Triage Operator Heartbeat**. Click
**Execute workflow**.

**Expect:** By default, nothing is sent, for the same reason as the daily summary: sending
is switched off out of the box regardless of how the workflow is triggered.

**Verify:** To see this actually fire, turn it on the same way as above, replacing `digest`
with `heartbeat` in the command, then run the workflow again. It only actually alerts if
enough time has passed since the last message arrived, so on a board that's been active
recently it may report nothing to do even while switched on; that's correct behavior, not a
failure.

---

## Running the unanswered-emergency check on demand

**Do:** Open n8n → **Workflows** → **Maintenance Triage Emergency Escalation**. Click
directly on the schedule trigger node, then **Execute workflow**. This workflow normally
runs itself every 15 minutes; this forces it to run immediately instead of waiting.

**Expect:** Nothing visible happens unless there's an emergency on the board that's more
than 15 minutes old and still hasn't been tapped.

**Verify:** To see it actually do something, submit an emergency, don't tap any button on
its alert, and either wait 15 minutes or backdate it for a test:
```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage `
  -c "update triage.tickets set received_at = now() - interval '20 minutes' where ref = 'MR-0001';"
```
Run the workflow again. A second alert should reach Telegram for that request.

---

## Importing a folder of past emails in bulk

Useful when someone hands you a batch of real maintenance emails to run through the system
at once, rather than one at a time.

**Why this needs a command, not a screen:** this is a bulk-file operation with an access
token attached, and no upload page was built for it; the only path in is the script
written for exactly this purpose.

**Do:**
```powershell
python .\scripts\run-stage-7-batch-import.py .\path\to\your\folder --label "some-label"
```
Point it at a folder of `.eml` or `.txt` files.

**Expect:** Each file becomes a card on the board, the same as if it had arrived
individually.

**Verify:** The command prints where it wrote a report:
`data/import-batches/<batch-id>/report.html`. Open that file in a browser. It summarizes
every message imported, how it was classified, and how many would have alerted, plus a
`review.csv` you can fill in with the correct answers if you want to check accuracy
afterward.

---

## Resetting the board to a clean, empty state

**Why this needs a command, not a screen:** there is no delete or reset control anywhere
in the board or n8n for clearing test data; it has to be done directly against the record
store.

**Do:**
```powershell
.\scripts\reset-stage-8-demo-state.ps1
```

**Expect:** The command reports what it cleared.

**Verify:** Open the board. It's empty. Your settings, credentials, workflows, and the
board's access link are untouched; only the requests themselves were cleared.

---

## Saving and restoring a snapshot

Useful before or after a demo, so you can always get back to a known board state.

**Why this needs a command, not a screen:** same reason as the reset above.

**Save:**
```powershell
.\scripts\save-stage-8-demo-snapshot.ps1 -Name clean
```

**Restore:**
```powershell
.\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean
```

**Expect:** Save reports the file it wrote. Restore clears the board first, then loads
exactly what was saved.

**Verify:** Open the board after restoring and confirm it matches what you expect to see.

---

## Changing settings that don't have a screen yet

Response targets, quiet hours, who gets alerted, and the mailbox sender identity all live
in one settings record rather than a page you can click through today. Each change is a
short database command rather than a saved script, because there's no reusable form for
one-off settings edits yet.

The shape is always the same:
```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage `
  -c "update triage.config set value = jsonb_set(value, '{<setting>}', '<new-value>') where key = '<group>';"
```

**Example, updating the public link used in alert buttons after starting a new tunnel:**
```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage `
  -c "update triage.config set value = jsonb_set(value, '{public_base_url}', to_jsonb('https://your-current-tunnel.trycloudflare.com'::text), true) where key = 'board';"
```

**Verify any change** by reading the value back:
```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage `
  -c "select value from triage.config where key = '<group>';"
```

---

## Troubleshooting

| Symptom | Where to look, and whether it's UI or a command |
|---|---|
| Board shows a 404 | Check the token in the URL matches what's stored (see "Changing settings," `key = 'board'`). UI: confirm the workflow is Active. |
| A Telegram alert shows no buttons, just text | Reasonably rare rendering issue; reopen the alert workflow in n8n and confirm nothing else changed. UI check. |
| An alert's board link opens `localhost` on your phone | The public link setting is stale after starting a new tunnel; update it with the command above. Command. |
| Tapping approve twice seems to have sent twice | Check the board card; it should show exactly one send and one recorded event. If it genuinely shows two, this is a real bug worth reporting, not expected behavior. |
| A card is stuck on "needs a person's judgment" with no clear reason | Open its detail page and read the reasoning shown there. Usually a temporary AI connection problem or a message with too little in it. UI check. |
| Nothing is being classified at all, everything lands as "needs review" | The AI connection may be failing repeatedly, which trips a temporary pause. Check the OpenAI credential in n8n. UI check. |
| A unit shows as a near match instead of exact | The unit name in the message didn't exactly match your unit list. Check the spelling in your unit list. UI/data check. |
| A form submission shows blank fields on the card | The form's fields may have been edited since the automation was set up; check the field labels match. UI check. |
| The daily summary or quiet-inbox check never sends anything | Confirm it's actually switched on; see "Changing settings" above. Command to check and change. |
| The unanswered-emergency check doesn't seem to do anything | It only acts on emergencies older than 15 minutes that haven't been tapped; nothing to do is the correct result most of the time. |
| A newly switched-on workflow's link doesn't work yet | Restart n8n from Docker Desktop so the new address is picked up. Command/Docker Desktop action. |
