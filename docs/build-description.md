# Maintenance Triage Build Description

## Purpose and current state

This document is the technical handover for the local maintenance-triage demo. It is the primary reference for someone who needs to explain the build, run it, troubleshoot it, or make a controlled change. Product-facing behavior is summarized in docs/how-the-system-works.md; the practical demo runbook is docs/operating-guide.md.

The build turns tenant maintenance messages into a manager-controlled decision flow. It accepts requests from email, web form, and Telegram; identifies urgency and missing information; continues a constrained tenant conversation; proposes suitable vendors; and makes the manager the approval point for vendor contact.

The current implementation is Stage 9, published for a local demo. It is not a production property-management system. It has no PMS/work-order integration, verified tenant identity, vendor appointment integration, automatic dispatch, automatic closure, or production hosting configuration.

## Product position

The selling point is not "an AI chatbot." It is a practical operating layer for a property manager: routine messages are organized, unsafe cases are surfaced, missing detail is collected before the manager is interrupted, vendor options are matched to property and trade, and the manager remains in control of vendor email.

The demo should not claim that it replaces established property-maintenance products or that no other tool does maintenance automation. It demonstrates a lightweight, manager-controlled triage and communication layer that can sit ahead of an existing work-order process.

## Architecture

    Gmail IMAP ------------------\
    n8n Form --------------------- Tenant Intake ------\
    Tenant Telegram bot ---------- Tenant Telegram ----- Maintenance Triage Engine
                                                                  |
                                           +----------------------+---------------------+
                                           |                      |                     |
                                      Postgres              Airtable             Manager Desk
                                   authoritative          manager view                  |
                                           |                       roster          Manager Telegram
                                           |                                             |
                                           +--------------------------------------- Gmail SMTP
                                                                                         |
                                                                                   Tenant Telegram

### Component ownership

| Component | Responsibility | Authority |
|---|---|---|
| n8n | Triggers, routing, model calls, notifications, SMTP orchestration | Orchestrator only |
| Postgres | Ticket identity, conversation state, idempotency, events, locks, configuration | Authoritative operational state |
| Airtable | Visible manager workspace plus demo tenant/vendor roster | Mirror and roster source |
| OpenAI Responses API | Structured classification and draft content | Advisory model output |
| Tenant Telegram bot | Tenant conversation channel after intake | Delivery channel |
| Manager Telegram bot | Manager alerts and explicit vendor selection | Decision channel |
| Gmail IMAP/SMTP | Email intake, onboarding links, approved vendor email | Controlled test integration |

Postgres is intentionally not replaced by Airtable. Airtable is easy to present and manage, but it is not trusted to enforce unique ticket references, inbound-message idempotency, or one-send-only vendor dispatch.

## Runtime and local services

Docker Compose starts three local services:

| Service | Purpose | Local endpoint |
|---|---|---|
| n8n | Workflow editor and runtime | http://localhost:5678 |
| Postgres 16 | triage schema and durable state | 127.0.0.1:5432 |
| GreenMail | Local mail simulator for non-live checks | Compose internal service |

The production-facing Telegram callback requires a reachable HTTPS URL. For local tests, use scripts/start-cloudflare-tunnel.ps1, place the temporary URL in local .env as N8N_WEBHOOK_URL, restart n8n, then publish the live Telegram triggers. A tunnel is only for the local demo.

Start and stop the stack:

    .\scripts\start-local.ps1
    .\scripts\stop-local.ps1
    docker compose ps

## Active workflows

Only these five operational workflows should be active in n8n:

| Workflow | n8n ID | Responsibility |
|---|---|---|
| Maintenance Triage Engine | maintenance-triage-core-stage-4 | Normalize, classify, apply safety rules, persist, sync, draft, vendor-match |
| Maintenance Tenant Intake | mt-tenant-intake-stage-9 | Gmail IMAP and form intake; onboarding email; call core |
| Maintenance Tenant Telegram | mt-tenant-telegram-stage-9 | Tenant bot start, direct intake, /new, clarification, and status questions |
| Maintenance Manager Desk | mt-manager-desk-stage-9 | Manager alerts, vendor buttons, Hold, SMTP send, and result updates |
| Maintenance Operations | mt-operations-stage-9 | Digest, heartbeat, overdue/unanswered-emergency checks |

