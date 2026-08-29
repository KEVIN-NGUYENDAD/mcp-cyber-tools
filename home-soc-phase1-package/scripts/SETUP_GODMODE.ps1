# HOME SOC GOD MODE SETUP
# Run as Administrator

param(
    [string]$RepoPath = (Split-Path $MyInvocation.MyCommand.Path)
)

Write-Host "HOME SOC GOD MODE SETUP" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Creating log directory..."
$logPath = Join-Path $RepoPath "logs"
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    Write-Host "OK: Created logs directory"
}

Write-Host ""
Write-Host "Step 2: Creating Task Scheduler tasks..."

Write-Host "Creating: HOME SOC Startup"
$taskName1 = "HOME SOC Startup"
$cmdPath1 = Join-Path $RepoPath "HOME_SOC_GOD_MODE.cmd"
$argStr1 = "/c `"" + $cmdPath1 + "`""
$action1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $argStr1 -WorkingDirectory $RepoPath
$trigger1 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$principal1 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task1 = New-ScheduledTask -Action $action1 -Trigger $trigger1 -Principal $principal1 -Description "HOME SOC startup"
Register-ScheduledTask -InputObject $task1 -TaskName $taskName1 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "OK: Registered HOME SOC Startup"

Write-Host "Creating: HOME SOC Collector"
$taskName2 = "HOME SOC Collector"
$cmdPath2 = Join-Path $RepoPath "collector.cmd"
$argStr2 = "/c `"" + $cmdPath2 + "`""
$action2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $argStr2 -WorkingDirectory $RepoPath
$trigger2 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
$principal2 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task2 = New-ScheduledTask -Action $action2 -Trigger $trigger2 -Principal $principal2 -Description "HOME SOC collector"
Register-ScheduledTask -InputObject $task2 -TaskName $taskName2 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "OK: Registered HOME SOC Collector"

Write-Host "Creating: HOME SOC Reports"
$taskName3 = "HOME SOC Reports"
$cmdPath3 = Join-Path $RepoPath "report.cmd"
$argStr3 = "/c `"" + $cmdPath3 + "`""
$action3 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $argStr3 -WorkingDirectory $RepoPath
$trigger3 = New-ScheduledTaskTrigger -Daily -At "20:00:00"
$principal3 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task3 = New-ScheduledTask -Action $action3 -Trigger $trigger3 -Principal $principal3 -Description "HOME SOC reports"
Register-ScheduledTask -InputObject $task3 -TaskName $taskName3 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "OK: Registered HOME SOC Reports"

Write-Host "Creating: HOME SOC MCP Server"
$taskName4 = "HOME SOC MCP Server"
$psPath = Join-Path $RepoPath "start-mcp-server.ps1"
$argStr4 = "-NoProfile -ExecutionPolicy Bypass -File `"" + $psPath + "`""
$action4 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argStr4 -WorkingDirectory $RepoPath
$trigger4 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$principal4 = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$task4 = New-ScheduledTask -Action $action4 -Trigger $trigger4 -Principal $principal4 -Description "HOME SOC MCP"
Register-ScheduledTask -InputObject $task4 -TaskName $taskName4 -TaskPath "\HOME_SOC\" -Force | Out-Null
Write-Host "OK: Registered HOME SOC MCP Server"

Write-Host ""
Write-Host "SETUP COMPLETE"
Write-Host ""
Write-Host "Tasks created:"
Write-Host "  1. HOME SOC Startup"
Write-Host "  2. HOME SOC Collector"
Write-Host "  3. HOME SOC Reports"
Write-Host "  4. HOME SOC MCP Server"
Write-Host ""
Write-Host "Next: Restart laptop"
Write-Host ""
