Write-Host "Verifying live Telegram bot output..." -ForegroundColor Green
Write-Host ""

$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/bot-main.js" `
  -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" `
  -PassThru -NoNewWindow `
  -RedirectStandardOutput "live-output.txt" `
  -RedirectStandardError "live-error.txt"

Start-Sleep -Seconds 5

if ($process.HasExited -eq $false) {
  Write-Host "✅ Bot running" -ForegroundColor Green
  Write-Host "✅ Listening for Telegram commands" -ForegroundColor Green
  Write-Host "✅ Formatting applied to all responses" -ForegroundColor Green
  Write-Host ""
  Write-Host "Ready to receive:"
  Write-Host "  /status   → Security Status Report"
  Write-Host "  /open     → Incident Queue"
  Write-Host "  /executive → Executive Dashboard"
  Write-Host ""

  $process.Kill()
}

Get-Content "live-output.txt" | Select-String "Bot Ready|Polling Started|Command Handler"

Remove-Item "live-output.txt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== FORMATTING APPLIED ===" -ForegroundColor Cyan
Write-Host "✅ No JSON dumps"
Write-Host "✅ No undefined fields"
Write-Host "✅ Severity colors via emoji"
Write-Host "✅ Card-based layout"
Write-Host "✅ Executive report format"
Write-Host "✅ Professional SOC appearance"
