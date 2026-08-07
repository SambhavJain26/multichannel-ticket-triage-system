# How The System Works

A plain-language explanation of what this project does, end to end, written for
understanding the behavior, not for editing the code. Its one job: at every point, you
should know which workflow, and where it matters, which node or function, is responsible.

This is custom automation built inside a property management company's existing inbox
and phone. It is not a product. There is no login, no seat, no subscription. Any
dashboard, form, or board here exists so a human can see what the automation did.

Most of this document is internal. Two sections are written to be read by, or read aloud
to, someone who runs a property management company rather than someone who edits
workflows: "The Problem This Solves" at the top, and "Running This Inside Your Business"
at the end. Those two assume no technical background. Everything between them assumes you
want the mechanism.

## The Problem This Solves

Written for someone who runs a property management company. No technical background
assumed.

### What happens today

A tenant notices something wrong and tells you however feels natural to them. A rambling
email at 11pm. A text to the manager's personal mobile. A voicemail. A portal submission
typed in a panic. A message to the company's Facebook page. There is no standard format,
there is no urgency field, and the tenant frequently does not know how serious their own
problem is.

Those messages land undifferentiated in one inbox. A person reads every single one,
decides in their head how urgent it is, works out which trade is needed, judges whether
it can wait until Monday, and writes a reply. Dozens of times a day, while doing four
other jobs. Outside business hours, not at all.

That reading-and-sorting step is the entire subject of this project. In the standard
fourteen-stage work order lifecycle, it is stage three, sitting between intake and trade
identification. Everything downstream depends on getting it right, and it happens
entirely inside someone's head.

### Why it stays broken

Triage is invisible work. It appears on no report. Nobody has ever been thanked for
correctly identifying that a request was routine. It is pure cognitive load spread across
a day, and it is the first thing to degrade when the operations manager is busy, which is
precisely when the volume is highest.

The volume is real. Maintenance accounts for 40 to 50 percent of all inbound tenant
communication. One operational benchmark puts it at 15 to 25 requests per 100 doors per
week, so a 300-door portfolio handles 45 to 75 a week, every week. Analysis of more than
193,000 rental maintenance requests found tenants submit about 3.3 requests per unit per
year, with a median resolution time of 13.1 days.

The coverage gap is also real. Business hours are roughly 40 out of 168 hours in a week.
Seventy-six percent of the week is uncovered by default, and emergencies do not respect
business hours. Pipes freeze at night. Heating fails in the evening. Tenants notice water
when they get home.

### Getting it wrong is expensive in both directions

This is what makes triage hard rather than merely tedious.

**Under-response.** A genuine emergency sits unread because it looked like routine noise.
A failed supply line under a kitchen sink becomes a $12,000 water damage claim across two
units instead of a $150 plumber visit. Habitability failures carry legal exposure on top
of the repair cost, because most jurisdictions require a landlord to address habitability
issues within a reasonable window, and the definition of reasonable scales with severity.
No heat in the middle of winter may require a response within 24 hours. A cracked
windowpane does not.

**Over-response.** A tenant calls the after-hours line about a running toilet. The
answering service cannot assess it, so protocol says dispatch, and an emergency plumber
attends at weekend call-out rates. Three hundred and forty dollars for a flapper valve
that would have cost sixty on Monday. That happens roughly twice a month across a
portfolio and never appears as a line item anywhere.

A manager without a triage system fails in both directions at once, because the same
overloaded person makes both kinds of error on the same day.

### Why it costs more than the repair bill

Slow maintenance response is identified as the number one factor in tenant non-renewal
decisions, with delays beyond 48 hours on non-emergency requests being significant.
Separately, 31 percent of tenants uncertain about renewing said they would stay if their
property manager were more responsive to maintenance requests. A turnover runs roughly
$4,000 per unit once vacancy, make-ready, marketing, and re-leasing are combined, and the
management fee goes to zero while the unit sits empty.

On the owner side, 38 percent of rental owners name maintenance their top source of
stress, ahead of filling vacancies, managing residents, or collecting rent. Owners
evaluate their manager on five factors, and two of them, maintenance execution and
communication speed, are directly about this.

So the chain runs: slow triage, slow response, non-renewal, four thousand dollars, plus
an owner who quietly loses confidence. Maintenance is a revenue problem wearing a cost
problem's clothes.

### What this project actually changes

It removes the manual reading-and-sorting step, so the human decision happens on
pre-organized information instead of a raw inbox.

It does not decide whether the repair gets done well, how fast a vendor arrives, whether
the owner approves the spend, or whether a call turned out to be an emergency after the
fact. Those stay human. Every request still reaches a person exactly as it does today.
The only difference is that it arrives pre-sorted, pre-drafted, with the dangerous ones at
the top and a response clock already running.

The industry's own urgency taxonomy, published by the major property management software
vendors, is the one this project uses: Emergency means an immediate safety or habitability
threat, targeted within about an hour. Urgent means not immediately dangerous but it
worsens if left, targeted within 24 hours. Routine is everything else. Those targets are
configurable per client and are treated as operational targets throughout, never as legal
deadlines.

## The One-Paragraph Version

A maintenance message arrives by email, web form, or batch import. The intake workflow
normalizes it, checks the last 24 hours for a duplicate or an open thread, and calls
OpenAI to classify it. A separate, deterministic rules layer checks the same text against
a fixed list of safety keywords and can only raise the priority the model chose, never
lower it. The ticket is stored either way, even when the model call fails. If a tenant
reply is allowed, a second call drafts it along with a vendor note. A follow-up workflow
matches the unit against a roster, then decides whether to alert the manager on Telegram,
based on priority, quiet hours, and how many alerts have already gone out that hour. An
emergency alert carries an approve button, and nothing reaches a tenant until a person
taps it. The board renders the current state on request and stores nothing of its own.

