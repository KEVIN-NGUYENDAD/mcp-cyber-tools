@echo off
REM HOME SOC - Laptop Auto-Collection Startup Script
REM Copy this to Laptop and add to Startup folder

cd /d "%~dp0"

echo.
echo ===================================================================
echo  HOME SOC - LAPTOP AUTO-COLLECTION
echo ===================================================================
echo.
echo  Device: LAPTOP
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
