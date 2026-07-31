[CmdletBinding()]
param(
    [switch]$RemoveVolumes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($RemoveVolumes) {
        Write-Warning "This removes local n8n and Postgres demo volumes."
        docker compose down --volumes
    }
    else {
        docker compose down
    }
}
finally {
    Pop-Location
}
