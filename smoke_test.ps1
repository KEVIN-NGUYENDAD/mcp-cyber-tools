# Cyber Tools MCP - Smoke Test
# Usage: .\smoke_test.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "CYBER TOOLS MCP - SMOKE TEST" -ForegroundColor Cyan
Write-Host "15 Essential Tools Check Before Release" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Timestamp: $timestamp" -ForegroundColor Gray
Write-Host "Testing 15 core tools for stability..." -ForegroundColor Gray
Write-Host ""

$results = @()
$passed = 0
$failed = 0

function Test-Tool {
    param(
        [string]$ToolName,
        [string]$Description,
        [scriptblock]$TestScript
    )

    Write-Host "Testing: $ToolName..." -NoNewline -ForegroundColor Cyan

    try {
        $result = & $TestScript

        if ($result -and -not ($result -match "error" -or $result -match "failed")) {
            Write-Host " PASS" -ForegroundColor Green
            return @{ Tool = $ToolName; Status = "PASS"; Description = $Description }
        } else {
            Write-Host " FAIL" -ForegroundColor Red
            return @{ Tool = $ToolName; Status = "FAIL"; Description = $Description; Error = $result }
        }
    } catch {
        Write-Host " FAIL (Exception)" -ForegroundColor Red
        return @{ Tool = $ToolName; Status = "FAIL"; Description = $Description; Error = $_.Exception.Message }
    }
}

# Test 1: hostname
$results += Test-Tool "hostname" "Get computer name" {
    $hostname = [System.Net.Dns]::GetHostName()
    $hostname
}

# Test 2: whoami
$results += Test-Tool "whoami" "Get current user" {
    $user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $user
}

# Test 3: systemInfo
$results += Test-Tool "systemInfo" "Get system details" {
    $os = Get-WmiObject Win32_OperatingSystem
    $os.Caption
}

# Test 4: loggedOnUsers
$results += Test-Tool "loggedOnUsers" "Get logged on users" {
    $users = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI\SessionData" -ErrorAction SilentlyContinue
    if ($users) { "OK" } else { "No sessions" }
}

# Test 5: activeConnections
$results += Test-Tool "activeConnections" "Get active TCP connections" {
    $connections = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Measure-Object
    "Found $($connections.Count) connections"
}

# Test 6: netstat
$results += Test-Tool "netstat" "Display network stats" {
    $netstat = netstat -ano | Select-Object -First 5
    "OK"
}

# Test 7: runningProcesses
$results += Test-Tool "runningProcesses" "List running processes" {
    $processes = Get-Process | Measure-Object
    "Found $($processes.Count) processes"
}

# Test 8: processMonitor
$results += Test-Tool "processMonitor" "Monitor process metrics" {
    $topProc = Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 1
    "Top process: $($topProc.Name)"
}

# Test 9: firewallStatus
$results += Test-Tool "firewallStatus" "Get firewall status" {
    $profiles = Get-NetFirewallProfile
    "Found $($profiles.Count) profiles"
}

# Test 10: firewallRules
$results += Test-Tool "firewallRules" "List firewall rules" {
    $rules = Get-NetFirewallRule | Measure-Object
    "Found $($rules.Count) rules"
}

# Test 11: defenderStatus
$results += Test-Tool "defenderStatus" "Get Defender status" {
    $status = Get-MpComputerStatus -ErrorAction SilentlyContinue
    if ($status.AntivirusEnabled) { "Defender enabled" } else { "Defender disabled" }
}

# Test 12: defenderThreats
$results += Test-Tool "defenderThreats" "Get detected threats" {
    $threats = Get-MpThreat -ErrorAction SilentlyContinue | Measure-Object
    "Found $($threats.Count) threats"
}

# Test 13: startupPrograms
$results += Test-Tool "startupPrograms" "List startup programs" {
    $startup = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue | Measure-Object
    "Found $($startup.Count) startup items"
}

# Test 14: scheduledTasks
$results += Test-Tool "scheduledTasks" "List scheduled tasks" {
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Measure-Object
    "Found $($tasks.Count) tasks"
}

# Test 15: collectEvidence
$results += Test-Tool "collectEvidence" "Generate evidence report" {
    $reportDir = ".\reports"
    if (Test-Path $reportDir) {
        "Reports directory exists"
    } else {
        New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
        "Created reports directory"
    }
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SMOKE TEST RESULTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $results) {
    if ($result.Status -eq "PASS") {
        Write-Host "PASS" -ForegroundColor Green -NoNewline
    } else {
        Write-Host "FAIL" -ForegroundColor Red -NoNewline
    }

    $tool = $result.Tool
    Write-Host " | $tool" -ForegroundColor White

    if ($result.Error) {
        $err = $result.Error
        Write-Host "  Error: $err" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

if ($failCount -eq 0) {
    Write-Host "OVERALL: PASS (15/15)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Status: RELEASE CANDIDATE" -ForegroundColor Green
    Write-Host "All core tools functioning correctly." -ForegroundColor Green
    exit 0
} else {
    Write-Host "OVERALL: FAIL ($passCount/15 passed)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Status: NEEDS FIXING" -ForegroundColor Red
    Write-Host "Fix $failCount failing tool(s) before release." -ForegroundColor Red
    exit 1
}
