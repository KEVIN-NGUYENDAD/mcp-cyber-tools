# Setup scheduled task to run auto-collector until 8PM
Write-Host "🤖 Setting up HOME SOC Desktop Auto-Collection..." -ForegroundColor Green

# Get current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$collectorScript = Join-Path $scriptPath "desktop-auto-collector.js"

# Verify script exists
if (-not (Test-Path $collectorScript)) {
    Write-Host "❌ Error: desktop-auto-collector.js not found at $collectorScript" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found collector script: $collectorScript" -ForegroundColor Green

# Create task action
$action = New-ScheduledTaskAction `
    -Execute "node" `
    -Argument $collectorScript `
    -WorkingDirectory $scriptPath

Write-Host "✅ Task action created" -ForegroundColor Green

# Create trigger - run now
$trigger = New-ScheduledTaskTrigger `
    -AtStartup

Write-Host "✅ Trigger created (will run on startup)" -ForegroundColor Green

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable

Write-Host "✅ Settings configured" -ForegroundColor Green

# Register the task
$taskName = "HOME-SOC-Desktop-Auto-Collector"
$taskPath = "\Cyber Tools\"

try {
    # Remove existing task if it exists
    Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false -ErrorAction SilentlyContinue

    # Register new task
    Register-ScheduledTask `
        -TaskName $taskName `
        -TaskPath $taskPath `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "HOME SOC Desktop Auto-Collector - runs until 8PM and generates report" `
        -Force | Out-Null

    Write-Host "✅ Task registered: $taskName" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error registering task: $_" -ForegroundColor Red
    exit 1
}

# Option to start immediately
Write-Host ""
Write-Host "Task Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Options:"
Write-Host "1. Start collection NOW (manual):     node $collectorScript"
Write-Host "2. Task will run on next system boot"
Write-Host "3. To stop:                           Stop-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Data will be collected every 30 minutes until 8PM"
Write-Host "Final report will be generated and saved to: DESKTOP-AUTO-COLLECTION-REPORT.md"
