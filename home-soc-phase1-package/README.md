# ⚠️ DEPRECATED - HOME SOC Phase 1-4 Complete Package

**This directory is DEPRECATED.** It contains an old package structure with files in `src/` subdirectories.

**➡️ USE INSTEAD:** See [DEPLOYMENT.md](../DEPLOYMENT.md) at the repository root for current setup instructions.

The actual source files are now at the root level:
- `home-soc-mcp-server.js` (not `src/home-soc-mcp-server.js`)
- `network-collector.js` (not `src/network-collector.js`)
- `baseline-analyzer.js` (not `src/baseline-analyzer.js`)

This directory is kept for historical reference only.

---

**Hệ thống giám sát an ninh mạng nhà thông minh**

Phiên bản hoàn chỉnh HOME SOC Phase 1 với đầy đủ tính năng: Baseline Detection, Enhanced Metrics, Dashboard Web, Threat Prediction.

---

## 📋 Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
3. [Phase 1-4 Chi Tiết](#phase-1-4-chi-tiết)
4. [Cấu Trúc Package](#cấu-trúc-package)
5. [Hướng Dẫn Triển Khai](#hướng-dẫn-triển-khai)
6. [Sử Dụng Dashboard](#sử-dụng-dashboard)
7. [Sử Dụng MCP Tools](#sử-dụng-mcp-tools)
8. [Backup & Restore](#backup--restore)

---

## 🎯 Tổng Quan

HOME SOC Phase 1-4 là giải pháp **100% Local** giám sát mạng nhà an toàn:

- ✅ **0 Cloud Dependency** - Tất cả dữ liệu lưu local
- ✅ **Real-time Alerts** - Phát hiện thiết bị lạ ngay lập tức
- ✅ **Baseline Learning** - Học pattern device hàng ngày/giờ
- ✅ **Threat Prediction** - Dự đoán mức đe dọa (0-100 score)
- ✅ **Web Dashboard** - Xem trạng thái real-time trên browser
- ✅ **MCP Integration** - Kết nối với Claude Code trên laptop

**Windows Desktop = SOC Core Node**
- Chạy MCP Server
- Thu thập ARP data mỗi 30 phút
- Fast scan mỗi 5 phút (khi có nghi ngờ)
- Tạo báo cáo hàng ngày 8 PM
- Lưu trữ baseline & alerts

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────┐
│         Windows Laptop (SOC Core)           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   home-soc-mcp-server.js             │  │ ← MCP Server
│  │   (JSON-RPC 2.0, 8 tools)            │  │
│  └──────────────────────────────────────┘  │
│               ↑        ↑                    │
│               │        │                    │
│    ┌──────────┴─────┬──┴─────────┐        │
│    │                │            │        │
│    ▼                ▼            ▼        │
│  network-      baseline-     alerts-     │
│  collector.js  analyzer.js   system      │
│  (ARP data)    (learning)               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   reports/home-soc-state/       │   │
│  │   ├── device-history.json       │   │
│  │   ├── network-history.json      │   │
│  │   ├── baseline.json             │   │
│  │   ├── alerts.json               │   │
│  │   └── changes.json              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   dashboard.html (Local Web UI) │   │ ← Xem real-time
│  │   + Chart.js visualization      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
        ↑
        │ Claude Code (trên laptop)
        │ Kết nối MCP Server
        │
    Claude AI
```

---

## 📊 Phase 1-4 Chi Tiết

### Phase 1: Baseline & Anomaly Detection

**File:** `src/baseline-analyzer.js`

Tự động học pattern device theo giờ và ngày:

```javascript
// Định Dạng baseline.json
{
  "hourly": {
    "08": { 
      "avg": 5.2,           // Trung bình thiết bị vào 8 sáng
      "min": 3,             // Tối thiểu
      "max": 8,             // Tối đa
      "stdDev": 1.5,        // Độ lệch chuẩn
      "count": 48           // Số mẫu
    }
  },
  "daily": {
    "monday": { "avg": 5.1 },
    "tuesday": { "avg": 5.3 }
  },
  "overall": {
    "avg": 5.2,
    "min": 0,
    "max": 20
  }
}
```

**Anomaly Detection:**
- Sử dụng quy tắc 2-sigma: nếu độ lệch > 2×stdDev → ANOMALY
- Severity: HIGH (>3 sigma), MEDIUM (2-3 sigma)
- Tự động trigger Fast Scan Mode

---

### Phase 2: Enhanced Collector

**File:** `src/network-collector.js`

Nâng cấp từ 30 phút 1 lần → thêm Fast Scan 5 phút:

```javascript
// Các metrics mới
{
  "metrics": {
    "gatewayLatency": 2,           // ms ping gateway
    "cameraLatencies": {
      "192.168.1.100": 5,          // ms ping camera 1
      "192.168.1.101": 4
    }
  }
}
```

**Chế Độ Hoạt Động:**

| Mode | Interval | Trigger | Mục Đích |
|------|----------|---------|----------|
| Normal | 30 phút | Task Scheduler | Thu thập dữ liệu thường xuyên |
| Fast Scan | 5 phút | Tự động (khi phát hiện device mới) | Xác minh nghi ngờ |

**Auto-Alert System:**
- 🚨 New Device → Severity: HIGH
- ⚠️ Device Offline → Severity: MEDIUM
- 📊 Anomaly → Severity: HIGH/MEDIUM

---

### Phase 3: Dashboard Web (Local Only)

**File:** `dashboard/dashboard.html`

Web UI đơn giản, không cần backend:

```html
<!-- Cấu trúc Dashboard -->
┌─────────────────────────────────┐
│  🏠 HOME SOC Dashboard           │
├─────────────────────────────────┤
│ [Status: GREEN]   [Score: 95]   │
├─────────────────────────────────┤
│ 🖥️ Devices: 5      📹 Cameras: 3 │
│ 🚨 Alerts: 0       📊 Stability: 95% │
├─────────────────────────────────┤
│ 📈 Device Count Timeline (48h)  │
│ [CHART LINE: ups/downs]          │
├─────────────────────────────────┤
│ ⏰ Hourly Baseline Pattern      │
│ [CHART BAR: 08:5 09:5 10:6 ...]  │
├─────────────────────────────────┤
│ 🚨 Recent Alerts                │
│ - [HIGH] new-device: 192.168... │
│ - [INFO] device-offline: 10.0.. │
└─────────────────────────────────┘
```

**Tính Năng:**
- ✅ Load data từ `reports/home-soc-state/` (localhost)
- ✅ Auto-refresh 30 giây
- ✅ Chart.js timeline + baseline bars
- ✅ Dark theme, responsive
- ✅ Zero external dependencies (offline mode)

**Cách Xem:**
```bash
# Mở file trực tiếp
file:///C:/mcp-cyber-tools/dashboard.html

# Hoặc dùng simple server
python -m http.server 8000
# Rồi truy cập: http://localhost:8000/dashboard.html
```

---

### Phase 4: Threat Level Prediction

**Tool MCP:** `predictThreatLevel`

Dự đoán mức đe dọa mạng dựa trên 4 yếu tố:

```javascript
// Response Example
{
  "threatScore": 62,              // 0-100 (62 = ORANGE)
  "threatLevel": "ORANGE",        // GREEN, YELLOW, ORANGE, RED
  "prediction": {
    "currentDevices": 8,          // Thiết bị hiện tại
    "expectedDevices": 5,         // Dự kiến từ baseline
    "deviation": 3,               // Sai lệch
    "deviationPercent": 60,       // 60% cao hơn expected
    "criticalAlerts": 2,          // Alerts HIGH severity
    "recentAlerts": 1             // Alerts trong 1 giờ cuối
  },
  "factors": {
    "deviceAnomaly": "HIGH",      // Devices lệch so baseline
    "alertTrend": "NORMAL",       // Alerts trend
    "networkStability": "UNSTABLE" // Device count volatile
  },
  "recommendation": "WARNING: Phát hiện nhiều thay đổi. Tăng cường giám sát."
}
```

**Threat Score Calculation:**

```
Threat Score = Base(20) + Device(0-30) + Alerts(0-45) + Stability(0-15)

Device Anomaly (0-30):
  - > 50% deviation → +30
  - > 25% deviation → +20
  - > 10% deviation → +10

Critical Alerts (0-25):
  - +5 per high-severity alert

Recent Alerts (0-20):
  - +4 per alert in last hour

Network Stability (0-15):
  - High variance → +15
```

**Threat Levels:**
- 🟢 GREEN (0-40) - Normal, continue monitoring
- 🟡 YELLOW (40-60) - Caution, check device history
- 🟠 ORANGE (60-80) - Warning, increase monitoring
- 🔴 RED (80-100) - Critical, investigate immediately

---

## 📁 Cấu Trúc Package

```
home-soc-phase1-package/
├── src/                           # Core engine
│   ├── home-soc-mcp-server.js    # MCP Server (8 tools)
│   ├── network-collector.js      # Network data collection
│   ├── baseline-analyzer.js      # Learn baseline patterns
│   └── collector-telemetry.js    # Quality metrics
│
├── scripts/                       # Windows automation
│   ├── SETUP_GODMODE.ps1         # Create Task Scheduler tasks
│   └── start-mcp-server.ps1      # Launch MCP server
│
├── dashboard/                     # Web UI
│   └── dashboard.html            # Real-time monitoring dashboard
│
├── reports/                       # Data storage
│   └── home-soc-state/
│       ├── device-history.json   # Current devices + cameras
│       ├── network-history.json  # Snapshots + metrics
│       ├── baseline.json         # Hourly/daily patterns
│       ├── alerts.json           # Security alerts
│       └── changes.json          # Change log
│
├── mcp.json                       # MCP configuration
├── README.md                      # Documentation
└── VERSION.txt                    # Version info
```

---

## 🚀 Hướng Dẫn Triển Khai

### Bước 1: Chuẩn Bị Thư Mục

```powershell
# Trên Windows laptop
cd C:\mcp-cyber-tools

# Copy package vào
xcopy home-soc-phase1-package\src\* .
xcopy home-soc-phase1-package\scripts\* .
xcopy home-soc-phase1-package\dashboard\* .
```

### Bước 2: Chạy PowerShell Setup (Admin)

```powershell
# Mở PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\SETUP_GODMODE.ps1

# Kết quả: 4 Task Scheduler tasks được tạo
#   - Startup (lúc logon)
#   - Collector (mỗi 30 phút)
#   - Reports (8 PM hàng ngày)
#   - MCP Server (lúc logon)
```

### Bước 3: Copy MCP Config

```bash
# Copy mcp.json vào Claude Code profile
cp mcp.json C:\Users\[username]\.claude\mcp.json

# Restart Claude Code on laptop
```

### Bước 4: Restart Windows

```powershell
# Để Task Scheduler activation hoạt động
Restart-Computer
```

### Bước 5: Xác Minh Hoạt Động

```powershell
# Kiểm tra Task Scheduler
Get-ScheduledTask -TaskName "*HOME*"

# Kiểm tra MCP Server log
type C:\mcp-cyber-tools\logs\mcp-server.log

# Kiểm tra device-history.json được cập nhật
type C:\mcp-cyber-tools\reports\home-soc-state\device-history.json

# Mở dashboard
start "C:\mcp-cyber-tools\dashboard.html"
```

---

## 🌐 Sử Dụng Dashboard

### Truy Cập Dashboard

**Cách 1: Trực tiếp (Recommended)**
```
File → Open → C:\mcp-cyber-tools\dashboard.html
```

**Cách 2: Simple HTTP Server**
```powershell
cd C:\mcp-cyber-tools
python -m http.server 8000

# Sau đó truy cập: http://localhost:8000/dashboard.html
```

### Hiểu Các Widget

| Widget | Ý Nghĩa |
|--------|---------|
| **Devices Online** | Số thiết bị hiện tại trên mạng |
| **Cameras** | Số camera online/offline |
| **Alerts** | Tổng alerts + critical count |
| **Network Stability** | Ổn định mạng (%) dựa variance |
| **Timeline Chart** | Device count 48 giờ qua |
| **Baseline Pattern** | Hourly average devices |
| **Alerts List** | 10 alert gần nhất |

### Diễn Giải Màu Sắc

- 🟢 **Green** - Ổn định, không nghi ngờ
- 🟡 **Yellow** - Cảnh báo nhẹ, kiểm tra lịch sử
- 🟠 **Orange** - Cảnh báo, tăng cường giám sát
- 🔴 **Red** - Nguy hiểm, điều tra ngay

---

## 🛠️ Sử Dụng MCP Tools

### Kết Nối từ Claude Code (Laptop)

1. Mở Claude Code **trên laptop** (không cloud)
2. Settings → MCP
3. Chọn "home-soc" server
4. Status: **CONNECTED** ✓

### 8 Công Cụ Có Sẵn

```
1️⃣  discoverDevices
    → Danh sách thiết bị trên mạng
    Input: (none)
    Output: IP, MAC, vendor, lastSeen

2️⃣  networkStatus
    → Trạng thái mạng (gateway, stability, avg)
    Input: (none)
    Output: deviceCount, stabilityScore, snapshots

3️⃣  cameraStatus
    → Trạng thái camera (online/offline)
    Input: (none)
    Output: camerasMonitored, onlineCount, onlinePercentage

4️⃣  gatewayStatus
    → Kiểm tra router/gateway
    Input: (none)
    Output: status, IP, model, firmwareVersion

5️⃣  deviceHistory
    → Lịch sử thu thập (timeline)
    Input: (none)
    Output: timeline[timestamp, deviceCount, changes]

6️⃣  changeHistory
    → 10 thay đổi gần nhất
    Input: (none)
    Output: type, IP, MAC, severity

7️⃣  getAlerts
    → Danh sách alerts
    Input: (none)
    Output: totalAlerts, recentAlerts[], critical[]

8️⃣  predictThreatLevel
    → Dự đoán mức đe dọa
    Input: (none)
    Output: threatScore, threatLevel, factors, recommendation
```

### Ví Dụ Sử Dụng Claude Code

```
User: "Kiểm tra trạng thái mạng"

Claude: [Gọi predictThreatLevel tool]
Result: {
  "threatScore": 45,
  "threatLevel": "YELLOW",
  "currentDevices": 6,
  "expectedDevices": 5,
  "recommendation": "CAUTION: Có một số cảnh báo. Kiểm tra lịch sử thiết bị."
}

Claude: "Mạng bình thường nhưng có 6 thiết bị (expected 5). 
Đề xuất: kiểm tra device-history.json để xem device mới là gì."
```

---

## 💾 Backup & Restore

### Backup Toàn Bộ

```powershell
# Tạo backup
$backupDir = "C:\backups\home-soc-$(Get-Date -f 'yyyy-MM-dd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir
Copy-Item -Path "C:\mcp-cyber-tools\reports" -Destination "$backupDir\" -Recurse
Copy-Item -Path "C:\mcp-cyber-tools\logs" -Destination "$backupDir\" -Recurse
Write-Host "✓ Backup: $backupDir"
```

### Restore từ Backup

```powershell
# Restore dữ liệu
$backupDir = "C:\backups\home-soc-2026-08-29-120000"
Copy-Item -Path "$backupDir\reports\*" -Destination "C:\mcp-cyber-tools\reports\" -Recurse -Force
Copy-Item -Path "$backupDir\logs\*" -Destination "C:\mcp-cyber-tools\logs\" -Recurse -Force
Write-Host "✓ Restored from: $backupDir"
```

### Tự Động Backup Hàng Ngày

```powershell
# Thêm PowerShell script vào Task Scheduler
$scriptContent = @'
$backupDir = "C:\backups\home-soc-$(Get-Date -f 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $backupDir -Force
Copy-Item -Path "C:\mcp-cyber-tools\reports" -Destination "$backupDir\" -Recurse -Force
'@

$scriptContent | Out-File "C:\mcp-cyber-tools\scripts\daily-backup.ps1"

# Chạy hàng ngày 11 PM
Register-ScheduledTask -TaskName "HOME-SOC-Backup" `
  -Action (New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-ExecutionPolicy Bypass C:\mcp-cyber-tools\scripts\daily-backup.ps1") `
  -Trigger (New-ScheduledTaskTrigger -Daily -At "23:00")
```

---

## 📈 Monitoring & Maintenance

### Kiểm Tra Hằng Ngày

```powershell
# 1. Kiểm tra MCP Server chạy
Get-Process | grep node

# 2. Kiểm tra log gần nhất
tail -f C:\mcp-cyber-tools\logs\mcp-server.log

# 3. Kiểm tra alerts
type C:\mcp-cyber-tools\reports\home-soc-state\alerts.json

# 4. Kiểm tra network-history size
(Get-Item C:\mcp-cyber-tools\reports\home-soc-state\network-history.json).Length
```

### Dọn Dẹp Dữ Liệu Cũ (Tùy Chọn)

```javascript
// network-history.json giữ max 100 snapshots (≈ 3-4 ngày)
// baseline.json được update tự động (không cần dọn)
// alerts.json giữ max 1000 alerts

// Nếu muốn reset toàn bộ:
rm C:\mcp-cyber-tools\reports\home-soc-state\*.json
# MCP Server sẽ tạo lại tự động
```

---

## 🔧 Troubleshooting

### MCP Server Không Kết Nối

```
✗ Problem: Claude Code không thấy MCP tools

Solution:
1. Kiểm tra mcp.json tồn tại: C:\Users\[username]\.claude\mcp.json
2. Kiểm tra mcp.json format đúng
3. Kiểm tra MCP Server chạy: Get-Process node
4. Restart Claude Code on laptop
5. Kiểm tra port 3000 không bị block
```

### Network Collector Không Chạy

```
✗ Problem: device-history.json không update

Solution:
1. Kiểm tra Task Scheduler: Get-ScheduledTask -TaskName "HOME-*"
2. Kiểm tra task status: READY (not DISABLED)
3. Kiểm tra log: C:\mcp-cyber-tools\logs\
4. Manual run: node C:\mcp-cyber-tools\network-collector.js
5. Kiểm tra ARP available: arp -a
```

### Dashboard Không Load Dữ Liệu

```
✗ Problem: Charts không hiển thị

Solution:
1. Kiểm tra JSON files tồn tại: 
   - device-history.json
   - network-history.json
   - baseline.json
2. Validate JSON: https://jsonlint.com/
3. Kiểm tra browser console (F12) có error
4. Thử Simple Server: python -m http.server 8000
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Collection Time** | ~10 giây (ARP + ping) |
| **Memory Usage** | ~30-50 MB |
| **Log File Size** | ~1-2 MB/tháng |
| **Network History** | ~50 KB (100 snapshots) |
| **Dashboard Load** | <1 giây (local files) |

---

## 🔒 Bảo Mật & Privacy

✅ **100% Local**
- Không gửi data ra ngoài
- Không có API calls
- Không có tracking

✅ **Windows Firewall**
- MCP Server chạy localhost:3000 (nội bộ)
- ARP queries không vượt qua gateway

✅ **Data Retention**
- device-history: 100 collections (~3-4 ngày)
- baseline.json: vô hạn (update liên tục)
- alerts.json: 1000 entries (~1-2 tuần)

---

## 📝 License & Support

**Phase 1-4 Complete - Stable Release**
- Version: 1.0.0
- Stable: Yes
- Last Updated: 2026-08-29

---

## 🎯 Tiếp Theo?

Sau khi Phase 1-4 chạy ổn định, có thể mở rộng:

- **Phase 5**: Email alerts (Gmail SMTP)
- **Phase 6**: Database (SQLite local storage)
- **Phase 7**: Mobile app (Flask web server)
- **Phase 8**: AI learning (Anomaly auto-tune thresholds)

---

**Tạo bởi:** HOME SOC Development Team  
**Ngôn Ngữ:** JavaScript (Node.js + MCP)  
**Nền Tảng:** Windows Laptop (Local Only)  
**Loại Lưu Trữ:** JSON files (./reports/home-soc-state)
