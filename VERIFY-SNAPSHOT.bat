@echo off
REM HOME SOC - Manual Verification Test
REM Chạy lệnh này để kiểm tra kết quả thực tế vs tool

echo.
echo =====================================================================
echo  HOME SOC - MANUAL VERIFICATION TEST
echo =====================================================================
echo.

echo [1] IPv4 ADDRESSES
echo ===========================
ipconfig | findstr "IPv4 Address"
echo.

echo [2] WiFi STATUS
echo ===========================
netsh wlan show interfaces | findstr "SSID State Signal"
echo.

echo [3] DNS SERVERS
echo ===========================
ipconfig /all | findstr "DNS Servers" /A 1
echo.

echo [4] BROWSER PROCESSES
echo ===========================
powershell -NoExit -Command "Get-Process browser -ErrorAction SilentlyContinue | Sort-Object WorkingSet -Descending | Format-Table Name, ID, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet/1MB,0)}} -AutoSize"
echo.

echo [5] SYSTEM MEMORY
echo ===========================
powershell -NoExit -Command "$os = Get-CimInstance Win32_OperatingSystem; $total = [math]::Round($os.TotalVisibleMemorySize/1024/1024, 1); $free = [math]::Round($os.FreePhysicalMemory/1024/1024, 1); $used = $total - $free; $percent = [math]::Round(($used / $total) * 100); Write-Host \"Total: $total GB | Free: $free GB | Used: $used GB | Usage: $percent%\""
echo.

echo [6] NETWORK CONNECTIONS
echo ===========================
powershell -NoExit -Command "$connCount = (Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Measure-Object).Count; Write-Host \"Total Connections: $connCount\""
echo.

echo [7] BATTERY STATUS
echo ===========================
powershell -NoExit -Command "Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Format-Table EstimatedChargeRemaining, Status"
echo.

echo =====================================================================
echo  VERIFICATION COMPLETE - Copy results and paste to Claude
echo =====================================================================
echo.
pause
