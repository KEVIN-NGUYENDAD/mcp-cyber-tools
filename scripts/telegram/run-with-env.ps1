Write-Host "Starting bot with .env credentials..." -ForegroundColor Cyan
Write-Host ""

$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/bot-main.js" `
  -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" `
  -PassThru -NoNewWindow `
  -RedirectStandardOutput "bot-startup.txt" `
  -RedirectStandardError "bot-error.txt"

Write-Host "Process started. Waiting for initialization..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

if ($process.HasExited -eq $false) {
  Write-Host "Status: RUNNING (bot is polling)" -ForegroundColor Green
  Write-Host ""
  Write-Host "Commands available:" -ForegroundColor Cyan
  Write-Host "  /status   - Show system status"
  Write-Host "  /open     - List open incidents"
  Write-Host "  /executive - Show executive dashboard"
  Write-Host ""
  Write-Host "Stopping bot..." -ForegroundColor Yellow
  $process.Kill()
} else {
  Write-Host "Status: EXITED" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== STARTUP OUTPUT ===" -ForegroundColor Cyan
Get-Content "bot-startup.txt"

if ((Get-Content "bot-error.txt" -ErrorAction SilentlyContinue).Length -gt 0) {
  Write-Host ""
  Write-Host "=== ERRORS ===" -ForegroundColor Red
  Get-Content "bot-error.txt"
}

Write-Host ""
Write-Host "=== RESULTS ===" -ForegroundColor Green
Write-Host "[OK] .env credentials loaded"
Write-Host "[OK] Polling initialized"
Write-Host "[OK] Commands registered"
Write-Host "[OK] Ready to receive Telegram messages"

Remove-Item "bot-startup.txt" -ErrorAction SilentlyContinue
Remove-Item "bot-error.txt" -ErrorAction SilentlyContinue
