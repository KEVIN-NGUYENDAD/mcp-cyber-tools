#Requires -RunAsAdministrator
<#
 HOME SOC COMPLETE AUTO SETUP - Ultra Simple Version
 Run this as Administrator in PowerShell
#>

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      HOME SOC MCP SERVER - COMPLETE AUTO SETUP               ║" -ForegroundColor Cyan
Write-Host "║              Phase 1–4 Deployment                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Setup directory
Write-Host "[1/8] Setting up directory..." -ForegroundColor Yellow
cd C:\ 2>$null
if (-not (Test-Path "C:\mcp-cyber-tools")) {
    Write-Host "  Cloning repository..." -ForegroundColor Gray
    git clone https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools.git 2>$null
}
cd C:\mcp-cyber-tools
Write-Host "✅ Directory ready: C:\mcp-cyber-tools`n" -ForegroundColor Green

# 2. Fix execution policy
Write-Host "[2/8] Fixing PowerShell policies..." -ForegroundColor Yellow
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
Write-Host "✅ Policies updated`n" -ForegroundColor Green

# 3. Check Node.js
Write-Host "[3/8] Checking Node.js..." -ForegroundColor Yellow
$nodeVer = node --version 2>$null
if (-not $nodeVer) {
    Write-Host "❌ Node.js not found! Install from https://nodejs.org/" -ForegroundColor Red
    pause; exit 1
}
Write-Host "✅ Node.js $nodeVer found`n" -ForegroundColor Green

# 4. Install dependencies
Write-Host "[4/8] Installing dependencies..." -ForegroundColor Yellow
npm install --force 2>&1 | Where-Object { $_ -match "added|up to date" }
Write-Host "✅ Dependencies installed`n" -ForegroundColor Green

# 5. Verify files
Write-Host "[5/8] Verifying required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "src\home-soc-mcp-server.js",
    "dashboard\dashboard.html",
    "config.json"
)
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        pause; exit 1
    }
}
Write-Host "✅ All files present`n" -ForegroundColor Green

# 6. Setup Claude config
Write-Host "[6/8] Configuring Claude MCP..." -ForegroundColor Yellow
$claudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $claudeDir)) { mkdir $claudeDir -Force >$null }

$mcpJson = @"
{
  "mcpServers": {
    "home-soc": {
      "command": "node",
      "args": ["C:\\mcp-cyber-tools\\src\\home-soc-mcp-server.js"],
      "cwd": "C:\\mcp-cyber-tools",
      "description": "HOME SOC MCP Server",
      "env": {
        "HOME_SOC_STATE": "C:\\mcp-cyber-tools\\reports\\home-soc-state"
      }
    }
  }
}
"@
$mcpJson | Set-Content "$claudeDir\mcp.json" -Force
Write-Host "✅ Claude config created`n" -ForegroundColor Green

# 7. Test server
Write-Host "[7/8] Testing MCP server (5 second test)..." -ForegroundColor Yellow
$process = Start-Process -FilePath "node" -ArgumentList "src\home-soc-mcp-server.js" -NoNewWindow -PassThru -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5
Stop-Process -InputObject $process -Force -ErrorAction SilentlyContinue 2>$null
Write-Host "✅ Server test passed`n" -ForegroundColor Green

# 8. Setup Task Scheduler
Write-Host "[8/8] Configuring auto-start (Task Scheduler)..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "HOME-SOC-MCP-Server" -Confirm:$false -ErrorAction SilentlyContinue
$action = New-ScheduledTaskAction -Execute "C:\Program Files\nodejs\node.exe" -Argument "C:\mcp-cyber-tools\src\home-soc-mcp-server.js" -WorkingDirectory "C:\mcp-cyber-tools"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "HOME-SOC-MCP-Server" -Action $action -Trigger $trigger -Settings $settings -Description "HOME SOC MCP Server" -RunLevel Highest -Force >$null
Write-Host "✅ Auto-start configured`n" -ForegroundColor Green

# Complete
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║             ✅ SETUP COMPLETE - READY FOR DEPLOYMENT         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Restart Windows: Restart-Computer" -ForegroundColor White
Write-Host "  2. After restart, open Claude Code" -ForegroundColor White
Write-Host "  3. Check: Settings > MCP Servers > home-soc (should be ✅ Connected)" -ForegroundColor White
Write-Host "  4. Test: @discoverDevices`n" -ForegroundColor White

$restart = Read-Host "Restart Windows now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Restart-Computer -Force
} else {
    Write-Host "Setup complete! Please restart Windows manually.`n" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}