The distinction that governs the whole design: it reports what a message says and what a
fixed rule concluded from it. It never decides on its own that something can wait.

## The Workflows

Thirteen workflows are active. Nothing runs outside them, and every behavior described
anywhere in this document belongs to exactly one of these rows.

| Workflow, as named in n8n | id | Triggered by | What it owns |
|---|---|---|---|
| Maintenance Triage Core | `maintenance-triage-core-stage-4` | Execute Sub-workflow (called by every ingestion path) | Normalize, dedupe/thread, classify, apply safety rules, insert the ticket, draft |
| Maintenance Triage Email Ingest | `mt-email-ingest-stage-7` | IMAP trigger on the demo mailbox | Parse an inbound email, save any attachments, hand it to Core |
| Maintenance Triage Form Ingest | `mt-form-ingest-stage-7` | Form Trigger `TenantReportForm`, path `report-issue` | Parse a web-form submission, hand it to Core, show the reference number |
| Maintenance Triage Import Bridge | `mt-import-bridge-stage-7` | Webhook `POST /webhook/stage-7-import`, token-checked | Accept a batch-imported message from the prospect-sample importer, hand it to Core |
| Maintenance Triage Fixture Fire | `mt-fixture-fire-stage-7` | Manual trigger | Inject the six live-demo fixtures, staggered two seconds apart, hand each to Core |
| Maintenance Triage Post Ingest | `mt-post-ingest-stage-7` | Execute Sub-workflow (called after Core by every ingestion path) | Match the unit against the roster, decide whether to call Alert Dispatch |
| Maintenance Triage Alert Dispatch | `mt-alert-dispatch-stage-6` | Execute Sub-workflow (called by Post Ingest and by Emergency Escalation) | Decide whether an alert should fire, send it, record the outcome |
| Maintenance Triage Telegram Callback | `mt-telegram-callback-stage-6` | Telegram Trigger, `callback_query` updates | Receive a button tap, hand it to Approval Action, answer and edit the original message |
| Maintenance Triage Approval Action | `mt-approval-action-stage-6` | Execute Sub-workflow (called by Telegram Callback) | Claim the approve/hold/not-emergency action exactly once, send the approved reply |
| Maintenance Triage Emergency Escalation | `mt-emergency-escalation-stage-6` | Schedule, every 15 minutes | Find unacknowledged emergencies past the escalation window, re-run them through Alert Dispatch |
| Maintenance Triage Board | `maintenance-triage-board-stage-5` | Webhook `GET /webhook/board`, token-checked | Render the list view and, with `?ref=`, the detail view, from the current database state |
| Maintenance Triage Daily Digest | `mt-digest-stage-8` | Manual trigger, plus schedule (cron `0 7 * * *`) | Email a summary of open emergencies, breached response targets, and overdue items |
| Maintenance Triage Operator Heartbeat | `mt-heartbeat-stage-8` | Manual trigger, plus schedule, every 15 minutes | Alert the operator, not the client, when ingestion has gone quiet |

Read that table as three groups. Four workflows are doors into the system: Email Ingest,
Form Ingest, Import Bridge, and Fixture Fire. All four hand off to the same Core, which
means a fixture and a real 2am email travel through identical logic, and a bug found on
one is a bug found on all four. Three workflows are the output path: Alert Dispatch
decides whether a phone rings, Telegram Callback receives the human's answer, and Approval
Action is the only place a message leaves for a tenant. The rest are supporting: Post
Ingest connects intake to alerting, Board renders, and Digest, Heartbeat, and Emergency
Escalation run on schedules.

Two more workflow files exist and do not run: `maintenance-triage-stage-4-driver.json`
and `maintenance-triage-stage-6-driver.json`. Both were manual test harnesses used to
validate Core and the Stage 6 alert/approval chain during the build, and both were
unpublished once their stage passed. If you see them in `workflows/`, that is why. They
are worth keeping because they can be republished to exercise Core or the alert chain in
isolation without an inbound message.

## The Parts Underneath

Distinct from the workflows above. These are the components the workflows use.

**n8n** runs all thirteen workflows and keeps the execution history, which is the audit
trail: every run, what it did, and when. Every workflow file is generated by a script in
`scripts/`, not hand-edited in the browser, which is why the same logic can be regenerated
identically after a reset. Workflows are imported and published through the n8n command
line rather than clicked together, so the state of the system is reproducible from files.

**Postgres**, specifically the `triage` schema, is the durable state and, in several
places, more of the decision logic than the workflow diagrams alone would suggest. Seven
tables hold everything: `tickets`, `events`, `config`, `feedback`, `units`,
`import_batches`, and `import_items`. The `events` table is append-only and is the reason
any ticket's history can be reconstructed after the fact. See "What Lives In Postgres"
below for the decisions that live in SQL rather than in a visible node.

**The OpenAI model** is called from exactly two places, both inside Core: `HTTP OpenAI
Classification` and `HTTP OpenAI Draft`, both `HTTP Request` nodes posting directly to
`https://api.openai.com/v1/responses` with a strict JSON Schema. This project does not use
n8n's built-in OpenAI node for these calls, because the installed local n8n version,
`2.29.10`, only exposes an older OpenAI node implementation that predates Responses API
and strict-schema support. The model reads a message and returns a classification. It is
never asked whether to override its own answer; a separate Code node decides that. See
"Why Reading And Deciding Are Separate" below. Both calls are configured to continue on
failure rather than halt the workflow, which is what turns an API outage into a stored
`NEEDS_REVIEW` ticket instead of a lost message.

