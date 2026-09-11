@echo off
REM SentinelOps Telegram Bot Startup Script
REM This script starts the PM2 managed bot process

echo [%date% %time%] Starting SentinelOps Telegram Bot...

REM Navigate to bot directory
cd /d "C:\GitHub\mcp-cyber-tools\scripts\telegram"

REM Start PM2 with saved configuration
pm2 resurrect

REM Verify bot started
pm2 list

REM Log startup
echo [%date% %time%] SentinelOps Telegram Bot started successfully >> "C:\GitHub\mcp-cyber-tools\logs\startup.log"