Maintenance Triage Demo Tools (mt-demo-tools-stage-9) is the only additional workflow and must remain inactive. It exists for fixture import and rehearsal. The project retains older JSON exports as historical artifacts; they must not be republished as operational workflows.

Generate, import, and publish through the checked-in tooling:

    .\scripts\apply-stage-9.ps1
    .\scripts\validate-stage-9.ps1
    .\scripts\import-stage-9-workflows.ps1 -PublishLiveTriggers -CleanupLegacy

-CleanupLegacy unpublishes legacy workflow snapshots and restarts local n8n as required. In n8n 2.29.10, changing a database active flag alone does not always remove a published trigger snapshot.

## Tenant journeys

### Email and form intake

1. A tenant sends an email to the shared demo mailbox or submits the n8n form.
2. Maintenance Tenant Intake normalizes the message and invokes the Triage Engine.
3. The engine allocates a durable MR-xxxx reference, deduplicates input, records request/event history, calls the model, applies safety rules, and syncs the result to Airtable.
4. The workflow sends exactly one onboarding email with a Telegram deep link. Its subject starts [MT-SYSTEM] so IMAP discards it rather than triaging it as a new tenant message.
5. The link contains a one-time, expiring pairing token. Starting the tenant bot binds that Telegram chat to the existing request; the conversation then continues in Telegram.

The token is intentionally a demo-only convenience. Anyone holding the link can bind the chat. A real implementation needs verified identity binding through a tenant portal, authenticated phone number, property-management system, or comparable mechanism.

The form trigger node is named TenantIntakeForm. Local n8n can double-encode a space-bearing Form Trigger node name, so later changes must preserve a compact name.

### Direct tenant Telegram intake

The current tenant bot is a dedicated conversation channel for one known demo tenant, analogous to a dedicated SMS number. Its profile is configured locally:

| Profile field | Demo value |
|---|---|
| Tenant | Demo Tenant |
| Email | sambhavn8n@gmail.com |
| Property | Maple Court |
| Unit | 2B |

The workflow injects this trusted context into every direct Telegram request before classification. It must not ask the tenant for name, phone number, property, unit, or email. Supporting several tenants later requires separate configured bots/numbers or verified identity binding.

| Tenant action | Expected result |
|---|---|
| Unpaired /start | Welcome message only; no ticket |
| First normal maintenance message | Creates a Telegram-sourced request |
| /new | Prompts for a distinct issue; next non-command message starts it |
| Reply while details are missing | Adds to the same ticket and reruns triage |
| Status/progress/ETA question | One truthful consolidated status response; no new ticket |

### Clarification and status behavior

The bot is not a free-form property manager. Its automatic tenant responses are limited to acknowledgement, deterministic prompts for reported missing information, factual status messages, and a provider-contacted update only after a successful manager-approved SMTP send.

Clarification can request missing issue detail, access permission, pets, and onset where material. It asks no more than three questions in one reply and continues whenever a mapped missing field remains. There is no arbitrary two-message cap. A vague request remains in tenant clarification instead of producing premature manager vendor alerts.

Legal, accommodation, unreadable, prompt-injection, and otherwise human-only cases are routed to manager review. They are not auto-dispatched or given an invented outcome.

Status routing runs before new-ticket creation. It recognizes status, update, progress, ETA, arrival, fixing, resolution, and completion language. A question such as "When will all these issues be resolved?" is not a maintenance request. The reply lists every open NEW_ISSUE request for that chat, up to ten, once each. Before a vendor email succeeds, it says the request is with the manager. Afterwards, it says a maintenance provider has been contacted and an update will follow. It never invents an appointment or arrival time, calls triage, creates a new MR reference, or duplicates a manager approval message.

## Triage engine

### Model contract

The engine calls the OpenAI Responses API through an n8n HTTP Request node. The installed n8n 2.29.10 OpenAI node did not expose the required Responses API and strict schema controls, so HTTP Request is the supported implementation here.

| Use | Model |
|---|---|
| Default classifier and drafter | gpt-5-nano |
| Fallback for unsafe or unstable model behavior | gpt-5.6-luna |

The versioned model contract is kept in:

| File | Content |
|---|---|
| prompts/classification-system.txt | Classification instruction |
| prompts/maintenance-triage.schema.json | Strict classification JSON schema |
| prompts/drafting-system.txt | Vendor draft instruction |
| prompts/maintenance-drafts.schema.json | Strict draft JSON schema |

