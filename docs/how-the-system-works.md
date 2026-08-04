# How The System Works

A plain-language explanation of what this project does, end to end, written for
understanding the behavior, not for editing the code. Its one job: at every point, you
should know which workflow, and where it matters, which node or function, is responsible.

This is custom automation built inside a property management company's existing inbox
and phone. It is not a product. There is no login, no seat, no subscription. Any
dashboard, form, or board here exists so a human can see what the automation did.

## The One-Paragraph Version

A maintenance message arrives by email, web form, or batch import. The intake workflow
normalizes it, checks the last 24 hours for a duplicate or an open thread, and calls
OpenAI to classify it. A separate, deterministic rules layer checks the same text
against a fixed list of safety keywords and can only raise the priority the model chose,
never lower it. The ticket is stored either way, even when the model call fails. If a
tenant reply is allowed, a second call drafts it along with a vendor note. A follow-up
workflow matches the unit against a roster, then decides whether to alert the manager on
Telegram, based on priority, quiet hours, and how many alerts have already gone out that
hour. An emergency alert carries an approve button, and nothing reaches a tenant until a
person taps it. The board renders the current state on request and stores nothing of its
own.

The distinction that governs the whole design: it reports what a message says and what a
fixed rule concluded from it. It never decides on its own that something can wait.

## The Workflows

Everything the system does is one of these. Thirteen are active.

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

Two more workflow files exist and do not run: `maintenance-triage-stage-4-driver.json`
and `maintenance-triage-stage-6-driver.json`. Both were manual test harnesses used to
validate Core and the Stage 6 alert/approval chain during the build, and both were
unpublished once their stage passed. If you see them in `workflows/`, that is why.

## The Parts Underneath

Distinct from the workflows above. These are the components the workflows use.

**n8n** runs all thirteen workflows and keeps the execution history, which is the audit
trail: every run, what it did, and when.

**Postgres**, specifically the `triage` schema, is the durable state and, in several
places, more of the decision logic than the workflow diagrams alone would suggest. See
"What Lives In Postgres" below.

**The OpenAI model** is called from exactly two places, both inside Core: `HTTP OpenAI
Classification` and `HTTP OpenAI Draft`, both `HTTP Request` nodes posting directly to
`https://api.openai.com/v1/responses` with a strict JSON Schema. This project does not
use n8n's built-in OpenAI node for these calls, because the installed local n8n version,
`2.29.10`, only exposes an older OpenAI node implementation that predates Responses API
and strict-schema support. The model reads a message and returns a classification. It is
never asked whether to override its own answer; a separate Code node decides that. See
"Why Reading And Deciding Are Separate" below.

**Telegram** is the manager alert channel and the only place an approval action starts.

**The demo Gmail mailbox** is both doors: `maintenance-triage-demo-imap-domain` reads
inbound mail, `maintenance-triage-demo-smtp-domain` sends the approved tenant reply and
the daily digest.

**Disk storage** holds attachment files under `/data/attachments`, written before
anything else touches the message, and batch-import artifacts under
`/data/import-batches/<batch-id>/`.

**The board** is a page rendered on request. It has no login and stores nothing of its
own; every load reads the current database state fresh.

## The Journey Of One Request

Tracing an inbound email end to end, by real node name, in execution order.

**Workflow: Maintenance Triage Email Ingest.** `Demo Mailbox IMAP Trigger` fires on an
unread message. `Prepare Email Core Payload` extracts sender, subject, body, and
threading headers, and lists any attachments. `Has Email Attachment` routes attachments
to `Write Email Attachment`, which saves each file to `/data/attachments/` before
anything reads it. `Build Email Core Payload` reassembles the message with its saved
attachment paths, because the file-write node drops everything else. `Execute Core
Workflow` calls Core and waits for it.

