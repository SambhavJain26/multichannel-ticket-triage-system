[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        Write-Host "Created local .env from .env.example. Review it before adding real credentials."
    }

    docker compose up -d
    Write-Host ""
    Write-Host "Local services are starting:"
    Write-Host "- n8n: http://localhost:5678"
    Write-Host "- Postgres: 127.0.0.1:5432"
    Write-Host "- GreenMail SMTP: 127.0.0.1:3025"
    Write-Host "- GreenMail IMAP: 127.0.0.1:3143"
    Write-Host "- GreenMail UI/API: http://localhost:8080"
    Write-Host ""
    Write-Host "Run .\scripts\validate-stage-1.ps1 once the containers are healthy."
}
finally {
    Pop-Location
}
