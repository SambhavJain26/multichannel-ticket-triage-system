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

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"

    Write-Host "Validating generated workflow JSON..."
    python .\scripts\build-stage-4-workflows.py | Out-Host
    Get-Content -Raw workflows\maintenance-triage-core.json | ConvertFrom-Json | Out-Null
    Get-Content -Raw workflows\maintenance-triage-stage-4-driver.json | ConvertFrom-Json | Out-Null
    Get-Content -Raw prompts\maintenance-triage.schema.json | ConvertFrom-Json | Out-Null
    Get-Content -Raw prompts\maintenance-drafts.schema.json | ConvertFrom-Json | Out-Null

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Applying Stage 4 DB support..."
    .\scripts\apply-stage-4.ps1

    Write-Host "Resetting local Stage 4 ticket/event data..."
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "truncate triage.feedback, triage.events, triage.tickets restart identity; alter sequence triage.ticket_ref_seq restart with 1; update triage.config set value = value || jsonb_build_object('consecutive_model_failures', 0, 'degraded_until', null, 'degraded_alerted_at', null, 'llm_calls_today', 0, 'llm_call_day', null) where key = 'runtime_state';" | Out-Host

    Write-Host "Checking required n8n credentials..."
    Assert-Sql -Label "Postgres credential" -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-postgres-local';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "OpenAI credential" -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-openai';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host "Importing Stage 4 workflows..."
    .\scripts\import-stage-4-workflows.ps1

    $driverId = Invoke-ScalarSql -Sql "select id from workflow_entity where name = 'Maintenance Triage Stage 4 Driver' limit 1;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if (-not $driverId) {
        throw "Stage 4 driver workflow was not imported."
    }

    Write-Host "Executing Stage 4 driver workflow $driverId..."
    docker compose run --rm --no-deps -T n8n execute --id=$driverId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 4 driver workflow execution failed with exit code $LASTEXITCODE."
    }

    Write-Host "Checking Stage 4 database outcomes..."
    Assert-Sql -Label "created ticket count" -Sql "select count(*) from triage.tickets;" -Expected "12" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "duplicate ignored events" -Sql "select count(*) from triage.events where action = 'duplicate_ignored';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "live demo priority matches" -Sql "select count(*) from triage.tickets where subject in ('01-understated-gas','02-panicked-burst-pipe-no-unit','03-urgent-squeaky-door','04-buried-lede','05-spanish-no-hot-water','06-accommodation-request') and ((subject in ('01-understated-gas','02-panicked-burst-pipe-no-unit') and priority = 'EMERGENCY') or (subject in ('04-buried-lede','05-spanish-no-hot-water') and priority = 'URGENT') or (subject in ('03-urgent-squeaky-door','06-accommodation-request') and priority = 'ROUTINE'));" -Expected "6" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "safety override events" -Sql "select count(*) from triage.events where action = 'overridden';" -Expected "3" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "accommodation draft suppressed" -Sql "select count(*) from triage.tickets where subject = '06-accommodation-request' and human_only and draft_body is null and vendor_note is null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Spanish draft generated" -Sql "select count(*) from triage.tickets where subject = '05-spanish-no-hot-water' and draft_body is not null and vendor_note is not null;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "simulated model errors became NEEDS_REVIEW" -Sql "select count(*) from triage.tickets where subject like 'simulated failure%' and priority = 'NEEDS_REVIEW';" -Expected "3" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "degraded mode set" -Sql "select case when (value->>'degraded_until') is not null then 1 else 0 end from triage.config where key = 'runtime_state';" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host ""
    Write-Host "Stage 4 validation passed."
}
finally {
    Pop-Location
}
