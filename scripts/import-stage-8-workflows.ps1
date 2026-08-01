[CmdletBinding()]
param(
    [switch]$PublishSchedules
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
    python .\scripts\build-stage-8-workflows.py

    @(
        "workflows\maintenance-triage-daily-digest.json",
        "workflows\maintenance-triage-operator-heartbeat.json"
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

    $containerDir = "/tmp/maintenance-triage-stage-8"
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    @(
        "maintenance-triage-daily-digest.json",
        "maintenance-triage-operator-heartbeat.json"
    ) | ForEach-Object {
        docker compose cp "workflows\$_" "n8n:$containerDir/$_"
    }

    docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    if ($PublishSchedules) {
        @(
            "mt-digest-stage-8",
            "mt-heartbeat-stage-8"
        ) | ForEach-Object {
            docker compose exec -T n8n n8n publish:workflow --id=$_ | Out-Host
        }
        Write-Host "Stage 8 digest and heartbeat workflows published. Config rows remain the send/no-send gate."
    }
    else {
        Write-Host "Stage 8 workflows imported but not published. Use -PublishSchedules after reviewing digest/heartbeat config."
    }

    Write-Host "Restarting n8n so active schedule metadata is refreshed..."
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

    Write-Host "Stage 8 workflows imported into project $projectId."
}
finally {
    Pop-Location
}