**Telegram** is the manager alert channel and the only place an approval action starts. It
is deliberately not a tenant-facing channel; in the US a general renter does not have
Telegram installed, and would not expect their property manager to message them there. The
manager is one known person who installs the app once, which is exactly what makes it work
on that side.

**The demo Gmail mailbox** is both doors: `maintenance-triage-demo-imap-domain` reads
inbound mail, `maintenance-triage-demo-smtp-domain` sends the approved tenant reply and
the daily digest. The mailbox should stay dedicated to this project, because publishing
the IMAP trigger against an inbox with unrelated unread mail ingests those messages
immediately.

**Disk storage** holds attachment files under `/data/attachments`, written before anything
else touches the message, and batch-import artifacts under `/data/import-batches/<batch-id>/`.
The ordering matters: the file survives even if every later step fails.

**The board** is a page rendered on request. It has no login and stores nothing of its
own; every load reads the current database state fresh, auto-refreshes every five seconds
on the list view, and is protected by a single shared token in the query string.

## The Journey Of One Request

Tracing an inbound email end to end, by real node name, in execution order. Every other
intake path joins this same sequence at the Core step.

### Intake

**Workflow: Maintenance Triage Email Ingest.** `Demo Mailbox IMAP Trigger` fires on an
unread message. `Prepare Email Core Payload` extracts sender, subject, body, and threading
headers, and lists any attachments. It handles both plain-text and HTML bodies, and falls
back to generating a message id if the sender's mail client did not supply one, because
the threading logic later depends on that field existing.

`Has Email Attachment` routes attachments to `Write Email Attachment`, which saves each
file to `/data/attachments/` before anything reads it. `Build Email Core Payload`
reassembles the message with its saved attachment paths, because the file-write node drops
everything else on the item. `Execute Core Workflow` calls Core and waits for it.

### Core, part one: is this even a new request

**Workflow: Maintenance Triage Core**, called as a sub-workflow. `Normalize Request`
strips quoted replies, signatures, and common footers, collapses whitespace, and truncates
to 1,500 characters. That truncation is deliberate: it bounds the cost and latency of the
model call, and 1,500 characters is more than enough for any maintenance report that has
had its quoted history removed.

`Postgres Dedupe Thread Gate` is one query doing two jobs. It checks whether this exact
body hash was seen in the last 24 hours, which catches a tenant sending the same message
twice or a mail loop. Separately it checks whether the message's `In-Reply-To` or
`References` headers match an existing ticket's outbound or inbound message id, which
catches a tenant replying to the acknowledgment we already sent them.

`Prepare Gate Decision` and `Should Create Ticket` branch on the result. A duplicate gets a
`duplicate_ignored` event written against the original ticket and stops. A reply to an
existing thread reopens that ticket with a `tenant_replied` event and stops. Anything new
continues. This is the reason a tenant answering "thanks, when is someone coming?" does not
create a second card on the board or fire a second emergency alert.

### Core, part two: classify, then decide

For a genuinely new message, `Prepare Classification Request` builds the OpenAI request
body, unless a test-mode flag calls for a mocked or simulated-error response instead. The
same node also short-circuits the call entirely if the system is in degraded mode or has
hit the daily model-call cap, so an outage or a runaway loop cannot run up cost.

`HTTP OpenAI Classification` sends it. `Attach Classifier Response` reattaches the result
to the original item, because the HTTP node returns only its own response.

`Apply Safety Rules` is the single most important node in the project. It runs the ten
keyword-signal checks, applies the negation guard, merges the result with the model's own
`safety_signals`, and computes the final priority. See "What The Safety Rules Layer
Checks" below for exactly what it looks for.

`Postgres Insert Ticket Events` writes the ticket and its `ingested`, `classified`, and, if
a rule fired, `overridden` events in one statement. The same statement updates the
model-failure counters used for degraded mode: a success resets the consecutive-failure
count and increments today's call count, a failure increments the failure count and, on
the third consecutive failure, sets a ten-minute `degraded_until` window.

There is no branch on which a message fails to produce a row. If the model call timed out,
returned malformed JSON, or never happened, the ticket still exists with the raw body and a
`NEEDS_REVIEW` priority. This is the property the whole product is selling, and it is
enforced by structure rather than by a retry.

### Core, part three: draft

If the ticket allows a draft, `Prepare Draft Request` and `HTTP OpenAI Draft` write a
tenant reply, a vendor note, and any clarifying questions, and `Postgres Update Draft`
stores them. The tenant reply is under 80 words and written as the office; the vendor note
is under 60 words and written for a trade contractor. Neither may promise a date, a time,
an appointment, or a cost.

A draft is only attempted when the priority is not `NEEDS_REVIEW`, the ticket is not
human-only, the model said this is a maintenance request, and the request type is not
`NOT_A_REQUEST`. Everything else reaches the board with no draft at all, which is a
deliberate refusal rather than a failure.

`Route By Priority` sends the result out one of four dead-end branches (`Emergency
Result`, `Needs Review Result`, `Urgent Result`, `Routine Result`) purely so the
sub-workflow returns something. Because Execute Sub-workflow branches like this do not
merge back into one item stream, every caller downstream reselects the ticket by `msg_id`
rather than trusting this node's output shape. That is a real n8n behavior, not a design
preference, and it is why the ingestion workflows treat Core as a database-writing side
effect.

### Roster match, then the alert decision

**Workflow: Maintenance Triage Post Ingest**, called next. `Postgres Match Unit Roster`
reselects the ticket by `msg_id` (or ticket id) and, in one query, matches its unit string
against `triage.units`. An exact label match wins, disambiguated by a property-name hint in
the message text if the same label exists at more than one property. Failing that, the
nearest label by digit and length similarity is recorded as a near-miss, which is how "unit
12B" against a roster containing "12A" produces a visible near-miss rather than a silent
wrong answer. A message with no unit at all is recorded as not-stated, not as a failure.

