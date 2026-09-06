$projectDir = "$env:APPDATA\Claude\Projects\mcp-cyber-tools"
$iphoneDataDir = "$projectDir\iphone-data"

if (-not (Test-Path $iphoneDataDir)) {
    mkdir $iphoneDataDir -Force | Out-Null
}

Write-Host "iPhone Data Collection"
$deviceName = Read-Host "Device Name"
$battery = Read-Host "Battery"
$wifiSSID = Read-Host "WiFi"
$apps = Read-Host "Apps"

$date = Get-Date -Format "yyyy-MM-dd"
$json = @{ device=$deviceName; battery=$battery; wifi=$wifiSSID; apps=$apps } | ConvertTo-Json

"$json" | Out-File "$iphoneDataDir\iphone-snapshot-$date.json" -Encoding UTF8

cd $projectDir
git add iphone-data/
git commit -m "data: iPhone snapshot $date"
git push origin learning-factory-v2

Write-Host "Done!"
