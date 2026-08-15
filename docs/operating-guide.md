# Operating Guide

This guide runs the Stage 9 Telegram and Airtable demo. It assumes the local Docker stack
and the existing Gmail IMAP/SMTP, OpenAI, Postgres, Airtable, manager Telegram, and tenant
Telegram credentials are already working. It is a local synthetic-data demo, not a
production property-management deployment.

## Before a call

1. Start the local services and confirm n8n is available at `http://localhost:5678`.
2. Start a fresh HTTPS tunnel and update `N8N_WEBHOOK_URL` before publishing Telegram
   trigger workflows. A quick-tunnel URL is temporary.
3. In n8n, confirm that exactly five operational workflows are active: Triage Engine,
   Tenant Intake, Tenant Telegram, Manager Desk, and Operations. `Maintenance Triage Demo
   Tools` must remain inactive.
4. Run the guarded reset, apply it only after reviewing its counts, then create or restore a
   clean snapshot. This removes old demo tickets such as `MR-0002` from both Postgres and
   the visible Airtable workspace.
5. Open the Airtable base before beginning the demo. It is the manager workspace; Postgres
   remains the authoritative automation record.

```powershell
.\scripts\start-local.ps1
.\scripts\reset-demo.ps1
.\scripts\reset-demo.ps1 -Apply
.\scripts\save-stage-9-demo-snapshot.ps1 -Name clean
```

## One-time setup

### 1. Create the tenant Telegram bot

Create a separate bot with BotFather. In n8n, create a Telegram credential named
`maintenance-triage-tenant-telegram-bot`. Do not reuse the manager bot credential.

### 2. Create Airtable workspace data

Create a local Airtable personal access token with the schema and record read/write scopes
for the base, then set it only in the current terminal:

```powershell
$env:AIRTABLE_PAT = "your-local-token"
python .\scripts\setup-stage-9-airtable.py --base-id appYourBaseId --apply
```

For the existing text-only demo tables, delete only `Requests`, `Conversations`, `Tenant
Roster`, and `Vendors` in the Airtable UI first. Airtable's public API cannot delete or
convert existing table schemas. Then rebuild and replay the local demo state:

```powershell
.\scripts\rebuild-stage-9-airtable.ps1 -BaseId appYourBaseId
```

The rebuild creates typed linked records, single/multiple selects, email, phone, checkbox,
number, long-text, date, lookup, and audit-time fields. It leaves any other Airtable tables
untouched and re-syncs the local Postgres demo tickets and conversation history.

Create an n8n Airtable credential named `maintenance-triage-airtable` using the same token.
The setup script creates `Requests`, `Conversations`, `Tenant Roster`, and `Vendors`, then
seeds synthetic tenants and vendors. Every synthetic vendor points to
`sambhavn8n@gmail.com` for controlled testing.

### 3. Save local identifiers

Use the Airtable base URL and the tenant bot username, without `@`:

```powershell
.\scripts\configure-stage-9-airtable.ps1 `
  -BaseId appYourBaseId `
  -BaseUrl https://airtable.com/appYourBaseId `
  -TenantBotUsername YourTenantBot
