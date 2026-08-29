# HOME SOC - Windows Deployment Guide

> **⚠️ IMPORTANT:** This guide covers deployment to **Windows Desktop** (SOC Core Node). HOME SOC requires Windows with Node.js installed.

## Prerequisites

- Windows 10/11 or Windows Server 2019+
- Node.js 18+ ([download](https://nodejs.org/))
- PowerShell 5.0+ (usually pre-installed)
- Claude Desktop (latest version)
- Git (for pulling updates)

## Architecture Overview

```
Windows Desktop (SOC Core Node)
├── C:\mcp-cyber-tools\              # Project root
│   ├── home-soc-mcp-server.js       # MCP server (root level, not src/)
│   ├── network-collector.js         # Device discovery & ARP scanning
│   ├── baseline-analyzer.js         # Statistical anomaly detection
│   ├── config.json                  # Configuration (gateway IP, thresholds)
│   ├── package.json                 # Dependencies
│   └── reports/home-soc-state/      # Live data storage (JSON files)
│       ├── device-history.json      # Current devices, camera status, gateway
│       ├── alerts.json              # Security alerts
│       ├── baseline.json            # Learned patterns (hourly/daily)
│       ├── network-history.json     # Device count timeseries
│       └── changes.json             # Device add/remove events
│
└── %APPDATA%\Claude\claude_desktop_config.json
    └── mcpServers.home-soc          # MCP server registration
        └── command: node home-soc-mcp-server.js
```

## Installation Steps

### 1. Clone Repository

```powershell
# Navigate to your projects directory
cd C:\
git clone https://github.com/kevin-nguyendad/mcp-cyber-tools.git
cd mcp-cyber-tools
```

### 2. Install Node.js Dependencies

```powershell
npm install --force
```

This installs the MCP SDK and utilities needed by the server.

### 3. Configure Network Settings

Edit `config.json` to match your network:

```json
{
  "network": {
    "gatewayIP": "192.168.0.1",    // ← Change to YOUR gateway IP (router)
    "cameraIPs": []                // ← Add camera IPs if you have them
  },
  "alerts": {
    "enabled": true,
    "onNewDevice": true            // Alert when unknown device joins
  }
}
```

**To find your gateway IP:**
```powershell
ipconfig /all
# Look for "Default Gateway" under your active adapter
```

### 4. Register MCP Server with Claude Desktop

**⚠️ Important:** Claude Desktop reads from **`%APPDATA%\Claude\claude_desktop_config.json`**, NOT `~/.claude/mcp.json`.

#### Option A: Manual (GUI)

1. Open Claude Desktop
2. Go to **Settings** → **Developer** → **Model Context Protocol**
3. Click **Add MCP Server** (or edit the JSON directly)
4. Configure:
   ```json
   {
     "name": "home-soc",
     "command": "node",
     "args": ["C:\\mcp-cyber-tools\\home-soc-mcp-server.js"],
     "cwd": "C:\\mcp-cyber-tools"
   }
   ```
5. Restart Claude Desktop

#### Option B: PowerShell Script

```powershell
# Run as Administrator
$claudeConfigPath = "$env:USERPROFILE\AppData\Roaming\Claude\claude_desktop_config.json"

# Read existing config (preserves cyber-tools, pdf-viewer, etc.)
$config = Get-Content $claudeConfigPath | ConvertFrom-Json

# Add/update home-soc entry
$config.mcpServers."home-soc" = @{
    command = "node"
    args = @("C:\mcp-cyber-tools\home-soc-mcp-server.js")
    cwd = "C:\mcp-cyber-tools"
}

# Write back
$config | ConvertTo-Json | Set-Content $claudeConfigPath -Force
Write-Host "✅ MCP server registered"
```

### 5. Verify Connection

1. Restart Claude Desktop
2. Go to **Settings** → **Developer** → **Model Context Protocol**
3. Look for `home-soc` — should show **✅ Connected**

If disconnected:
- Check `reports/home-soc-state/mcp-server.log` for errors
- Verify paths in `config.json` are correct
- Restart Claude Desktop

## First Network Scan

### Manual Collection (Recommended for testing)

```powershell
cd C:\mcp-cyber-tools
node network-collector.js
```

This will:
- Scan ARP table for devices
- Ping the gateway and any cameras
- Measure latency
- Store results in `reports/home-soc-state/device-history.json`
- Alert on new/offline devices
- Update baseline analysis

Output example:
```
📡 Network Collector - Normal Collection
=============================================

📋 Reading ARP table...
   Found: 3 devices
   Previous: 3 devices

📹 Checking camera presence...
   Online: 0/0

📊 Measuring metrics...
   Gateway latency: 2ms

✅ Collection complete
   Stored to:
   - device-history.json (devices + camera status)
   - changes.json (change log)
   - network-history.json (snapshots + metrics)
   - baseline.json (hourly/daily patterns)
   - alerts.json (security alerts)
```

### Using Claude Tools

Once MCP server is connected, test with Claude:

```
@discoverDevices
@homeSocStatus
@predictThreatLevel
@getAlerts
```

## Automated Collection (Optional)

To run collection automatically, use Windows Task Scheduler:

### Create Scheduled Task (PowerShell)

```powershell
# Run as Administrator

$TaskName = "HOME-SOC-Network-Collector"
$ScriptPath = "C:\mcp-cyber-tools\network-collector.js"
$NodePath = "C:\Program Files\nodejs\node.exe"

# Remove old task if exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create action (run collector every 30 minutes)
$Action = New-ScheduledTaskAction -Execute $NodePath -Argument $ScriptPath -WorkingDirectory "C:\mcp-cyber-tools"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "HOME SOC Network Collection (30min interval)" -RunLevel Highest -Force

Write-Host "✅ Task created: $TaskName"
Write-Host "   Runs at: System startup + every 30 minutes"
```

## File Structure Reference

### State Files (Auto-Generated)

These JSON files are created in `reports/home-soc-state/` and read by MCP tools:

| File | Purpose | Updated |
|------|---------|---------|
| `device-history.json` | Current devices, gateway status, cameras | Every collection |
| `baseline.json` | Normal device count patterns by hour/day | Every collection |
| `network-history.json` | 30+ device count snapshots | Every collection |
| `changes.json` | New/offline device events | When detected |
| `alerts.json` | Security alerts (new device, offline device, anomalies) | When triggered |
| `mcp-server.log` | MCP server operation log | Continuous |

### Configuration Files

| File | Purpose | Edit? |
|------|---------|-------|
| `config.json` | Network settings, alert thresholds | ✅ Yes |
| `package.json` | Dependencies | ⚠️ Careful |
| `.claude/mcp.json` | Reference config (NOT read by Claude Desktop) | ❌ No |
| `HANDOFF.md` | Known issues and workarounds | Reference only |

## Configuration Options

### config.json Reference

```json
{
  "paths": {
    "stateDir": "./reports/home-soc-state",
    "logsDir": "./logs"
  },
  "network": {
    "collectionInterval": 1800000,      // 30 minutes (ms)
    "fastScanInterval": 300000,         // 5 minutes (ms)
    "gatewayIP": "192.168.0.1",         // Change to YOUR gateway
    "cameraIPs": []                     // Add cameras if present
  },
  "alerts": {
    "enabled": true,
    "onNewDevice": true,                // Alert on unknown device
    "onDeviceOffline": true,            // Alert when device disappears
    "maxAlerts": 1000                   // Keep recent 1000 alerts
  }
}
```

## Troubleshooting

### "Cannot find module '@modelcontextprotocol/sdk'"

**Solution:**
```powershell
cd C:\mcp-cyber-tools
npm install --force
```

### "EPERM: operation not permitted, mkdir 'C:\WINDOWS\system32\...'"

**Cause:** Process running with wrong working directory

**Solution:** Verify `cwd` in Claude Desktop config points to `C:\mcp-cyber-tools`

### "Found 0 devices" / "Gateway unknown"

**Cause:** ARP table empty (devices haven't communicated recently) or gateway ping failing

**Solution:**
- Run `ping 192.168.0.1` to test gateway connectivity
- Access router web UI or ping devices to refresh ARP cache
- Run `arp -a` to see current ARP entries

### MCP Server Disconnected

**Check the log:**
```powershell
cat .\reports\home-soc-state\mcp-server.log
```

**Common issues:**
- Port already in use (restart Claude)
- Node.js not in PATH (use full path in config)
- File permissions (run as Admin if needed)

## Testing Tools

### Test MCP Server Locally

```powershell
cd C:\mcp-cyber-tools
node home-soc-mcp-server.js
# Will output JSON-RPC messages; Ctrl+C to stop
```

### Test Network Collector

```powershell
cd C:\mcp-cyber-tools
node network-collector.js
# Runs one collection cycle and exits
```

### Test Baseline Analyzer

```powershell
cd C:\mcp-cyber-tools
node baseline-analyzer.js
# Outputs: overall avg, range, anomalies detected
```

## Next Steps

1. ✅ Configure `config.json` with your gateway IP
2. ✅ Register MCP server with Claude Desktop
3. ✅ Run first manual collection: `node network-collector.js`
4. ✅ Verify Claude tools work: `@discoverDevices`
5. ⚙️ (Optional) Set up automatic collection via Task Scheduler
6. 📊 Monitor alerts and device changes in Claude

## Known Issues & Limitations

See [HANDOFF.md](./HANDOFF.md) for:
- Two threat level tools using inverted scales (documented but not fixed)
- Gateway firmware/model fields always return "unknown"
- ARP cache only shows recently-contacted devices (not full subnet discovery)
- MAC-to-vendor lookup currently manual (no OUI database tool)

## Support

For issues with:
- **Deployment:** Check `reports/home-soc-state/mcp-server.log`
- **Network collection:** Run manually with `node network-collector.js` to see errors
- **Configuration:** Verify paths in `config.json` match your Windows setup

---

**Last Updated:** 2026-08-29  
**Status:** Production Ready (Phase 1-4 Complete)
