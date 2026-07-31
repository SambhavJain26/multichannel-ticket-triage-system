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

function Assert-LocalPort {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        throw "$Name is not listening on local port $Port"
    }

    $loopbackOnly = $connections | Where-Object {
        $_.LocalAddress -in @("127.0.0.1", "::1")
    }

    if (-not $loopbackOnly) {
        throw "$Name is listening on port $Port, but not on loopback"
    }

    Write-Host "OK: $Name is listening on loopback port $Port"
}

function Wait-HttpOk {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Name,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host "OK: $Name responded with HTTP $($response.StatusCode)"
                return
            }

            $lastError = "$Name returned HTTP $($response.StatusCode)"
        }
        catch {
            $lastError = $_.Exception.Message
        }

        Start-Sleep -Seconds 2
    }

    throw "$Name did not respond at $Uri within $TimeoutSeconds seconds. Last error: $lastError"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath ".env")) {
        throw ".env is missing. Run .\scripts\start-local.ps1 first or copy .env.example to .env."
    }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $n8nPort = [int](Get-DotEnvValue -Name "N8N_PORT" -Default "5678")
    $postgresPort = [int](Get-DotEnvValue -Name "POSTGRES_PORT" -Default "5432")
    $greenmailSmtpPort = [int](Get-DotEnvValue -Name "GREENMAIL_SMTP_PORT" -Default "3025")
    $greenmailImapPort = [int](Get-DotEnvValue -Name "GREENMAIL_IMAP_PORT" -Default "3143")
    $greenmailUser = Get-DotEnvValue -Name "GREENMAIL_USER" -Default "maintenance@example.test"
    $greenmailPassword = Get-DotEnvValue -Name "GREENMAIL_PASSWORD" -Default "greenmail-local-password"

    Write-Host "Validating Docker Compose config..."
    docker compose config | Out-Null

    Write-Host "Checking container status..."
    docker compose ps

    Write-Host "Checking Postgres readiness..."
    docker compose exec -T postgres pg_isready -U $postgresUser -d $postgresDb | Out-Host

    Write-Host "Checking n8n HTTP endpoint..."
    Wait-HttpOk -Uri "http://localhost:$n8nPort" -Name "n8n"

    Assert-LocalPort -Port $n8nPort -Name "n8n"
    Assert-LocalPort -Port $postgresPort -Name "Postgres"

    Write-Host "Checking GreenMail SMTP/IMAP..."
    python .\scripts\greenmail-smoke-test.py `
        --host 127.0.0.1 `
        --smtp-port $greenmailSmtpPort `
        --imap-port $greenmailImapPort `
        --username $greenmailUser `
        --password $greenmailPassword

    Write-Host ""
    Write-Host "Stage 1 local runtime validation passed."
}
finally {
    Pop-Location
}