**Workflow: Maintenance Triage Core**, called as a sub-workflow. `Normalize Request`
strips quoted replies, signatures, and common footers, collapses whitespace, and
truncates to 1,500 characters. `Postgres Dedupe Thread Gate` is one query that checks
whether this body hash was seen in the last 24 hours, and separately whether the
message's `In-Reply-To` or `References` headers match an existing ticket's outbound or
inbound message id. `Prepare Gate Decision` and `Should Create Ticket` branch on the
result: a duplicate gets a `duplicate_ignored` event and stops; a reply to an existing
thread reopens that ticket with a `tenant_replied` event and stops; anything new
continues.

For a genuinely new message, `Prepare Classification Request` builds the OpenAI request
body (unless a test-mode flag calls for a mocked or simulated-error response instead).
`HTTP OpenAI Classification` sends it. `Attach Classifier Response` reattaches the
result to the original item. `Apply Safety Rules` is the single most important node in
the project: it runs the ten keyword-signal checks, applies the negation guard, merges
the result with the model's own `safety_signals`, and computes the final priority. See
"What The Safety Rules Layer Checks" below. `Postgres Insert Ticket Events` writes the
ticket and its `ingested`, `classified`, and, if a rule fired, `overridden` events in one
statement, and updates the model-failure counters used for degraded mode.

If the ticket allows a draft, `Prepare Draft Request` and `HTTP OpenAI Draft` write a
tenant reply, a vendor note, and any clarifying questions, and `Postgres Update Draft`
stores them. `Route By Priority` sends the result out one of four dead-end branches
(`Emergency Result`, `Needs Review Result`, `Urgent Result`, `Routine Result`) purely so
the sub-workflow returns something; because Execute Sub-workflow branches like this don't
merge back into one item stream, every caller downstream reselects the ticket by
`msg_id` rather than trusting this node's output shape.

**Workflow: Maintenance Triage Post Ingest**, called next. `Postgres Match Unit Roster`
reselects the ticket by `msg_id` (or ticket id) and, in one query, matches its unit
string against `triage.units`: exact label match, disambiguated by a property-name hint
in the message text if the same label exists at more than one property, else the nearest
label by digit and length similarity as a near-miss. `Should Dispatch Alert` only
proceeds if this was a genuinely new ticket, not a duplicate or a reopened thread, so a
reply to an existing conversation never re-alerts.

**Workflow: Maintenance Triage Alert Dispatch**, called next. `Postgres Load Alert
Context` loads the ticket plus the current `board`, `contacts`, `company`, `quiet_hours`,
and `limits` config, and a count of alerts sent in the last hour. `Prepare Alert Action`
is a Code node that decides: whether this priority alerts at all, whether it alerts
silently, whether quiet hours or the hourly rate cap hold it back, and whether the
ticket is already handled and should not be touched again. See "Notification Policy"
below. If a real send is due, one of three Telegram nodes fires
(`Telegram Send Emergency Alert`, `Telegram Send Urgent Alert`, or `Telegram Send Review
Alert`), each with its own explicit inline-keyboard rows rather than one shared
expression, because a shared expression silently produces a plain-text message with no
buttons in this n8n version. Either path ends at a Postgres write that sets status to
`ALERTED`, unless the ticket is already `ACKED`, `ACK_SENT`, or `HELD`, in which case the
write is a no-op on status.

A human then taps a button on their phone.

**Workflow: Maintenance Triage Telegram Callback.** `TelegramCallbackTrigger` fires on
the tap. `Normalize Telegram Callback` extracts the `act:<ticket_id>:<action>` payload
and the actor. `Execute Approval Action` calls Approval Action and waits.

**Workflow: Maintenance Triage Approval Action**, called as a sub-workflow.
`Postgres Approval Gate` is one query whose `UPDATE ... WHERE` clause is the entire
double-approve guard: an `approve` action only claims the ticket if its status is not
already `ACKED` or `ACK_SENT`, `human_only` is false, its priority is not `NEEDS_REVIEW`,
and a draft exists. A second tap, or a tap on a ticket that never qualified for
a draft, matches zero rows and falls through to `already_handled` or `refused`. If the
claim succeeded, `Prepare Email Payload` builds the outbound email (routed to the
configured test inbox while `outbound_email.mode` is `test_only`), and `SMTP Send
Approved Reply` sends it. `Postgres Finalize Approved Email` sets status to `ACK_SENT`
and stores the outbound message id only on success; a failed send is recorded as
`last_alert_error` without pretending the reply went out.

