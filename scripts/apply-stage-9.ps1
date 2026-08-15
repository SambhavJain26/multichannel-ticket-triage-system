[CmdletBinding()]
param()

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
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    Get-Content -Raw db\postgres\008-stage-9-telegram-airtable.sql |
        docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f -
    Get-Content -Raw db\postgres\009-stage-9-telegram-pretriage.sql |
        docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f -
    Write-Host "Stage 9 Telegram and Airtable support applied."
}
finally {
    Pop-Location
}