The classifier produces normalized summary, priority, trade, safety signals, missing information, human-only state, and rationale. Workflows accept either direct structured output or the API wrapper form under output.

### Deterministic boundaries

AI provides language understanding but does not carry the entire safety burden. The engine applies narrow post-model rules where predictable maintenance semantics protect users or reduce unstable classifications.

- Gas smell/leak, active flood or burst pipe, sewage, fire/smoke, sparking, exposed wiring, burning smell, breaker trouble, and material security danger escalate appropriately.
- A contained ceiling drip with a bucket and no electrical, structural, or spreading risk is urgent rather than automatically emergency.
- A squeaky/noisy door hinge is routine unless it affects locking, closing, access, or creates injury/security concern.
- A standalone ceiling or exhaust fan failure with no HVAC/electrical-danger context is ROUTINE and APPLIANCE, not electrical work.
- A water leak, drip, pooling, or wet area at a pipe, sink, faucet/tap, toilet, shower, bathtub, drain, or water heater is PLUMBING, even if the model returns GENERAL. A gas leak remains a safety case and is never routed through this plumbing boundary.
- Accommodation and legal-sensitive matters are human-only. The system suppresses an unsafe automatic draft and routes the manager to review.
- NEEDS_REVIEW is a system state; the model does not own it.

The engine preserves trusted labelled tenant context supplied by intake when the model omits it. It maps a safety signal to a trade only when the model returned UNKNOWN, so ordinary model classification remains primary.

### Priority and age

Priorities and review states are visible to the manager. Age-based rules create OVERDUE board/digest status for overdue routine or urgent requests. Age alone must never create an emergency phone alert. This demo does not dispatch a vendor automatically.

## Manager journey and vendor dispatch

For a complete, non-human-only maintenance request, the engine reads active Airtable vendors and finds candidates matching the request's property and trade. It selects up to three candidates, ordered by numeric vendor priority. A ticket is not eligible for vendor buttons while missing_info is non-empty, it is human-only, its priority is NEEDS_REVIEW, it is fixture/import output, or it otherwise needs review.

The manager Telegram message contains the MR reference, priority, trade, property/unit, issue summary, a natural property-office vendor email preview, and only actual vendor buttons plus Hold. The keyboard has fixed variants for zero, one, two, and three candidates. It never renders placeholder buttons. Zero matches and manager-review cases show Hold only. A no-match ticket is NEEDS_VENDOR_ASSIGNMENT and sends no vendor email.

Selecting a vendor is explicit one-tap approval. Hold sends no email.

Before SMTP, the Manager Desk inserts a vendor-send attempt. triage.vendor_send_attempts has a unique ticket_id, so only the first valid callback can claim a ticket. A repeated Telegram tap cannot create a second send.

On SMTP success, the workflow writes SENT to Postgres/Airtable then tells the tenant that a maintenance provider has been contacted and an update will follow. On failure it records FAILED and shows the result to the manager/Airtable; the tenant does not receive a provider-contacted update.

Every system-generated email uses an IMAP-exclusion subject prefix:

| Email type | Subject prefix |
|---|---|
| Telegram onboarding | [MT-SYSTEM] |
| Vendor dispatch | [MT-SYSTEM][VENDOR] |

Inbound normalization treats prefixes as case-insensitive even when email clients add Re: or whitespace. This prevents a shared controlled mailbox from re-ingesting its own onboarding or vendor mail and replaying approval loops.

## Postgres data model

All application tables use the triage schema.

| Table | Purpose |
|---|---|
| tickets | Authoritative request and triage state |
| events | Audit/event history |
| feedback | Review/training feedback |
| config | Runtime configuration by category/key |
| units | Local unit roster |
| import_batches, import_items | Fixture and follow-up import state |
| tenant_chats | Telegram chat bindings and routing state |
| tenant_pairing_tokens | Expiring one-time email/form Telegram pairing tokens |
| ticket_messages | Per-ticket inbound/outbound conversation messages |
| ticket_vendor_candidates | Matched vendor candidates and order |
| vendor_send_attempts | Explicit approval claim and send result |
| airtable_roster_links | Durable Airtable record IDs for linked roster values |

