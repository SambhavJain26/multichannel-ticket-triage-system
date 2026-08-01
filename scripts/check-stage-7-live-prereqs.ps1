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

    $imapCount = Invoke-ScalarSql -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-demo-imap-domain' and type = 'imap';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    $smtpCount = Invoke-ScalarSql -Sql "select count(*) from credentials_entity where name = 'maintenance-triage-demo-smtp-domain' and type = 'smtp';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if ($imapCount -ne "1") {
        throw "Missing n8n IMAP credential maintenance-triage-demo-imap-domain. Run .\scripts\import-demo-mail-credentials.ps1 -EmailAddress <mailbox> and enter the app password."
    }
    if ($smtpCount -ne "1") {
        throw "Missing n8n SMTP credential maintenance-triage-demo-smtp-domain. Run .\scripts\import-demo-mail-credentials.ps1 -EmailAddress <mailbox> and enter the app password."
    }

    $fromEmail = Invoke-ScalarSql -Sql "select coalesce(value->>'from_email','') from triage.config where key='outbound_email';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    $mode = Invoke-ScalarSql -Sql "select coalesce(value->>'mode','') from triage.config where key='outbound_email';" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if ($mode -ne "live") {
        throw "triage.config.outbound_email.mode must be live for Stage 7 real mailbox validation."
    }
    if (-not $fromEmail -or $fromEmail -eq "PLACEHOLDER_DEMO_MAILBOX" -or $fromEmail -match "@example\.test$") {
        throw "triage.config.outbound_email.from_email is still a placeholder. Re-run import-demo-mail-credentials.ps1."
    }

    $published = Invoke-ScalarSql -Sql "select count(*) from workflow_entity where id in ('mt-email-ingest-stage-7','mt-form-ingest-stage-7','mt-import-bridge-stage-7') and active = true;" -PostgresUser $postgresUser -PostgresDb $postgresDb
    if ($published -ne "3") {
        throw "Stage 7 live ingestion workflows are not all published. Run .\scripts\import-stage-7-workflows.ps1 -PublishLiveTriggers."
    }

    Write-Host "Stage 7 live prerequisites passed for $fromEmail."
}
finally {
    Pop-Location
}
