# SentinelOps Installation Verification Script
# Run this after installing SentinelOps-Setup.exe to verify everything is working

param(
    [switch]$Verbose
)

Write-Host "=" * 60
Write-Host "SentinelOps Installation Verification" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

$errors = @()
$warnings = @()

# 1. Check if installation directory exists
Write-Host "1️⃣  Checking installation directory..." -ForegroundColor Yellow
$installPath = 'C:\Program Files\SentinelOps'
if (Test-Path $installPath) {
    Write-Host "   ✓ Directory found: $installPath" -ForegroundColor Green
    $files = Get-ChildItem $installPath -Recurse | Measure-Object
    Write-Host "   ✓ Contains $($files.Count) files/folders"
} else {
    $errors += "Installation directory not found at $installPath"
    Write-Host "   ✗ Directory not found" -ForegroundColor Red
}

# 2. Check if agent binary exists
Write-Host ""
Write-Host "2️⃣  Checking agent binary..." -ForegroundColor Yellow
$agentExe = Join-Path $installPath 'sentinel_agent.exe'
if (Test-Path $agentExe) {
    $fileInfo = Get-Item $agentExe
    Write-Host "   ✓ Binary found: $agentExe" -ForegroundColor Green
    Write-Host "   ✓ Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB"
} else {
    $errors += "Agent binary not found at $agentExe"
    Write-Host "   ✗ Binary not found" -ForegroundColor Red
}

# 3. Check scheduled task
Write-Host ""
Write-Host "3️⃣  Checking scheduled task..." -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName 'SentinelOpsAgent' -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "   ✓ Task 'SentinelOpsAgent' registered" -ForegroundColor Green
    Write-Host "   ✓ Status: $($task.State)"
    Write-Host "   ✓ Enabled: $($task.Enabled)"

    $taskInfo = Get-ScheduledTaskInfo -InputObject $task -ErrorAction SilentlyContinue
    if ($taskInfo) {
        Write-Host "   ✓ Last Run: $($taskInfo.LastRunTime)"
        Write-Host "   ✓ Next Run: $($taskInfo.NextRunTime)"
    }

    # Check if task is scheduled to run at startup
    $taskDef = $task.Triggers
    if ($taskDef | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskBootTrigger' }) {
        Write-Host "   ✓ Configured to run at system startup" -ForegroundColor Green
    } else {
        $warnings += "Task may not be configured to run at startup"
        Write-Host "   ⚠️  Warning: Task trigger not verified as boot trigger" -ForegroundColor Yellow
    }
} else {
    $errors += "Scheduled task 'SentinelOpsAgent' not found"
    Write-Host "   ✗ Task not registered" -ForegroundColor Red
}

# 4. Check task privileges
Write-Host ""
Write-Host "4️⃣  Checking task security..." -ForegroundColor Yellow
if ($task) {
    $principal = $task.Principal
    Write-Host "   ✓ Principal: $($principal.UserId)" -ForegroundColor Green
    Write-Host "   ✓ Run Level: $($principal.RunLevel)"

    if ($principal.UserId -eq 'SYSTEM') {
        Write-Host "   ✓ Running as SYSTEM (correct)" -ForegroundColor Green
    } else {
        $warnings += "Task may not be running with SYSTEM privileges"
        Write-Host "   ⚠️  Task running as: $($principal.UserId)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   (Skipped - task not found)" -ForegroundColor Gray
}

# 5. Check .env.example
Write-Host ""
Write-Host "5️⃣  Checking configuration files..." -ForegroundColor Yellow
$envExample = Join-Path $installPath '.env.example'
if (Test-Path $envExample) {
    Write-Host "   ✓ Configuration template found: .env.example" -ForegroundColor Green
} else {
    $warnings += "Configuration template .env.example not found"
    Write-Host "   ⚠️  .env.example not found" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=" * 60
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "SentinelOps is properly installed and ready to run."
    Write-Host "The agent will start automatically at next system boot."
    exit 0
} else {
    if ($errors.Count -gt 0) {
        Write-Host ""
        Write-Host "❌ ERRORS ($($errors.Count)):" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "   • $_" }
    }

    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠️  WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "   • $_" }
    }

    Write-Host ""
    Write-Host "Please review the issues above." -ForegroundColor Yellow
    exit 1
}