```

### 4. Publish Stage 9

Telegram triggers need a current public HTTPS `N8N_WEBHOOK_URL`. Start a tunnel, save its
URL in the local `.env`, restart n8n, then run:

```powershell
.\scripts\apply-stage-9.ps1
.\scripts\validate-stage-9.ps1 -LivePrerequisites
.\scripts\import-stage-9-workflows.ps1 -PublishLiveTriggers -CleanupLegacy
```

`-CleanupLegacy` deactivates the old board, separate alert/approval, Stage 7 intake, and
Stage 8 schedule workflows. It does not delete their exports, so rollback remains possible.
The active workflows are then:

1. Maintenance Triage Engine
2. Maintenance Tenant Intake
3. Maintenance Tenant Telegram
4. Maintenance Manager Desk
5. Maintenance Operations

The inactive `Maintenance Triage Demo Tools` workflow is only for rehearsals.

## Run the demo

### Email or form request

**Do:** Send a maintenance email to the shared mailbox or submit the form from the
`Maintenance Tenant Intake` workflow.

**Expect:** Airtable receives a request record. The controlled Gmail inbox receives one
`[MT-SYSTEM]` onboarding email with a Telegram deep link.

**Verify:** Open the link, start the tenant bot, and confirm it replies with either a
receipt or the required clarification questions. System-marked onboarding and vendor emails
are intentionally ignored by IMAP, so they cannot create a loop. Both email types use a
subject beginning `[MT-SYSTEM]`.

### Direct tenant Telegram request

**Do:** Message the tenant bot with a maintenance issue. An unpaired `/start` only opens
the conversation and does not create a ticket. Use `/new`, then send the next message as a
second unrelated issue.

**Expect:** A generic opening is kept as preliminary conversation and receives a focused
prompt for the actual symptom; it creates no request or manager alert. Once the tenant
names a concrete issue, the bot creates one request using the accumulated conversation,
asks only the details required for classification, and keeps replies on the same active
ticket.

**Verify:** Check Airtable `Requests` and `Conversations`. The current tenant bot is a
dedicated bot for the configured demo tenant, so it automatically supplies that tenant's
name, property, unit, and email to triage. It does not ask for a phone number or location.
A vague request keeps receiving focused issue or access prompts until the required details
are supplied. Once clear, the manager receives the vendor-choice alert; sensitive or
human-only requests receive the Hold-only manager review alert.

### Tenant status question

**Do:** In an open tenant conversation, ask "When will all these issues be resolved?"

**Expect:** The bot sends one message listing every open request in the chat. Before vendor
contact, it says the request is with the manager. After vendor email succeeds, it says a
provider was contacted and an update will follow.

**Verify:** Each request appears once. The bot must not state or imply an unconfirmed
arrival time, create another request, or send another manager approval message.

### Manager vendor selection

**Do:** Open the manager Telegram alert for a complete request.

**Expect:** The alert shows the request summary, proposed vendor email, only the active
matching vendor buttons, and Hold. There are never empty placeholder buttons.

**Verify:** Tap one vendor button once. A single email is sent to
`sambhavn8n@gmail.com`, Airtable records the selected vendor and send state, and the tenant
bot receives the provider-contacted update. A second tap reports that the request is already
handled and does not send again.

### No vendor and sensitive requests

**Do:** Remove matching vendors from Airtable, submit an accommodation/legal request, or
leave the required clarification details unanswered.

**Expect:** The manager receives a review path, but there is no vendor-send button that can
send mail.

**Verify:** Airtable shows `NEEDS_VENDOR_ASSIGNMENT` or the human-review state. No tenant
ETA or vendor email is sent.

## Reset and validation

Run structural validation after code changes:

```powershell
.\scripts\validate-stage-9.ps1
```

Run the five-pass fixture rehearsal after Stage 9 workflows are published:

```powershell
.\scripts\run-stage-9-rehearsal.ps1 -Runs 5
```

Clear local operational data before a call:

```powershell
.\scripts\reset-demo.ps1
# Review the reported local and Airtable record counts, then apply:
.\scripts\reset-demo.ps1 -Apply
.\scripts\save-stage-9-demo-snapshot.ps1 -Name clean
```

Restore the clean state between calls:

```powershell
.\scripts\restore-stage-9-demo-snapshot.ps1 -Name clean
```

The complete reset clears Postgres tickets, conversations, pairing tokens, vendor-send
attempts, event history, generated local artifacts, Airtable Requests and Airtable
Conversations. It resets the next reference to `MR-0001`. It preserves Airtable Tenant
Roster and Vendors, local units and configuration, credentials, workflow definitions, and
all secrets. The command is a dry run unless `-Apply` is supplied. Use `-LocalOnly` only
when Airtable should deliberately retain its current records. Previously delivered Telegram
and email messages remain visible in those external services. Internal ticket IDs are not
reused, so old manager approval buttons cannot affect requests created after the reset.

## Failure checks

- Airtable unavailable: Postgres still records the request and manager action. Fix the
  Airtable credential/configuration, then re-run the manager workflow for that ticket.
- Tenant bot unavailable: email/form requests remain in Airtable awaiting Telegram link;
  no tenant reply is silently lost.
- Vendor SMTP failure: Airtable and the manager alert show failure. The tenant does not get
  the provider-contacted update.
- Duplicate vendor selection: Postgres accepts only the first claim for a ticket.
- IMAP self-email loop: onboarding and vendor-dispatch emails use a subject starting
  `[MT-SYSTEM]`; they are marked read and discarded before triage.
