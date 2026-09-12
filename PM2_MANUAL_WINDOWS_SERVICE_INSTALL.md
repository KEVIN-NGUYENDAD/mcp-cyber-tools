# Manual PM2 Windows Service Installation

**Status**: ⚠️ Module online but awaiting Administrator action

**Root Cause**: PM2 module requires Administrator privileges and interactive input to create Windows service.

---

## 🔧 Manual Installation Steps

### Step 1: Open PowerShell as Administrator

1. Press `Win + X`
2. Select **"PowerShell (Admin)"** or **"Windows Terminal (Admin)"**
3. Click **"Yes"** on the UAC prompt

### Step 2: Verify Current Status

```powershell
# Check if PM2 processes exist
pm2 list

# Check if service already exists
Get-Service | Where-Object {$_.Name -like "*PM2*"}
```

Expected:
```
sentinelops-bot           online
sentinelops-daily-brief   online
pm2-windows-service       online

(Get-Service shows nothing yet)
```

### Step 3: Install Windows Service

**Method A: Using the fixed PowerShell script (RECOMMENDED)**

```powershell
# Run the installer script
& "C:\GitHub\mcp-cyber-tools\scripts\install-pm2-windows-service-admin.ps1"
```

The script will:
1. Verify Administrator status
2. Run the pm2-windows-service module installer
3. Create Windows service
4. Start the service
5. Verify the installation

**Method B: Direct Windows Service Creation (if Method A fails)**

```powershell
# Create the Windows service directly
$modulePath = "$env:USERPROFILE\.pm2\modules\pm2-windows-service"
$installerPath = "$modulePath\node_modules\pm2-windows-service\bin\pm2-service-install.cmd"

if (Test-Path $installerPath) {
    & $installerPath
} else {
    Write-Host "Installer script not found at: $installerPath"
}
```

**Method C: NPM Installation (Advanced)**

```powershell
# Try NPM-based installation
npm run -g pm2 windows-service-install
```

---

## ✅ Verification After Installation

### Step 1: Check Service Exists

```powershell
Get-Service | Where-Object {$_.Name -like "*PM2*"}
```

**Expected output**:
```
Status   Name                DisplayName
------   ----                -----------
Running  PM2 service for... PM2 service for node.js
```

### Step 2: Check Service Properties

```powershell
$service = Get-Service | Where-Object {$_.Name -like "*PM2*"}
$service | Select-Object Name, DisplayName, Status, StartType
```

**Expected**:
```
Name         : PM2 service for node.js
DisplayName  : PM2 service for node.js
Status       : Running
StartType    : Automatic
```

### Step 3: Verify SC Registry

```cmd
sc query PM2
```

**Expected**:
```
SERVICE_NAME: PM2
        TYPE               : 110  WIN32_OWN_PROCESS (interactive)
        STATE              : 4  RUNNING
        WIN32_EXIT_CODE    : 0  (0x0)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
```

---

## 🔄 Reboot Test

After installation, test auto-start:

```powershell
# Save PM2 configuration
pm2 save

# Restart Windows
Restart-Computer -Force
```

**After reboot**:

```cmd
pm2 list
```

**Expected**:
```
┌────┬────────────────────────┬─────────┬─────────────┐
│ id │ name                   │ status  │ uptime      │
├────┼────────────────────────┼─────────┼─────────────┤
│ 0  │ sentinelops-bot        │ online  │ 2m          │
│ 1  │ sentinelops-daily-brief│ online  │ 1m          │
└────┴────────────────────────┴─────────┴─────────────┘
```

---

## 🛠️ Troubleshooting

### Service Not Created

**Check logs**:
```powershell
Get-Content "$env:USERPROFILE\.pm2\logs\pm2-windows-service-error.log" -Tail 100
```

**Look for**:
- "Run this as administrator" → Not running as Admin
- "EACCES" or "Permission denied" → UAC issue
- "ENOENT" or "not found" → Missing installer file

### Service Created But Won't Start

**Check event logs**:
```powershell
Get-EventLog -LogName System -Source ServiceControl | Select-Object TimeGenerated, EventID, Message | Select-Object -First 10
```

**Try manual start**:
```cmd
net start "PM2 service for node.js"
```

### After Reboot, Services Don't Come Online

**Check service status**:
```cmd
sc query PM2
```

**Check if still running**:
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*PM2*" -or $_.ProcessName -like "*node*"}
```

**Manually start PM2**:
```cmd
pm2 resurrect
pm2 list
```

---

## 📋 Success Checklist

After completing the manual installation:

- [ ] PowerShell running as Administrator
- [ ] Installer script/command executed successfully
- [ ] `Get-Service` shows PM2 service
- [ ] Service Status is "Running"
- [ ] Service StartType is "Automatic"
- [ ] `sc query PM2` returns STATE: 4 (RUNNING)
- [ ] Rebooted Windows
- [ ] After reboot: `pm2 list` shows both processes online
- [ ] sentinelops-bot process running
- [ ] sentinelops-daily-brief process running

---

## 🎯 Final Verification

```powershell
# All-in-one verification script
Write-Host "=== PM2 Windows Service Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Service Status
$service = Get-Service | Where-Object {$_.Name -like "*PM2*"} -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "[OK] Service found" -ForegroundColor Green
    Write-Host "  Name: $($service.Name)"
    Write-Host "  Status: $($service.Status)"
    Write-Host "  StartType: $($service.StartType)"
} else {
    Write-Host "[ERROR] Service not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. PM2 Processes
Write-Host "PM2 Processes:" -ForegroundColor Cyan
& pm2 list

Write-Host ""

# 3. Success Indication
Write-Host "[SUCCESS] Windows Service fully operational" -ForegroundColor Green
Write-Host "Processes will auto-start after Windows reboot" -ForegroundColor Green
```

---

## 📞 Support

If installation still fails after these steps:

1. Verify running as Administrator: `[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)`
2. Check UAC settings in Windows Security
3. Try disabling antivirus temporarily during installation
4. Check Windows Event Viewer for service-related errors
5. Reinstall pm2-windows-service module: `pm2 uninstall pm2-windows-service && pm2 install pm2-windows-service`

---

**Last Updated**: 2026-09-12  
**Status**: Ready for manual Administrator installation ✅

Once you complete these steps, the PM2 Windows Service will be fully operational and processes will auto-start on Windows boot.
