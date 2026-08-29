# Startup Auto-Collection Setup Guide

**No Admin Rights Required** - Just 3 steps to auto-start collection on every boot

---

## 🚀 Setup (One-Time Only)

### **Step 1: Open Windows Startup Folder**

Press **Windows Key + R**, type:
```
shell:startup
```

Press **Enter** → Startup folder opens

---

### **Step 2: Create Shortcut**

In the Startup folder, right-click → **New → Shortcut**

Paste this path:
```
C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\START-AUTO-COLLECTION.bat
```

Click **Next**

Name it: `HOME SOC Collection`

Click **Finish**

---

### **Step 3: Done! ✅**

Shortcut is now in Startup folder.

**From now on:**
- Every time you boot → collection starts automatically
- Every 30 min → data collected
- At 8PM → report generated

---

## 🎯 What Happens on Boot

```
1. You start computer
2. Windows loads
3. Startup folder runs
4. AUTO-COLLECTION starts
5. Window appears (minimize if you want)
6. Every 30 min → new snapshot
7. At 8PM → STOP + REPORT generated
8. You can close the window or minimize
```

---

## 📁 Files Created

```
auto-collection-data/
  ├── snapshot-1.json (time: started)
  ├── snapshot-2.json (30 min later)
  ├── snapshot-3.json (30 min later)
  └── snapshot-N.json (at 8PM)

collection-log.json
DESKTOP-AUTO-COLLECTION-REPORT.md ← 8PM Report
```

---

## ⏹️ To Stop Collection

**Option 1**: Close the collection window

**Option 2**: In PowerShell:
```powershell
Stop-Process -Name node
```

**Option 3**: To disable auto-startup:
- Open Startup folder (Windows Key + R → shell:startup)
- Delete the "HOME SOC Collection" shortcut

---

## ✅ Verify Setup

After creating the shortcut:

1. **Check Startup folder** → should have "HOME SOC Collection" shortcut
2. **Restart computer** → collection window should appear
3. **Check auto-collection-data folder** → should have snapshot-1.json

---

## 🎯 At 8PM

Report will be generated automatically:
```
DESKTOP-AUTO-COLLECTION-REPORT.md
```

Open it to see:
- Timeline of all collections
- Device status
- Findings summary
- Action recommendations

---

**Done!** Collection will now run automatically on every startup until 8PM. ✅
