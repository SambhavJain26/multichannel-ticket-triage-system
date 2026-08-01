[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$EmailAddress,
    [string]$AppPassword,
    [string]$ImapHost = "imap.gmail.com",
    [int]$ImapPort = 993,
    [string]$SmtpHost = "smtp.gmail.com",
    [int]$SmtpPort = 587
)

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

    if (-not $AppPassword) {
        $securePassword = Read-Host -Prompt "App password for $EmailAddress" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        try {
            $AppPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        }
        finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }

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
            id   = "stage7DemoImapDomain"
            name = "maintenance-triage-demo-imap-domain"
            type = "imap"
            data = @{
                host                   = $ImapHost
                port                   = $ImapPort
                user                   = $EmailAddress
                password               = $AppPassword
                secure                 = $true
                allowUnauthorizedCerts = $false
            }
        },
        @{
            id   = "stage7DemoSmtpDomain"
            name = "maintenance-triage-demo-smtp-domain"
            type = "smtp"
            data = @{
                host            = $SmtpHost
                port            = $SmtpPort
                user            = $EmailAddress
                password        = $AppPassword
                secure          = $false
                disableStartTls = $false
                hostName        = ""
            }
        }
    )

    New-Item -ItemType Directory -Force -Path "tmp" | Out-Null
    $hostImportPath = Join-Path (Resolve-Path "tmp") "n8n-demo-mail-credentials-import.json"
    $containerImportPath = "/tmp/n8n-demo-mail-credentials-import.json"

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

    $escapedEmail = $EmailAddress.Replace("'", "''")
    docker compose exec -T postgres psql `
        -U $postgresUser `
        -d $postgresDb `
        -v ON_ERROR_STOP=1 `
        -c "insert into triage.config (key, value) values ('outbound_email', jsonb_build_object('mode','live','from_email','$escapedEmail','from_name','Demo Maintenance Desk','message_id_domain', split_part('$escapedEmail','@',2))) on conflict (key) do update set value = triage.config.value || excluded.value;" | Out-Host

    Assert-CredentialExists -Name "maintenance-triage-demo-imap-domain" -PostgresUser $postgresUser -PostgresDb $postgresDb
    Assert-CredentialExists -Name "maintenance-triage-demo-smtp-domain" -PostgresUser $postgresUser -PostgresDb $postgresDb

    Write-Host ""
    Write-Host "Imported demo mailbox credentials into project ${projectId}:"
    Write-Host "- maintenance-triage-demo-imap-domain"
    Write-Host "- maintenance-triage-demo-smtp-domain"
    Write-Host "Updated triage.config.outbound_email for live approved replies from $EmailAddress."
}
finally {
    Pop-Location
}