`Should Dispatch Alert` only proceeds if this was a genuinely new ticket, not a duplicate
or a reopened thread, so a reply to an existing conversation never re-alerts.

**Workflow: Maintenance Triage Alert Dispatch**, called next. `Postgres Load Alert Context`
loads the ticket plus the current `board`, `contacts`, `company`, `quiet_hours`, and
`limits` config, and a count of alerts sent in the last hour, all in one query.

`Prepare Alert Action` is a Code node that decides four things: whether this priority
alerts at all, whether it alerts silently, whether quiet hours or the hourly rate cap hold
it back, and whether the ticket is already handled and should not be touched again. See
"Notification Policy" below for the resulting table.

If a real send is due, one of three Telegram nodes fires (`Telegram Send Emergency Alert`,
`Telegram Send Urgent Alert`, or `Telegram Send Review Alert`), each with its own explicit
inline-keyboard rows rather than one shared expression. A shared expression silently
produces a plain-text message with no buttons in this n8n version, which is why three
nearly identical nodes exist instead of one. The emergency alert carries approve, hold, and
not-emergency buttons plus a board link; the urgent alert carries approve and a board link;
the review alert carries only a board link, because a `NEEDS_REVIEW` ticket has no draft to
approve.

Either path ends at a Postgres write that sets status to `ALERTED`, unless the ticket is
already `ACKED`, `ACK_SENT`, or `HELD`, in which case the write is a no-op on status. That
guard is what stops a re-run from regressing a ticket someone already handled.

A human then taps a button on their phone.

### The human tap, and the only outbound path

**Workflow: Maintenance Triage Telegram Callback.** `TelegramCallbackTrigger` fires on the
tap. `Normalize Telegram Callback` extracts the `act:<ticket_id>:<action>` payload and the
actor. `Execute Approval Action` calls Approval Action and waits.

**Workflow: Maintenance Triage Approval Action**, called as a sub-workflow.
`Postgres Approval Gate` is one query whose `UPDATE ... WHERE` clause is the entire
double-approve guard: an `approve` action only claims the ticket if its status is not
already `ACKED` or `ACK_SENT`, `human_only` is false, its priority is not `NEEDS_REVIEW`,
and a draft exists. A second tap, or a tap on a ticket that never qualified for a draft,
matches zero rows and falls through to `already_handled` or `refused`. Hold and
not-emergency work the same way, and not-emergency additionally writes a row to
`triage.feedback` recording the correction.

If the claim succeeded, `Prepare Email Payload` builds the outbound email, routed to the
configured test inbox while `outbound_email.mode` is `test_only`. `Should Send Approved
Email` gates it and `SMTP Send Approved Reply` sends it. `Postgres Finalize Approved Email`
sets status to `ACK_SENT` and stores the outbound message id only on success; a failed send
is recorded as `last_alert_error` without pretending the reply went out.

Back in Telegram Callback, `Telegram Answer Callback` acknowledges the tap first, because
Telegram's `answerQuery` does not preserve upstream context for later nodes. The approval
result is reattached afterward, and `Telegram Edit Alert Message` rewrites the original
alert in place with the outcome, so the manager's phone shows what happened rather than a
stale set of buttons.

## Why Reading And Deciding Are Separate

The most important design decision in the project, and it is visible in the node list.

`HTTP OpenAI Classification` only ever returns a JSON object matching the
`maintenance_triage` schema. It is never asked whether a message deserves an override, only
what the message says. `Apply Safety Rules`, a plain Code node with no model call in it, is
the only place a priority can change, and it can only raise a priority, never lower one:
`maxPriority` always keeps the higher of the model's answer and
`EMERGENCY`-if-a-keyword-rule-fired.

This confines the part of the system that could produce a wrong answer to reading language,
and reading is checkable. The raw model JSON, the rules that fired, and the reason are all
one click away in the board's detail view, behind the "Technical audit" disclosure.

There is a second reason worth stating out loud, because it is the answer to the obvious
objection about prompt injection. A forwarded newsletter, a marketing email, or a tenant
who has read too much about chatbots can all put instruction-shaped text into the message
body. Even if that text talked the model out of calling something an emergency, the keyword
layer runs afterward and can only escalate. It cannot be argued with, because it is not
reasoning about anything. It is checking whether a word is present.

## What The Safety Rules Layer Checks

All in `Apply Safety Rules`, `workflows/maintenance-triage-core.json`.

Ten word-boundary regex signals run against the cleaned message text, each guarded by a
negation lookback so "no smell of gas" or "isn't sparking" does not fire the rule: `GAS`,
`CARBON_MONOXIDE`, `SMOKE_FIRE`, `FLOOD`, `SEWAGE`, `NO_HEAT`, `NO_WATER`, `NO_COOLING`,
`SECURITY`, `ELECTRICAL`. Any hit forces the priority to at least `EMERGENCY` and writes an
`overridden` event naming the signal.

Word boundaries matter more than they look. A naive substring match on "gas" fires on "gas
bill", "gas station", and "gas stove igniter". A naive match on "no heat" fires on "there's
no heat problem in the bedroom". The negation guard looks backward a short distance from
each match and suppresses the rule if the phrase was negated. Over-firing is acceptable and
costs a phone call. Under-firing is not acceptable, so every fire is logged as an event
rather than silently applied.

Three further deterministic boundaries sit on top of that, added after repeated live
rehearsal exposed small model variance on specific demo cases:

- `routineSqueakyDoor` keeps a squeaky- or noisy-door complaint `ROUTINE` even if the
  tenant marks it urgent, unless the message also mentions a lock, closure, access problem,
  or injury. A door that will not lock is a security issue; a door that squeaks is not.
