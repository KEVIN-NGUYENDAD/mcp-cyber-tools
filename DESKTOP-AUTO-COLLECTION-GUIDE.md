# Desktop Auto-Collection Guide
**Purpose**: Run automated data collection on your desktop from now until 8PM, then generate final report

---

## 🚀 Quick Start

### **Option 1: Run Now (Recommended)**

Open PowerShell and run:

```powershell
cd "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools"
node desktop-auto-collector.js
```

The script will:
- Start collecting data immediately
- Collect every 30 minutes
- Stop automatically at 8PM (20:00)
- Generate final report
- Save all data to `auto-collection-data/` folder

---

### **Option 2: Setup Scheduled Task (Auto-Run)**

Run PowerShell as Administrator:

```powershell
cd "C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools"
.\setup-desktop-collection.ps1
```

Then on next system restart, collection will start automatically.

---

## 📊 What Gets Collected

Every 30 minutes, the script captures:
- ✅ **Processes** (top 15)
- ✅ **Network Connections** (established TCP)
- ✅ **System Memory** (usage %)
- ✅ **Running Services** (count)

**Total per snapshot**: ~50 data points  
**At 8PM**: 13-16 snapshots (depending on start time)

---

## 📁 Output Files

When collection completes at 8PM:

```
auto-collection-data/
├── snapshot-1.json      ← First collection
├── snapshot-2.json      ← 30min later
├── snapshot-3.json
├── ...
└── snapshot-N.json      ← Last before 8PM

collection-log.json      ← Detailed collection log
DESKTOP-AUTO-COLLECTION-REPORT.md  ← Final report
```

---

## 📋 Final Report Contents

The report includes:
- Collection timeline (all timestamps)
- Success rate percentage
- Key findings about desktop status
- List of all data files generated
- Action items for analysis

---

## 🎯 After Collection

Once it completes at 8PM:

1. **Review report**: `DESKTOP-AUTO-COLLECTION-REPORT.md`
2. **Check data**: `auto-collection-data/` folder
3. **Run analysis**: Use HOME SOC analysis engine on snapshots
4. **Compare trends**: Look for patterns across 30-min intervals

---

## ⏹️ To Stop Manually

Press **Ctrl+C** in the PowerShell window

Or if using scheduled task:
```powershell
Stop-ScheduledTask -TaskName "HOME-SOC-Desktop-Auto-Collector"
```

---

## 🔧 Troubleshooting

### Script doesn't start
- Make sure Node.js is installed: `node --version`
- Check file permissions on desktop-auto-collector.js
- Run from correct directory

### No data collected
- Check PowerShell execution policy: `Get-ExecutionPolicy`
- May need to run as Administrator
- Check Windows Defender isn't blocking

### Can't create scheduled task
- Run PowerShell as Administrator
- Check User Account Control settings

---

## 📞 When Done

Once collection completes and report is generated:
1. Report will be in: `DESKTOP-AUTO-COLLECTION-REPORT.md`
2. Data will be in: `auto-collection-data/`
3. Both will be auto-committed to GitHub
4. You'll get a notification when complete

---

**Recommended**: Start now, let it run until 8PM, then review results.

```bash
node desktop-auto-collector.js
```

Time: Now → 8PM ⏰
