[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Default
    )

    if (-not (Test-Path -LiteralPath ".env")) {
        return $Default
    }

    $line = Get-Content -LiteralPath ".env" |
        Where-Object { $_ -match "^\s*$([regex]::Escape($Name))=" } |
        Select-Object -First 1

    if (-not $line) {
        return $Default
    }

    return ($line -replace "^\s*$([regex]::Escape($Name))=", "").Trim().Trim('"').Trim("'")
}

function Invoke-ScalarSql {
    param(
        [Parameter(Mandatory = $true)][string]$Sql,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    $result = docker compose exec -T postgres psql `
        -U $PostgresUser `
        -d $PostgresDb `
        -At `
        -v ON_ERROR_STOP=1 `
        -c $Sql

    return (($result | Select-Object -First 1) -as [string]).Trim()
}

function Assert-Sql {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Sql,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    $actual = Invoke-ScalarSql -Sql $Sql -PostgresUser $PostgresUser -PostgresDb $PostgresDb
    if ($actual -ne $Expected) {
        throw "$Label expected $Expected, got $actual"
    }
    Write-Host "OK: $Label = $actual"
}

function Get-GreenMailSubjectCount {
    param(
        [Parameter(Mandatory = $true)][string]$SubjectNeedle
    )

    $script = @'
import imaplib
import sys

subject = sys.argv[1]
with imaplib.IMAP4("127.0.0.1", 3143, timeout=10) as imap:
    imap.login("maintenance@example.test", "greenmail-local-password")
    imap.select("INBOX")
    status, data = imap.search(None, "SUBJECT", f'"{subject}"')
    if status != "OK" or not data or not data[0]:
        print(0)
    else:
        print(len(data[0].split()))
'@

    $count = $script | python - $SubjectNeedle
    if ($LASTEXITCODE -ne 0) {
        throw "Could not query GreenMail IMAP for subject '$SubjectNeedle'."
    }
    return [int](($count | Select-Object -First 1) -as [string]).Trim()
}

function Invoke-BoardRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Url
    )

    $bodyPath = Join-Path $env:TEMP ("maintenance-triage-stage-6-board-" + [guid]::NewGuid().ToString() + ".html")
    try {
        $status = & curl.exe -sS -o $bodyPath -w "%{http_code}" $Url
        if ($LASTEXITCODE -ne 0) {
            throw "curl failed for $Url"
        }
        return @{
            Status = (($status | Select-Object -First 1) -as [string]).Trim()
            Body = Get-Content -Raw -LiteralPath $bodyPath
        }
    }
    finally {
        if (Test-Path -LiteralPath $bodyPath) {
            Remove-Item -LiteralPath $bodyPath -Force
        }
    }
}

function Assert-Contains {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Body,
        [Parameter(Mandatory = $true)][string]$Needle
    )

    if (-not $Body.Contains($Needle)) {
        throw "$Label did not contain expected text: $Needle"
    }
    Write-Host "OK: $Label contains '$Needle'"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $n8nPort = Get-DotEnvValue -Name "N8N_PORT" -Default "5678"

    Write-Host "Validating generated Stage 6 workflow JSON..."
    python .\scripts\build-stage-6-workflows.py | Out-Host
    @(
        "workflows\maintenance-triage-alert-dispatch.json",
        "workflows\maintenance-triage-approval-action.json",
        "workflows\maintenance-triage-telegram-callback.json",
        "workflows\maintenance-triage-emergency-escalation.json",
        "workflows\maintenance-triage-stage-6-driver.json"
    ) | ForEach-Object {
        Get-Content -Raw $_ | ConvertFrom-Json | Out-Null
    }

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Applying Stage 4, 5, and 6 database support..."
    .\scripts\apply-stage-4.ps1
    .\scripts\apply-stage-5.ps1
    .\scripts\apply-stage-6.ps1

    Assert-Sql -Label "Stage 6 outbound columns" -Sql "select count(*) from information_schema.columns where table_schema='triage' and table_name='tickets' and column_name in ('telegram_chat_id','outbound_to','outbound_sent_at','last_alert_error');" -Expected "4" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "outbound email config" -Sql "select count(*) from triage.config where key = 'outbound_email' and value->>'mode' = 'test_only' and value->>'test_to' = 'maintenance@example.test';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Stage 6 indexes" -Sql "select count(*) from pg_indexes where schemaname='triage' and indexname in ('tickets_stage_6_emergency_escalation_idx','tickets_stage_6_approval_guard_idx','events_stage_6_alert_rate_idx');" -Expected "3" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Checking required n8n credentials..."
    Assert-Sql -Label "Postgres credential" -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-postgres-local';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Telegram credential" -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-telegram-bot';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "SMTP credential" -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-greenmail-smtp-local';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Resetting local ticket/event/feedback data for Stage 6 validation..."
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "truncate triage.feedback, triage.events, triage.tickets restart identity; alter sequence triage.ticket_ref_seq restart with 1; update triage.config set value = value || jsonb_build_object('consecutive_model_failures', 0, 'degraded_until', null, 'degraded_alerted_at', null, 'llm_calls_today', 0, 'llm_call_day', null) where key = 'runtime_state';" | Out-Host

    Write-Host "Importing Stage 4, Stage 5, and Stage 6 workflows..."
    .\scripts\import-stage-4-workflows.ps1
    .\scripts\import-stage-5-board.ps1
    .\scripts\import-stage-6-workflows.ps1

    $stage4DriverId = Invoke-ScalarSql -Sql "select id from workflow_entity where name = 'Maintenance Triage Stage 4 Driver' limit 1;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if (-not $stage4DriverId) {
        throw "Stage 4 driver workflow was not imported."
    }

    Write-Host "Executing Stage 4 driver workflow $stage4DriverId..."
    docker compose run --rm --no-deps -T n8n execute --id=$stage4DriverId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 4 driver workflow execution failed with exit code $LASTEXITCODE."
    }

    Assert-Sql -Label "Stage 4 fixture tickets" -Sql "select count(*) from triage.tickets;" -Expected "12" -PostgresUser $postgresUser -PostgresDb $postgresDb

    $mailBefore = Get-GreenMailSubjectCount -SubjectNeedle "[MR-0001]"
    $stage6DriverId = Invoke-ScalarSql -Sql "select id from workflow_entity where name = 'Maintenance Triage Stage 6 Driver' limit 1;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if (-not $stage6DriverId) {
        throw "Stage 6 driver workflow was not imported."
    }

    Write-Host "Executing Stage 6 driver workflow $stage6DriverId..."
    docker compose run --rm --no-deps -T n8n execute --id=$stage6DriverId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 6 driver workflow execution failed with exit code $LASTEXITCODE."
    }

    $mailAfter = Get-GreenMailSubjectCount -SubjectNeedle "[MR-0001]"
    if (($mailAfter - $mailBefore) -ne 1) {
        throw "Expected exactly one new GreenMail message for MR-0001, got before=$mailBefore after=$mailAfter."
    }
    Write-Host "OK: approval sent exactly one GreenMail message for MR-0001"

    Write-Host "Checking Stage 6 alert and approval outcomes..."
    Assert-Sql -Label "mock emergency alert event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0001' and e.action='telegram_alert_mocked';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "urgent alert event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0005' and e.action='telegram_alert_mocked';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "needs-review alert events" -Sql "select case when count(*) >= 4 then 1 else 0 end from triage.events e join triage.tickets t on t.id=e.ticket_id where t.priority='NEEDS_REVIEW' and e.action='telegram_alert_mocked';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "routine skipped event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0003' and e.action='telegram_alert_skipped';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "human-only skipped event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0006' and e.detail->>'reason'='routine_human_only_no_alert';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "quiet-hours urgent held event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0005' and e.detail->>'reason'='urgent_quiet_hours_held';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "rate-cap grouped event" -Sql "select count(*) from triage.events where action='telegram_alert_grouped';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "simulated Telegram failure event" -Sql "select count(*) from triage.events e join triage.tickets t on t.id=e.ticket_id where t.ref='MR-0007' and e.action='telegram_alert_failed' and t.last_alert_error is not null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "approved ticket status" -Sql "select count(*) from triage.tickets where ref='MR-0001' and status='ACK_SENT' and out_msg_id is not null and outbound_to='maintenance@example.test' and outbound_sent_at is not null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "double approve guarded" -Sql "select count(*) from triage.events where ticket_id=(select id from triage.tickets where ref='MR-0001') and action='tenant_reply_sent';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "hold status without email" -Sql "select count(*) from triage.tickets where ref='MR-0005' and status='HELD' and out_msg_id is null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "not emergency downgraded" -Sql "select count(*) from triage.tickets where ref='MR-0002' and priority='URGENT' and status='ACKED' and out_msg_id is null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "not emergency feedback" -Sql "select count(*) from triage.feedback where ticket_id=(select id from triage.tickets where ref='MR-0002') and was='EMERGENCY' and became='URGENT';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "human-only approval refused" -Sql "select count(*) from triage.tickets where ref='MR-0006' and out_msg_id is null and status <> 'ACK_SENT';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Backdating failed emergency to verify escalation predicate..."
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "update triage.tickets set received_at = now() - interval '20 minutes', alerted_at = null, acked_at = null, status = 'NEW' where ref = 'MR-0007';" | Out-Host

    Assert-Sql -Label "emergency escalation selects failed alert" -Sql "with cfg as (select value from triage.config where key='escalate_after') select count(*) from triage.tickets t, cfg where t.ref='MR-0007' and t.priority='EMERGENCY' and t.acked_at is null and t.received_at < now() - make_interval(mins => coalesce((cfg.value->>'EMERGENCY_minutes')::int, 15));" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    $token = Invoke-ScalarSql -Sql "select value->>'token' from triage.config where key = 'board';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    $board = Invoke-BoardRequest -Url "http://localhost:$n8nPort/webhook/board?t=$token"
    if ($board.Status -ne "200") {
        throw "Board expected HTTP 200 after Stage 6, got $($board.Status)."
    }
    Assert-Contains -Label "board reply sent state" -Body $board.Body -Needle "Reply sent"

    Write-Host ""
    Write-Host "Stage 6 validation passed."
    Write-Host "Manual live Telegram gate remains: set real chat IDs, start an HTTPS tunnel, set N8N_WEBHOOK_URL, then run .\scripts\import-stage-6-workflows.ps1 -PublishTelegramCallback."
}
finally {
    Pop-Location
}