- `containedCeilingDrip` pulls a bucket-contained ceiling drip back from `EMERGENCY` to
  `URGENT`, unless the message also mentions spreading water, collapse, or an electrical
  hazard near the water. A drip with a bucket under it is genuinely urgent and genuinely not
  an emergency, and the model was inconsistent about that boundary across runs.
- `lowInformation` forces `NEEDS_REVIEW` when the model reports a new issue with no concrete
  detail and the message itself looks unreadable, is an "attachment only" note, or names an
  unknown trade with almost no substance. This is the deterministic answer to garbage input,
  not a model guess.

`NEEDS_REVIEW` is a system-only state. It is not in the model's output schema; the model
cannot choose it. Only the rules layer can defer. It is forced by, in order of what triggers
it: the OpenAI call failing or returning invalid JSON, the model reporting `LOW` confidence
alongside an active safety signal, the model reporting the message is not a maintenance
request while a safety rule still fired on the text, or the `lowInformation` check above.

That last combination deserves a note. A message the model calls "not a maintenance request"
which nonetheless contains the word "gas" is exactly the shape of a mistake worth waking
someone for, so it is escalated to a human rather than resolved either way automatically.

## Notification Policy

Computed entirely in `Prepare Alert Action`, `workflows/maintenance-triage-alert-dispatch.json`.

| Priority | Business hours | Quiet hours |
|---|---|---|
| EMERGENCY | Alerts, audible | Alerts, audible. No exception. |
| URGENT | Alerts, silent | Held |
| NEEDS_REVIEW, with a safety signal | Alerts, silent | Alerts, silent |
| NEEDS_REVIEW, no safety signal | Alerts, silent | Held |
| ROUTINE, or human-only | Board only | Board only |

The distinction that makes this table valuable: evaluation is immediate and per message,
notification is deferred by policy. Every message is triaged within seconds, all night, so
the board is always current. What gets deferred is only whether anything makes a sound.
Five messages arriving between midnight and 3am, three routine, one urgent, one possible gas
smell, produce exactly one buzz.

Two more rules sit on top of that table. An hourly cap (`limits.max_alerts_per_hour`,
default 6) groups anything past the limit instead of sending it. And a ticket already
`ACKED`, `ACK_SENT`, or `HELD` is never touched again by this workflow, so a re-run cannot
regress a handled ticket's status back to `ALERTED`.

Age is not an input to this table at all. An aged routine or urgent ticket becomes an
`OVERDUE` board and digest flag through a separate query in the board and digest workflows,
and never reaches this alert path. This is deliberate and is a correction to a common design
instinct: a fourteen-day-old squeaky door is not a safety emergency, and putting it on the
same channel as a gas smell destroys the only thing that makes the alert channel valuable,
which is that it never cries wolf.

## What Lives In Postgres Rather Than n8n

There are no stored functions, procedures, or triggers anywhere in this project's database.
Every table in `db/postgres/` is created with plain `CREATE TABLE` statements, and the
config seed files write JSON values, nothing else.

That is a real structural choice, not an oversight. The decision logic here lives directly
inside the queries of specific Postgres nodes, as common table expressions. Reading the n8n
canvas alone hides it, because the canvas shows a box labeled "Postgres" and not the
forty-line query inside it. These are the nodes that carry real decisions rather than plain
storage:

- `Postgres Dedupe Thread Gate` (Core): the dedupe and thread-match decision, in one query.
- `Postgres Match Unit Roster` (Post Ingest): exact, ambiguous, near-miss, or not-found roster matching.
- `Postgres Approval Gate` (Approval Action): the double-approve guard and the human-only/NEEDS_REVIEW refusal, both enforced in the `UPDATE ... WHERE` clause itself.
- `Postgres Load Board Data` (Board): the entire list and detail view, including priority ranking and the overdue computation.
- `Postgres Load Digest Context` (Daily Digest) and `Postgres Load Heartbeat State`
  (Operator Heartbeat): their respective aggregate queries. The heartbeat's should-alert
  decision is a boolean computed in SQL, not in a Code node.
- `Postgres Record Real Alert` and `Postgres Record Mock Or Skipped Alert` (Alert Dispatch):
  the same no-status-regression guard described above.

Three indexes encode business rules directly in their `WHERE` clause, which is worth knowing
if a query stops matching expectations after a schema change:
`tickets_stage_6_emergency_escalation_idx` (`priority='EMERGENCY' AND acked_at IS NULL AND
closed_at IS NULL`), `tickets_stage_6_approval_guard_idx` (`status IN ('NEW', 'ALERTED',
'ACKED', 'HELD')`), and `events_stage_6_alert_rate_idx` (`action IN
('telegram_alert_sent', 'telegram_alert_mocked', 'telegram_alert_grouped')`).

`triage.config` holds every tunable value as a JSON row, not a code constant. This is what
makes the same build reusable for a second client without editing a workflow:

| Key | Holds |
|---|---|
| `sla_minutes` | Response target per priority, in minutes. Default `{EMERGENCY:60, URGENT:1440, ROUTINE:4320, NEEDS_REVIEW:120}` |
| `overdue_days` | Days before a routine or urgent ticket becomes `OVERDUE`. Default `{ROUTINE:10, URGENT:3}` |
| `escalate_after` | Minutes before an unacknowledged emergency re-alerts. Default `{EMERGENCY_minutes:15}` |
| `contacts` | Telegram chat ids for primary, secondary, and operator contacts |
| `company` | Display name, office hours, sender name, timezone |
| `quiet_hours` | Start, end, timezone, and the emergency-only flag |
| `limits` | Daily model-call cap and hourly alert cap |
| `runtime_state` | Consecutive model-failure count, `degraded_until`, and today's model-call count |
| `board` | The board's access token and its list bounds (`recent_hours`, `max_cards`); `public_base_url` is set by hand, not seeded |
| `outbound_email` | Send mode (`test_only` or `live`), sender identity, test inbox |
| `ingestion` | The batch-import token and the attachment/batch storage roots |
| `digest` | Enabled flag (default false), send hour, recipient |
| `heartbeat` | Enabled flag (default false), quiet threshold, repeat-suppression window |

