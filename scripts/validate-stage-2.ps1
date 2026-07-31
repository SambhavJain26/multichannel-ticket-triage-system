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

function Assert-SqlCount {
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

    Write-Host "Checking Docker services..."
    docker compose ps | Out-Host

    Write-Host "Checking triage tables..."
    Assert-SqlCount `
        -Label "triage table count" `
        -Sql "select count(*) from information_schema.tables where table_schema = 'triage' and table_name in ('tickets','events','config','feedback');" `
        -Expected "4" `
        -PostgresUser $postgresUser `
        -PostgresDb $postgresDb

    Write-Host "Checking required indexes..."
    Assert-SqlCount `
        -Label "triage index count" `
        -Sql "select count(*) from pg_indexes where schemaname = 'triage' and indexname in ('tickets_status_priority_received_at_idx','tickets_body_hash_received_at_idx','tickets_thread_root_id_idx','tickets_msg_id_idx','tickets_out_msg_id_idx','events_ticket_id_at_idx','events_action_at_idx','feedback_ticket_id_at_idx');" `
        -Expected "8" `
        -PostgresUser $postgresUser `
        -PostgresDb $postgresDb

    Write-Host "Checking config rows..."
    Assert-SqlCount `
        -Label "triage config key count" `
        -Sql "select count(*) from triage.config where key in ('sla_minutes','overdue_days','escalate_after','contacts','company','quiet_hours','limits');" `
        -Expected "7" `
        -PostgresUser $postgresUser `
        -PostgresDb $postgresDb

    Write-Host "Checking fixture corpus..."
    python .\scripts\validate-stage-2.py

    Write-Host ""
    Write-Host "Stage 2 validation passed."
}
finally {
    Pop-Location
}
