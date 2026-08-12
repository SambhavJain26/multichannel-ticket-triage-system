# Operating Guide

This guide runs the Stage 9 Telegram and Airtable demo. It assumes the local Docker stack
and the existing Gmail IMAP/SMTP, OpenAI, Postgres, and manager Telegram credentials are
already working.

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
are intentionally ignored by IMAP, so they cannot create a loop.

### Direct tenant Telegram request

**Do:** Message the tenant bot with a maintenance issue. An unpaired `/start` only opens
the conversation and does not create a ticket. Use `/new`, then send the next message as a
second unrelated issue.

**Expect:** The bot records the request, asks only the details required for classification,
and keeps replies on the same active ticket.

**Verify:** Check Airtable `Requests` and `Conversations`. A vague request receives at most
two clarification rounds before the manager review state and a Hold-only manager alert.

### Tenant status question

**Do:** In an open tenant conversation, ask "When is someone coming?"

**Expect:** Before vendor contact, the bot says the request is escalated to the manager.
After vendor email succeeds, it says a provider was contacted and an update will follow.

**Verify:** It must not state or imply an unconfirmed arrival time, and it must not create a
second request.

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
.\scripts\reset-stage-9-demo-state.ps1
.\scripts\save-stage-9-demo-snapshot.ps1 -Name clean
```

Restore the clean state between calls:

```powershell
.\scripts\restore-stage-9-demo-snapshot.ps1 -Name clean
```

These commands clear only local demo tickets, conversation rows, pairing tokens, vendor-send
attempts, event history, and generated local artifacts. They preserve Airtable configuration,
unit roster, credentials, workflow definitions, and all secrets.

## Failure checks

- Airtable unavailable: Postgres still records the request and manager action. Fix the
  Airtable credential/configuration, then re-run the manager workflow for that ticket.
- Tenant bot unavailable: email/form requests remain in Airtable awaiting Telegram link;
  no tenant reply is silently lost.
- Vendor SMTP failure: Airtable and the manager alert show failure. The tenant does not get
  the provider-contacted update.
- Duplicate vendor selection: Postgres accepts only the first claim for a ticket.
- IMAP self-email loop: requests with a subject starting `[MT-SYSTEM]` are marked read and
  discarded before triage.
