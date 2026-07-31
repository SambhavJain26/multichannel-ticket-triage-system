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
Write-Host "Copy the trycloudflare.com HTTPS URL into n8n only for temporary callback testing."
Write-Host "Keep this terminal open while testing Telegram callback webhooks."
cloudflared tunnel --url $Url