Tickets have two identities: an internal database identity used by callbacks/foreign keys, and a visible MR-xxxx reference allocated through triage.next_ticket_ref() and triage.ticket_ref_seq. The allocator skips collisions, which protects creation after a data-only snapshot restore. Restore tooling realigns the visible sequence to the highest restored reference.

Do not restart the internal ticket identity sequence during reset. Old Telegram messages contain internal callback identifiers; reusing one could let an old button act on a later ticket. Reset only the visible MR reference sequence.

ticket_messages is unique across channel, direction, and external_message_id. vendor_send_attempts is unique per ticket. These two constraints are the core protection against duplicated inbound messages and duplicated vendor sends.

## Airtable workspace

Airtable is a typed relational mirror and the demo roster source.

| Table | Primary field | Important typed fields |
|---|---|---|
| Requests | Reference | Status/priority/source/trade/vendor-status selects; linked tenant and vendors; email; property; unit; long summary; missing-info multi-select; human-only checkbox; Telegram ID; timestamps |
| Conversations | Conversation | Linked request; direction/channel/intent/delivery-state selects; long body; external ID; timestamp |
| Tenant Roster | Tenant name | Email; property; unit; Telegram ID; active checkbox; linked requests |
| Vendors | Vendor name | Email; phone; multi-select trades/properties; numeric priority; active checkbox; suggested/selected request links |

Sync writes select values, booleans, ISO date-time values, and linked-record ID arrays. It must omit a missing select value instead of writing an empty string, because Airtable can reject that with HTTP 422. For an older typed table that lacks a display-only choice, sync filters the unsupported choice rather than breaking the record write.

Airtable's public schema API cannot delete a table, convert field types, amend select choices in this environment, or create native created/last-modified-time fields. The demo therefore uses Postgres-backed Created At and Last Synced fields. To replace old text-only tables, manually delete only Requests, Conversations, Tenant Roster, and Vendors from the synthetic demo base, then run:

    $env:AIRTABLE_PAT = "local-token-not-for-source-control"
    .\scripts\rebuild-stage-9-airtable.ps1 -BaseId appYourBaseId

The guarded rebuild reseeds synthetic rosters, clears local Airtable links, creates typed tables, and replays Postgres requests/conversations. Never use it against a client or production base.

## Configuration and credentials

No secret belongs in workflow JSON, Git, screenshots, or chat. Use local .env for runtime values and named n8n credentials for integrations.

| Credential name | Use |
|---|---|
| maintenance-triage-postgres-local | Postgres |
| maintenance-triage-openai | OpenAI Responses API |
| maintenance-triage-demo-imap-domain | Gmail IMAP intake |
| maintenance-triage-demo-smtp-domain | Gmail SMTP onboarding/vendor sends |
| maintenance-triage-telegram-bot | Manager Telegram bot |
| maintenance-triage-tenant-telegram-bot | Tenant Telegram bot |
| maintenance-triage-airtable | Airtable workspace and roster |

triage.config includes sla_minutes, overdue_days, escalate_after, contacts, company, quiet_hours, limits, runtime_state, outbound_email, ingestion, digest, heartbeat, tenant_telegram, airtable, and system_mail. Daily digest and heartbeat behavior are implemented but disabled by default to avoid surprise messages.

## Operations workflow

Maintenance Operations owns:
- a manually runnable/scheduled daily email digest of open emergencies, breached targets, overdue work, and previous-day counts;
- a fifteen-minute heartbeat that alerts only the operator Telegram chat if ingestion is silent past the configured threshold; and
- unanswered-emergency and aging checks.

Heartbeat stores a baseline and last-alert timestamp and suppresses repeated alerts. It is not a tenant feature. Schedules remain disabled by config in a clean demo state.

## Validation and rehearsal

Run the Stage 9 validator after implementation changes:

    .\scripts\validate-stage-9.ps1
    .\scripts\validate-stage-9.ps1 -LivePrerequisites

The structural validator compiles helpers, generates/parses workflow JSON, runs the Stage 9 conversation-routing regression test, validates Docker Compose, applies/checks migrations, and checks configuration/workflow contracts. Live-prerequisite mode verifies Airtable and tenant-bot configuration are not placeholders.

Fixture-first rehearsal is the call-readiness gate:

    .\scripts\run-stage-9-rehearsal.ps1 -Runs 5