Back in Telegram Callback, `Telegram Answer Callback` acknowledges the tap first,
because Telegram's `answerQuery` does not preserve upstream context for later nodes. The
approval result is reattached afterward, and `Telegram Edit Alert Message` rewrites the
original alert in place with the outcome.

## Why Reading And Deciding Are Separate

`HTTP OpenAI Classification` only ever returns a JSON object matching the
`maintenance_triage` schema. It is never asked whether a message deserves an override,
only what the message says. `Apply Safety Rules`, a plain Code node with no model call
in it, is the only place a priority can change, and it can only raise a priority, never
lower one: `maxPriority` always keeps the higher of the model's answer and
`EMERGENCY`-if-a-keyword-rule-fired.

This confines the part of the system that could produce a wrong answer to reading
language, and reading is checkable. The raw model JSON, the rules that fired, and the
reason are all one click away in the board's detail view, behind the "Technical audit"
disclosure.

## What The Safety Rules Layer Checks

All in `Apply Safety Rules`, `workflows/maintenance-triage-core.json`.

Ten word-boundary regex signals run against the cleaned message text, each guarded by a
negation lookback so "no smell of gas" or "isn't sparking" does not fire the rule:
`GAS`, `CARBON_MONOXIDE`, `SMOKE_FIRE`, `FLOOD`, `SEWAGE`, `NO_HEAT`, `NO_WATER`,
`NO_COOLING`, `SECURITY`, `ELECTRICAL`. Any hit forces the priority to at least
`EMERGENCY` and writes an `overridden` event naming the signal.

Three further deterministic boundaries sit on top of that, added after live rehearsal
exposed small model variance on specific demo cases:

- `routineSqueakyDoor` keeps a squeaky- or noisy-door complaint `ROUTINE` even if the
  tenant marks it urgent, unless the message also mentions a lock, closure, access
  problem, or injury.
- `containedCeilingDrip` pulls a bucket-contained ceiling drip back from `EMERGENCY` to
  `URGENT`, unless the message also mentions spreading water, collapse, or an electrical
  hazard near the water.
- `lowInformation` forces `NEEDS_REVIEW` when the model reports a new issue with no
  concrete detail and the message itself looks unreadable, is an "attachment only" note,
  or names an unknown trade with almost no substance. This is the deterministic answer
  to garbage input, not a model guess.

`NEEDS_REVIEW` is a system-only state. It is not in the model's output schema; the model
cannot choose it. It is forced by, in order of what triggers it: the OpenAI call
failing or returning invalid JSON, the model reporting `LOW` confidence alongside an
active safety signal, the model reporting the message is not a maintenance request while
a safety rule still fired on the text, or the `lowInformation` check above.

## Notification Policy

Computed entirely in `Prepare Alert Action`, `workflows/maintenance-triage-alert-dispatch.json`.

| Priority | Business hours | Quiet hours |
|---|---|---|
| EMERGENCY | Alerts, audible | Alerts, audible. No exception. |
| URGENT | Alerts, silent | Held |
| NEEDS_REVIEW, with a safety signal | Alerts, silent | Alerts, silent |
| NEEDS_REVIEW, no safety signal | Alerts, silent | Held |
| ROUTINE, or human-only | Board only | Board only |

Two more rules sit on top of that table. An hourly cap (`limits.max_alerts_per_hour`,
default 6) groups anything past the limit instead of sending it. And a ticket already
`ACKED`, `ACK_SENT`, or `HELD` is never touched again by this workflow, so a re-run
cannot regress a handled ticket's status back to `ALERTED`. Age is not an input to this
table at all: an aged routine or urgent ticket becomes an `OVERDUE` board and digest flag
through a separate query in the board and digest workflows, and never reaches this alert
path.

