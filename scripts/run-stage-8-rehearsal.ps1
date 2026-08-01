[CmdletBinding()]
param(
    [int]$Runs = 5
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

function Assert-Sql {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Sql,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$PostgresUser,
        [Parameter(Mandatory = $true)][string]$PostgresDb
    )

    $actual = Invoke-ScalarSql -Sql $Sql -PostgresUser $PostgresUser -PostgresDb $PostgresDb
    if ($actual -ne $Expected) {
        throw "$Label expected $Expected, got $actual"
    }
    Write-Host "OK: $Label = $actual"
}

function Wait-N8n {
    param([string]$Port)

    $deadline = (Get-Date).AddSeconds(90)
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    throw "n8n did not become reachable on port $Port."
}

function Invoke-N8nWorkflowCli {
    param([Parameter(Mandatory = $true)][string]$WorkflowId)

    docker compose stop n8n | Out-Host
    try {
        docker compose run --rm --no-deps -T n8n execute --id=$WorkflowId | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Workflow $WorkflowId failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        docker compose up -d n8n | Out-Host
    }
}

function Invoke-BoardCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][string]$Port
    )

    $uri = "http://localhost:$Port/webhook/board?t=$Token"
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 20
    if ($response.StatusCode -ne 200) {
        throw "Board expected HTTP 200, got $($response.StatusCode)."
    }
    if (-not $response.Content.Contains("Maintenance board")) {
        throw "Board did not render expected maintenance board text."
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($Runs -lt 1) {
        throw "Runs must be at least 1."
    }

    $postgresUser = Get-DotEnvValue -Name "POSTGRES_USER" -Default "maintenance_triage"
    $postgresDb = Get-DotEnvValue -Name "POSTGRES_DB" -Default "maintenance_triage"
    $n8nPort = Get-DotEnvValue -Name "N8N_PORT" -Default "5678"
    $token = Invoke-ScalarSql -Sql "select value->>'token' from triage.config where key='board';" -PostgresUser $postgresUser -PostgresDb $postgresDb

    $stability = @{}
    $fixtureId = "mt-fixture-fire-stage-7"
    for ($i = 1; $i -le $Runs; $i++) {
        Write-Host "Stage 8 rehearsal run $i of $Runs..."
        .\scripts\reset-stage-8-demo-state.ps1 | Out-Host
        Invoke-N8nWorkflowCli -WorkflowId $fixtureId
        Wait-N8n -Port $n8nPort

        Assert-Sql -Label "run $i ticket count" -Sql "select count(*) from triage.tickets;" -Expected "6" -PostgresUser $postgresUser -PostgresDb $postgresDb
        Assert-Sql -Label "run $i live priority matches" -Sql "select count(*) from triage.tickets where subject in ('01-understated-gas','02-panicked-burst-pipe-no-unit','03-urgent-squeaky-door','04-buried-lede','05-spanish-no-hot-water','06-accommodation-request') and ((subject in ('01-understated-gas','02-panicked-burst-pipe-no-unit') and priority = 'EMERGENCY') or (subject in ('04-buried-lede','05-spanish-no-hot-water') and priority = 'URGENT') or (subject in ('03-urgent-squeaky-door','06-accommodation-request') and priority = 'ROUTINE'));" -Expected "6" -PostgresUser $postgresUser -PostgresDb $postgresDb
        Assert-Sql -Label "run $i unit match events" -Sql "select count(*) from triage.events where action='unit_matched';" -Expected "6" -PostgresUser $postgresUser -PostgresDb $postgresDb
        Assert-Sql -Label "run $i real Telegram sends" -Sql "select count(*) from triage.events where action='telegram_alert_sent';" -Expected "0" -PostgresUser $postgresUser -PostgresDb $postgresDb
        Assert-Sql -Label "run $i safety overrides" -Sql "select count(*) from triage.events where action='overridden';" -Expected "2" -PostgresUser $postgresUser -PostgresDb $postgresDb
        Invoke-BoardCheck -Token $token -Port $n8nPort

        $rows = docker compose exec -T postgres psql `
            -U $postgresUser `
            -d $postgresDb `
            -At `
            -v ON_ERROR_STOP=1 `
            -c "select subject || '=' || priority from triage.tickets order by subject;"
        foreach ($row in $rows) {
            $text = (($row | Select-Object -First 1) -as [string]).Trim()
            if (-not $text) {
                continue
            }
            $parts = $text.Split("=", 2)
            if (-not $stability.ContainsKey($parts[0])) {
                $stability[$parts[0]] = New-Object System.Collections.Generic.List[string]
            }
            $stability[$parts[0]].Add($parts[1])
        }
    }

    foreach ($key in $stability.Keys) {
        $values = @($stability[$key])
        if (@($values | Select-Object -Unique).Count -ne 1) {
            throw "Fixture $key was unstable across runs: $($values -join ', ')"
        }
    }

    Write-Host ""
    Write-Host "Stage 8 fixture rehearsal passed across $Runs clean run(s)."
}
finally {
    Pop-Location
}
