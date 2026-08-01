[CmdletBinding()]
param(
    [switch]$PublishLiveTriggers
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
    python .\scripts\build-stage-5-board-workflow.py
    python .\scripts\build-stage-6-workflows.py
    python .\scripts\build-stage-7-workflows.py

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

    $containerDir = "/tmp/maintenance-triage-stage-7"
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    @(
        "maintenance-triage-board.json",
        "maintenance-triage-alert-dispatch.json",
        "maintenance-triage-approval-action.json",
        "maintenance-triage-post-ingest.json",
        "maintenance-triage-email-ingest.json",
        "maintenance-triage-form-ingest.json",
        "maintenance-triage-fixture-fire.json",
        "maintenance-triage-import-bridge.json"
    ) | ForEach-Object {
        docker compose cp "workflows\$_" "n8n:$containerDir/$_"
    }

    docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    @(
        "maintenance-triage-board-stage-5",
        "mt-alert-dispatch-stage-6",
        "mt-approval-action-stage-6",
        "mt-post-ingest-stage-7",
        "mt-import-bridge-stage-7",
        "mt-fixture-fire-stage-7"
    ) | ForEach-Object {
        docker compose exec -T n8n n8n publish:workflow --id=$_ | Out-Host
    }

    if ($PublishLiveTriggers) {
        docker compose exec -T n8n n8n publish:workflow --id=mt-email-ingest-stage-7 | Out-Host
        docker compose exec -T n8n n8n publish:workflow --id=mt-form-ingest-stage-7 | Out-Host
        Write-Host "Live email and form ingestion workflows published."
    }
    else {
        Write-Host "Email and form ingestion workflows imported but not published. Use -PublishLiveTriggers after configuring real IMAP/SMTP credentials."
    }

    Write-Host "Restarting n8n so active webhooks/forms are registered..."
    docker compose restart n8n | Out-Host

    $deadline = (Get-Date).AddSeconds(90)
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5678" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    if ((Get-Date) -ge $deadline) {
        throw "n8n did not become reachable after restart."
    }

    Write-Host "Stage 7 workflows imported into project $projectId."
}
finally {
    Pop-Location
}
