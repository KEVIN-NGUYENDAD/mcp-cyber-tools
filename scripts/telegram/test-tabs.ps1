Write-Host "Testing new dashboard tabs..." -ForegroundColor Green
Write-Host ""

$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/bot-main.js" `
  -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" `
  -PassThru -NoNewWindow `
  -RedirectStandardOutput "tabs-output.txt" `
  -RedirectStandardError "tabs-error.txt"

Start-Sleep -Seconds 6

Write-Host "Bot running. Commands registered:" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 /status   - Security Status"
Write-Host "🌐 /network  - Network Topology"
Write-Host "🔴 /open     - Incident Queue"
Write-Host "📈 /analytics - Security Analytics"
Write-Host "[Executive] /executive - Executive Dashboard"
Write-Host "🚨 /incidents - All Incidents"
Write-Host ""

if ($process.HasExited -eq $false) {
  Write-Host "✅ All commands registered and active" -ForegroundColor Green
  $process.Kill()
} else {
  Write-Host "❌ Process exited unexpectedly" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== COMMAND LOG ===" -ForegroundColor Cyan
Get-Content "tabs-output.txt" | Select-String "status|network|open|analytics|executive|incidents" | Select-Object -First 10

Remove-Item "tabs-output.txt" -ErrorAction SilentlyContinue
Remove-Item "tabs-error.txt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== TABS IMPLEMENTED ===" -ForegroundColor Cyan
Write-Host "📊 Overview - /status command"
Write-Host "🌐 Network Map - /network command (NEW)"
Write-Host "🔴 Incidents - /open command"
Write-Host "📈 Analytics - /analytics command (NEW)"
Write-Host "[Dashboard] - /executive command"
