# iPhone Data Monitor - Auto capture from iCloud + Push GitHub
# Place iPhone data in: %USERPROFILE%\iCloudDrive\mcp-cyber-tools\
# This script monitors and auto-commits to GitHub

$projectDir = "$env:APPDATA\Claude\Projects\mcp-cyber-tools"
$icloudDir = "$env:USERPROFILE\iCloudDrive\mcp-cyber-tools"
$iphoneDataDir = "$projectDir\iphone-data"
$logFile = "$projectDir\iphone-monitor.log"

# Create directories if needed
if (-not (Test-Path $iphoneDataDir)) {
    New-Item -ItemType Directory $iphoneDataDir -Force | Out-Null
}

function Log {
    param([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $msg" | Tee-Object -Append $logFile
}

Log "🍎 iPhone Data Monitor Started"
Log "📁 Project: $projectDir"
Log "☁️  iCloud Dir: $icloudDir"

# Monitor for new iPhone data files
$lastCheck = Get-Date

while ($true) {
    try {
        # Check if iCloud directory exists
        if (-not (Test-Path $icloudDir)) {
            Log "⚠️  iCloud dir not found yet (waiting for sync)"
            Start-Sleep -Seconds 60
            continue
        }

        # Get new iPhone data files
        $files = Get-ChildItem $icloudDir -Filter "*.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt $lastCheck }

        if ($files) {
            Log "📱 Found $(($files | Measure-Object).Count) new iPhone data file(s)"

            foreach ($file in $files) {
                try {
                    # Copy to project
                    $destFile = "$iphoneDataDir\$($file.Name)"
                    Copy-Item $file.FullName $destFile -Force
                    Log "  ✅ Copied: $($file.Name)"

                    # Read and display data
                    $data = Get-Content $destFile | ConvertFrom-Json
                    Log "  📊 Device: $($data.device_name)"
                    Log "  🔋 Battery: $($data.battery)%"
                    Log "  📶 WiFi: $($data.wifi_ssid)"
                    Log "  🕐 Time: $($data.timestamp)"

                } catch {
                    Log "  ❌ Error processing $($file.Name): $_"
                }
            }

            # Git operations
            Log "📤 Pushing to GitHub..."

            try {
                Set-Location $projectDir

                # Stage iPhone data
                git add iphone-data/ 2>&1 | Out-Null

                # Commit
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                git commit -m "data: iPhone metrics - $timestamp" 2>&1 | Out-Null
                Log "  ✅ Committed"

                # Push
                git push origin learning-factory-v2 2>&1 | Out-Null
                Log "  ✅ Pushed to GitHub"

                # Clean up iCloud file
                foreach ($file in $files) {
                    Remove-Item $file.FullName -Force
                    Log "  🗑️  Cleaned up: $($file.Name)"
                }

            } catch {
                Log "  ❌ Git error: $_"
            }

            $lastCheck = Get-Date
        }

    } catch {
        Log "❌ Error in monitor loop: $_"
    }

    # Check every 5 minutes
    Start-Sleep -Seconds 300
}
