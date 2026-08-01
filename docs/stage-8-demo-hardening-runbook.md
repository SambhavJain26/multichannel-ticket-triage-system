# Stage 8 Demo Hardening Runbook

Stage 8 makes the local demo repeatable. The primary rehearsal path is fixture-first, because it avoids mailbox timing and real notification noise. Live Gmail and Telegram remain separate smoke checks.

## Apply And Import

```powershell
.\scripts\apply-stage-8.ps1
.\scripts\import-stage-8-workflows.ps1 -PublishSchedules
```

The digest and heartbeat workflows can be active safely because `triage.config.digest.enabled` and `triage.config.heartbeat.enabled` default to `false`.

## Clean Demo State

Use this before every rehearsal or prospect call:

```powershell
.\scripts\reset-stage-8-demo-state.ps1
```

This clears local operational demo rows and generated local artifacts:

- `triage.tickets`
- `triage.events`
- `triage.feedback`
- `triage.import_batches`
- `triage.import_items`
- `data/attachments`
- `data/import-batches`

It preserves durable config, unit roster, n8n credentials, workflow definitions, and the board token.

## Snapshot And Restore

Create a clean snapshot after reset:

```powershell
.\scripts\reset-stage-8-demo-state.ps1
.\scripts\save-stage-8-demo-snapshot.ps1 -Name clean
```

Restore it between calls:

```powershell
.\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean
```

Snapshots are written under ignored `data/demo-snapshots/` and must not be committed.

Use snapshots for clean local demo state unless you have tested a restore of the exact populated state. The data-only dump can warn about the self-referential ticket thread foreign key; clean reset/save/restore is the supported call-prep path.

## Fixture Rehearsal

Run the five-pass fixture-first rehearsal:

```powershell
.\scripts\run-stage-8-rehearsal.ps1 -Runs 5
```

The rehearsal resets local state each run, fires the six live-demo fixtures, verifies stable priorities, checks roster matching, confirms no real Telegram alert was sent during fixture mode, and checks board HTTP 200.

Current measured result on 2026-08-01: five clean runs passed with 30/30 expected priorities, zero real Telegram sends, two expected safety overrides per run, roster checks, and board HTTP 200.

## Digest And Heartbeat

Digest is email-based. Heartbeat alerts the operator Telegram chat, not the client.

Run structural validation without live sends:

```powershell
.\scripts\validate-stage-8.ps1
```

Run one live digest email and one live heartbeat Telegram:

```powershell
.\scripts\validate-stage-8.ps1 -LiveNotifications
```

Run the full destructive rehearsal too:

```powershell
.\scripts\validate-stage-8.ps1 -LiveNotifications -RunRehearsal
```

## Live Smoke

After fixture rehearsal passes:

1. Confirm the current tunnel URL is in `triage.config.board.public_base_url`.
2. Confirm the Gmail inbox has no unrelated unread mail.
3. Send one controlled maintenance email to the demo mailbox.
4. Confirm the board card appears, roster matching is visible, and Telegram alert lands.
5. Reset local state before any prospect call if the smoke test created setup artifacts.