## What Lives In Postgres Rather Than n8n

There are no stored functions, procedures, or triggers anywhere in this project's
database. Every table in `db/postgres/` is created with plain `CREATE TABLE` statements,
and the config seed files write JSON values, nothing else. That is a real structural
choice, not an oversight: unlike a project with dedicated SQL functions, the decision
logic here lives directly inside the queries of specific Postgres nodes, as CTEs. Reading
the n8n canvas alone hides it. These are the ones that carry real decisions rather than
plain storage:

- `Postgres Dedupe Thread Gate` (Core): the dedupe and thread-match decision, in one query.
- `Postgres Match Unit Roster` (Post Ingest): exact, ambiguous, near-miss, or not-found roster matching.
- `Postgres Approval Gate` (Approval Action): the double-approve guard and the human-only/NEEDS_REVIEW refusal, both enforced in the `UPDATE ... WHERE` clause itself.
- `Postgres Load Board Data` (Board): the entire list and detail view, including priority ranking and the overdue computation.
- `Postgres Load Digest Context` (Daily Digest) and `Postgres Load Heartbeat State`
  (Operator Heartbeat): their respective aggregate queries. The heartbeat's
  should-alert decision is a boolean computed in SQL, not in a Code node.
- `Postgres Record Real Alert` and `Postgres Record Mock Or Skipped Alert` (Alert
  Dispatch): the same no-status-regression guard described above.

Three indexes encode business rules directly in their `WHERE` clause, which is worth
knowing if a query stops matching expectations after a schema change:
`tickets_stage_6_emergency_escalation_idx` (`priority='EMERGENCY' AND acked_at IS NULL
AND closed_at IS NULL`), `tickets_stage_6_approval_guard_idx` (`status IN ('NEW',
'ALERTED', 'ACKED', 'HELD')`), and `events_stage_6_alert_rate_idx` (`action IN
('telegram_alert_sent', 'telegram_alert_mocked', 'telegram_alert_grouped')`).

`triage.config` holds every tunable value as a JSON row, not a code constant:

| Key | Holds |
|---|---|
| `sla_minutes` | Response target per priority, in minutes. Default `{EMERGENCY:60, URGENT:1440, ROUTINE:4320, NEEDS_REVIEW:120}` |
| `overdue_days` | Days before a routine or urgent ticket becomes `OVERDUE`. Default `{ROUTINE:10, URGENT:3}` |
| `escalate_after` | Minutes before an unacknowledged emergency re-alerts. Default `{EMERGENCY_minutes:15}` |
| `contacts` | Telegram chat ids for primary, secondary, and operator contacts |
| `company` | Display name, office hours, sender name, timezone |
| `quiet_hours` | Start, end, timezone, and the emergency-only flag |
| `limits` | Daily LLM call cap and hourly alert cap |
| `runtime_state` | Consecutive model-failure count, `degraded_until`, and today's LLM call count |
| `board` | The board's access token and its list bounds (`recent_hours`, `max_cards`); `public_base_url` is set by hand, not seeded |
| `outbound_email` | Send mode (`test_only` or `live`), sender identity, test inbox |
| `ingestion` | The batch-import token and the attachment/batch storage roots |
| `digest` | Enabled flag (default false), send hour, recipient |
| `heartbeat` | Enabled flag (default false), quiet threshold, repeat-suppression window |

## The Approval Gate And The Double-Approve Guard

Worth stating plainly because it is the one guarantee the whole advisory-only story
depends on: nothing reaches a tenant unless a human taps approve, and a second tap
cannot send a second email. Both are enforced by the same mechanism, the `WHERE` clause
on `Postgres Approval Gate`'s `UPDATE` statement in Approval Action. The row only
updates, and the email only gets prepared, if the current status is not already
`ACKED`/`ACK_SENT`. There is no code path that checks this after the fact; the guarantee
is that the second tap's `UPDATE` matches zero rows.

