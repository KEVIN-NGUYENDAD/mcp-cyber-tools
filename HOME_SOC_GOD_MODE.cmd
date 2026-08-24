@echo off
REM HOME SOC GOD MODE - Master Startup Script
REM Runs automatically on laptop startup
REM Orchestrates: Collector -> MCP Server -> Claude

setlocal enabledelayedexpansion

set REPO_PATH=%~dp0
set NODE_PATH=%REPO_PATH%
set LOG_PATH=%REPO_PATH%logs

if not exist "%LOG_PATH%" mkdir "%LOG_PATH%"

REM Log startup
echo [%date% %time%] HOME SOC GOD MODE Starting >> "%LOG_PATH%\godmode.log"

REM Start MCP Server (silent background)
start /b "HOME SOC MCP" cmd /c "cd /d "%NODE_PATH%" && node home-soc-mcp-server.js >> "%LOG_PATH%\mcp.log" 2>&1"
echo [%date% %time%] MCP Server started >> "%LOG_PATH%\godmode.log"

REM Run initial collection
echo [%date% %time%] Running initial collection >> "%LOG_PATH%\godmode.log"
cd /d "%NODE_PATH%"
call node network-collector.js >> "%LOG_PATH%\collector.log" 2>&1
call node router-agent.js >> "%LOG_PATH%\router.log" 2>&1

REM Run telemetry
call node collector-telemetry.js >> "%LOG_PATH%\telemetry.log" 2>&1

echo [%date% %time%] HOME SOC GOD MODE Initialized >> "%LOG_PATH%\godmode.log"
echo HOME SOC Active - Monitoring Network
