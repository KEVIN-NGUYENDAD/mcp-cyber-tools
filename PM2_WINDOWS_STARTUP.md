# PM2 Windows Auto-Start Setup

**Status**: Ready for installation ✅

This guide explains how to set up PM2 to automatically start on Windows boot.

---

## 🚀 Quick Setup (Recommended)

### Method 1: Batch File (Easiest)

1. **Open Command Prompt as Administrator**:
   - Right-click on "Command Prompt"
   - Select "Run as Administrator"
   - Click "Yes" on the UAC prompt

2. **Run the installer**:
   ```cmd
   cd C:\GitHub\mcp-cyber-tools\scripts
   install-pm2-service.bat
   ```

3. **Verify installation**:
   ```cmd
   services.msc
   ```
   Look for `pm2-windows-service` with status "Running"

---

### Method 2: Manual PowerShell

1. **Open PowerShell as Administrator**:
   - Right-click on "PowerShell"
   - Select "Run as Administrator"
   - Click "Yes" on the UAC prompt

2. **Install the service**:
   ```powershell
   pm2-windows-service install
   ```

3. **Verify**:
   ```powershell
   Get-Service "pm2-windows-service"
   ```

---

## ✅ What Gets Auto-Started

After installation, these processes start automatically on boot:

```
pm2 processes:
├── sentinelops-bot (Telegram bot) ✅
└── sentinelops-daily-brief (Daily brief worker) ✅
```

---

## 🔍 Verification

### Check Service Status

**Command Prompt**:
```cmd
sc query pm2-windows-service
```

**PowerShell**:
```powershell
Get-Service "pm2-windows-service" | Select Name, Status, StartType
```

**Services GUI**:
```cmd
services.msc
```

Expected output:
```
Name            Status  StartType
----            ------  ---------
pm2-windows-service Running Automatic
```

---

## 🛠️ Service Management

### Start the Service

```cmd
net start "pm2-windows-service"
```

### Stop the Service

```cmd
net stop "pm2-windows-service"
```

### Restart the Service

```cmd
net stop "pm2-windows-service" && net start "pm2-windows-service"
```

### View Service Status

```powershell
Get-Service "pm2-windows-service" | Format-List
```

---

## 📋 Current PM2 Configuration

**Processes Saved**:
```
✅ sentinelops-bot
   - Node.js Telegram bot
   - Uptime: 27h+
   - Auto-restarts on crash

✅ sentinelops-daily-brief
   - Node.js daily brief worker
   - Runs daily at 3:00 PM UTC
   - Executes: python run_daily_brief.py
```

**Configuration Location**:
```
C:\Users\[username]\.pm2\dump.pm2
```

---

## 📝 Logs

### PM2 Logs
```cmd
pm2 logs
pm2 logs sentinelops-bot
pm2 logs sentinelops-daily-brief
```

### Daily Brief Logs
```cmd
tail -f C:\GitHub\mcp-cyber-tools\logs\daily-brief.log
```

### Windows Service Logs
```powershell
Get-EventLog -LogName System -Source "pm2-windows-service" -Newest 10
```

---

## ⚙️ Advanced Configuration

### Auto-Restart on Crash

Already configured in PM2:
```cmd
pm2 start <app> --max-restarts 10 --min-uptime 10s
```

### Health Monitoring

Check process health:
```cmd
pm2 status
pm2 monit
```

### Process Resurrection (Manual)

If PM2 crashes, restore all processes:
```cmd
pm2 resurrect
```

---

## 🔄 Uninstall (If Needed)

### Remove Windows Service

**PowerShell as Administrator**:
```powershell
pm2-windows-service uninstall
```

**Command Prompt as Administrator**:
```cmd
sc delete pm2-windows-service
```

### Keep PM2 Process List

The processes remain saved in:
```
C:\Users\[username]\.pm2\dump.pm2
```

You can restore them later with:
```cmd
pm2 resurrect
```

---

## 🚨 Troubleshooting

### Service Won't Start

1. Check if PM2 is installed:
   ```cmd
   npm list -g pm2
   ```

2. Check error logs:
   ```powershell
   Get-EventLog -LogName Application -Source "pm2-windows-service" -Newest 10
   ```

3. Restart the service:
   ```cmd
   net stop "pm2-windows-service"
   net start "pm2-windows-service"
   ```

### Processes Not Running After Reboot

1. Verify service is running:
   ```cmd
   net start "pm2-windows-service"
   ```

2. Check PM2 status:
   ```cmd
   pm2 list
   ```

3. Resurrect processes if needed:
   ```cmd
   pm2 resurrect
   ```

### Service Already Exists

If reinstalling, uninstall first:
```cmd
pm2-windows-service uninstall
```

Then reinstall:
```cmd
pm2-windows-service install
```

---

## 📊 Current System State

**Windows Version**: Windows 11 (or later)  
**PM2 Version**: Latest (installed)  
**Node.js**: Running  
**Processes Saved**: 2 (sentinelops-bot, sentinelops-daily-brief)  

---

## ✨ Benefits of PM2 Windows Service

✅ **Auto-Start**: Processes start when Windows boots  
✅ **Auto-Recovery**: Crashed processes restart automatically  
✅ **Unified Management**: Control all processes from PM2  
✅ **Logging**: Centralized process logs  
✅ **Monitoring**: Real-time process metrics  
✅ **No Manual Intervention**: Set and forget  

---

## 🎯 Next Steps

1. **Install PM2 Windows Service** (requires Administrator):
   ```cmd
   cd C:\GitHub\mcp-cyber-tools\scripts
   install-pm2-service.bat
   ```

2. **Verify** after installation:
   ```cmd
   pm2 list
   ```

3. **Test reboot** (optional):
   - Restart Windows
   - Verify processes auto-started:
     ```cmd
     pm2 list
     ```

---

**Last Updated**: 2026-09-12  
**Status**: Ready for deployment ✅

For questions about PM2, see official docs: https://pm2.keymetrics.io/docs/usage/startup/
