$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/bot-main.js" -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" -PassThru -NoNewWindow -RedirectStandardOutput "bot-output.txt" -RedirectStandardError "bot-error.txt"

Start-Sleep -Seconds 3

if ($process.HasExited -eq $false) {
  Write-Host "[OK] Process is still running"
  $process.Kill()
} else {
  Write-Host "[ERROR] Process exited immediately"
}

Write-Host ""
Write-Host "=== OUTPUT ==="
Get-Content "bot-output.txt"

if ((Get-Content "bot-error.txt" -ErrorAction SilentlyContinue).Length -gt 0) {
  Write-Host ""
  Write-Host "=== ERRORS ==="
  Get-Content "bot-error.txt"
}

Remove-Item "bot-output.txt" -ErrorAction SilentlyContinue
Remove-Item "bot-error.txt" -ErrorAction SilentlyContinue
