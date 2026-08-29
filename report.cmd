@echo off
REM HOME SOC REPORTS - Daily at 8:00 PM
REM Generates comprehensive, executive, and operations briefs
REM Uses accumulated evidence from collector

setlocal enabledelayedexpansion

set REPO_PATH=%~dp0
set LOG_PATH=%REPO_PATH%logs

if not exist "%LOG_PATH%" mkdir "%LOG_PATH%"

cd /d "%REPO_PATH%"

REM Report timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

echo [%mydate% %mytime%] Report generation started >> "%LOG_PATH%\report.log"

REM Generate comprehensive brief
node home-soc-brief.js >> "%LOG_PATH%\brief.log" 2>&1
if %ERRORLEVEL% neq 0 echo [%mydate% %mytime%] home-soc-brief FAILED >> "%LOG_PATH%\report.log"

REM Generate executive brief (Vietnamese)
node home-soc-executive-brief.js >> "%LOG_PATH%\executive.log" 2>&1
if %ERRORLEVEL% neq 0 echo [%mydate% %mytime%] home-soc-executive-brief FAILED >> "%LOG_PATH%\report.log"

REM Generate operations brief
node home-soc-ops-brief.js >> "%LOG_PATH%\ops.log" 2>&1
if %ERRORLEVEL% neq 0 echo [%mydate% %mytime%] home-soc-ops-brief FAILED >> "%LOG_PATH%\report.log"

REM Run telemetry
node collector-telemetry.js >> "%LOG_PATH%\telemetry.log" 2>&1

echo [%mydate% %mytime%] Report generation complete >> "%LOG_PATH%\report.log"
