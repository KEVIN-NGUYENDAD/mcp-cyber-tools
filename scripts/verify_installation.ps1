param([switch]$Verbose)

Write-Host "SentinelOps Installation Verification" -ForegroundColor Cyan
$errors = @()
$warnings = @()
$installPath = 'C:\Program Files\SentinelOps'
$task = $null

if (Test-Path $installPath) {
    Write-Host "[PASS] Installation directory found" -ForegroundColor Green
} else {
    $errors += "Installation directory not found"
    Write-Host "[FAIL] Installation directory not found" -ForegroundColor Red
}

$agentExe = Join-Path $installPath 'sentinel_agent.exe'
if (Test-Path $agentExe) {
    Write-Host "[PASS] Agent binary found" -ForegroundColor Green
} else {
    $errors += "Agent binary not found"
    Write-Host "[FAIL] Agent binary not found" -ForegroundColor Red
}

$task = Get-ScheduledTask -TaskName 'SentinelOpsAgent' -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "[PASS] Scheduled task found" -ForegroundColor Green
    if ($task.Principal.UserId -eq 'SYSTEM') {
        Write-Host "[PASS] Task runs as SYSTEM" -ForegroundColor Green
    } else {
        $warnings += "Task does not run as SYSTEM"
        Write-Host "[WARN] Task does not run as SYSTEM" -ForegroundColor Yellow
    }
} else {
    $errors += "Scheduled task not found"
    Write-Host "[FAIL] Scheduled task not found" -ForegroundColor Red
}

Write-Host ""
if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    exit 0
} else {
    if ($errors.Count -gt 0) {
        Write-Host "❌ ERRORS: $($errors.Count)" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "   - $_" }
    }
    if ($warnings.Count -gt 0) {
        Write-Host "⚠️  WARNINGS: $($warnings.Count)" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "   - $_" }
    }
    exit 1
}
