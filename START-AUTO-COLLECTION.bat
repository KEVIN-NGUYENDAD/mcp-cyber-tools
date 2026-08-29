@echo off
REM HOME SOC - Desktop Auto-Collection Startup Script
REM This runs the auto-collector every time you start the computer

cd /d "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools"

echo.
echo ===================================================================
echo  HOME SOC - DESKTOP AUTO-COLLECTION
echo ===================================================================
echo.
echo  Starting data collection...
echo  Data will be collected every 30 minutes until 8:00 PM
echo  Report will be generated at 8:00 PM
echo.
echo  Process: Keep this window open or minimize it
echo  To stop: Close this window
echo.
echo ===================================================================
echo.

node desktop-auto-collector.js

pause
