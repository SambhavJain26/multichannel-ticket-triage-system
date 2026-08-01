[CmdletBinding()]
param()

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

function Invoke-ScalarSql {
    param(
        [Parameter(Mandatory = $true)][string]$Sql,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    $result = docker compose exec -T postgres psql `
        -U $PostgresUser `
        -d $PostgresDb `
        -At `
        -v ON_ERROR_STOP=1 `
        -c $Sql

    return (($result | Select-Object -First 1) -as [string]).Trim()
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $webhookUrl = Get-DotEnvValue -Name "N8N_WEBHOOK_URL" -Default ""

    $contacts = Invoke-ScalarSql -Sql "select value from triage.config where key = 'contacts';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    $hasRealPrimary = Invoke-ScalarSql -Sql "select case when coalesce((select value->>'primary_chat_id' from triage.config where key='contacts'), '') <> '' and coalesce((select value->>'primary_chat_id' from triage.config where key='contacts'), '') not like 'PLACEHOLDER_%' then 1 else 0 end;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    $hasHttpsWebhook = if ($webhookUrl -match "^https://") { "1" } else { "0" }

    Write-Host "Contacts config: $contacts"
    if ($hasRealPrimary -eq "1") {
        Write-Host "OK: primary_chat_id is configured."
    }
    else {
        Write-Host "MISSING: Set triage.config.contacts.primary_chat_id to a real Telegram chat ID."
    }

    if ($hasHttpsWebhook -eq "1") {
        Write-Host "OK: N8N_WEBHOOK_URL is HTTPS: $webhookUrl"
    }
    else {
        Write-Host "MISSING: Set N8N_WEBHOOK_URL to the current HTTPS tunnel URL before publishing the Telegram callback trigger."
    }

    if ($hasRealPrimary -eq "1" -and $hasHttpsWebhook -eq "1") {
        Write-Host "Stage 6 live Telegram prerequisites look ready."
    }
    else {
        Write-Host "Stage 6 automated validation can still run in mock mode."
    }
}
finally {
    Pop-Location
}
