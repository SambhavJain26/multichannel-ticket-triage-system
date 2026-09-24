#Requires -Version 5.1
<#
.SYNOPSIS
    Render an Automation Concept Brief HTML file to a print-ready, pixel-perfect PDF.

.DESCRIPTION
    Uses headless Microsoft Edge or Google Chrome with an isolated user profile
    to render Letter-sized (8.5in x 11in) client-facing concept briefs.
    Verifies that the PDF was generated and reports page count and file size.

.PARAMETER Source
    Path to the HTML brief file to render.
    Defaults to concept-brief\examples\maintenance-triage-brief.html.

.PARAMETER Output
    Path to save the resulting PDF.
    Defaults to the same filename with a .pdf extension.

.EXAMPLE
    .\scripts\render-pdf.ps1

.EXAMPLE
    .\scripts\render-pdf.ps1 -Source "template.html" -Output "concept-brief.pdf"
#>

[CmdletBinding()]
param(
    [string] $Source,
    [string] $Output,
    [int]    $VirtualTimeBudget = 4000
)

$ErrorActionPreference = 'Stop'

$scriptDir = $PSScriptRoot
$conceptDir = Split-Path -Parent $scriptDir

# Resolve Default Source
if (-not $Source) {
    $Source = Join-Path $conceptDir "examples\maintenance-triage-brief.html"
}

if (-not (Test-Path $Source)) {
    throw "Source HTML file not found: $Source"
}

$sourceItem = Get-Item $Source

# Resolve Default Output
if (-not $Output) {
    $Output = Join-Path $sourceItem.DirectoryName ($sourceItem.BaseName + ".pdf")
}

$outItem = [System.IO.Path]::GetFullPath($Output)
$outDir  = Split-Path -Parent $outItem
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# Find Chrome or Edge
function Find-Browser {
    $candidates = @(
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    throw "No Microsoft Edge or Google Chrome executable found on this machine."
}

$browser = Find-Browser
Write-Host "Rendering using: $browser" -ForegroundColor Cyan
Write-Host "Source:  $($sourceItem.FullName)"
Write-Host "Target:  $outItem"

$profileDir = Join-Path $env:TEMP ('brief-render-' + [guid]::NewGuid().ToString('N'))
$url = 'file:///' + ($sourceItem.FullName -replace '\\', '/')

$browserArgs = @(
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--no-pdf-header-footer',
    '--run-all-compositor-stages-before-draw',
    "--user-data-dir=$profileDir",
    "--virtual-time-budget=$VirtualTimeBudget",
    "--print-to-pdf=$outItem",
    $url
)

$proc = Start-Process -FilePath $browser -ArgumentList $browserArgs -NoNewWindow -Wait -PassThru

# Clean up temporary profile dir if practical
if (Test-Path $profileDir) {
    try { Remove-Item -Path $profileDir -Recurse -Force -ErrorAction SilentlyContinue } catch {}
}

if ($proc.ExitCode -ne 0 -or -not (Test-Path $outItem)) {
    throw "Failed to render PDF (Process Exit Code: $($proc.ExitCode))"
}

# Inspect PDF Page Count and Metadata
$bytes = [System.IO.File]::ReadAllBytes($outItem)
$txt   = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
$pages = ([regex]::Matches($txt, '/Type\s*/Page(?![s])')).Count
$sizeKb = [math]::Round($bytes.Length / 1KB, 1)

Write-Host "[OK] PDF Rendered successfully!" -ForegroundColor Green
Write-Host "  Pages:     $pages pages" -ForegroundColor Yellow
Write-Host "  File Size: $sizeKb KB" -ForegroundColor Yellow
Write-Host "  Output:    $outItem" -ForegroundColor Green

if ($pages -gt 3) {
    Write-Warning "The document rendered $pages pages. Standard brief target is 3 pages."
}
