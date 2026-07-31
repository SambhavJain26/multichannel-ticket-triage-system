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

function Assert-CredentialExists {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    $count = docker compose exec -T postgres psql `
        -U $PostgresUser `
        -d $PostgresDb `
        -At `
        -c "select count(*) from credentials_entity where name = '$Name';"

    $count = ($count | Select-Object -First 1).Trim()
    if ($count -ne "1") {
        throw "Expected exactly one n8n credential named $Name, found $count."
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath ".env")) {
        throw ".env is missing. Run .\scripts\start-local.ps1 first."
    }

    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresPassword = Get-DotEnvValue -Name "POSTGRES_PASSWORD" -Default "replace_with_local_postgres_password"
    $greenmailUser = Get-DotEnvValue -Name "GREENMAIL_USER" -Default "maintenance@example.test"
    $greenmailPassword = Get-DotEnvValue -Name "GREENMAIL_PASSWORD" -Default "greenmail-local-password"

    $projectId = docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -At `
        -c "select id from project where type = 'personal' limit 1;"

    $projectId = ($projectId | Select-Object -First 1).Trim()
    if (-not $projectId) {
        throw "Could not find a personal n8n project. Create the n8n owner account first."
    }

    $credentials = @(
        @{
            id   = "stage1PgLocal"
            name = "maintenance-triage-postgres-local"
            type = "postgres"
            data = @{
                host                   = "postgres"
                port                   = 5432
                database               = $postgresDb
                user                   = $postgresUser
                password               = $postgresPassword
                maxConnections         = 100
                allowUnauthorizedCerts = $false
                ssl                    = "disable"
            }
        },
        @{
            id   = "stage1ImapLocal"
            name = "maintenance-triage-greenmail-imap-local"
            type = "imap"
            data = @{
                host                   = "greenmail"
                port                   = 3143
                user                   = $greenmailUser
                password               = $greenmailPassword
                secure                 = $false
                allowUnauthorizedCerts = $false
            }
        },
        @{
            id   = "stage1SmtpLocal"
            name = "maintenance-triage-greenmail-smtp-local"
            type = "smtp"
            data = @{
                host            = "greenmail"
                port            = 3025
                user            = $greenmailUser
                password        = $greenmailPassword
                secure          = $false
                disableStartTls = $true
                hostName        = ""
            }
        }
    )

    New-Item -ItemType Directory -Force -Path "tmp" | Out-Null
    $hostImportPath = Join-Path (Resolve-Path "tmp") "n8n-local-credentials-import.json"
    $containerImportPath = "/tmp/n8n-local-credentials-import.json"

    try {
        $json = $credentials | ConvertTo-Json -Depth 10
        $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::WriteAllText($hostImportPath, $json, $utf8NoBom)
        docker compose cp $hostImportPath "n8n:$containerImportPath"
        docker compose exec -T n8n n8n import:credentials --input=$containerImportPath --projectId=$projectId
    }
    finally {
        Remove-Item -LiteralPath $hostImportPath -ErrorAction SilentlyContinue
        docker compose exec -u root -T n8n rm -f $containerImportPath | Out-Null
    }

    Assert-CredentialExists -Name "maintenance-triage-postgres-local" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-CredentialExists -Name "maintenance-triage-greenmail-imap-local" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-CredentialExists -Name "maintenance-triage-greenmail-smtp-local" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host ""
    Write-Host "Imported local n8n credentials into project ${projectId}:"
    Write-Host "- maintenance-triage-postgres-local"
    Write-Host "- maintenance-triage-greenmail-imap-local"
    Write-Host "- maintenance-triage-greenmail-smtp-local"
}
finally {
    Pop-Location
}
