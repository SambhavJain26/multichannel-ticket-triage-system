[CmdletBinding()]
param([string]$Name = "clean")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue { param([string]$Name,[string]$Default) if(-not(Test-Path .env)){return $Default}; $line=Get-Content .env|Where-Object{$_ -match "^\s*$([regex]::Escape($Name))="}|Select-Object -First 1; if(-not $line){return $Default}; return ($line -replace "^\s*$([regex]::Escape($Name))=","").Trim().Trim('"').Trim("'") }

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($Name -notmatch '^[a-zA-Z0-9._-]+$') { throw "Snapshot name must contain only letters, numbers, dot, underscore, or hyphen." }
    $postgresUser=Get-DotEnvValue "POSTGRES_USER" "maintenance_triage"; $postgresDb=Get-DotEnvValue "POSTGRES_DB" "maintenance_triage"
    New-Item -ItemType Directory -Force -Path data\demo-snapshots | Out-Null
    docker compose exec -T postgres pg_dump -U $postgresUser -d $postgresDb --data-only --column-inserts --table=triage.tickets --table=triage.events --table=triage.feedback --table=triage.import_batches --table=triage.import_items --table=triage.tenant_chats --table=triage.tenant_pairing_tokens --table=triage.ticket_messages --table=triage.ticket_vendor_candidates --table=triage.vendor_send_attempts | Set-Content -LiteralPath (Join-Path data\demo-snapshots "$Name.sql") -Encoding UTF8
    Write-Host "Saved Stage 9 local demo snapshot to data\demo-snapshots\$Name.sql"
}
finally { Pop-Location }
