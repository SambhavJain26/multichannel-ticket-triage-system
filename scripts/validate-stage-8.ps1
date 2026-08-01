[CmdletBinding()]
param(
    [switch]$LiveNotifications,
    [switch]$RunRehearsal
)

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

function Wait-N8n {
    param([string]$Port)

    $deadline = (Get-Date).AddSeconds(90)
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    throw "n8n did not become reachable on port $Port."
}

function Invoke-N8nWorkflowCli {
    param([Parameter(Mandatory = $true)][string]$WorkflowId)

    docker compose stop n8n | Out-Host
    try {
        $output = docker compose run --rm --no-deps -T n8n execute --id=$WorkflowId 2>&1
        $output | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Workflow $WorkflowId failed with exit code $LASTEXITCODE."
        }
        return ($output -join "`n")
    }
    finally {
        docker compose up -d n8n | Out-Host
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $n8nPort = Get-DotEnvValue -Name "N8N_PORT" -Default "5678"

    Write-Host "Validating Stage 8 generated workflow JSON..."
    python .\scripts\build-stage-8-workflows.py | Out-Host
    @(
        "workflows\maintenance-triage-daily-digest.json",
        "workflows\maintenance-triage-operator-heartbeat.json"
    ) | ForEach-Object {
        Get-Content -Raw $_ | ConvertFrom-Json | Out-Null
    }

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Applying Stage 8 config..."
    .\scripts\apply-stage-8.ps1
    Assert-Sql -Label "digest config" -Sql "select count(*) from triage.config where key='digest' and value ? 'enabled' and value ? 'to_email';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "heartbeat config" -Sql "select count(*) from triage.config where key='heartbeat' and value ? 'threshold_minutes' and value ? 'repeat_suppression_minutes';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Importing Stage 8 workflows..."
    .\scripts\import-stage-8-workflows.ps1 -PublishSchedules
    Wait-N8n -Port $n8nPort
    Assert-Sql -Label "Stage 8 workflows active" -Sql "select count(*) from workflow_entity where id in ('mt-digest-stage-8','mt-heartbeat-stage-8') and active;" -Expected "2" -PostgresUser $postgresUser -PostgresDb $postgresDb

    $token = Invoke-ScalarSql -Sql "select value->>'token' from triage.config where key='board';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    .\scripts\reset-stage-8-demo-state.ps1 | Out-Host
    $emptyBoardStart = Get-Date
    $board = Invoke-WebRequest -Uri "http://localhost:$n8nPort/webhook/board?t=$token" -UseBasicParsing -TimeoutSec 20
    $emptyBoardMs = [int]((Get-Date) - $emptyBoardStart).TotalMilliseconds
    if ($board.StatusCode -ne 200 -or -not $board.Content.Contains("Nothing waiting.")) {
        throw "Clean reset did not return the board to empty."
    }
    if ($emptyBoardMs -gt 10000) {
        throw "Clean board took $emptyBoardMs ms, expected under 10000 ms."
    }
    Write-Host "OK: clean reset returned board to empty in $emptyBoardMs ms"

    .\scripts\save-stage-8-demo-snapshot.ps1 -Name clean-validation | Out-Host
    .\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean-validation | Out-Host
    Assert-Sql -Label "restored clean snapshot ticket count" -Sql "select count(*) from triage.tickets;" -Expected "0" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Checking overdue board/digest behavior without Telegram escalation..."
    $overdueSql = @"
insert into triage.tickets (
    ref, source, received_at, from_address, subject, body_raw, body_clean, body_hash,
    model_json, model_priority, model_name, prompt_tokens, completion_tokens,
    is_maintenance_request, request_type, priority, priority_reason, trade,
    unit_identifier, issue_summary, safety_signals, missing_info, confidence, language,
    status, sla_due_at
)
values (
    'MR-9998',
    'fixture',
    now() - interval '11 days',
    'stage-8-overdue-routine@example.test',
    'stage-8-overdue-routine-check',
    'Unit 14A bathroom door squeaks every time it opens.',
    'Unit 14A bathroom door squeaks every time it opens.',
    encode(digest('stage-8-overdue-routine-check', 'sha256'), 'hex'),
    '{"priority":"ROUTINE","issue_summary":"Bathroom door squeaks","safety_signals":["NONE"],"missing_info":[]}'::jsonb,
    'ROUTINE',
    'stage-8-validation',
    0,
    0,
    true,
    'NEW_ISSUE',
    'ROUTINE',
    'Synthetic Stage 8 overdue check.',
    'GENERAL',
    '14A',
    'Bathroom door squeaks',
    '["NONE"]'::jsonb,
    '[]'::jsonb,
    'HIGH',
    'en',
    'NEW',
    now() - interval '8 days'
);
"@
    $overdueSql | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host
    $overdueBoard = Invoke-WebRequest -Uri "http://localhost:$n8nPort/webhook/board?t=$token" -UseBasicParsing -TimeoutSec 20
    if ($overdueBoard.StatusCode -ne 200 -or -not $overdueBoard.Content.Contains("MR-9998") -or -not $overdueBoard.Content.Contains("OVERDUE")) {
        throw "Backdated routine ticket did not render as OVERDUE on the board."
    }
    Write-Host "OK: backdated routine ticket rendered OVERDUE on the board"
    Assert-Sql -Label "overdue routine digest candidate" -Sql "with c as (select value from triage.config where key='overdue_days') select count(*) from triage.tickets t, c where t.ref='MR-9998' and t.priority in ('ROUTINE','URGENT') and t.closed_at is null and t.status <> 'CLOSED' and t.received_at < now() - make_interval(days => coalesce((c.value->>t.priority)::int, 999999));" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "age alone real Telegram sends" -Sql "select count(*) from triage.events where action='telegram_alert_sent';" -Expected "0" -PostgresUser $postgresUser -PostgresDb $postgresDb
    .\scripts\reset-stage-8-demo-state.ps1 | Out-Host

    if ($LiveNotifications) {
        Write-Host "Running live digest and heartbeat notification checks..."
        $recipient = Invoke-ScalarSql -Sql "select coalesce(nullif((select value->>'from_email' from triage.config where key='outbound_email'), ''), 'maintenance@example.test');" -PostgresUser $postgresUser -PostgresDb $postgresDb
        $configSql = @"
update triage.config
set value = value || jsonb_build_object('enabled', true, 'to_email', '$recipient')
where key = 'digest';
update triage.config
set value = value || jsonb_build_object('enabled', true, 'threshold_minutes', 0, 'repeat_suppression_minutes', 180, 'baseline_at', now() - interval '2 hours', 'last_alert_at', null)
where key = 'heartbeat';
"@
        $configSql | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host

        $digestOutput = Invoke-N8nWorkflowCli -WorkflowId "mt-digest-stage-8"
        Wait-N8n -Port $n8nPort
        if ($digestOutput -notmatch "accepted|messageId|250 ") {
            throw "Digest workflow did not show an accepted SMTP send."
        }
        Write-Host "OK: digest workflow sent through SMTP"

        $heartbeatOutput = Invoke-N8nWorkflowCli -WorkflowId "mt-heartbeat-stage-8"
        Wait-N8n -Port $n8nPort
        if ($heartbeatOutput -notmatch "telegram_message_id|message_id|result") {
            throw "Heartbeat workflow did not show a Telegram send result."
        }
        Write-Host "OK: heartbeat workflow attempted operator Telegram alert"

        $secondHeartbeatOutput = Invoke-N8nWorkflowCli -WorkflowId "mt-heartbeat-stage-8"
        Wait-N8n -Port $n8nPort
        if ($secondHeartbeatOutput -notmatch "heartbeat_skipped") {
            throw "Heartbeat repeat suppression did not skip the immediate second run."
        }
        Write-Host "OK: heartbeat repeat suppression skipped the immediate second run"

        $restoreSql = @"
update triage.config
set value = value || jsonb_build_object('enabled', false)
where key in ('digest', 'heartbeat');
"@
        $restoreSql | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host
    }
    else {
        Write-Host "Skipping live digest/heartbeat sends. Re-run with -LiveNotifications to send one digest email and one operator heartbeat Telegram."
    }

    if ($RunRehearsal) {
        .\scripts\run-stage-8-rehearsal.ps1 -Runs 5
    }
    else {
        Write-Host "Skipping five-run fixture rehearsal. Re-run with -RunRehearsal for the full destructive rehearsal."
    }

    Write-Host ""
    Write-Host "Stage 8 validation passed."
}
finally {
    Pop-Location
}
