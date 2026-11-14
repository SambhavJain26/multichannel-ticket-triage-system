# Maintenance Request Triage - Staged Development Plan

This plan is based on a full read of:

- `02-maintenance-triage.md`
- `foundation-2-maintenance-operations.md`
- `maintenance-triage-demo-build-plan.md`

The build target is a demo-depth advisory triage layer for US residential property management companies with 150-600 doors. The product reads inbound maintenance messages, classifies priority and trade, applies deterministic safety overrides, drafts human-approved replies, surfaces emergencies, and shows a priority-ordered board. It does not touch the client's PMS, dispatch vendors, suppress requests, auto-close tickets, or auto-reply without human approval.

The demo build is local-first. Production hosting on a VPS is a later deployment concern, not part of the initial demo build.

## Source Review Notes

The validated problem is strong: maintenance triage is high-volume, legally and commercially consequential, and currently handled as invisible human judgment across messy inbound channels. The central design constraint is advisory-only operation. Every request must still reach a human.

Material corrections and conflicts from the documents:

- The original problem note says aged routine items may escalate toward emergency review. The revised demo spec rejects phone-alert escalation for aged routine work. This plan follows the revised spec: aging creates an `OVERDUE` board/digest flag only, never an emergency phone alert.
- The original note suggests the classification step is not shipped by competitors. The revised spec says that is not true across the broader market. This plan avoids the claim that nobody else does AI triage and positions the demo against answering services, raw inbox triage, platform migration, and auto-dispatch risk.
- The original keyword list is too naive. This plan uses the revised spec's deterministic, escalate-only safety rules with word-boundary matching, negation guards, and event logging.
- The original classification schema is incomplete for demo safety. This plan includes `NOT_A_REQUEST`, `FOLLOW_UP`, accommodation/legal flagging, model failure handling, and a system-only `NEEDS_REVIEW` state.
- The original asks for 60+ realistic test variants. The revised demo spec defines 30 high-leverage fixtures. This plan builds the 30-fixture harness first as the demo gate; expanding beyond 30 remains a later hardening task.
- The demo script fires five weekend messages and separately opens the accommodation request. The fixture list marks six live fixtures. This plan treats that as intentional: five are injected live for sorting, and the accommodation item is shown as the human-only safety example.
- OpenAI model names, prices, accepted request parameters, Gmail App Password availability, tunnel behavior, and some PMS API details are time-sensitive. The implementation must verify them during the setup/model stages instead of assuming the spec is still current.

Implementation defaults unless you override them:

- Build locally on this machine with Docker. VPS and Caddy are production-only unless explicitly requested.
- Use a tunnel only where a public HTTPS callback is required, especially Telegram callback testing and optionally a temporary public board link. Preferred default: Cloudflare Tunnel or ngrok, selected during Stage 1 based on ease of setup.
- Use n8n's built-in OpenAI node for workflow model calls when the installed n8n version supports the V2 Text operation `Generate a Model Response` with `Output Format: JSON Schema`. This gives a maintainable visual workflow and still preserves schema-bound outputs.
- Keep direct OpenAI API calls in the standalone harness, where precise request bodies, repeatability, usage capture, and regression testing are easier.
- Use HTTP Request for OpenAI only as a fallback if the installed n8n OpenAI node cannot express the required schema/reasoning/model settings or fails to return the raw fields we need.
- Do not use n8n AI Agent/LangChain agent loops for the triage classifier. This is deterministic classification plus drafting, not an autonomous agent.
- The current live workflow model is `gpt-5.6-luna`, following live demo classification instability with `gpt-5-nano`. The historical harness retains its original nano benchmark; the pass/fail gate remains zero safety-signal misses and acceptable under-escalation behavior on the fixture harness.
- Use a dedicated IMAP mailbox for intake and a domain-authenticated sender identity for outbound demo replies if available. A plain Gmail sender is acceptable only for internal testing, not a prospect screen share.
- During early testing, approved outbound tenant replies go only to controlled test inboxes. Prospect-supplied addresses can be enabled intentionally during demo rehearsal once the approval gate and double-approve guard are verified.

Stage 1 setup choices confirmed:

- Use GreenMail as the local IMAP/SMTP simulator. A real demo mailbox/domain is deferred until outbound demo rehearsal.
- Use Cloudflare Tunnel quick tunnels for temporary HTTPS callback testing.

## Stage 1 - Local Environment, Accounts, and Runtime Setup

Goal: create the runtime foundation without assuming any account, API, or service already exists.

In scope:

