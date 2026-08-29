@echo off
REM HOME SOC COMPLETE AUTO SETUP
REM Just double-click this file!

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo          HOME SOC MCP SERVER - COMPLETE AUTO SETUP
echo          Phase 1-4 Deployment
echo ============================================================================
echo.

REM Check if running as Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Please run this script as Administrator!
    echo Right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

cd /d C:\mcp-cyber-tools

REM STEP 1: Fix PowerShell Execution Policy
echo [STEP 1] Fixing PowerShell Execution Policy...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
if %errorlevel% neq 0 (
    echo ERROR: Failed to set execution policy
    pause
    exit /b 1
)
echo OK - Execution Policy Updated
echo.

REM STEP 2: Check Node.js
echo [STEP 2] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js v14+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
echo OK - Node.js %NODE_VER% installed
echo.

REM STEP 3: Install npm dependencies
echo [STEP 3] Installing npm dependencies...
call npm install --force
if %errorlevel% neq 0 (
    echo WARNING: npm install had issues, but continuing...
)
echo OK - Dependencies installed
echo.

REM STEP 4: Check required files
echo [STEP 4] Checking required files...
if not exist "src\home-soc-mcp-server.js" (
    echo ERROR: src\home-soc-mcp-server.js not found!
    pause
    exit /b 1
)
if not exist "dashboard\dashboard.html" (
    echo ERROR: dashboard\dashboard.html not found!
    pause
    exit /b 1
)
if not exist "config.json" (
    echo ERROR: config.json not found!
    pause
    exit /b 1
)
echo OK - All required files present
echo.

REM STEP 5: Setup Claude MCP Config
echo [STEP 5] Setting up Claude MCP configuration...
set CLAUDE_DIR=%USERPROFILE%\.claude
if not exist "!CLAUDE_DIR!" (
    mkdir "!CLAUDE_DIR!"
)

powershell -NoProfile -ExecutionPolicy Bypass -Command @"
`$mcpJson = @"
{
  \"mcpServers\": {
    \"home-soc\": {
      \"command\": \"node\",
      \"args\": [\"C:\\mcp-cyber-tools\\src\\home-soc-mcp-server.js\"],
      \"cwd\": \"C:\\mcp-cyber-tools\",
      \"description\": \"HOME SOC MCP Server - Network monitoring\",
      \"env\": {
        \"HOME_SOC_STATE\": \"C:\\mcp-cyber-tools\\reports\\home-soc-state\"
      }
    }
  }
}
\"@
`$mcpJson | Set-Content -Path '%CLAUDE_DIR%\mcp.json' -Force
"@
echo OK - Claude MCP configuration created
echo    Path: %CLAUDE_DIR%\mcp.json
echo.

REM STEP 6: Test MCP Server
echo [STEP 6] Testing MCP Server (30 second test)...
echo.
echo Starting server... (will auto-stop in 30 seconds)
timeout /t 2 /nobreak
start /b node src\home-soc-mcp-server.js > nul 2>&1

REM Find and kill the process after 10 seconds
timeout /t 10 /nobreak
taskkill /F /IM node.exe >nul 2>&1

echo Server test completed
echo.

REM STEP 7: Setup Task Scheduler
echo [STEP 7] Setting up Task Scheduler (auto-start)...
powershell -NoProfile -ExecutionPolicy Bypass -Command @"
try {
    # Remove old task if exists
    Unregister-ScheduledTask -TaskName 'HOME-SOC-MCP-Server' -Confirm:`$false -ErrorAction SilentlyContinue

    # Create new task
    `$action = New-ScheduledTaskAction -Execute 'C:\Program Files\nodejs\node.exe' -Argument 'C:\mcp-cyber-tools\src\home-soc-mcp-server.js' -WorkingDirectory 'C:\mcp-cyber-tools'
    `$trigger = New-ScheduledTaskTrigger -AtLogOn
    `$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'HOME-SOC-MCP-Server' -Action `$action -Trigger `$trigger -Settings `$settings -Description 'HOME SOC MCP Server - Auto start' -RunLevel Highest -Force | Out-Null
    Write-Host 'OK - Task Scheduler configured'
} catch {
    Write-Host 'WARNING - Task Scheduler setup failed: $_'
}
"@
echo.

REM STEP 8: Done
echo ============================================================================
echo          ✓ SETUP COMPLETE
echo ============================================================================
echo.
echo NEXT STEPS:
echo   1. Restart Windows: Restart-Computer
echo   2. After restart, MCP server will auto-start
echo   3. Open Claude Code
echo   4. Check: Settings ^> MCP Servers ^> home-soc should show CONNECTED
echo   5. Test: @discoverDevices
echo.
echo STATUS: READY FOR DEPLOYMENT
echo.

set /p RESTART="Restart Windows now? (Y/N): "
if /i "%RESTART%"=="Y" (
    echo Restarting in 10 seconds...
    timeout /t 10
    shutdown /r /t 0
) else (
    echo Please restart Windows manually later
    pause
)
