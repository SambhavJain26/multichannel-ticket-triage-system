[CmdletBinding()]
param([int]$Runs = 5)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue { param([string]$Name,[string]$Default) if(-not(Test-Path .env)){return $Default}; $line=Get-Content .env|Where-Object{$_ -match "^\s*$([regex]::Escape($Name))="}|Select-Object -First 1; if(-not $line){return $Default}; return ($line -replace "^\s*$([regex]::Escape($Name))=","").Trim().Trim('"').Trim("'") }
function Assert-Scalar { param([string]$Label,[string]$Sql,[string]$Expected,[string]$User,[string]$Db) $actual=(docker compose exec -T postgres psql -U $User -d $Db -At -v ON_ERROR_STOP=1 -c $Sql | Select-Object -First 1).Trim(); if($actual -ne $Expected){throw "$Label expected $Expected, got $actual"}; Write-Host "OK: $Label" }

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if($Runs -lt 1){throw "Runs must be at least 1."}
    $user=Get-DotEnvValue "POSTGRES_USER" "maintenance_triage"; $db=Get-DotEnvValue "POSTGRES_DB" "maintenance_triage"
    $expected="select count(*) from workflow_entity where id in ('maintenance-triage-core-stage-4','mt-demo-tools-stage-9') and active=true;"
    $active=(docker compose exec -T postgres psql -U $user -d $db -At -c $expected | Select-Object -First 1).Trim()
    if($active -ne '1'){throw "Publish the Stage 9 Triage Engine first. Demo Tools intentionally stays inactive but can run through n8n CLI."}
    for($run=1;$run -le $Runs;$run++) {
        Write-Host "Stage 9 rehearsal run $run of $Runs..."
        .\scripts\reset-stage-9-demo-state.ps1 | Out-Host
        docker compose stop n8n | Out-Host
        try {
            docker compose run --rm --no-deps -T n8n execute --id=mt-demo-tools-stage-9 | Out-Host
            if($LASTEXITCODE -ne 0){throw "Demo tools execution failed."}
        }
        finally { docker compose up -d n8n | Out-Host }
        Assert-Scalar "run $run ticket count" "select count(*) from triage.tickets;" "6" $user $db
        Assert-Scalar "run $run expected priorities" "select count(*) from triage.tickets where (subject in ('01-understated-gas','02-panicked-burst-pipe-no-unit') and priority='EMERGENCY') or (subject in ('04-buried-lede','05-spanish-no-hot-water') and priority='URGENT') or (subject in ('03-urgent-squeaky-door','06-accommodation-request') and priority='ROUTINE');" "6" $user $db
        Assert-Scalar "run $run no vendor send attempts" "select count(*) from triage.vendor_send_attempts;" "0" $user $db
        Assert-Scalar "run $run no tenant messages" "select count(*) from triage.ticket_messages;" "0" $user $db
    }
    Write-Host "Stage 9 fixture rehearsal passed across $Runs clean run(s)."
}
finally { Pop-Location }
