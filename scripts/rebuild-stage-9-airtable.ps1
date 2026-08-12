[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BaseId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3 .\scripts\setup-stage-9-airtable.py --base-id $BaseId --apply --rebuild-demo-base
    if ($LASTEXITCODE -ne 0) { throw "Typed Airtable table creation failed." }
    py -3 .\scripts\sync-stage-9-airtable.py --reset-links
    if ($LASTEXITCODE -ne 0) { throw "Airtable replay from local Postgres failed." }
    Write-Host "Rebuilt only the typed Stage 9 demo tables and re-synced local Postgres state."
}
finally {
    Pop-Location
}