## The Approval Gate And The Double-Approve Guard

Worth stating plainly because it is the one guarantee the whole advisory-only story depends
on: nothing reaches a tenant unless a human taps approve, and a second tap cannot send a
second email.

Both are enforced by the same mechanism, the `WHERE` clause on `Postgres Approval Gate`'s
`UPDATE` statement in Approval Action. The row only updates, and the email only gets
prepared, if the current status is not already `ACKED` or `ACK_SENT`. There is no code path
that checks this after the fact; the guarantee is that the second tap's `UPDATE` matches
zero rows and the workflow therefore has nothing to send.

The other half of the same story is what the gate refuses outright. Approve on a human-only
ticket matches zero rows, because `human_only = false` is in the same `WHERE` clause.
Approve on a `NEEDS_REVIEW` ticket matches zero rows for the same reason. Neither of those is
a policy checked in a Code node somewhere; both are conditions on the row update.

If a future change ever moves a send node upstream of that gate, the guarantee silently
stops being true. That is why this section exists.

## What It Deliberately Refuses To Do

These are not gaps. They are the design.

It never dispatches a vendor. It never contacts a vendor at all, on any channel. It writes
the vendor note a manager would have written, and a human sends it.

It never suppresses, filters, or auto-closes a ticket. Every message that arrives gets a row
and a card, including spam, vendor mail, and auto-replies, which are classified
`NOT_A_REQUEST` and sorted to the bottom rather than deleted.

It never sends a tenant reply without a human tap, in every version, with no setting to
loosen it.

Age alone never triggers a phone alert. An old routine or urgent ticket only ever becomes an
`OVERDUE` board and digest flag.

A human-only ticket, meaning the model flagged an accommodation or legal-sensitive request,
never gets a draft generated at all.

A handled ticket can never be re-alerted back to `ALERTED` by a later run.

## What It Genuinely Cannot Do

These are limits of the build itself, not policy choices.

It does not write anything back to a property management system; there is no PMS integration
anywhere in this project. The manager still creates the work order. What is saved is the
reading, the triage decision, and the drafting, not the data entry.

It cannot look up a real unit, tenant, or lease. It only has what the message text says, and
a unit label is matched against a synthetic demo roster (`triage.units`), not a real one. If
a tenant writes "2B", the output is "2B". If they write nothing, the output is "unit not
stated" rather than a guess.

It does not interpret an attached photo; the board shows an attachment count as a chip,
nothing more. It does not transcribe a phone call or voicemail, though voicemail-transcript-
shaped text runs through the same text path as anything else.

Only English and Spanish have been tested. Any other language is untested rather than
unsupported.

It cannot guarantee compliance with any state's habitability response windows. Response
targets are configurable operational numbers and are never a legal deadline, and nothing it
writes states or implies a legal obligation.

It does not learn from corrections on its own. A not-emergency tap writes a row to
`triage.feedback`, and that row is a record for a human to act on, not training data.
Nothing changes behavior until someone changes the rules and says so.

The only outbound tenant channel is email. There is no SMS or text path in this build.

Its only measured accuracy is the six-fixture live-demo gate (see `docs/stage-3-scorecard.md`):
6 of 6 priority matches, zero under-escalations, zero over-escalations, zero missed safety
signals, on that fixture set. The full 30-fixture hardening run has not passed;
`progress-notes.md` records it as failed and deferred. Do not extrapolate the six-fixture
result into a broader accuracy claim.

It runs on one local Docker host with one operator behind it, not monitored production
infrastructure, and outbound mail currently sends from a demo sender identity with no
production deliverability setup (SPF, DKIM, DMARC) in place.

## Language Rules

This document, and anything built from it, should hold to the same rules the demo script
uses.

**Never say:** "the system does X" without naming the workflow. My platform, my tool, my
product, the app. Users, sign up, subscribers. That it will never miss an emergency, that it
verifies or confirms anything about a tenant's situation, that it is legal advice.

**Say instead:** the name of the responsible workflow. The manager, the office, whoever reads
the board. That everything still reaches a human, just pre-sorted. That a response target is
operational, not a deadline.

## Where Everything Lives

- **Tickets, events, config, feedback, units, import batches and items.** The `triage` schema
  in Postgres, defined across `db/postgres/001-create-triage-schema.sql` through
  `007-stage-8-hardening.sql`.
- **Attachments.** `/data/attachments/`, written before anything else reads the message.
- **Batch import reports.** `/data/import-batches/<batch-id>/report.html` and `review.csv`.
- **Clean-state snapshots.** `data/demo-snapshots/<name>.sql`, gitignored.
- **Local credential names.** Postgres `maintenance-triage-postgres-local`, OpenAI
  `maintenance-triage-openai`, Telegram `maintenance-triage-telegram-bot`, mailbox intake
  `maintenance-triage-demo-imap-domain`, mailbox outbound
  `maintenance-triage-demo-smtp-domain`.
- **API keys and mailbox passwords.** Inside n8n's encrypted credential store only, never in
  the project files, and never in a workflow export.
- **Local URLs.** n8n `http://localhost:5678`; board
  `http://localhost:5678/webhook/board?t=<board-token>`; the intake form
  `http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue`.

## Resetting And Staging

