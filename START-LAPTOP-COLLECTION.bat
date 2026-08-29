@echo off
REM HOME SOC - Laptop Auto-Collection Startup Script
REM Fixed: Navigate to project directory using absolute path

setlocal enabledelayedexpansion

REM Get username
for /f "tokens=1" %%a in ('whoami /user') do (
  for /f "tokens=3 delims=\" %%b in ('whoami') do (
    set USERNAME=%%b
  )
)

REM Use absolute path to project directory
set PROJ_DIR=%APPDATA%\Claude\Projects\mcp-cyber-tools
cd /d "!PROJ_DIR!"

if errorlevel 1 (
  echo ERROR: Cannot navigate to project directory
  echo Expected: !PROJ_DIR!
  pause
  exit /b 1
)

echo.
echo ===================================================================
echo  HOME SOC - LAPTOP AUTO-COLLECTION (FIXED)
echo ===================================================================
echo.
echo  Device: LAPTOP
echo  Working Directory: !PROJ_DIR!
echo  Starting data collection...
echo  Data will be collected every 30 minutes until 8:00 PM
echo.
echo  Process: Keep this window open or minimize it
echo  To stop: Close this window
echo.
echo ===================================================================
echo.

node laptop-auto-collector.js

pause
