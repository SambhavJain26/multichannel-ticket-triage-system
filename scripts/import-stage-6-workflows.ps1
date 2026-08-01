[CmdletBinding()]
param(
    [switch]$PublishTelegramCallback
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

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    python .\scripts\build-stage-6-workflows.py
    Get-ChildItem -LiteralPath workflows -Filter "maintenance-triage-*-stage-6*.json" -ErrorAction SilentlyContinue | Out-Null
    @(
        "workflows\maintenance-triage-alert-dispatch.json",
        "workflows\maintenance-triage-approval-action.json",
        "workflows\maintenance-triage-telegram-callback.json",
        "workflows\maintenance-triage-emergency-escalation.json",
        "workflows\maintenance-triage-stage-6-driver.json"
    ) | ForEach-Object {
        Get-Content -Raw $_ | ConvertFrom-Json | Out-Null
    }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"

    $projectId = docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -At `
        -c "select id from project where type = 'personal' limit 1;"

    $projectId = (($projectId | Select-Object -First 1) -as [string]).Trim()
    if (-not $projectId) {
        throw "Could not find a personal n8n project."
    }

    $containerDir = "/tmp/maintenance-triage-stage-6"
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    @(
        "maintenance-triage-alert-dispatch.json",
        "maintenance-triage-approval-action.json",
        "maintenance-triage-telegram-callback.json",
        "maintenance-triage-emergency-escalation.json",
        "maintenance-triage-stage-6-driver.json"
    ) | ForEach-Object {
        docker compose cp "workflows\$_" "n8n:$containerDir/$_"
    }

    docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    @(
        "mt-alert-dispatch-stage-6",
        "mt-approval-action-stage-6",
        "mt-emergency-escalation-stage-6",
        "mt-stage-6-driver"
    ) | ForEach-Object {
        docker compose exec -T n8n n8n publish:workflow --id=$_ | Out-Host
    }

    if ($PublishTelegramCallback) {
        docker compose exec -T n8n n8n publish:workflow --id=mt-telegram-callback-stage-6 | Out-Host
        Write-Host "Telegram callback workflow published. Verify N8N_WEBHOOK_URL uses a current HTTPS tunnel."
    }
    else {
        Write-Host "Telegram callback workflow imported but not published. Use -PublishTelegramCallback after setting real chat IDs and an HTTPS tunnel."
    }

    Write-Host "Stage 6 workflows imported into project $projectId."
}
finally {
    Pop-Location
}
