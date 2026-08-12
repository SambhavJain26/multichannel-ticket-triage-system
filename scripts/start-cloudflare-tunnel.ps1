[CmdletBinding()]
param(
    [string]$Url = "http://localhost:5678"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    throw "cloudflared was not found on PATH. Install Cloudflare Tunnel or use another HTTPS tunnel."
}

Write-Host "Starting temporary Cloudflare Tunnel for $Url"
Write-Host "Copy the trycloudflare.com HTTPS URL into .env as N8N_WEBHOOK_URL, then recreate n8n before activating Telegram triggers."
Write-Host "Keep this terminal open while testing Telegram callback webhooks."
cloudflared tunnel --url $Url
