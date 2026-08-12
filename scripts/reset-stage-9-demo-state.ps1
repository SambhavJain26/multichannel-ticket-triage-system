[CmdletBinding()]
param(
    [switch]$KeepGeneratedFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
    param([string]$Name, [string]$Default)
    if (-not (Test-Path -LiteralPath ".env")) { return $Default }
    $line = Get-Content -LiteralPath ".env" | Where-Object { $_ -match "^\s*$([regex]::Escape($Name))=" } | Select-Object -First 1
    if (-not $line) { return $Default }
    return ($line -replace "^\s*$([regex]::Escape($Name))=", "").Trim().Trim('"').Trim("'")
}

function Clear-DirectoryChildren {
    param([string]$Path)
    $dataRoot = Join-Path (Resolve-Path ".").Path "data"
    if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null; return }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $resolved.StartsWith($dataRoot, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to clear outside local data: $resolved" }
    Get-ChildItem -LiteralPath $resolved -Force | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $sql = @"
truncate triage.ticket_vendor_candidates, triage.vendor_send_attempts, triage.ticket_messages, triage.tenant_pairing_tokens, triage.tenant_chats, triage.import_items, triage.import_batches, triage.feedback, triage.events, triage.tickets;
alter sequence triage.ticket_ref_seq restart with 1;
update triage.config set value = value || jsonb_build_object('consecutive_model_failures',0,'degraded_until',null,'degraded_alerted_at',null,'llm_calls_today',0,'llm_call_day',null,'last_model_failure_at',null,'last_model_success_at',null) where key='runtime_state';
update triage.config set value = value || jsonb_build_object('baseline_at',now(),'last_alert_at',null,'last_checked_at',null) where key='heartbeat';
"@
    $sql | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f - | Out-Host
    if (-not $KeepGeneratedFiles) { Clear-DirectoryChildren "data\attachments"; Clear-DirectoryChildren "data\import-batches" }
    Write-Host "Stage 9 local demo state reset. Internal IDs were not reused, so old Telegram approval buttons remain invalid."
    Write-Host "Airtable configuration, unit roster, credentials, and workflows were preserved."
}
finally { Pop-Location }
