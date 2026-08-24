@echo off
REM HOME SOC COLLECTOR - Every 30 minutes
REM Triggered by Windows Task Scheduler
REM Lightweight network monitoring

setlocal enabledelayedexpansion

set REPO_PATH=%~dp0
set LOG_PATH=%REPO_PATH%logs

if not exist "%LOG_PATH%" mkdir "%LOG_PATH%"

cd /d "%REPO_PATH%"

REM Collection timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

echo [%mydate% %mytime%] Collection cycle started >> "%LOG_PATH%\collector.log"

REM Run collector
node network-collector.js >> "%LOG_PATH%\collector.log" 2>&1

REM Check exit code
if %ERRORLEVEL% neq 0 (
  echo [%mydate% %mytime%] ERROR: Collection failed >> "%LOG_PATH%\collector.log"
) else (
  echo [%mydate% %mytime%] Collection successful >> "%LOG_PATH%\collector.log"
)
