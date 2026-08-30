# HOME SOC PROJECT - CHECKPOINT

**Date**: 2026-08-30  
**Status**: 85% Complete - iPhone Shortcut Setup In Progress

---

## ✅ COMPLETED

### Network Security
- ✅ Removed malicious camera (192.168.0.25 - Telnet port 23)
- ✅ Disabled UPnP on router
- ✅ Disabled MoCA on router
- ✅ Router firewall: Custom Security (hardened)
- ✅ No port forwarding exposed
- ✅ **Network Status: 0 risks, 3 devices safe**

### Automated Collection
- ✅ Desktop auto-scan at startup (desktop-auto-collector.js)
- ✅ Laptop auto-collect every 30min until 8PM (laptop-auto-collector.js)
- ✅ Router scan daily 9PM (scheduled task)
- ✅ Auto-push to GitHub on all scans
- ✅ Network scan detects: Router, Reolink Camera, Laptop
- ✅ iOS Shortcut guide created (IPHONE-EASIEST.txt)

### Documentation
- ✅ Router security audit report (ROUTER-SECURITY-AUDIT-2026-08-30.md)
- ✅ iOS Shortcut setup guides (3 versions - from detailed to simple)
- ✅ Windows iPhone monitor script (iphone-icloud-monitor.ps1)
- ✅ GitHub auto-push for all data flows

---

## 🔄 IN PROGRESS

### iPhone Auto-Reporting (User Currently Working On)
- 🔵 Creating iOS Shortcut:
  - Step 1: Mở Shortcuts app (icon tím)
  - Step 2: Tạo "Ask for Text" x4 (Battery, WiFi, Apps, Device)
  - Step 3: Combine into text
  - Step 4: Save to iCloud → mcp-cyber-tools folder
  - Step 5: Setup automation (Daily 9 PM)

---

## ⏭️ REMAINING TASKS

### iPhone Shortcut (Next Session)
1. Finish creating 4 "Ask for Text" prompts
2. Add Text action to combine data
3. Add Save File action → iCloud
4. Test shortcut (play ▶️)
5. Run Windows monitor: `.\iphone-icloud-monitor.ps1`

### Optional Enhancements
- Add Samsung device detection (MAC OUI added, testing pending)
- Test WiFi-only mode on iPhone (currently using Cellular Data)
- iPad/iPad-2 auto-detection (MACs in scanner)
- Reolink camera MQTT monitoring (optional, low priority)

---

## 📊 CURRENT NETWORK STATE

| Device | IP | Status | Risk |
|---|---|---|---|
| Router (ARRIS) | 192.168.0.1 | ✅ Hardened | 0 |
| Reolink Camera | 192.168.0.21 | ✅ Safe | 0 |
| Laptop | 192.168.0.233 | ✅ Safe | 0 |
| Camera (Removed) | 192.168.0.25 | ❌ OFFLINE | - |

---

## 🔧 QUICK REFERENCE

### Start Collection
```powershell
# Windows
cd $env:APPDATA\Claude\Projects\mcp-cyber-tools
node startup-router-scan.js           # Scan network
.\iphone-icloud-monitor.ps1           # Monitor iPhone data
```

### Test Network
```powershell
node iot-device-scanner.js            # Full device scan
arp -a                                 # ARP table check
```

### GitHub Branch
- Branch: `learning-factory-v2`
- Auto-push on all collection
- Data dirs: `network-scan-data/`, `iphone-data/`

---

## 📝 NEXT SESSION TODO

1. **Continue iPhone Shortcut Setup** (User was at step 2 of 7)
   - File: IPHONE-EASIEST.txt (simple 7-step guide)
   - Already: Found "Ask for Text" action
   - Next: Add 4 prompts (Battery, WiFi, Apps, Device)

2. **Test iPhone Shortcut**
   - Run shortcut (▶️)
   - Answer 4 prompts
   - Verify file saved to iCloud

3. **Start Windows Monitor**
   - `.\iphone-icloud-monitor.ps1`
   - Monitor will auto-push iPhone data to GitHub

4. **Verify Full Pipeline**
   - iPhone → iCloud → Windows → GitHub

---

## 📁 KEY FILES

- `IPHONE-EASIEST.txt` - Simple 7-step guide (START HERE)
- `iphone-icloud-monitor.ps1` - Windows monitoring script
- `startup-router-scan.js` - Boot-time collection
- `iot-device-scanner.js` - Network security scanner
- `ROUTER-SECURITY-AUDIT-2026-08-30.md` - Full security report

---

## 💾 DATA STORED

- Network scans: `network-scan-data/` (JSON format)
- iPhone data: `iphone-data/` (JSON format)
- Router audit: `ROUTER-SECURITY-AUDIT-2026-08-30.md`
- All auto-pushed to GitHub learning-factory-v2 branch

---

**Status**: Ready to continue iPhone Shortcut setup next session 📱

**Time to Complete Remaining**: ~15 minutes (finish shortcut + test)

**Target**: Full HOME SOC automated by 2026-08-31