## What It Deliberately Refuses To Do

These are not gaps. They are the design.

It never dispatches a vendor, never suppresses or auto-closes a ticket, and never sends
a tenant reply without a human tap, in every version, with no setting to loosen this. Age
alone never triggers a phone alert; an old routine or urgent ticket only ever becomes an
`OVERDUE` board and digest flag. A human-only ticket, meaning the model flagged an
accommodation or legal-sensitive request, never gets a draft generated at all, and a
handled ticket can never be re-alerted back to `ALERTED` by a later run.

## What It Genuinely Cannot Do

These are limits of the build itself, not policy choices.

It does not write anything back to a property management system; there is no PMS
integration anywhere in this project. It cannot look up a real unit, tenant, or lease; it
only has what the message text says, and a unit label is matched against a synthetic demo
roster (`triage.units`), not a real one. It does not interpret an attached photo; the
board shows an attachment count as a chip, nothing more. It does not transcribe a phone
call or voicemail. Only English and Spanish have been tested; any other language is
untested. It cannot guarantee compliance with any state's habitability response windows;
response targets are configurable, operational numbers, never a legal deadline. Its only
measured accuracy is the six-fixture live-demo gate (see `docs/stage-3-scorecard.md`):
6 of 6 priority matches, zero under-escalations, zero over-escalations, zero missed
safety signals, on that fixture set. The full 30-fixture hardening run has not passed;
`progress-notes.md` records it as failed and deferred. Do not extrapolate the six-fixture
result into a broader accuracy claim. It runs on one local Docker host with one operator
behind it, not monitored production infrastructure, and outbound mail currently sends
from a demo sender identity with no production deliverability setup (SPF/DKIM/DMARC) in
place.

## Language Rules

This document, and anything built from it, should hold to the same rules the demo script
uses.

**Never say:** "the system does X" without naming the workflow. My platform, my tool, my
product, the app. Users, sign up, subscribers. That it will never miss an emergency, that
it verifies or confirms anything about a tenant's situation, that it is legal advice.

**Say instead:** the name of the responsible workflow. The manager, the office, whoever
reads the board. That everything still reaches a human, just pre-sorted. That a response
target is operational, not a deadline.

## Where Everything Lives

- **Tickets, events, config, feedback, units, import batches and items.** The `triage`
  schema in Postgres, defined across `db/postgres/001-create-triage-schema.sql` through
  `007-stage-8-hardening.sql`.
- **Attachments.** `/data/attachments/`, written before anything else reads the message.
- **Batch import reports.** `/data/import-batches/<batch-id>/report.html` and
  `review.csv`.
- **Clean-state snapshots.** `data/demo-snapshots/<name>.sql`, gitignored.
- **Local credential names.** Postgres `maintenance-triage-postgres-local`, OpenAI
  `maintenance-triage-openai`, Telegram `maintenance-triage-telegram-bot`, mailbox intake
  `maintenance-triage-demo-imap-domain`, mailbox outbound
  `maintenance-triage-demo-smtp-domain`.
- **Local URLs.** n8n `http://localhost:5678`; board
  `http://localhost:5678/webhook/board?t=<board-token>`; the intake form
  `http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue`.

## Resetting And Staging

`.\scripts\reset-stage-8-demo-state.ps1` truncates `triage.tickets`, `events`,
`feedback`, `import_batches`, and `import_items`, restarts the ticket reference
sequence, resets the runtime and heartbeat counters, and clears
`data/attachments`/`data/import-batches` unless `-KeepGeneratedFiles` is passed. It
leaves config, units, credentials, workflows, and the board token untouched.

`.\scripts\save-stage-8-demo-snapshot.ps1 -Name <name>` and
`.\scripts\restore-stage-8-demo-snapshot.ps1 -Name <name>` save and restore a
data-only dump of the same tables. `-Name clean` is the standard pre-call baseline.

