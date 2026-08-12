# Stage 9 Telegram and Airtable Runbook

Stage 9 replaces the custom board with Airtable, adds a separate tenant Telegram bot, and
changes manager approval from tenant email replies to vendor-email selection.

## Prerequisites

- Existing Gmail IMAP/SMTP, OpenAI, Postgres, and manager Telegram credentials in n8n.
- A separate tenant Telegram bot credential named `maintenance-triage-tenant-telegram-bot`.
- An Airtable credential named `maintenance-triage-airtable`.
- A current public HTTPS `N8N_WEBHOOK_URL` before activating either Telegram trigger.

The Airtable PAT must be granted access to the `Maintenance Triage Demo` base and these scopes:
`data.records:read`, `data.records:write`, `schema.bases:read`, and `schema.bases:write`.
The Airtable account that creates the token must have Creator-level access to that base.

The Stage 9 importer resolves n8n credential IDs from these names at import time. Do not edit workflow JSON to add credential IDs or secrets.

The Stage 9 migration is safe to rerun: it adds only missing configuration defaults and preserves any configured Airtable base or tenant bot values.

## Apply

```powershell
.\scripts\apply-stage-9.ps1
.\scripts\validate-stage-9.ps1
```

Create and seed the Airtable base, configure its IDs locally, then verify configuration:

```powershell
# Set AIRTABLE_PAT=your-local-token in the ignored .env file. Do not send this token in chat.
# Use the same token in the n8n Airtable credential.
python .\scripts\setup-stage-9-airtable.py --base-id appYourBaseId --apply
.\scripts\configure-stage-9-airtable.ps1 -BaseId appYourBaseId -BaseUrl https://airtable.com/appYourBaseId -TenantBotUsername YourTenantBot
.\scripts\validate-stage-9.ps1 -LivePrerequisites
```

Publish only after the credentials and tunnel are ready:

```powershell
.\scripts\start-cloudflare-tunnel.ps1
# In a second terminal, set the printed HTTPS URL as N8N_WEBHOOK_URL in .env,
# then run: docker compose up -d --force-recreate n8n
.\scripts\import-stage-9-workflows.ps1 -PublishLiveTriggers -CleanupLegacy
```

Run the fixture-first rehearsal after the Triage Engine is published. The demo-tools
workflow remains inactive and contains only the six synthetic fixture messages:

```powershell
.\scripts\run-stage-9-rehearsal.ps1 -Runs 5
```

## Live smoke sequence

1. Send a controlled request to the Gmail mailbox.
2. Or submit the local form at `/form/mt-tenant-intake-stage-9/tenantintakeform/report-issue`, selecting the property so vendor matching can apply property and trade together.
3. Confirm the `[MT-SYSTEM]` onboarding message arrives at `sambhavn8n@gmail.com`.
4. Open the deep link and start the tenant bot.
5. Confirm the Airtable request row, conversation history, and manager vendor-selection alert.
6. Choose a synthetic vendor once and verify one controlled SMTP email and one tenant Telegram update.
7. Ask for an ETA and verify the bot does not invent one.

Do not use a real tenant or vendor during this demo. The pairing link is deliberately
unverified and is not production-ready identity handling.

## Forget previous demo requests

Preview the exact local and Airtable record counts without deleting anything:

```powershell
.\scripts\reset-demo.ps1
```

Then perform the reset:

```powershell
.\scripts\reset-demo.ps1 -Apply
```

This clears only operational demo state and resets the next reference to `MR-0001`. It
preserves Tenant Roster, Vendors, configuration, credentials, workflow definitions, and
secrets. Use `-LocalOnly` only when the Airtable request history should deliberately remain.
Previously delivered Telegram/email messages are not erased, but old manager approval
buttons cannot affect future tickets because internal ticket IDs are never reused.