It executes six live-demo fixtures from clean state for five runs and must not send real Telegram or SMTP messages. A separate explicit smoke check must cover Gmail IMAP, form submission, direct tenant Telegram, manager selection, Airtable writes, one SMTP send, and the post-send tenant update.

| Measurement | Recorded demo result |
|---|---|
| Fixture rehearsal | 5 clean runs x 6 fixtures = 30 priority checks |
| Expected-priority matches | 30/30 during Stage 8 rehearsal |
| External sends in fixture rehearsal | Zero tenant messages and zero vendor-send attempts |
| Stage 3 six-fixture classifier result | 6/6 priority matches; zero under/over escalations and missed safety signals |
| Stage 3 average classify + draft latency | 10,895.3 ms |
| Stage 3 estimated cost per fixture | USD 0.003130 |

These figures apply to the recorded narrow demo set. Do not claim complete 30-fixture hardening or production-grade model reliability: the broader 30-fixture x three-run Stage 3 exercise had safety misses/under-escalations and remains deferred work.

## Reset, snapshots, and recovery

Before a demo, reset state rather than deleting one ticket:

    .\scripts\reset-demo.ps1
    .\scripts\reset-demo.ps1 -Apply
    .\scripts\save-stage-9-demo-snapshot.ps1 -Name clean
    .\scripts\restore-stage-9-demo-snapshot.ps1 -Name clean

reset-demo.ps1 is dry-run by default. With -Apply, it clears Airtable Conversations before Airtable Requests, then clears local tickets, events, feedback, imports, conversation state, pairing tokens, vendor attempts, runtime counters, generated attachments/import artifacts, and the visible MR sequence. It preserves Airtable tenant/vendor rosters, local configuration/units, workflow definitions, n8n credentials, and secrets. -LocalOnly deliberately leaves Airtable records untouched.

External Telegram/email history is not deleted. That is why internal Postgres IDs never restart.

For failed Airtable sync, Postgres remains correct. Repair Airtable credential/schema/config and replay durable state. For SMTP failure, leave the failed attempt visible to the manager and do not tell the tenant a provider was contacted. For tunnel failure, obtain a fresh public URL, update N8N_WEBHOOK_URL, restart n8n, and republish Telegram triggers.

## Safety, privacy, and limits

The project uses synthetic rosters and a controlled mailbox only. Demo vendor and onboarding email goes to sambhavn8n@gmail.com. No credentials, app passwords, bot tokens, Airtable PATs, external record exports, snapshots, or generated operational state are committed.

The system is advisory-only in the important sense: it never automatically dispatches/selects a vendor, confirms an appointment, closes a ticket, or promises an ETA. It may acknowledge a tenant, ask deterministic clarification questions, or send a factual status/provider-contacted update. Vendor email remains a manager action.

Before production, implement verified tenant identity, PMS/work-order integration, real vendor onboarding and appointment state, full fixture hardening, production authentication/observability/backups/retention, security review, and client-owned hosting.

## Source map for maintainers

| Need | Primary files |
|---|---|
| Current decisions and validation history | progress-notes.md |
| Staged scope | build-plan.md; maintenance-triage-demo-build-plan.md |
| Repository rules/gotchas | AGENTS.md |
| Stage 9 schema | db/postgres/008-stage-9-telegram-airtable.sql |
| Earlier schema/config | db/postgres/001-create-triage-schema.sql through 007-stage-8-hardening.sql |
| Workflow generator | scripts/build-stage-9-workflows.py |
| Workflow importer/publisher | scripts/import-stage-9-workflows.ps1 |
| Stage 9 validator | scripts/validate-stage-9.ps1 |
| Conversation regression test | scripts/test-stage-9-conversation-routing.js |
| Airtable tools | scripts/setup-stage-9-airtable.py; scripts/rebuild-stage-9-airtable.ps1; scripts/sync-stage-9-airtable.py |
| Reset/snapshot tools | scripts/reset-demo.ps1; scripts/reset-stage-9-demo-state.ps1; scripts/save-stage-9-demo-snapshot.ps1; scripts/restore-stage-9-demo-snapshot.ps1 |
| Prompt/schema contract | prompts/ |
| User-facing documentation | docs/operating-guide.md; docs/how-the-system-works.md |

When changing behavior, update the generator rather than hand-editing a generated n8n export, regenerate/import workflows, run Stage 9 validation and the relevant rehearsal, and record the decision/result in progress-notes.md.
