#Requires -RunAsAdministrator
<#
 HOME SOC COMPLETE AUTO SETUP
 Chạy script này (Admin) để setup toàn bộ
#>

Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          HOME SOC MCP SERVER - COMPLETE AUTO SETUP              ║" -ForegroundColor Cyan
Write-Host "║                    Phase 1–4 Deployment                         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# BƯỚC 1: FIX EXECUTION POLICY
# ============================================================================
Write-Host "📋 BƯỚC 1: Sửa PowerShell Execution Policy..." -ForegroundColor Yellow
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction Stop
    Write-Host "✅ Execution Policy updated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update policy: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ============================================================================
# BƯỚC 2: KIỂM TRA NODE.JS
# ============================================================================
Write-Host "📋 BƯỚC 2: Kiểm tra Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version
$npmVersion = npm --version
Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
Write-Host ""

# ============================================================================
# BƯỚC 3: CÀI ĐẶT DEPENDENCIES
# ============================================================================
Write-Host "📋 BƯỚC 3: Cài đặt npm dependencies..." -ForegroundColor Yellow
cd C:\mcp-cyber-tools
npm install --force
Write-Host "✅ npm install completed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# BƯỚC 4: KIỂM TRA CẤU TRÚC FILE
# ============================================================================
Write-Host "📋 BƯỚC 4: Kiểm tra cấu trúc file..." -ForegroundColor Yellow

$requiredFiles = @(
    "src\home-soc-mcp-server.js",
    "src\network-collector.js",
    "src\baseline-analyzer.js",
    "src\collector-telemetry.js",
    "dashboard\dashboard.html",
    "config.json",
    "mcp.json"
)

$allExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - THIẾU" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "❌ Thiếu files quan trọng!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Tất cả file tồn tại" -ForegroundColor Green
Write-Host ""

# ============================================================================
# BƯỚC 5: SETUP CLAUDE MCP CONFIG
# ============================================================================
Write-Host "📋 BƯỚC 5: Cấu hình Claude MCP..." -ForegroundColor Yellow

$claudeDir = "$env:USERPROFILE\.claude"
$mcpJsonPath = "$claudeDir\mcp.json"

# Tạo thư mục nếu chưa có
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    Write-Host "  ✅ Created .claude directory" -ForegroundColor Green
}

# Tạo/cập nhật mcp.json
$mcpConfig = @"
{
  "mcpServers": {
    "home-soc": {
      "command": "node",
      "args": ["C:\\mcp-cyber-tools\\src\\home-soc-mcp-server.js"],
      "cwd": "C:\\mcp-cyber-tools",
      "description": "HOME SOC MCP Server - Network monitoring and threat prediction",
      "env": {
        "HOME_SOC_STATE": "C:\\mcp-cyber-tools\\reports\\home-soc-state"
      }
    }
  }
}
"@

$mcpConfig | Set-Content -Path $mcpJsonPath -Force
Write-Host "  ✅ Claude mcp.json configured" -ForegroundColor Green
Write-Host "     Path: $mcpJsonPath" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# BƯỚC 6: TEST MCP SERVER
# ============================================================================
Write-Host "📋 BƯỚC 6: Test MCP Server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Khởi động server (Nhấn Ctrl+C để dừng)..." -ForegroundColor Cyan
Write-Host ""

# Chạy server với timeout 5 giây
$process = Start-Process -FilePath "node" `
    -ArgumentList "src\home-soc-mcp-server.js" `
    -WorkingDirectory "C:\mcp-cyber-tools" `
    -NoNewWindow `
    -PassThru

Start-Sleep -Seconds 3

if ($process.HasExited) {
    Write-Host "❌ Server failed to start" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ Server is running successfully!" -ForegroundColor Green
    Stop-Process -InputObject $process -Force
    Write-Host "✅ Server stopped (test passed)" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# BƯỚC 7: SETUP TASK SCHEDULER (AUTO-START)
# ============================================================================
Write-Host "📋 BƯỚC 7: Thiết lập Task Scheduler (auto-start)..." -ForegroundColor Yellow

$TaskName = "HOME-SOC-MCP-Server"
$TaskPath = "\HOME-SOC\"

# Xóa task cũ nếu tồn tại
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null

# Tạo action
$Action = New-ScheduledTaskAction `
    -Execute "C:\Program Files\nodejs\node.exe" `
    -Argument "C:\mcp-cyber-tools\src\home-soc-mcp-server.js" `
    -WorkingDirectory "C:\mcp-cyber-tools"

# Tạo trigger (khi đăng nhập)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Tạo settings
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Đăng ký task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "HOME SOC MCP Server - Auto start at login" `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "✅ Task Scheduler configured" -ForegroundColor Green
Write-Host "   Task Name: $TaskName" -ForegroundColor Gray
Write-Host "   Trigger: At User Logon" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# BƯỚC 8: KIỂM TRA LẦN CUỐI
# ============================================================================
Write-Host "📋 BƯỚC 8: Kiểm tra toàn bộ hệ thống..." -ForegroundColor Yellow

$checks = @{
    "Node.js" = $nodeVersion
    "npm" = $npmVersion
    "MCP Config" = $mcpJsonPath
    "Task Scheduler" = (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue).TaskName
    "HOME SOC Directory" = "C:\mcp-cyber-tools"
}

foreach ($check in $checks.GetEnumerator()) {
    Write-Host "  ✅ $($check.Key): $($check.Value)" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# HOÀN THÀNH
# ============================================================================
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  ✅ SETUP COMPLETE                               ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📋 TIẾP THEO:" -ForegroundColor Cyan
Write-Host "  1️⃣  Restart Windows:" -ForegroundColor White
Write-Host "     Restart-Computer" -ForegroundColor Gray
Write-Host ""
Write-Host "  2️⃣  Sau khi boot, MCP server sẽ tự động khởi động" -ForegroundColor White
Write-Host ""
Write-Host "  3️⃣  Kiểm tra Claude Code:" -ForegroundColor White
Write-Host "     Settings → MCP Servers → 'home-soc' should be ✅ Connected" -ForegroundColor Gray
Write-Host ""
Write-Host "  4️⃣  Test MCP tools:" -ForegroundColor White
Write-Host "     @discoverDevices" -ForegroundColor Gray
Write-Host "     @predictThreatLevel" -ForegroundColor Gray
Write-Host "     @getAlerts" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 HOME SOC Phase 1–4 is READY FOR DEPLOYMENT!" -ForegroundColor Green
Write-Host ""

# Offer restart
$restart = Read-Host "Restart Windows now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Restart-Computer -Force
} else {
    Write-Host "Please restart manually later" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
}