`.\scripts\reset-stage-8-demo-state.ps1` truncates `triage.tickets`, `events`, `feedback`,
`import_batches`, and `import_items`, restarts the ticket reference sequence, resets the
runtime and heartbeat counters, and clears `data/attachments` and `data/import-batches`
unless `-KeepGeneratedFiles` is passed. It leaves config, units, credentials, workflows, and
the board token untouched, so a reset returns the board to empty without undoing setup.

`.\scripts\save-stage-8-demo-snapshot.ps1 -Name <name>` and
`.\scripts\restore-stage-8-demo-snapshot.ps1 -Name <name>` save and restore a data-only dump
of the same tables. `-Name clean` is the standard pre-call baseline. Restore runs the reset
first, so it is safe to run against a board full of test tickets.

`.\scripts\run-stage-8-rehearsal.ps1 -Runs 5` resets, fires the live-demo fixtures through
the command line, and asserts ticket count, priority match, roster display, zero real
Telegram sends, and board HTTP 200, across every run. It then asserts the result was
identical across all runs, which is the check that catches model variance rather than
outright failure.

**Two cautions on `validate-stage-6.ps1`.** It asserts a `maintenance-triage-greenmail-smtp-local`
credential that was deliberately deleted during Stage 7, so it fails on that check
regardless of anything else. And it re-applies the Stage 6 SQL, which resets
`triage.config.outbound_email` back to `test_only` with the placeholder sender. After
running it, run `.\scripts\apply-stage-7.ps1` and re-set `from_email` to the real demo
mailbox, or live outbound mail will silently stop working.

## Troubleshooting

Every symptom names the workflow to open first.

| Symptom | Open first |
|---|---|
| Board returns 404 | Maintenance Triage Board, `Postgres Load Board Data`. Check the `t=` token in the URL against `triage.config.board.token`, and, for a detail page, that `?ref=` matches a real ticket. |
| Telegram alert is plain text with no buttons | Maintenance Triage Alert Dispatch. The inline keyboard must be explicit fixed-collection rows on the Telegram node; a whole keyboard passed as one expression silently drops the buttons in this n8n version. |
| Alert's board button opens `localhost` on a real phone | `triage.config.board.public_base_url` is not set to the current tunnel URL. |
| A second approval tap appears to send a second email | Maintenance Triage Approval Action, `Postgres Approval Gate`. Confirm the first tap moved status to `ACK_SENT`; the guard is in the `UPDATE ... WHERE` clause, not a separate check. |
| A handled ticket shows `ALERTED` again after a re-run | Maintenance Triage Alert Dispatch, `Postgres Record Real Alert` or `Postgres Record Mock Or Skipped Alert`. The status `CASE` should never overwrite `ACKED`, `ACK_SENT`, or `HELD`. |
| A ticket lands on `NEEDS_REVIEW` unexpectedly | Open the ticket's Technical audit panel on the board and read `model_error` and the review reason recorded in Core's `Apply Safety Rules`. Usually a bad OpenAI key, a timeout, or the `lowInformation` guard. |
| Everything is landing on `NEEDS_REVIEW` at once | Check `triage.config.runtime_state.degraded_until`. Three consecutive OpenAI failures trip a ten-minute degraded window in Core. The keyword rules still classify during that window. |
| Roster shows a near-miss instead of an exact match | Maintenance Triage Post Ingest, `Postgres Match Unit Roster`. Check `triage.units.unit_label` formatting, and whether the message names the property when the same unit label exists at more than one property. |
| Form submission shows blank or `field-0` values | Maintenance Triage Form Ingest, `Prepare Form Core Payload`. It reads real field labels first and falls back to `field-N`; check the form's configured labels have not drifted from `TenantReportForm`'s definition. |
| Approved replies stopped sending | Check `triage.config.outbound_email`. Running `validate-stage-6.ps1` resets it to `test_only` with a placeholder sender. |
| Digest or heartbeat never sends | Check `triage.config.digest.enabled` and `heartbeat.enabled`. Both default to false. |
| Emergency escalation does not page a second time | By design in this build. Maintenance Triage Emergency Escalation forces `mock_telegram: true` into every re-alert it triggers, so it never sends a second real message here. |
| A newly imported webhook or form 404s | Restart n8n. Local n8n `2.29.10` needs a restart to register a newly imported or published webhook's production path. |

## Running This Inside Your Business

Written for someone evaluating whether this could work in their own company. No technical
background assumed.

### The short version

Everything you have seen demonstrated runs on a laptop, using stand-ins where a real
business would use its own accounts. Putting it into your business means replacing each
stand-in with the thing you already use. The logic that sorts the messages does not change
at all.

Nothing here asks you to move into a new platform, retrain your tenants, or upgrade your
property management software.

### What changes, item by item

| In the demonstration | In your business |
|---|---|
| A Telegram alert to my phone | An alert to your team's phones. Telegram works if your team will install it; a text message is the usual production choice and is a straight swap of the sending step |
| A throwaway demo mailbox | Your existing maintenance email address, forwarded |
| Replies sent from a demo Gmail address | Replies sent from your own domain, set up so they reach the inbox rather than the spam folder |
| A made-up list of demo units | Your real unit list, exported once from whatever software you already use |
| Response targets I chose | The response targets you actually promise your owners |
| Quiet hours set to a generic evening window | Your hours, your timezone, your on-call rules |
| A shared board link | A private link per person on your team |
| A laptop running in my office | A small server in a US datacenter, in your company's name |
| Test messages I wrote | Your real inbound mail |

Two of those need a little more than a settings change. Sending from your own domain needs
DNS records set up so mail providers trust it, which I handle and which happens before
anything goes live. Alerting by text rather than Telegram needs a business number
registered in your company's name, which is paperwork I handle and which takes a couple of
weeks, so it is worth starting early if you want it. Everything else on that list is a
value in a settings table.