- Prepare Docker runtime on this machine.
- Set up local `n8n` and Postgres 16 via Docker Compose.
- Configure persistent local volumes for n8n and Postgres.
- Configure a tunnel for public HTTPS callbacks only when needed for Telegram testing or temporary external board access.
- Create or configure a dedicated IMAP/SMTP mailbox.
- Create a Telegram bot and capture chat IDs.
- Add OpenAI API credentials to n8n credentials, not workflow JSON.
- Seed initial config values for SLA targets, quiet hours, alert contacts, and limits.

Out of scope:

- VPS provisioning.
- Caddy setup.
- Any classification prompt iteration.
- Any tenant-facing workflow.
- Any PMS integration.
- SMS, Twilio, A2P 10DLC, voicemail transcription, or image analysis.

Verification:

- n8n UI loads locally.
- Postgres is reachable from n8n.
- IMAP receives a test email and SMTP sends a test email.
- Telegram sends a test message to the demo phone.
- Tunnel can expose local n8n over HTTPS when enabled.
- OpenAI credential is present but not embedded in exported workflow JSON.
- n8n workflows use built-in/core nodes only; no community nodes and no AI Agent/LangChain agent loops.

## Stage 2 - Data Model, Config, and Fixture Corpus

Goal: establish the database contract and test data before workflow logic depends on it.

In scope:

- Create the Postgres schema for `tickets`, `events`, `config`, and `feedback`.
- Include fields for threading, raw/model/rules output, drafts, status, SLA target, Telegram message IDs, and audit events.
- Seed config rows for SLA minutes, overdue thresholds, escalation timing, contacts, company settings, quiet hours, and spend/alert limits.
- Create the 30 synthetic fixture messages and matching expected JSON labels.
- Include the critical fixtures: gas, flood, squeaky door, buried lede, Spanish, accommodation/legal, CO alarm, negation trap, garbage input, implied gas/electrical danger, prompt injection, auto-responder loop, and voicemail-transcript-shaped text.

Out of scope:

- Calling OpenAI.
- n8n workflow import/building.
- Board UI.

Verification:

- Tables and indexes exist.
- Config query returns the expected seeded rows.
- Every fixture has a matching expected file.
- The expected labels cover all target states: `EMERGENCY`, `URGENT`, `ROUTINE`, `NEEDS_REVIEW`, `NOT_A_REQUEST`, `FOLLOW_UP`, and accommodation/legal human-only handling.

## Stage 3 - OpenAI Model Contract and Accuracy Harness

Goal: prove the model calls are structured, measurable, and cheap before wiring them into n8n.

In scope:

- Make a live minimal `/v1/chat/completions` request to verify the current OpenAI model string and accepted parameters.
- Save the known-good request shape.
- Build a standalone classification runner against the strict JSON schema.
- Build a standalone drafting runner against the strict draft schema.
- Implement the accuracy harness that runs fixtures repeatedly and prints overall match rate, confusion matrix, over-escalations, under-escalations, safety signals missed, latency, token usage, and estimated cost.
- Benchmark `gpt-5-nano` first. Benchmark `gpt-5.6-luna` as the fallback if nano misses safety cases, under-escalates too often, has unstable schema output, or produces weak drafts.
- Iterate prompts until the six demo fixtures and key safety fixtures are stable enough to proceed.

Out of scope:

- n8n workflow logic.
- Telegram alerts.
- Board rendering.

Verification:

- One command runs the fixture harness.
- All outputs validate against the schemas.
- The six demo fixtures classify consistently across repeated runs.
- Spanish fixture produces Spanish tenant reply and English vendor note.
- Accommodation/legal fixture produces no tenant draft path.
- The measured scorecard is saved or recorded for demo use.
- A model choice is recorded with accuracy, under-escalation count, safety-signal miss count, latency, and estimated cost. Cheapest only wins if safety performance is acceptable.

## Stage 4 - Core Triage Sub-Workflow

Goal: build the reusable n8n core that takes one normalized request and always produces a stored ticket or a logged duplicate/thread event.

In scope:

- Create an `Execute Sub-workflow Trigger` accepting source, sender, subject, raw body, received timestamp, attachments, and email threading headers.
- Normalize message bodies: strip quoted replies, signatures, common footers, collapse whitespace, truncate to 1,500 characters, compute body hash.
- Implement dedupe by body hash over a 24-hour window.
- Implement reply/thread handling using `Message-ID`, `In-Reply-To`, and `References`.
- Call OpenAI classification using the n8n built-in OpenAI node if it supports the required JSON Schema output and model/reasoning settings in the installed version; otherwise use HTTP Request as fallback.
- Implement circuit breaker/degraded mode after consecutive model failures.
- Enforce daily LLM call cap without dropping ticket rows.
- Apply deterministic escalate-only safety rules.
- Force `NEEDS_REVIEW` on bad JSON, API failure, low-confidence safety cases, and inconsistent safety cases.
- Insert ticket and audit events.
- Skip draft generation for human-only accommodation/legal items.
- Generate drafts for all other maintenance tickets.

