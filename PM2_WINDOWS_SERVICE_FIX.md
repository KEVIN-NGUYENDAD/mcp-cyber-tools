# PM2 Windows Service Installation Fix

**Status**: ⚠️ Service requires Administrator privileges to install

**Problem**: The `pm2-windows-service` module is installed and online in PM2, but the Windows service hasn't been created yet because it requires Administrator privileges.

---

## 🔧 Solution

### Quick Fix (Recommended)

1. **Open PowerShell as Administrator**
   - Press `Win + X`
   - Select "PowerShell (Admin)"
   - Click "Yes" on UAC prompt

2. **Set execution policy** (one-time):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   ```

3. **Run the installer script**:
   ```powershell
   & "C:\GitHub\mcp-cyber-tools\scripts\install-pm2-windows-service-admin.ps1"
   ```

4. **Verify installation**:
   ```cmd
   services.msc
   ```
   Look for service starting with "PM2"

---

## 📊 Current Status

```
✅ PM2 running
✅ sentinelops-bot online (27h+)
✅ sentinelops-daily-brief online (8m+)
✅ pm2-windows-service module online
❌ Windows Service NOT INSTALLED YET (needs Admin)
```

---

## 🚀 Installation Methods

### Method 1: PowerShell Script (EASIEST)

**Requirements**: Administrator PowerShell window

**Steps**:
```powershell
# 1. Open PowerShell as Administrator
# 2. Set execution policy
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# 3. Run installer
& "C:\GitHub\mcp-cyber-tools\scripts\install-pm2-windows-service-admin.ps1"
```

**What it does**:
- Verifies Administrator privileges
- Checks PM2 installation
- Verifies pm2-windows-service module
- Creates Windows service
- Starts the service
- Provides verification steps

---

### Method 2: Manual Command Prompt (ALTERNATIVE)

**Requirements**: Administrator Command Prompt

**Steps**:
```cmd
# 1. Open Command Prompt as Administrator
# 2. Navigate to PM2 modules
cd %USERPROFILE%\.pm2\modules\pm2-windows-service

# 3. Run the installer (if it exists)
npm run install
```

---

### Method 3: Direct PowerShell (ADVANCED)

**Requirements**: Administrator PowerShell

**Steps**:
```powershell
# Run the pm2-windows-service module directly
$modulePath = "$env:USERPROFILE\.pm2\modules\pm2-windows-service"
& node "$modulePath\node_modules\pm2-windows-service\bin\pm2-service-install.js"
```

---

## ✅ Verification

### After Installation

**Check service exists**:
```cmd
sc query PM2
```

Expected output:
```
SERVICE_NAME: PM2
STATE : RUNNING
```

**Check via GUI**:
- Press `Win + R`
- Type `services.msc`
- Look for service containing "PM2"

**Check via PowerShell**:
```powershell
Get-Service | Where-Object {$_.Name -like "*PM2*"} | Select-Object Name, Status, StartType
```

Expected: Status = Running, StartType = Automatic

---

## 🔍 Troubleshooting

### Service Not Created

**Check Module Logs**:
```powershell
Get-Content $env:USERPROFILE\.pm2\logs\pm2-windows-service-error.log -Tail 30
```

**Look for**:
- "Run this as administrator" hint ← needs Admin
- Permission denied errors ← needs Admin
- Module version issues ← try reinstalling

**Solution**: Run everything as Administrator

---

### Service Created But Not Starting

**Check Windows Event Logs**:
```powershell
Get-EventLog -LogName System | Where-Object {$_.Source -like "*PM2*"} | Select-Object TimeGenerated, EventID, Message
```

**Try Manual Start**:
```cmd
net start PM2
```

**Check PM2 Logs**:
```cmd
pm2 logs
```

---

### PM2 Processes Not Listed in Service

**Verify PM2 Processes**:
```cmd
pm2 list
```

Must show:
```
✓ sentinelops-bot ............ online
✓ sentinelops-daily-brief .... online
```

**Save PM2 Configuration**:
```cmd
pm2 save
```

**Resurrect Processes**:
```cmd
pm2 resurrect
```

---

## 🔄 Manual Auto-Start Alternative

If Windows service installation fails permanently, use Task Scheduler as backup:

**Create Task**:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "PM2 Auto-Start"
4. Trigger: "At startup"
5. Action: Start a program
   - Program: `C:\Program Files\nodejs\node.exe`
   - Arguments: `-e "require('pm2').connect(e => {if(e) process.exit(2); require('pm2').resurrect(() => process.exit(0))})" `

---

## 📝 Process Flow After Installation

```
Windows Boot
    ↓
Service: PM2
    ├── Resurrects saved processes
    ├── Starts sentinelops-bot
    ├── Starts sentinelops-daily-brief
    └── Monitoring active
        ↓
3:00 PM UTC
    ├── Daily Brief runs
    ├── Generates JSON + HTML
    ├── Sends Telegram
    └── Saves to Render
        ↓
On Crash
    ├── PM2 detects failure
    ├── Auto-restarts process
    ├── Logs event
    └── Service keeps running
```

---

## 🎯 Final Checklist

After running the installer:

- [ ] PM2 service is installed and running
- [ ] Service is set to "Automatic" start type
- [ ] Both processes show in `pm2 list`
- [ ] `pm2 save` executed
- [ ] `services.msc` shows "PM2*" service
- [ ] Service status is "Running"
- [ ] Test: Restart Windows, processes come back online

---

## 🚀 Success Indicators

When everything works:

```
✅ Windows starts
✅ PM2 service auto-starts
✅ sentinelops-bot comes online automatically
✅ sentinelops-daily-brief comes online automatically
✅ At 3:00 PM UTC, Daily Brief sends Telegram
✅ No manual intervention needed
```

---

## 📞 Support

If installation still fails:

1. **Verify Administrator**:
   ```powershell
   [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
   ```
   Should return: `True`

2. **Check UAC Settings**:
   - Settings → Privacy → App permissions
   - Ensure UAC is enabled

3. **Run Manual Start**:
   ```cmd
   net start PM2
   pm2 list
   ```

4. **Check Event Viewer**:
   - Search "Event Viewer"
   - Windows Logs → System
   - Look for PM2-related errors

5. **PM2 Logs**:
   ```cmd
   pm2 logs pm2-windows-service
   ```

---

**Last Updated**: 2026-09-12  
**Status**: Ready for Administrator installation ✅

Once installed, Daily Brief will be fully autonomous and production-ready.