### What you would need to provide

Five things, none of which take long:

1. **A forwarding rule on your maintenance inbox.** A copy of incoming mail goes to the
   triage address. Takes about five minutes to add and about five minutes to remove.
2. **Your unit list.** One spreadsheet export from your existing software: property name,
   unit label, and optionally the tenant name and contact. This is what turns "unit 2B" into
   "2B, Maple Court" on the board.
3. **Your escalation contacts.** Who gets the emergency alert, who is the backup, and how to
   reach both.
4. **Your response targets.** What you tell owners you do for an emergency, an urgent
   request, and a routine one. These become the countdown clock on each card.
5. **Your company details.** The name that appears on a tenant reply, your office hours, and
   whether replies should read formally or warmly.

That is the whole list. No software access, no admin credentials to your property management
system, no IT involvement.

### What does not change

**Your property management software.** Nothing is written into it, nothing is read from it,
and no plan upgrade is required. You still create the work order the way you do now. What
you stop doing is reading forty messages to work out which one to create first.

**Your tenants.** They keep reporting problems exactly where they report them today. There
is no portal to teach them, no app to install, no new address to remember.

**Your vendors.** Nothing in this contacts a vendor. It writes the note you would have
written, and you send it.

**Everything after triage.** Cost estimates, owner approval, vendor selection, scheduling,
invoicing, and closing the job all stay exactly as they are.

### What a first month looks like

**Week one, watching only.** The forwarding rule goes on and nothing sends. Every message
gets read, sorted, and put on the board, and drafts get written, but no tenant receives
anything and no phone rings. At the end of the week you compare what it flagged against what
your team actually did. This is the cheapest way to find out whether it reads your mail
correctly, and it costs you nothing but a forwarding rule.

**Week two, alerts on.** Emergency alerts start reaching your phone. Replies are still not
sending. You get a feel for how often it buzzes and whether the ones it escalates are the
ones you would have escalated.

**Week three, replies on, to your inbox.** Approved replies start sending, but only to a test
address you control, not to tenants. You approve a few and read what actually went out.

**Week four, live.** Approved replies reach tenants. By this point you have watched it read
three weeks of your real mail and you know what it does.

At every one of those stages, the tap is yours. There is no stage where it starts sending on
its own.

### How you turn it off

Remove the forwarding rule. That is the whole procedure, and you are back to exactly the
inbox you have today, in about five minutes. Nothing has been moved, nothing has been
migrated, and no data of yours is trapped anywhere.

This is worth saying at the start rather than at the end. The reason a maintenance-triage
system is a reasonable thing to try is that trying it is reversible.

### Where your data sits, and who can see it

Everything lives on one server in a US datacenter that only your administrator has access to,
over encrypted connections. The message text is sent to OpenAI's interface for classification.
OpenAI does not train on data sent through that interface and deletes it within 30 days.
Message bodies are kept for 30 days on your server and then purged, and that window is
configurable.

What is stored: tenant name, unit string, contact string, message body, the classification,
the drafts, and timestamps. What is never stored: social security numbers, lease documents,
payment or bank details, screening reports, or identity documents. If a tenant happens to put
one of those in a message, the message is stored as-is, which is worth knowing when you set
your retention rule.

If you ever want everything deleted, it can be done within a day and you can be shown that it
is gone.

### What it will not do for you

Stated here rather than buried, because these are the questions worth asking before rather
than after.

It will not create the work order in your software. It will not contact a vendor. It will not
reply to a tenant without you tapping approve. It will not catch every emergency, and it will
sometimes escalate something that turns out to be routine, which costs you a phone call. It
will not read a photo, only tell you one is attached. It will not handle voicemail or phone
calls; email and web form only. It will not text a tenant, because the only outbound tenant
channel built today is email. It will not tell you what your legal obligations are, because
habitability windows vary by state and this is not legal advice.

And it does not improve on its own overnight. When it gets something wrong, that correction is
recorded, someone changes a rule, and you are told what changed. Nothing about its behavior
shifts without a human deciding it should.

## Technical Pointers

For when you need to go a level deeper.

- **The workflows.** `workflows/`, one file per workflow, generated by `scripts/build-stage-*.py`
  rather than hand-edited. Change the generator, not the export.
- **Database structure and settings.** `db/postgres/001-create-triage-schema.sql` through
  `007-stage-8-hardening.sql`, applied in numeric order.
- **The classification prompt and output schema.** `prompts/classification-system.txt` and
  `prompts/maintenance-triage.schema.json`, embedded into
  `workflows/maintenance-triage-core.json` by the Stage 4 generator.
- **The drafting prompt and schema.** `prompts/drafting-system.txt` and
  `prompts/maintenance-drafts.schema.json`, embedded the same way.
- **The 30-fixture corpus and the six live-demo fixtures.** `fixtures/`; the live-demo set is
  also hardcoded directly in `workflows/maintenance-triage-fixture-fire.json`. Note that
  `scripts/validate-stage-2.py` hardcodes the counts 30 and 6, so adding a fixture means
  updating it.
- **The measured accuracy gate.** `docs/stage-3-scorecard.md`,
  `docs/stage-8-operator-cheat-sheet.md`.
- **Stage-by-stage build detail.** `docs/stage-1-local-runtime-runbook.md`,
  `docs/stage-7-ingestion-runbook.md`, `docs/stage-8-demo-hardening-runbook.md`,
  `docs/stage-8-pre-call-checklist.md`, `docs/stage-8-failure-rehearsal.md`.
- **Current status, decisions, and deviations.** `progress-notes.md`, read first in any session.
- **The staged plan.** `build-plan.md`.
- **The controlling demo spec.** `maintenance-triage-demo-build-plan.md`.