Out of scope:

- Public ingestion workflows.
- Board UI.
- Telegram approval buttons.

Verification:

- Each fixture produces exactly one ticket or a correct duplicate/thread event.
- A deliberately broken OpenAI key creates a `NEEDS_REVIEW` ticket instead of a failed execution.
- Gas safety override raises priority even when a mocked model output says routine.
- Negated safety text does not trigger a false safety override.
- Accommodation/legal fixture has null drafts and human-only status.
- Repeated same-message fixtures do not duplicate cards.
- Reply-to-acknowledgment fixtures append to the original ticket instead of creating a fresh alert.
- The OpenAI node output includes enough raw usage/metadata for cost logging, or the plan explicitly falls back to HTTP Request for those calls.

## Stage 5 - Board and Detail View

Goal: make the work visible in the form the demo actually sells: a priority-ordered work-order board.

In scope:

- Create the board webhook with token protection.
- Query open emergencies/urgent items plus recent tickets, bounded so the board does not grow forever.
- Render server-side HTML with no external dependencies.
- Include card states for emergency, urgent, routine, needs review, human-only/accommodation, and overdue.
- Include summary, ref, unit, trade, source, age, response target clock, override stamp, confidence, missing info, attachment chip, and reply status.
- Add simple auto-refresh.
- Create detail view by reference showing original message, model JSON, rules verdict, drafts, and event trail.

Out of scope:

- Login system.
- Admin/settings UI.
- React/Next.js/full web app.
- Tenant or vendor portal.

Verification:

- Board renders with a valid token and returns not-found/blocked behavior without it.
- Empty state is clean.
- Firing fixtures fills the board without manual refresh.
- All card states are visible from fixture data.
- Detail view explains why a ticket was classified or overridden.
- Board remains legible after repeated fixture runs.

## Stage 6 - Alerts, Approval Gate, and Outbound Email

Goal: implement the human-in-the-loop output path where emergencies wake the manager and tenant replies only send after approval.

In scope:

- Emergency Telegram alerts with summary, unit, tenant words, override reason, response target, board link, and inline buttons.
- Quiet notification policy for urgent items and `NEEDS_REVIEW` items based on safety signal and quiet hours.
- Telegram callback workflow for `approve`, `hold`, and `not_emergency`.
- SMTP tenant reply send only behind the approve callback.
- Double-approve guard so two people tapping approve sends one email.
- Store outbound `Message-ID` for future threading.
- Telegram message edit after action.
- Scheduled emergency escalation using the fail-safe predicate: emergency, unacked, older than 15 minutes.
- Alert-rate cap/grouping for bursts.

Out of scope:

- Auto-dispatch.
- Auto-reply without approval.
- Vendor contact.
- SMS alerts.

Verification:

- Emergency fixture alerts the phone quickly.
- Approve sends exactly one email to a test inbox and updates Telegram.
- Double approve sends one email and returns an "already sent" response.
- Hold changes status without sending.
- Not emergency downgrades to urgent and records feedback.
- Unacknowledged emergency escalates even if first alert delivery was forced to fail.
- Routine and quiet-hours urgent fixtures do not buzz the phone.
- Telegram callback testing works through the configured local HTTPS tunnel.

## Stage 7 - Ingestion Paths and Follow-Up Importer

Goal: connect real demo inputs to the core while keeping the core reusable.

In scope:

- IMAP email trigger mapped into the core sub-workflow.
- Attachment handling to disk with stored paths and card chips.
- Form trigger for tenant-style submission with completion screen and reference number.
- Fixture firing workflow that injects demo fixtures one at a time with staggered timing.
- Unit roster table and synthetic CSV matching for demo units.
- Batch importer for `.eml` and `.txt` prospect sample emails.
- One-page batch report showing sorted week, alert count, misses, over-48-hour items, and prospect-number arithmetic.
- Voicemail-transcript-shaped fixtures through the same text ingestion path.
- Sender identity is corrected before any screen share: outbound approved replies should not visibly come from a throwaway Gmail identity if a domain sender is available.

Out of scope:

- Direct voicemail/audio transcription.
- Image/photo interpretation.
- PMS write-back.
- Production-grade tenant identity verification.

Verification:

- Email from phone appears on board end to end.
- Form submission produces ticket and confirmation reference.
- Fixture runner produces staggered cards over the expected demo window.
- Email with photos stores files and displays attachment chip.
- Valid, invalid, and missing unit examples display correct roster match/near-miss/not-stated behavior.
- Dropping 20 `.eml` or `.txt` files produces a report without manual copy/paste.

