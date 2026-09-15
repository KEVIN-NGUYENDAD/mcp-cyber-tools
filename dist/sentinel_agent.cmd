@echo off
REM ============================================================================
REM SentinelOps Agent - FALLBACK runtime
REM
REM PRIMARY runtime is sentinel_agent.exe (self-contained, bundles Node).
REM Use this wrapper only when the .exe will not start. It needs Node.js on
REM PATH and the repo/install tree intact (web/, node_modules/).
REM
REM Removal criteria: 7 days production monitoring, 0 fallback uses, 0 exe
REM crashes. See docs/project/PROJECT_READY_STATE.md.
REM ============================================================================
setlocal

REM Installed layout: wrapper sits beside web\. Repo layout: wrapper is in dist\.
set "AGENT_ROOT=%~dp0"
if exist "%AGENT_ROOT%web\server.js" goto :run
set "AGENT_ROOT=%~dp0..\"
if exist "%AGENT_ROOT%web\server.js" goto :run

echo [FALLBACK] web\server.js not found near "%~dp0" 1>&2
echo [FALLBACK] Run the primary runtime sentinel_agent.exe instead. 1>&2
exit /b 1

:run
where node >nul 2>&1
if errorlevel 1 (
  echo [FALLBACK] Node.js not found on PATH - this wrapper requires it. 1>&2
  echo [FALLBACK] Run the primary runtime sentinel_agent.exe instead. 1>&2
  exit /b 1
)

cd /d "%AGENT_ROOT%"
echo [FALLBACK] Primary runtime is sentinel_agent.exe - starting wrapper instead.
node web\server.js %*
exit /b %errorlevel%
