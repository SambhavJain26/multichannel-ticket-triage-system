[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$LocalOnly,
    [switch]$KeepGeneratedFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
    param([string]$Name, [string]$Default)
    if (-not (Test-Path -LiteralPath ".env")) { return $Default }
    $line = Get-Content -LiteralPath ".env" |
        Where-Object { $_ -match "^\s*$([regex]::Escape($Name))=" } |
        Select-Object -First 1
    if (-not $line) { return $Default }
    return ($line -replace "^\s*$([regex]::Escape($Name))=", "").Trim().Trim('"').Trim("'")
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $countsSql = @"
select json_build_object(
  'tickets', (select count(*) from triage.tickets),
  'messages', (select count(*) from triage.ticket_messages),
  'vendor_attempts', (select count(*) from triage.vendor_send_attempts)
)::text;
"@
    $localCounts = $countsSql | docker compose exec -T postgres psql `
        -U $postgresUser -d $postgresDb -At -v ON_ERROR_STOP=1 -f -
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect local demo state." }
    Write-Host "Local demo state: $($localCounts.Trim())"

    if (-not $LocalOnly) {
        if ($Apply) {
            py -3 .\scripts\clear-stage-9-airtable-state.py --apply
        }
        else {
            py -3 .\scripts\clear-stage-9-airtable-state.py
        }
        if ($LASTEXITCODE -ne 0) { throw "Airtable demo-state check/reset failed. Local Postgres was not changed." }
    }
    else {
        Write-Host "Airtable will be preserved because -LocalOnly was supplied."
    }

    if (-not $Apply) {
        Write-Host "Dry run only. Run .\scripts\reset-demo.ps1 -Apply to perform the reset."
        return
    }

    $resetArgs = @{}
    if ($KeepGeneratedFiles) { $resetArgs.KeepGeneratedFiles = $true }
    & .\scripts\reset-stage-9-demo-state.ps1 @resetArgs

    $remaining = docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -At `
        -v ON_ERROR_STOP=1 -c "select count(*) from triage.tickets;"
    if ($LASTEXITCODE -ne 0 -or $remaining.Trim() -ne "0") {
        throw "Local reset verification failed: $($remaining.Trim()) tickets remain."
    }
    Write-Host "Reset complete. The next valid request will be MR-0001."
    Write-Host "Preserved: Airtable Tenant Roster/Vendors, local units/config, n8n credentials, and workflows."
    Write-Host "Already delivered Telegram and email messages remain visible, but old approval buttons cannot target new tickets."
}
finally {
    Pop-Location
}
