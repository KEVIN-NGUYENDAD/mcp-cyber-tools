# PowerShell script to schedule Daily Brief at 3:00 PM every day
# Run as Administrator

$taskName = "SentinelOps-DailyBrief"
$taskPath = "\SentinelOps\"
$taskDescription = "Generate and send SentinelOps Daily Brief at 3:00 PM via Telegram and Email"

# Script to run
$scriptPath = "C:\GitHub\mcp-cyber-tools\scripts\run_daily_brief.py"
$pythonPath = "python"  # Assumes python is in PATH

# Create action
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory "C:\GitHub\mcp-cyber-tools\scripts"

# Create trigger (3:00 PM every day)
$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "3:00 PM"

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Create principal (run with current user)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME"

# Create and register task
$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description $taskDescription

Register-ScheduledTask `
    -TaskName $taskName `
    -InputObject $task `
    -Force `
    -ErrorAction Stop

Write-Host "✓ Task '$taskName' created successfully"
Write-Host "  Scheduled for: Every day at 3:00 PM"
Write-Host "  Script: $scriptPath"
Write-Host ""
Write-Host "To verify: Get-ScheduledTask -TaskName '$taskName' | Select *"
