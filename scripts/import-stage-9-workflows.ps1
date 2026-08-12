[CmdletBinding()]
param(
    [switch]$PublishLiveTriggers,
    [switch]$CleanupLegacy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
    param([string]$Name, [string]$Default)
    if (-not (Test-Path -LiteralPath ".env")) { return $Default }
    $line = Get-Content -LiteralPath ".env" | Where-Object { $_ -match "^\s*$([regex]::Escape($Name))=" } | Select-Object -First 1
    if (-not $line) { return $Default }
    return ($line -replace "^\s*$([regex]::Escape($Name))=", "").Trim().Trim('"').Trim("'")
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($CleanupLegacy -and -not $PublishLiveTriggers) {
        throw "-CleanupLegacy requires -PublishLiveTriggers. Do not retire working workflows before the replacement triggers are live."
    }
    python .\scripts\build-stage-4-workflows.py
    python .\scripts\build-stage-9-workflows.py
    $files = @(
        "maintenance-triage-core.json",
        "maintenance-triage-tenant-intake.json",
        "maintenance-triage-tenant-telegram.json",
        "maintenance-triage-manager-desk.json",
        "maintenance-triage-operations.json",
        "maintenance-triage-demo-tools.json"
    )
    $files | ForEach-Object { Get-Content -Raw "workflows\$_" | ConvertFrom-Json | Out-Null }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $projectId = docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -At -c "select id from project where type = 'personal' limit 1;"
    $projectId = (($projectId | Select-Object -First 1) -as [string]).Trim()
    if (-not $projectId) { throw "Could not find a personal n8n project." }

    $containerDir = "/tmp/maintenance-triage-stage-9"
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    $files | ForEach-Object { docker compose cp "workflows\$_" "n8n:$containerDir/$_" }
    docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    if ($PublishLiveTriggers) {
        @("maintenance-triage-core-stage-4", "mt-tenant-intake-stage-9", "mt-tenant-telegram-stage-9", "mt-manager-desk-stage-9", "mt-operations-stage-9") | ForEach-Object {
            docker compose exec -T n8n n8n publish:workflow --id=$_ | Out-Host
        }
        if ($CleanupLegacy) {
            $legacy = @("mt-alert-dispatch-stage-6", "mt-approval-action-stage-6", "maintenance-triage-board-stage-5", "mt-digest-stage-8", "mt-email-ingest-stage-7", "mt-emergency-escalation-stage-6", "mt-fixture-fire-stage-7", "mt-form-ingest-stage-7", "mt-import-bridge-stage-7", "mt-heartbeat-stage-8", "mt-post-ingest-stage-7", "maintenance-triage-stage-4-driver", "mt-stage-6-driver", "mt-telegram-callback-stage-6")
            $quoted = ($legacy | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ","
            docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -c "update workflow_entity set active=false where id in ($quoted);" | Out-Host
            Write-Host "Legacy workflows were deactivated, not deleted. Their exports remain available for rollback."
        }
        docker compose restart n8n | Out-Host
    }
    else {
        Write-Host "Stage 9 workflows imported but not published. Create the Airtable and tenant Telegram credentials, configure a public HTTPS N8N_WEBHOOK_URL, then use -PublishLiveTriggers."
    }
}
finally {
    Pop-Location
}