## Stage 8 - Digest, Aging, Heartbeat, and Demo Hardening

Goal: make the demo reliable enough to run live and honest enough to recover from failures.

In scope:

- Daily digest workflow with open emergencies, breached response targets, overdue routine/urgent items, and yesterday's counts.
- Aging logic that marks overdue items on board/digest without phone alerts.
- Heartbeat workflow that alerts the operator, not the client, when ingestion appears silent beyond the configured window.
- Clean demo database snapshot and restore command.
- End-to-end repeated fixture runs from clean state.
- Failure rehearsals: OpenAI key failure, model slowness, Telegram failure, Postgres/board failure, network failure, wrong classification.
- Fallback 90-second screen recording.
- Final demo script checklist and pre-call checklist.
- Final accuracy harness run and saved scorecard.
- Demo collateral: one short operator cheat sheet containing the measured accuracy scorecard, actual token/cost number, failure recovery lines, data-handling answer, competitor-aware positioning, and the explicit "what not to claim" list.
- Confirm the live demo flow: five injected weekend fixtures, prospect-written live input, then accommodation/legal fixture shown as the human-only example.

Out of scope:

- Production multi-client hosting.
- Signed per-user board tokens.
- External uptime monitoring beyond a simple demo heartbeat.
- Legal documents, DPA, E&O insurance, and production client onboarding materials.

Verification:

- Digest can be triggered manually and reads cleanly.
- Backdated fixture becomes overdue and does not alert by phone.
- Stopping ingestion produces an operator-only heartbeat alert.
- Clean restore returns the board to empty quickly.
- Six demo fixtures classify identically across five clean runs.
- Failure modes have been observed and the response lines are rehearsed.
- Fallback recording plays offline.

## Stage 9 - Telegram Conversation, Airtable, and Vendor Approval

Goal: make Telegram the tenant conversation channel, make Airtable the manager workspace,
and make vendor email an explicit manager choice.

In scope:

- Email, form, and Telegram tenant intake through the same triage engine.
- One onboarding email for email/form requests, containing an expiring tenant-bot deep link.
- Tenant Telegram receipt, deterministic clarification, and truthful status templates.
- Two-round clarification limit, followed by `NEEDS_REVIEW`.
- Airtable `Requests`, `Conversations`, `Tenant Roster`, and `Vendors` tables with synthetic demo data.
- Trade/property vendor suggestions and one-tap manager vendor selection in Telegram.
- One-send-only vendor SMTP guard and tenant provider-contacted update after SMTP success.
- Consolidation to five active workflows: Triage Engine, Tenant Intake, Tenant Telegram,
  Manager Desk, and Operations. Keep only inactive demo tools for rehearsal.

Out of scope:

- Production tenant identity verification for Telegram pairing.
- Automatic vendor dispatch, appointment confirmation, or tenant ETA promises.
- Real tenant/vendor email or SMS testing.

Verification:

- Structural validation of schema, generated workflows, and Docker Compose.
- Controlled email/form pairing link, direct Telegram request, clarification, and status-query checks.
- Airtable request/conversation visibility and vendor trade/property selection.
- One manager vendor selection yields one controlled SMTP email; duplicate selection does not.
- Vendor failure and no-match paths keep the tenant update unsent and remain visible to the manager.

## Post-Demo Production Backlog

These are deliberately not part of the demo stages:

- Client-owned production VPS per client.
- Caddy reverse proxy and production HTTPS certificates.
- Client-domain SPF, DKIM, DMARC, bounce monitoring, and deliverability hardening.
- Dead-letter queue and deeper retry/backoff coverage.
- Real signed, expiring, revocable board tokens.
- Attachment retention purge.
- External uptime monitoring and weekly canary self-test.
- Per-client unit/tenant roster import from real data.
- Alert-storm grouping by property/time window.
- Same-sender grouping beyond email thread headers.
- Photo analysis behind a flag.
- Voicemail/audio transcription.
- SMS intake or alerting with client-owned A2P 10DLC registration.
- Rentec Direct write-back as a paid phase 2 for eligible Rentec clients.
- Weekly analytics and correction review loop.
- One-page data-handling summary, short DPA, written advisory-only scope clause, and production runbook.

## How To Use This Plan Across Sessions

At the start of each future session:

1. Read `progress-notes.md` first.
2. Read the stage section in this file for the stage being started.
3. Build only that stage unless the user explicitly expands scope.
4. Verify the stage using its verification checklist.
5. Update `progress-notes.md` with completion status, deviations, test results, and remaining issues.
