[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BaseId,
    [Parameter(Mandatory = $true)][string]$BaseUrl,
    [Parameter(Mandatory = $true)][string]$TenantBotUsername
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

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $escapedBaseId = $BaseId.Replace("'", "''")
    $escapedBaseUrl = $BaseUrl.TrimEnd('/').Replace("'", "''")
    $escapedBot = $TenantBotUsername.TrimStart('@').Replace("'", "''")
    $sql = @"
update triage.config
set value = value || jsonb_build_object('enabled', true, 'base_id', '$escapedBaseId', 'base_url', '$escapedBaseUrl')
where key = 'airtable';
update triage.config
set value = value || jsonb_build_object('bot_username', '$escapedBot')
where key = 'tenant_telegram';
"@
    $sql | docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -f -
    Write-Host "Saved Airtable base and tenant bot username in local Postgres config."
}
finally {
    Pop-Location
}
