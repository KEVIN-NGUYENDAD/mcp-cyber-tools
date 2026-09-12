@echo off
REM Batch file to schedule Daily Brief for 3:00 PM every day
REM Run as Administrator

echo Setting up SentinelOps Daily Brief scheduled task...
echo.

REM Use PowerShell to create the task
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0schedule-daily-brief.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task created successfully!
    echo.
    echo Verify with:
    echo   schtasks /query /tn SentinelOps-DailyBrief /v
) else (
    echo.
    echo ERROR: Failed to create task. Make sure to run as Administrator.
    pause
    exit /b 1
)
