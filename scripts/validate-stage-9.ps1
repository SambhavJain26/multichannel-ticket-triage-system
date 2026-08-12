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
    python -m py_compile scripts\build-stage-4-workflows.py scripts\build-stage-9-workflows.py scripts\setup-stage-9-airtable.py scripts\sync-stage-9-airtable.py
    python .\scripts\build-stage-4-workflows.py | Out-Host
    python .\scripts\build-stage-9-workflows.py | Out-Host
    @("maintenance-triage-core.json","maintenance-triage-tenant-intake.json","maintenance-triage-tenant-telegram.json","maintenance-triage-manager-desk.json","maintenance-triage-operations.json","maintenance-triage-demo-tools.json") | ForEach-Object { Get-Content -Raw "workflows\$_" | ConvertFrom-Json | Out-Null }
    node .\scripts\test-stage-9-conversation-routing.js | Out-Host
    docker compose config | Out-Null
    .\scripts\apply-stage-4.ps1 | Out-Host
    .\scripts\apply-stage-9.ps1
    $user=Get-DotEnvValue "POSTGRES_USER" "maintenance_triage"; $db=Get-DotEnvValue "POSTGRES_DB" "maintenance_triage"
    Assert-Scalar "Stage 9 tables" "select count(*) from information_schema.tables where table_schema='triage' and table_name in ('tenant_chats','tenant_pairing_tokens','ticket_messages','vendor_send_attempts','ticket_vendor_candidates','airtable_roster_links');" "6" $user $db
    Assert-Scalar "Stage 9 ticket columns" "select count(*) from information_schema.columns where table_schema='triage' and table_name='tickets' and column_name in ('tenant_chat_id','clarification_round','vendor_status','selected_vendor_id','airtable_record_id');" "5" $user $db
    Assert-Scalar "Stage 9 configuration" "select count(*) from triage.config where key in ('tenant_telegram','airtable','system_mail');" "3" $user $db
    Assert-Scalar "Ticket reference allocator" "select count(*) from pg_proc where oid = 'triage.next_ticket_ref()'::regprocedure;" "1" $user $db
    if((Get-Content -Raw workflows\maintenance-triage-core.json) -notmatch 'triage\.next_ticket_ref\(\)') { throw "Core workflow does not use the safe ticket-reference allocator." }
    $managerWorkflow = Get-Content -Raw workflows\maintenance-triage-manager-desk.json | ConvertFrom-Json
    $keyboardNodes = @($managerWorkflow.nodes | Where-Object { $_.name -like 'Telegram Send Manager Keyboard *' })
    $emptyKeyboardNodes = @($keyboardNodes | Where-Object { $_.parameters.inlineKeyboard.rows.Count -eq 0 })
    if($keyboardNodes.Count -ne 4 -or $emptyKeyboardNodes.Count -gt 0) { throw "Manager keyboard variants are incomplete." }
    if((Get-Content -Raw workflows\maintenance-triage-manager-desk.json) -match 'No additional vendor') { throw "Manager workflow still contains placeholder vendor buttons." }
    $managerAlert = $managerWorkflow.nodes | Where-Object { $_.name -eq 'Prepare Manager Vendor Alert' } | Select-Object -First 1
    $managerUpsert = $managerWorkflow.nodes | Where-Object { $_.name -eq 'Prepare Airtable Request Upsert' } | Select-Object -First 1
    if($managerAlert.parameters.jsCode -notmatch 'vendor_dispatch_eligible' -or $managerAlert.parameters.jsCode -notmatch 'should_send_manager:Boolean\(ticket.id') { throw "Manager review notifications are not safely routed." }
    if($managerUpsert.parameters.jsCode -notmatch 'const add =') { throw "Airtable request sync can write empty select values." }
    if($managerUpsert.parameters.jsCode -notmatch "PET_ON_SITE") { throw "Airtable request sync does not handle legacy Missing Info choice sets." }
    $tenantWorkflow = Get-Content -Raw workflows\maintenance-triage-tenant-telegram.json | ConvertFrom-Json
    if(-not ($tenantWorkflow.nodes | Where-Object { $_.name -eq 'Prepare Direct Telegram Welcome' })) { throw "Tenant direct Telegram welcome path is missing." }
    if(-not ($tenantWorkflow.nodes | Where-Object { $_.name -eq 'Reattach Tenant Event Context' })) { throw "Tenant Telegram database lookup drops its event context." }
    if($tenantWorkflow.connections.'Postgres Load Tenant Chat'.main[0][0].node -ne 'Reattach Tenant Event Context') { throw "Tenant Telegram context is not restored before routing." }
    $tenantRoute = $tenantWorkflow.nodes | Where-Object { $_.name -eq 'Route Tenant Message' } | Select-Object -First 1
    if($tenantRoute.parameters.jsCode -notmatch 'isStatusQuestion' -or $tenantRoute.parameters.jsCode -notmatch 'resolved') { throw "Tenant status routing does not cover conversational completion questions." }
    if($tenantRoute.parameters.jsCode -match 'clarification_round\s*\|\|\s*0\)\s*<\s*2') { throw "Tenant clarification still has a two-round cap." }
    $tenantReceipt = $tenantWorkflow.nodes | Where-Object { $_.name -eq 'Prepare New Ticket Tenant Reply' } | Select-Object -First 1
    $clarificationResponse = $tenantWorkflow.nodes | Where-Object { $_.name -eq 'Prepare Clarification Response' } | Select-Object -First 1
    if($tenantReceipt.parameters.jsCode -match 'contact number' -or $clarificationResponse.parameters.jsCode -match 'contact number') { throw "Tenant Telegram still asks for a phone number despite having a reply channel." }
    if($tenantReceipt.parameters.jsCode -match 'Which property and unit is this for\?' -or $clarificationResponse.parameters.jsCode -match 'Which property and unit is this for\?') { throw "Dedicated tenant Telegram still asks for a configured location." }
    if($tenantReceipt.parameters.jsCode -notmatch 'PET_ON_SITE' -or $clarificationResponse.parameters.jsCode -notmatch 'PET_ON_SITE') { throw "Tenant clarification does not cover pet access details." }
    if($clarificationResponse.parameters.jsCode -notmatch 'hasClarificationPrompt') { throw "Tenant clarification does not keep asking while required details are missing." }
    if($clarificationResponse.parameters.jsCode -notmatch 'should_notify_manager:readyForVendor \|\| needsManager') { throw "Completed or review-required clarification replies do not reach the manager." }
    if(-not ($tenantWorkflow.nodes | Where-Object { $_.name -eq 'Decide New Ticket Manager Notification' })) { throw "New tenant requests still notify the manager before their missing details are resolved." }
    if($tenantWorkflow.connections.'Postgres Link New Tenant Ticket'.main[0][0].node -ne 'Decide New Ticket Manager Notification') { throw "New tenant requests bypass the missing-details manager gate." }
    $coreWorkflow = Get-Content -Raw workflows\maintenance-triage-core.json | ConvertFrom-Json
    $coreRules = $coreWorkflow.nodes | Where-Object { $_.name -eq 'Apply Safety Rules' } | Select-Object -First 1
    if($coreRules.parameters.jsCode -notmatch 'value !== "CONTACT"') { throw "The triage engine does not remove CONTACT when a reply channel is already available." }
    if($coreRules.parameters.jsCode -notmatch 'labeledValue' -or $coreRules.parameters.jsCode -notmatch 'safetyTrade' -or $coreRules.parameters.jsCode -notmatch 'routineFanFailure') { throw "The triage engine does not preserve trusted profile data or known maintenance trade routing." }
    $newTicketPayload = $tenantWorkflow.nodes | Where-Object { $_.name -eq 'Prepare New Ticket Payload' } | Select-Object -First 1
    if($newTicketPayload.parameters.jsCode -notmatch 'tenant_profile' -or $newTicketPayload.parameters.jsCode -notmatch 'Property:') { throw "Dedicated tenant Telegram does not inject its known tenant profile." }
    if($newTicketPayload.parameters.jsCode -notmatch 'tenant_email') { throw "Dedicated tenant Telegram does not preserve its roster identity." }
    $vendorEmail = $managerWorkflow.nodes | Where-Object { $_.name -eq 'Prepare Vendor Email' } | Select-Object -First 1
    if($vendorEmail.parameters.jsCode -notmatch 'Could you please take a look at') { throw "Vendor email body is not the natural property-office format." }
    if($vendorEmail.parameters.jsCode -notmatch 'vendor_subject_prefix' -or $vendorEmail.parameters.jsCode -notmatch '\[MT-SYSTEM\]\[VENDOR\]') { throw "Vendor email does not carry the shared-mailbox loop marker." }
    if((Get-Content -Raw scripts\setup-stage-9-airtable.py) -notmatch 'PET_ON_SITE') { throw "New Airtable demo tables omit the PET_ON_SITE Missing Info option." }
    Write-Host "OK: manager keyboard variants and direct Telegram intake"
    if($LivePrerequisites) {
      Assert-Scalar "Airtable configured" "select count(*) from triage.config where key='airtable' and value->>'enabled'='true' and coalesce(value->>'base_id','')<>'';" "1" $user $db
      Assert-Scalar "Tenant bot configured" "select count(*) from triage.config where key='tenant_telegram' and value->>'bot_username' not like 'PLACEHOLDER%';" "1" $user $db
      Write-Host "Live prerequisite configuration is present. Verify the Airtable and tenant Telegram credentials in n8n before publishing triggers."
    }
    Write-Host "Stage 9 structural validation passed."
}
finally { Pop-Location }
