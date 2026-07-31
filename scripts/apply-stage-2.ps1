[CmdletBinding()]
param(
    [switch]$Reset
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

function Invoke-PostgresSqlFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    Get-Content -Raw -LiteralPath $Path |
        docker compose exec -T postgres psql `
            -U $PostgresUser `
            -d $PostgresDb `
            -v ON_ERROR_STOP=1
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"

    docker compose ps postgres | Out-Host

    if ($Reset) {
        Write-Warning "Resetting local triage schema only. n8n internal tables and credentials are not touched."
        "DROP SCHEMA IF EXISTS triage CASCADE;" |
            docker compose exec -T postgres psql `
                -U $postgresUser `
                -d $postgresDb `
                -v ON_ERROR_STOP=1
    }

    Invoke-PostgresSqlFile `
        -Path "db/postgres/001-create-triage-schema.sql" `
        -PostgresUser $postgresUser `
        -PostgresDb $postgresDb

    Invoke-PostgresSqlFile `
        -Path "db/postgres/002-seed-config.sql" `
        -PostgresUser $postgresUser `
        -PostgresDb $postgresDb

    Write-Host "Stage 2 schema and config seed applied."
}
finally {
    Pop-Location
}
