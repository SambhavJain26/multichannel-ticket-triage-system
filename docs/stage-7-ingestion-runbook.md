# Stage 7 Ingestion Runbook

Stage 7 uses one real Gmail or Google Workspace mailbox for both intake and approved replies. n8n needs two credentials because IMAP and SMTP are separate credential types:

- `maintenance-triage-demo-imap-domain`
- `maintenance-triage-demo-smtp-domain`

Do not paste the app password into chat or commit it. Import it locally:

```powershell
.\scripts\import-demo-mail-credentials.ps1 -EmailAddress "maintenance@your-domain.com"
```

The script prompts for the app password securely, creates both n8n credentials, and updates `triage.config.outbound_email` to `live`.

## Import Workflows

```powershell
.\scripts\apply-stage-7.ps1
.\scripts\import-stage-7-workflows.ps1 -PublishLiveTriggers
.\scripts\check-stage-7-live-prereqs.ps1
```

Use `-PublishLiveTriggers` only after the real IMAP and SMTP credentials exist. The import bridge and fixture workflow can be published without live mailbox credentials.

Before publishing the live IMAP trigger, use a dedicated demo mailbox or archive unrelated unread inbox mail. The trigger can ingest existing unread mail immediately after activation.

For live Telegram alerts from the local demo, set the board URL to the current HTTPS tunnel before sending test mail:

```powershell
docker compose exec -T postgres psql -U maintenance_triage -d maintenance_triage -c "update triage.config set value = jsonb_set(value, '{public_base_url}', to_jsonb('https://your-current-tunnel.trycloudflare.com'::text), true) where key = 'board';"
```

## Live Email Test

1. Send a maintenance email from another inbox or a phone to the demo mailbox.
2. Confirm a new card appears on `http://localhost:5678/webhook/board?t=<board-token>`.
3. Open the card and confirm source is `email`, unit roster status is visible, and attachments show as chips if attached.
4. Approve the Telegram reply only when the recipient is a controlled test address.
5. Confirm the approved reply is sent through `maintenance-triage-demo-smtp-domain`.

## Live Form Test

In local n8n `2.29.10`, the imported Form Trigger currently registers under the workflow and node name:

```text
http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue
```

If the form returns 404 after import, query `webhook_entity` and use the registered `/form/...` path.

## Batch Import

Drop `.eml` and `.txt` samples into an ignored local folder, then run:

```powershell
python .\scripts\run-stage-7-batch-import.py .\data\prospect-samples --label "prospect-week"
```

The importer writes:

- `data/import-batches/<batch-id>/report.html`
- `data/import-batches/<batch-id>/review.csv`

The first report does not claim accuracy. After a human fills in corrected labels in `review.csv`, pass that file back with `--reviewed-csv` to calculate misses.
