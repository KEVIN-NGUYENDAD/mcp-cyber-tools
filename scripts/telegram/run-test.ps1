$process = Start-Process -FilePath "node" -ArgumentList "scripts/telegram/telegramBot.js" -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools" -PassThru -RedirectStandardOutput "bot-output.txt" -RedirectStandardError "bot-error.txt"

Start-Sleep -Seconds 4

Stop-Process -Id $process.Id -Force

Write-Host "=== STDOUT ==="
Get-Content "bot-output.txt"

Write-Host ""
Write-Host "=== STDERR ==="
Get-Content "bot-error.txt"

Remove-Item "bot-output.txt" -ErrorAction SilentlyContinue
Remove-Item "bot-error.txt" -ErrorAction SilentlyContinue
