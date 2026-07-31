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

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    python .\scripts\build-stage-4-workflows.py

    Get-Content -Raw workflows\maintenance-triage-core.json | ConvertFrom-Json | Out-Null
    Get-Content -Raw workflows\maintenance-triage-stage-4-driver.json | ConvertFrom-Json | Out-Null

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

    $containerDir = "/tmp/maintenance-triage-stage-4-workflows"
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    docker compose cp workflows\maintenance-triage-core.json "n8n:$containerDir/maintenance-triage-core.json"
    docker compose cp workflows\maintenance-triage-stage-4-driver.json "n8n:$containerDir/maintenance-triage-stage-4-driver.json"

    docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    docker compose exec -T n8n n8n publish:workflow --id=maintenance-triage-core-stage-4 | Out-Host
    docker compose exec -T n8n n8n publish:workflow --id=maintenance-triage-stage-4-driver | Out-Host

    Write-Host "Stage 4 workflows imported into project $projectId."
}
finally {
    Pop-Location
}
