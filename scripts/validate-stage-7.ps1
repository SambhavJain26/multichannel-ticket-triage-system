[CmdletBinding()]
param(
    [switch]$LiveMailbox
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

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"

    Write-Host "Validating generated Stage 5, Stage 6, and Stage 7 workflow JSON..."
    python .\scripts\build-stage-5-board-workflow.py | Out-Host
    python .\scripts\build-stage-6-workflows.py | Out-Host
    python .\scripts\build-stage-7-workflows.py | Out-Host
    @(
        "workflows\maintenance-triage-board.json",
        "workflows\maintenance-triage-alert-dispatch.json",
        "workflows\maintenance-triage-approval-action.json",
        "workflows\maintenance-triage-post-ingest.json",
        "workflows\maintenance-triage-email-ingest.json",
        "workflows\maintenance-triage-form-ingest.json",
        "workflows\maintenance-triage-fixture-fire.json",
        "workflows\maintenance-triage-import-bridge.json"
    ) | ForEach-Object {
        Get-Content -Raw $_ | ConvertFrom-Json | Out-Null
    }

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Applying Stage 4, 5, 6, and 7 database support..."
    .\scripts\apply-stage-4.ps1
    .\scripts\apply-stage-5.ps1
    .\scripts\apply-stage-6.ps1
    .\scripts\apply-stage-7.ps1

    Assert-Sql -Label "Stage 7 ticket columns" -Sql "select count(*) from information_schema.columns where table_schema='triage' and table_name='tickets' and column_name in ('unit_match_status','matched_unit_id','unit_match_display','unit_match_reason');" -Expected "4" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Stage 7 units seeded" -Sql "select count(*) from triage.units where active;" -Expected "20" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Stage 7 import tables" -Sql "select count(*) from information_schema.tables where table_schema='triage' and table_name in ('import_batches','import_items');" -Expected "2" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-Sql -Label "Stage 7 ingestion token" -Sql "select count(*) from triage.config where key='ingestion' and length(value->>'import_token') >= 32;" -Expected "1" -PostgresUser $postgresUser -PostgresDb $postgresDb

    if ($LiveMailbox) {
        .\scripts\check-stage-7-live-prereqs.ps1
    }
    else {
        Write-Host "Skipping live mailbox prerequisite check. Re-run with -LiveMailbox after importing the Gmail/Workspace IMAP and SMTP credentials."
    }

    Write-Host ""
    Write-Host "Stage 7 structural validation passed."
}
finally {
    Pop-Location
}
