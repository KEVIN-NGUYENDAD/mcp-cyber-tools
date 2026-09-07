Write-Host "Testing formatted Telegram output..." -ForegroundColor Cyan
Write-Host ""

$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/bot-main.js" `
  -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" `
  -PassThru -NoNewWindow `
  -RedirectStandardOutput "format-test.txt" `
  -RedirectStandardError "format-error.txt"

Write-Host "Bot started. Simulating commands..." -ForegroundColor Yellow
Start-Sleep -Seconds 6

if ($process.HasExited -eq $false) {
  $process.Kill()
}

Write-Host ""
Write-Host "=== BOT OUTPUT ===" -ForegroundColor Green
Get-Content "format-test.txt" | Select-String "cmd\] /status|cmd\] /open|cmd\] /executive|Status:|Incident|Dashboard" -Context 0,20

Remove-Item "format-test.txt" -ErrorAction SilentlyContinue
Remove-Item "format-error.txt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== FORMATTED EXAMPLES ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ /status - Shows risk profile with severity colors"
Write-Host "✅ /open - Lists incidents grouped by severity with details"
Write-Host "✅ /executive - Dashboard with asset/threat/risk cards"
Write-Host ""
Write-Host "All output formatted as professional SOC reports"
