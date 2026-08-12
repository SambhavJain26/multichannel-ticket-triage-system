[CmdletBinding()]
param([string]$Name = "clean")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue { param([string]$Name,[string]$Default) if(-not(Test-Path .env)){return $Default}; $line=Get-Content .env|Where-Object{$_ -match "^\s*$([regex]::Escape($Name))="}|Select-Object -First 1; if(-not $line){return $Default}; return ($line -replace "^\s*$([regex]::Escape($Name))=","").Trim().Trim('"').Trim("'") }

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($Name -notmatch '^[a-zA-Z0-9._-]+$') { throw "Snapshot name must contain only letters, numbers, dot, underscore, or hyphen." }
    $path=Join-Path data\demo-snapshots "$Name.sql"; if(-not(Test-Path -LiteralPath $path)){throw "Snapshot not found: $path"}
    .\scripts\reset-stage-9-demo-state.ps1 -KeepGeneratedFiles
    $postgresUser=Get-DotEnvValue "POSTGRES_USER" "maintenance_triage"; $postgresDb=Get-DotEnvValue "POSTGRES_DB" "maintenance_triage"
    Get-Content -Raw -LiteralPath $path | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host
    $repairTicketRefSequence = @"
WITH max_ref AS (
  SELECT max(substring(ref FROM '^MR-([0-9]+)$')::bigint) AS value
  FROM triage.tickets
  WHERE ref ~ '^MR-[0-9]+$'
)
SELECT setval('triage.ticket_ref_seq', coalesce(value, 1), value IS NOT NULL)
FROM max_ref;
"@
    $repairTicketRefSequence | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host
    Write-Host "Restored Stage 9 local demo snapshot from $path"
}
finally { Pop-Location }