`.\scripts\run-stage-8-rehearsal.ps1 -Runs 5` resets, fires the six live-demo fixtures
through the CLI, and asserts ticket count, priority match, roster display, zero real
Telegram sends, and board HTTP 200, across every run, then asserts the result was
identical across all runs.

## Troubleshooting

| Symptom | Open first |
|---|---|
| Board returns 404 | Maintenance Triage Board, `Postgres Load Board Data`. Check the `t=` token in the URL against `triage.config.board.token`, and, for a detail page, that `?ref=` matches a real ticket. |
| Telegram alert is plain text with no buttons | Maintenance Triage Alert Dispatch. The inline keyboard must be explicit fixed-collection rows on the Telegram node; a whole keyboard passed as one expression silently drops the buttons in this n8n version. |
| Alert's board button opens `localhost` on a real phone | `triage.config.board.public_base_url` is not set to the current Cloudflare Tunnel URL. |
| A second approval tap appears to send a second email | Maintenance Triage Approval Action, `Postgres Approval Gate`. Confirm the first tap moved status to `ACK_SENT`; the guard is in the `UPDATE ... WHERE` clause, not a separate check. |
| A handled ticket shows `ALERTED` again after a re-run | Maintenance Triage Alert Dispatch, `Postgres Record Real Alert` / `Postgres Record Mock Or Skipped Alert`. The status `CASE` should never overwrite `ACKED`/`ACK_SENT`/`HELD`. |
| A ticket lands on `NEEDS_REVIEW` unexpectedly | Open the ticket's Technical audit panel on the board and read `model_error` and the review reason recorded in Core's `Apply Safety Rules`. Usually a bad OpenAI key, a timeout, or the `lowInformation` guard. |
| Everything is landing on `NEEDS_REVIEW` at once | Check `triage.config.runtime_state.degraded_until`. Three consecutive OpenAI failures trip a 10-minute degraded window in Core. |
| Roster shows a near-miss instead of an exact match | Maintenance Triage Post Ingest, `Postgres Match Unit Roster`. Check `triage.units.unit_label` formatting, and whether the message names the property when the same unit label exists at more than one property. |
| Form submission shows blank or `field-0` values | Maintenance Triage Form Ingest, `Prepare Form Core Payload`. It reads real field labels first and falls back to `field-N`; check the form's configured labels haven't drifted from `TenantReportForm`'s definition. |
| Digest or heartbeat never sends | Check `triage.config.digest.enabled` and `heartbeat.enabled`. Both default to false. |
| Emergency escalation doesn't page a second time | By design in this build. Maintenance Triage Emergency Escalation forces `mock_telegram: true` into every re-alert it triggers, so it never sends a second real Telegram message here. |
| A newly imported webhook or form 404s | Restart n8n. Local n8n `2.29.10` needs a restart to register a newly imported or published webhook's production path. |

## Technical Pointers

- **The workflows.** `workflows/`, one file per workflow, generated by
  `scripts/build-stage-*.py` rather than hand-edited.
- **Database structure and settings.** `db/postgres/001-create-triage-schema.sql`
  through `007-stage-8-hardening.sql`.
- **The 30-fixture corpus and the 6 live-demo fixtures.** `fixtures/`; the live-demo
  set is also hardcoded directly in `workflows/maintenance-triage-fixture-fire.json`.
- **The measured accuracy gate.** `docs/stage-3-scorecard.md`,
  `docs/stage-8-operator-cheat-sheet.md`.
- **Stage-by-stage build detail.** `docs/stage-*-runbook.md`,
  `docs/stage-8-pre-call-checklist.md`, `docs/stage-8-failure-rehearsal.md`.
- **Current status, decisions, and deviations.** `progress-notes.md`.
- **The controlling demo spec.** `maintenance-triage-demo-build-plan.md`.
