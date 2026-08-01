[CmdletBinding()]
param(
    [string]$Name = "clean"
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
    if ($Name -notmatch '^[a-zA-Z0-9._-]+$') {
        throw "Snapshot name must contain only letters, numbers, dot, underscore, or hyphen."
    }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $snapshotDir = "data\demo-snapshots"
    New-Item -ItemType Directory -Force -Path $snapshotDir | Out-Null
    $snapshotPath = Join-Path $snapshotDir "$Name.sql"

    docker compose exec -T postgres pg_dump `
        -U $postgresUser `
        -d $postgresDb `
        --data-only `
        --column-inserts `
        --table=triage.tickets `
        --table=triage.events `
        --table=triage.feedback `
        --table=triage.import_batches `
        --table=triage.import_items |
        Set-Content -LiteralPath $snapshotPath -Encoding UTF8

    Write-Host "Saved local demo snapshot to $snapshotPath"
}
finally {
    Pop-Location
}
