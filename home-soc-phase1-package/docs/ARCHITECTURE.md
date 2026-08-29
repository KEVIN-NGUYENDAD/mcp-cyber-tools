# HOME SOC System Architecture

## 🏢 Core Node: Windows Desktop

**Windows Desktop là TRUNG TÂM của hệ thống HOME SOC**

```
Windows Laptop (SOC CORE NODE)
├── MCP Server (JSON-RPC 2.0)
├── Network Collector (ARP + Ping)
├── Baseline Analyzer (Pattern Learning)
├── Dashboard (Web UI)
└── Task Scheduler (Orchestrator)
        ↓
   Real Home Network
        ↓
   ARP Table ← Devices, Cameras, Router
```

## 🔄 Data Pipeline

1. **Task Scheduler** (every 30 min)
   → Run network-collector.js

2. **Network Collector**
   → execSync("arp -a")
   → Ping cameras
   → Detect changes
   → Save JSON files

3. **Baseline Analyzer** (auto-run)
   → Read network-history.json
   → Calculate stats (hourly/daily)
   → Detect anomalies (2-sigma)
   → Save baseline.json

4. **MCP Server** (listening)
   → Provide 8 tools
   → Read JSON files
   → Return formatted data

5. **Dashboard** (browser)
   → Fetch JSON via fetch()
   → Plot charts
   → Show alerts

## 📁 File Structure

```
C:\mcp-cyber-tools\
├── src/
│   ├── home-soc-mcp-server.js
│   ├── network-collector.js
│   ├── baseline-analyzer.js
│   └── collector-telemetry.js
├── scripts/
│   ├── SETUP_GODMODE.ps1
│   └── start-mcp-server.ps1
├── dashboard/
│   └── dashboard.html
├── reports/home-soc-state/
│   ├── device-history.json
│   ├── network-history.json
│   ├── baseline.json
│   ├── alerts.json
│   └── changes.json
├── logs/
│   └── mcp-server.log
├── config.json
└── mcp.json
```

## 🛠️ 8 MCP Tools

All tools read from local JSON files:

1. **discoverDevices** → device-history.json
2. **networkStatus** → network-history.json
3. **cameraStatus** → device-history.json
4. **gatewayStatus** → device-history.json
5. **deviceHistory** → device-history.json
6. **changeHistory** → changes.json
7. **getAlerts** → alerts.json
8. **predictThreatLevel** → baseline.json + network-history.json + alerts.json

## ⚙️ Threat Score Calculation

```
threatScore = 20 + deviceAnomalies + alertFactors + stabilityFactors

deviceAnomalies (0-30):
  If deviation > 50% → +30
  If deviation > 25% → +20
  If deviation > 10% → +10

alertFactors (0-25):
  +5 per high-severity alert
  +4 per recent alert (last hour)

stabilityFactors (0-15):
  High variance → +15

Total: 0-100
Levels: GREEN(0-40), YELLOW(40-60), ORANGE(60-80), RED(80-100)
```

## 🔐 Security Model

- **Zero Cloud**: No external API calls
- **Localhost Only**: MCP server on 127.0.0.1:3000
- **File-based**: All data in local JSON files
- **Windows Firewall**: Blocks external access by default

## 📊 Performance

- **Collection Time**: ~10 seconds
- **Memory**: 30-50 MB
- **Disk**: ~1 MB per month
- **CPU**: < 2% idle

## ✅ Ready for Production

Phase 1-4 Complete
Stable Release
2026-08-29
