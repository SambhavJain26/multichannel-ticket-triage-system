# Stage 9 Telegram and Airtable Runbook

Stage 9 replaces the custom board with Airtable, adds a separate tenant Telegram bot, and
changes manager approval from tenant email replies to vendor-email selection.

## Prerequisites

- Existing Gmail IMAP/SMTP, OpenAI, Postgres, and manager Telegram credentials in n8n.
- A separate tenant Telegram bot credential named `maintenance-triage-tenant-telegram-bot`.
- An Airtable credential named `maintenance-triage-airtable`.
- A current public HTTPS `N8N_WEBHOOK_URL` before activating either Telegram trigger.

## Apply

```powershell
.\scripts\apply-stage-9.ps1
.\scripts\validate-stage-9.ps1
```

Create and seed the Airtable base, configure its IDs locally, then verify configuration:

```powershell
$env:AIRTABLE_PAT = "your-local-token"
python .\scripts\setup-stage-9-airtable.py --base-id appYourBaseId --apply
.\scripts\configure-stage-9-airtable.ps1 -BaseId appYourBaseId -BaseUrl https://airtable.com/appYourBaseId -TenantBotUsername YourTenantBot
.\scripts\validate-stage-9.ps1 -LivePrerequisites
```

Publish only after the credentials and tunnel are ready:

```powershell
.\scripts\import-stage-9-workflows.ps1 -PublishLiveTriggers -CleanupLegacy
```

Run the fixture-first rehearsal after the Triage Engine is published. The demo-tools
workflow remains inactive and contains only the six synthetic fixture messages:

```powershell
.\scripts\run-stage-9-rehearsal.ps1 -Runs 5
```

## Live smoke sequence

1. Send a controlled request to the Gmail mailbox.
2. Confirm the `[MT-SYSTEM]` onboarding message arrives at `sambhavn8n@gmail.com`.
3. Open the deep link and start the tenant bot.
4. Confirm the Airtable request row, conversation history, and manager vendor-selection alert.
5. Choose a synthetic vendor once and verify one controlled SMTP email and one tenant Telegram update.
6. Ask for an ETA and verify the bot does not invent one.

Do not use a real tenant or vendor during this demo. The pairing link is deliberately
unverified and is not production-ready identity handling.
