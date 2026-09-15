@echo off
REM SentinelOps Agent - Batch wrapper for Node.js server
cd /d "%~dp0\.."
node server.js %*
exit /b %errorlevel%
