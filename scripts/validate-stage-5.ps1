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

function Invoke-BoardRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Url
    )

    $bodyPath = Join-Path $env:TEMP ("maintenance-triage-board-" + [guid]::NewGuid().ToString() + ".html")
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

function Assert-NotContains {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Body,
        [Parameter(Mandatory = $true)][string]$Needle
    )

    if ($Body.Contains($Needle)) {
        throw "$Label unexpectedly contained text: $Needle"
    }
    Write-Host "OK: $Label does not contain '$Needle'"
}

function Assert-Status {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][hashtable]$Response,
        [Parameter(Mandatory = $true)][string]$Expected
    )

    if ($Response.Status -ne $Expected) {
        throw "$Label expected HTTP $Expected, got $($Response.Status)"
    }
    Write-Host "OK: $Label HTTP $Expected"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $n8nPort = Get-DotEnvValue -Name "N8N_PORT" -Default "5678"

    Write-Host "Validating generated Stage 5 workflow JSON..."
    python .\scripts\build-stage-5-board-workflow.py | Out-Host
    Get-Content -Raw workflows\maintenance-triage-board.json | ConvertFrom-Json | Out-Null

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Applying database support..."
    .\scripts\apply-stage-4.ps1
    .\scripts\apply-stage-5.ps1

    Assert-Sql -Label "board config row" -Sql "select count(*) from triage.config where key = 'board' and length(value->>'token') >= 32 and (value->>'recent_hours')::int = 48 and (value->>'max_cards')::int = 60;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Resetting local ticket/event data for Stage 5 validation..."
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "truncate triage.feedback, triage.events, triage.tickets restart identity; alter sequence triage.ticket_ref_seq restart with 1; update triage.config set value = value || jsonb_build_object('consecutive_model_failures', 0, 'degraded_until', null, 'degraded_alerted_at', null, 'llm_calls_today', 0, 'llm_call_day', null) where key = 'runtime_state';" | Out-Host

    Write-Host "Importing required workflows..."
    .\scripts\import-stage-4-workflows.ps1
    .\scripts\import-stage-5-board.ps1

    $token = Invoke-ScalarSql -Sql "select value->>'token' from triage.config where key = 'board';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if (-not $token) {
        throw "Board token was not generated."
    }

    $baseUrl = "http://localhost:$n8nPort/webhook/board"
    $missingToken = Invoke-BoardRequest -Url $baseUrl
    Assert-Status -Label "missing token" -Response $missingToken -Expected "404"
    Assert-Contains -Label "missing token page" -Body $missingToken.Body -Needle "The board link is missing or invalid."

    $badToken = Invoke-BoardRequest -Url "${baseUrl}?t=bad-token"
    Assert-Status -Label "bad token" -Response $badToken -Expected "404"
    Assert-NotContains -Label "bad token page" -Body $badToken.Body -Needle "MR-"

    $emptyBoard = Invoke-BoardRequest -Url "${baseUrl}?t=$token"
    Assert-Status -Label "empty board" -Response $emptyBoard -Expected "200"
    Assert-Contains -Label "empty board" -Body $emptyBoard.Body -Needle "Nothing waiting."

    $driverId = Invoke-ScalarSql -Sql "select id from workflow_entity where name = 'Maintenance Triage Stage 4 Driver' limit 1;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if (-not $driverId) {
        throw "Stage 4 driver workflow was not imported."
    }

    Write-Host "Executing Stage 4 driver workflow $driverId for board data..."
    docker compose run --rm --no-deps -T n8n execute --id=$driverId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 4 driver workflow execution failed with exit code $LASTEXITCODE."
    }

    Write-Host "Backdating one routine ticket to exercise OVERDUE board state..."
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "update triage.tickets set received_at = now() - interval '11 days', sla_due_at = now() - interval '10 days' where subject = '03-urgent-squeaky-door';" | Out-Host

    Assert-Sql -Label "overdue routine priority unchanged" -Sql "select priority from triage.tickets where subject = '03-urgent-squeaky-door';" -Expected "ROUTINE" -PostgresUser $postgresUser -PostgresDb $postgresDb

    $filledBoard = Invoke-BoardRequest -Url "${baseUrl}?t=$token"
    Assert-Status -Label "filled board" -Response $filledBoard -Expected "200"
    Assert-Contains -Label "filled board emergency" -Body $filledBoard.Body -Needle "Emergency"
    Assert-Contains -Label "filled board urgent" -Body $filledBoard.Body -Needle "Urgent"
    Assert-Contains -Label "filled board routine" -Body $filledBoard.Body -Needle "Routine"
    Assert-Contains -Label "filled board needs review" -Body $filledBoard.Body -Needle "Needs review"
    Assert-Contains -Label "filled board human-only" -Body $filledBoard.Body -Needle "HUMAN DECISION REQUIRED - no reply written"
    Assert-Contains -Label "filled board override" -Body $filledBoard.Body -Needle "OVERRIDE - GAS"
    Assert-Contains -Label "filled board reply status" -Body $filledBoard.Body -Needle "Reply written - waiting for you"
    Assert-Contains -Label "filled board overdue" -Body $filledBoard.Body -Needle "OVERDUE"

    $badTokenAfterData = Invoke-BoardRequest -Url "${baseUrl}?t=bad-token"
    Assert-Status -Label "bad token after data" -Response $badTokenAfterData -Expected "404"
    Assert-NotContains -Label "bad token after data" -Body $badTokenAfterData.Body -Needle "MR-0001"

    $detail = Invoke-BoardRequest -Url "${baseUrl}?t=$token&ref=MR-0001"
    Assert-Status -Label "detail page" -Response $detail -Expected "200"
    Assert-Contains -Label "detail original message" -Body $detail.Body -Needle "Original message"
    Assert-Contains -Label "detail AI readout" -Body $detail.Body -Needle "AI readout"
    Assert-Contains -Label "detail technical audit" -Body $detail.Body -Needle "Technical audit"
    Assert-Contains -Label "detail rules verdict" -Body $detail.Body -Needle "Rule safety keyword:"
    Assert-Contains -Label "detail tenant reply" -Body $detail.Body -Needle "The reply, waiting for you"
    Assert-Contains -Label "detail vendor note" -Body $detail.Body -Needle "Vendor note"
    Assert-Contains -Label "detail event trail" -Body $detail.Body -Needle "Event trail"

    Write-Host "Executing Stage 4 driver a second time to verify bounded/legible board behavior..."
    docker compose run --rm --no-deps -T n8n execute --id=$driverId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Second Stage 4 driver execution failed with exit code $LASTEXITCODE."
    }

    $cardCount = Invoke-ScalarSql -Sql "with board as (select value from triage.config where key = 'board') select case when count(*) <= ((select value from board)->>'max_cards')::int then 1 else 0 end from triage.tickets;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if ($cardCount -ne "1") {
        throw "Ticket count exceeded configured board max after repeated fixture runs."
    }
    Write-Host "OK: repeated fixture runs remain within configured board bound"

    Write-Host ""
    Write-Host "Stage 5 validation passed."
    Write-Host "Board URL: ${baseUrl}?t=$token"
}
finally {
    Pop-Location
}
