# HOME SOC GOD MODE SETUP
# PowerShell script to automate Windows Task Scheduler configuration
# Run as Administrator

param(
    [string]$RepoPath = (Split-Path $MyInvocation.MyCommand.Path)
)

Write-Host "HOME SOC GOD MODE SETUP" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Creating log directory..."
$logPath = Join-Path $RepoPath "logs"
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    Write-Host "✓ Created: $logPath"
}

Write-Host ""
Write-Host "Step 2: Creating Task Scheduler tasks..."

# Task 1: Startup (runs at logon)
Write-Host "  Creating: HOME SOC Startup"
$taskName1 = "HOME SOC Startup"
$cmdPath1 = Join-Path $RepoPath "HOME_SOC_GOD_MODE.cmd"
$action1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmdPath1`"" -WorkingDirectory $RepoPath
$trigger1 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$principal1 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task1 = New-ScheduledTask -Action $action1 -Trigger $trigger1 -Principal $principal1 -Description "HOME SOC startup initialization"
Register-ScheduledTask -InputObject $task1 -TaskName $taskName1 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "  ✓ Registered: $taskName1"

# Task 2: Collector (every 30 minutes)
Write-Host "  Creating: HOME SOC Collector"
$taskName2 = "HOME SOC Collector"
$cmdPath2 = Join-Path $RepoPath "collector.cmd"
$action2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmdPath2`"" -WorkingDirectory $RepoPath
$trigger2 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
$principal2 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task2 = New-ScheduledTask -Action $action2 -Trigger $trigger2 -Principal $principal2 -Description "HOME SOC network collection every 30 minutes"
Register-ScheduledTask -InputObject $task2 -TaskName $taskName2 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "  ✓ Registered: $taskName2"

# Task 3: Reports (daily at 8:00 PM)
Write-Host "  Creating: HOME SOC Reports"
$taskName3 = "HOME SOC Reports"
$cmdPath3 = Join-Path $RepoPath "report.cmd"
$action3 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmdPath3`"" -WorkingDirectory $RepoPath
$trigger3 = New-ScheduledTaskTrigger -Daily -At "20:00:00"
$principal3 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task3 = New-ScheduledTask -Action $action3 -Trigger $trigger3 -Principal $principal3 -Description "HOME SOC report generation daily at 8:00 PM"
Register-ScheduledTask -InputObject $task3 -TaskName $taskName3 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "  ✓ Registered: $taskName3"

# Task 4: MCP Server (at startup)
Write-Host "  Creating: HOME SOC MCP Server"
$taskName4 = "HOME SOC MCP Server"
$psPath = Join-Path $RepoPath "start-mcp-server.ps1"
$action4 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$psPath`"" -WorkingDirectory $RepoPath
$trigger4 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$principal4 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task4 = New-ScheduledTask -Action $action4 -Trigger $trigger4 -Principal $principal4 -Description "HOME SOC MCP server for Claude integration"
Register-ScheduledTask -InputObject $task4 -TaskName $taskName4 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "  ✓ Registered: $taskName4"

Write-Host ""
Write-Host "Step 3: Configuration Summary"
Write-Host "  Repository: $RepoPath"
Write-Host "  Logs: $logPath"
Write-Host "  Tasks: 4 registered"
Write-Host ""

Write-Host "SETUP COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "Scheduled Tasks:"
Write-Host "  1. HOME SOC Startup     - At user logon"
Write-Host "  2. HOME SOC Collector   - Every 30 minutes"
Write-Host "  3. HOME SOC Reports     - Daily 8:00 PM"
Write-Host "  4. HOME SOC MCP Server  - At user logon"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "  1. Restart your laptop"
Write-Host "  2. Check logs/ directory for collection logs"
Write-Host "  3. View reports in reports/ directory"
Write-Host ""

$collectorLog = Join-Path $logPath "collector.log"
Write-Host "Monitor collection: Get-Content '$collectorLog' -Tail 10 -Wait"
Write-Host ""
