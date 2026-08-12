[CmdletBinding()]
param(
    [switch]$LivePrerequisites
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue { param([string]$Name,[string]$Default) if(-not(Test-Path .env)){return $Default}; $line=Get-Content .env|Where-Object{$_ -match "^\s*$([regex]::Escape($Name))="}|Select-Object -First 1; if(-not $line){return $Default}; return ($line -replace "^\s*$([regex]::Escape($Name))=","").Trim().Trim('"').Trim("'") }
function Assert-Scalar { param([string]$Label,[string]$Sql,[string]$Expected,[string]$User,[string]$Db) $actual=(docker compose exec -T postgres psql -U $User -d $Db -At -v ON_ERROR_STOP=1 -c $Sql | Select-Object -First 1).Trim(); if($actual -ne $Expected){throw "$Label expected $Expected, got $actual"}; Write-Host "OK: $Label" }

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    python -m py_compile scripts\build-stage-4-workflows.py scripts\build-stage-9-workflows.py scripts\setup-stage-9-airtable.py
    python .\scripts\build-stage-4-workflows.py | Out-Host
    python .\scripts\build-stage-9-workflows.py | Out-Host
    @("maintenance-triage-core.json","maintenance-triage-tenant-intake.json","maintenance-triage-tenant-telegram.json","maintenance-triage-manager-desk.json","maintenance-triage-operations.json","maintenance-triage-demo-tools.json") | ForEach-Object { Get-Content -Raw "workflows\$_" | ConvertFrom-Json | Out-Null }
    docker compose config | Out-Null
    .\scripts\apply-stage-9.ps1
    $user=Get-DotEnvValue "POSTGRES_USER" "maintenance_triage"; $db=Get-DotEnvValue "POSTGRES_DB" "maintenance_triage"
    Assert-Scalar "Stage 9 tables" "select count(*) from information_schema.tables where table_schema='triage' and table_name in ('tenant_chats','tenant_pairing_tokens','ticket_messages','vendor_send_attempts','ticket_vendor_candidates');" "5" $user $db
    Assert-Scalar "Stage 9 ticket columns" "select count(*) from information_schema.columns where table_schema='triage' and table_name='tickets' and column_name in ('tenant_chat_id','clarification_round','vendor_status','selected_vendor_id','airtable_record_id');" "5" $user $db
    Assert-Scalar "Stage 9 configuration" "select count(*) from triage.config where key in ('tenant_telegram','airtable','system_mail');" "3" $user $db
    if($LivePrerequisites) {
      Assert-Scalar "Airtable configured" "select count(*) from triage.config where key='airtable' and value->>'enabled'='true' and coalesce(value->>'base_id','')<>'';" "1" $user $db
      Assert-Scalar "Tenant bot configured" "select count(*) from triage.config where key='tenant_telegram' and value->>'bot_username' not like 'PLACEHOLDER%';" "1" $user $db
      Write-Host "Live prerequisite configuration is present. Verify the Airtable and tenant Telegram credentials in n8n before publishing triggers."
    }
    Write-Host "Stage 9 structural validation passed."
}
finally { Pop-Location }
