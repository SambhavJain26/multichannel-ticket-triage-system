[CmdletBinding()]
param(
    [switch]$PublishLiveTriggers,
    [switch]$CleanupLegacy
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

function Get-CredentialMap {
    param([string]$PostgresUser, [string]$PostgresDb)

    $rows = docker compose exec -T postgres psql -U $PostgresUser -d $PostgresDb -At -F "|" -v ON_ERROR_STOP=1 -c "select id, name, type from credentials_entity order by name;"
    $map = @{}
    foreach ($row in $rows) {
        $parts = ([string]$row).Split("|", 3)
        if ($parts.Count -ne 3) { continue }
        $key = "$($parts[1])|$($parts[2])"
        if ($map.ContainsKey($key)) {
            throw "Multiple n8n credentials match '$key'. Keep one credential with that name and type before importing."
        }
        $map[$key] = $parts[0]
    }
    return $map
}

function Write-WorkflowWithResolvedCredentials {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [hashtable]$CredentialMap
    )

    $workflow = Get-Content -Raw $SourcePath | ConvertFrom-Json
    foreach ($node in @($workflow.nodes)) {
        $credentialsProperty = $node.PSObject.Properties["credentials"]
        if ($null -eq $credentialsProperty -or $null -eq $credentialsProperty.Value) { continue }
        foreach ($credentialProperty in @($credentialsProperty.Value.PSObject.Properties)) {
            $credential = $credentialProperty.Value
            $credentialName = [string]$credential.name
            if ([string]::IsNullOrWhiteSpace($credentialName)) {
                throw "Node '$($node.name)' has a credential without a name."
            }
            $key = "$credentialName|$($credentialProperty.Name)"
            if (-not $CredentialMap.ContainsKey($key)) {
                throw "n8n credential '$credentialName' of type '$($credentialProperty.Name)' was not found for node '$($node.name)'."
            }
            $credential.id = $CredentialMap[$key]
        }
    }
    $json = $workflow | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($DestinationPath, $json, (New-Object System.Text.UTF8Encoding($false)))
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
$stagingDir = $null
try {
    if ($CleanupLegacy -and -not $PublishLiveTriggers) {
        throw "-CleanupLegacy requires -PublishLiveTriggers. Do not retire working workflows before the replacement triggers are live."
    }
    python .\scripts\build-stage-4-workflows.py
    python .\scripts\build-stage-9-workflows.py
    $files = @(
        "maintenance-triage-core.json",
        "maintenance-triage-tenant-intake.json",
        "maintenance-triage-tenant-telegram.json",
        "maintenance-triage-manager-desk.json",
        "maintenance-triage-operations.json",
        "maintenance-triage-demo-tools.json"
    )
    $files | ForEach-Object { Get-Content -Raw "workflows\$_" | ConvertFrom-Json | Out-Null }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $credentialMap = Get-CredentialMap -PostgresUser $postgresUser -PostgresDb $postgresDb
    $projectId = docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -At -c "select id from project where type = 'personal' limit 1;"
    $projectId = (($projectId | Select-Object -First 1) -as [string]).Trim()
    if (-not $projectId) { throw "Could not find a personal n8n project." }

    $containerDir = "/tmp/maintenance-triage-stage-9"
    $stagingDir = Join-Path ([System.IO.Path]::GetTempPath()) ("maintenance-triage-stage-9-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $stagingDir | Out-Null
    $files | ForEach-Object {
        Write-WorkflowWithResolvedCredentials -SourcePath "workflows\$_" -DestinationPath (Join-Path $stagingDir $_) -CredentialMap $credentialMap
    }
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null
    docker compose exec -u root -T n8n mkdir -p $containerDir | Out-Null
    $files | ForEach-Object { docker compose cp (Join-Path $stagingDir $_) "n8n:$containerDir/$_" }
    $importOutput = docker compose exec -T n8n n8n import:workflow --separate --input=$containerDir --projectId=$projectId 2>&1
    $importOutput | Out-Host
    if ((($importOutput -join "`n") -match "(?i)error occurred|unexpected token|failed")) {
        throw "n8n reported an error while importing Stage 9 workflows."
    }
    docker compose exec -u root -T n8n rm -rf $containerDir | Out-Null

    $importIds = @("maintenance-triage-core-stage-4", "mt-tenant-intake-stage-9", "mt-tenant-telegram-stage-9", "mt-manager-desk-stage-9", "mt-operations-stage-9", "mt-demo-tools-stage-9")
    $quotedImportIds = ($importIds | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ","
    $importedCount = (docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -At -v ON_ERROR_STOP=1 -c "select count(*) from workflow_entity where id in ($quotedImportIds);" | Select-Object -First 1).Trim()
    if ($importedCount -ne $importIds.Count) {
        throw "Expected $($importIds.Count) Stage 9 workflow records after import, found $importedCount."
    }

    if ($PublishLiveTriggers) {
        @("maintenance-triage-core-stage-4", "mt-tenant-intake-stage-9", "mt-tenant-telegram-stage-9", "mt-manager-desk-stage-9", "mt-operations-stage-9") | ForEach-Object {
            docker compose exec -T n8n n8n publish:workflow --id=$_ | Out-Host
        }
        if ($CleanupLegacy) {
            $legacy = @("mt-alert-dispatch-stage-6", "mt-approval-action-stage-6", "maintenance-triage-board-stage-5", "mt-digest-stage-8", "mt-email-ingest-stage-7", "mt-emergency-escalation-stage-6", "mt-fixture-fire-stage-7", "mt-form-ingest-stage-7", "mt-import-bridge-stage-7", "mt-heartbeat-stage-8", "mt-post-ingest-stage-7", "maintenance-triage-stage-4-driver", "mt-stage-6-driver", "mt-telegram-callback-stage-6")
            $quoted = ($legacy | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ","
            docker compose exec -T postgres psql -U $postgresUser -d $postgresDb -v ON_ERROR_STOP=1 -c "update workflow_entity set active=false where id in ($quoted);" | Out-Host
            Write-Host "Legacy workflows were deactivated, not deleted. Their exports remain available for rollback."
        }
        docker compose restart n8n | Out-Host
    }
    else {
        Write-Host "Stage 9 workflows imported but not published. Create the Airtable and tenant Telegram credentials, configure a public HTTPS N8N_WEBHOOK_URL, then use -PublishLiveTriggers."
    }
}
finally {
    if ($stagingDir -and (Test-Path -LiteralPath $stagingDir)) {
        Remove-Item -LiteralPath $stagingDir -Recurse -Force
    }
    Pop-Location
}
