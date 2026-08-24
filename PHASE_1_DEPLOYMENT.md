# PHASE 1: REAL HOME SOC DEPLOYMENT
## 14-Day Evidence Collection

**Mission:** Deploy network monitoring without router login. Detect changes, track devices, identify risks using network evidence only.

---

## PREREQUISITES

### Install required tools on your home network desktop:

```bash
# Ubuntu/Debian
sudo apt-get install arp-scan nmap net-tools

# macOS  
brew install arp-scan nmap

# Fedora/RHEL
sudo dnf install arp-scan nmap
```

### Verify tools work:

```bash
which arp-scan
which nmap
which arp
```

---

## DEPLOYMENT STEPS

### 1. Clone to home network desktop

```bash
git clone https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools.git
cd mcp-cyber-tools
git checkout claude/dfir-triage-investigation-xhgwz7
```

### 2. Run initial discovery

```bash
# Test real device discovery (if tools installed)
node real-home-discovery.js

# This will find actual devices on your network:
# 📡 Scanning via arp-scan...
# 📡 Scanning via arp (system ARP table)...
# 🔍 Scanning via nmap (port detection)...
# Shows: IP, MAC, vendor, open ports
```

### 3. Generate initial HOME SOC baseline

```bash
# Run home network discovery to establish baseline
node home-network-discovery.js

# This creates:
# reports/home-soc-state/device-baseline.json (known devices)
# reports/home-soc-state/current-devices.json (today's snapshot)
# reports/home-soc-briefs/[date].html (today's brief)
```

### 4. Generate unified briefing

```bash
# Creates comprehensive brief showing:
# - Network score (0-100)
# - All devices online/offline
# - Camera status
# - Changes since yesterday
# - Top risks
node home-soc-brief.js
```

### 5. Schedule automated collection (14 days)

#### Option A: Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add these lines (adjust times/paths as needed):

# Daily at 8:00 PM - Run device discovery
0 20 * * * cd /path/to/mcp-cyber-tools && node real-home-discovery.js >> logs/discovery.log 2>&1

# Daily at 8:10 PM - Run HOME SOC brief  
10 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-brief.js >> logs/brief.log 2>&1

# Create logs directory first
mkdir -p /path/to/mcp-cyber-tools/logs
```

#### Option B: Windows Task Scheduler

```batch
# Create batch file: run-home-soc.bat
@echo off
cd C:\path\to\mcp-cyber-tools
node real-home-discovery.js
timeout /t 300 /nobreak
node home-soc-brief.js
```

Then schedule via Windows Task Scheduler:
- Task: Run home-soc.bat
- Trigger: Daily at 8:00 PM
- Repeat every 24 hours

#### Option C: Manual daily execution

```bash
# Run each morning/evening
node real-home-discovery.js
node home-soc-brief.js
```

---

## WHAT PHASE 1 TRACKS

### ✅ Device Inventory
- IP addresses
- MAC addresses
- Device vendors (from OUI database)
- Device types (router, camera, desktop, laptop, mobile, unknown)
- Online/offline status

### ✅ Change Detection
- **New devices** - Previously unseen IPs appear
- **Missing devices** - Known devices go offline
- **Port changes** - Open ports change on existing device
- **Vendor changes** - Firmware updates or spoofing detection

### ✅ Camera Monitoring
- Detects cameras by MAC/vendor (Hikvision, Axis, etc.)
- Checks if RTSP port (554) is open
- Checks if HTTP (80) is exposed
- Checks for HTTPS (443)
- Flags unencrypted access risks

### ✅ Router Monitoring
- Detects if web UI (port 80) is public
- Flags default credentials risk
- Monitors UPnP status
- Tracks open ports on router

### ✅ Network Scoring
- Score = 85 (baseline)
- -5 for new devices (unknown on network)
- -3 for offline devices (unexpected)
- -5 for port changes (unexpected services)
- -15 for CRITICAL risks
- -5 for HIGH risks
- Result: 0-100 score

### ✅ Daily Reports
- Comprehensive brief (all details)
- Executive brief (60-second read)
- Operations brief (30-second read)

---

## EXPECTED OUTPUT

### After first run:

```
reports/
├── home-soc-state/
│   ├── device-baseline.json          ← Known devices reference
│   ├── current-devices.json          ← Today's devices
│   ├── previous-devices.json         ← Yesterday's devices
│   ├── discovery-2026-08-24.json     ← Timestamped discovery
│   └── router-status.json            ← Router agent output
│
├── home-soc-briefs/
│   ├── 2026-08-24.html               ← Comprehensive brief
│   └── ...
│
├── home-soc-executive/
│   ├── 2026-08-24.html               ← 60-second executive brief
│   └── ...
│
└── home-soc-ops/
    ├── 2026-08-24.html               ← 30-second ops brief
    └── ...
```

### Sample brief output:

```
HOME SOC BRIEF - 2026-08-24

Network Score: 79/100 (YELLOW - Monitor)
├── Total Devices: 8
├── Online: 8/8
├── Cameras: 2
└── Risks: 5

CHANGES DETECTED
├── New Devices: 0
├── Offline Devices: 0
└── Port Changes: 0

TOP RISKS
1. RTSP Stream Exposed (Camera 1)
2. HTTP Access Enabled (Camera 2)
3. Default Credentials Check (Router)
4. UPnP Port Mapping Risk (Router)
5. Unknown Device Detected

CAMERAS STATUS
├── Camera 1: ONLINE, RTSP exposed
└── Camera 2: ONLINE, RTSP exposed
```

---

## 14-DAY EVALUATION CHECKLIST

### WEEK 1: Baseline Establishment

- [ ] Day 1: Deploy and run initial discovery
- [ ] Day 1: Verify all known devices detected
- [ ] Day 1: Confirm cameras detected and online
- [ ] Day 2-3: Check daily reports generate correctly
- [ ] Day 4-7: Verify scoring is stable (no major changes)

**Goal:** Establish what "normal" looks like on your network.

### WEEK 2: Change Detection Validation

- [ ] Intentionally bring device online (laptop, phone)
- [ ] Verify "New Device" is detected in report
- [ ] Disconnect a device
- [ ] Verify "Offline Device" is detected
- [ ] Check if score decreases appropriately
- [ ] Verify camera online/offline status tracked

**Goal:** Confirm change detection works in real scenarios.

### WEEK 3: Risk Assessment Evaluation

- [ ] Review camera risk findings (RTSP, HTTP exposure)
- [ ] Review router risk findings
- [ ] Check if risks are accurate for your setup
- [ ] Verify port detection is working
- [ ] Note any false positives/negatives

**Goal:** Validate risk assessment accuracy.

### WEEK 4: Final Review

- [ ] Collect 14 days of daily briefs
- [ ] Review trend (score stability, patterns)
- [ ] Count total change events
- [ ] Count total risks identified
- [ ] Decide: Valuable enough for Phase 2 router integration?

**Goal:** Determine if network monitoring provides actionable intelligence.

---

## PHASE 1 SUCCESS CRITERIA

### ✅ PASS if:
- Discovers all your home devices (≥80% accuracy)
- Detects when camera goes offline
- Detects when new device joins network
- Generates daily reports without errors
- Risk scores match your network configuration
- Runs for 14 days without issues

### ❌ FAIL if:
- Misses major devices (e.g., never sees cameras)
- Frequently false alarms (device marked offline when online)
- Risks are inaccurate or misleading
- Reports don't generate daily
- Significant crashes/errors

---

## TROUBLESHOOTING

### "No devices found"

**Check:**
```bash
# Verify network is active
ping 192.168.1.1

# Run ARP scan manually
arp -a

# Run nmap manually
nmap -sV 192.168.1.0/24

# Check network connectivity
ip route
```

### "Reports not generating"

**Check:**
```bash
# Verify Node.js works
node --version

# Run discovery manually
node home-network-discovery.js

# Check for errors in output
node home-soc-brief.js 2>&1 | tail -20
```

### "Missing devices in report"

**Check:**
- Device baseline may need updating
- Device may not be responding to ARP/nmap
- May need to adjust discovery subnet (default: 192.168.1.0/24)

---

## MANUAL TESTING STEPS

### Before scheduling, run these tests:

```bash
# 1. Test discovery with real tools
node real-home-discovery.js
cat reports/home-soc/router-status.json

# 2. Test baseline creation
node home-network-discovery.js
ls -la reports/home-soc-state/

# 3. Test unified brief generation
node home-soc-brief.js
ls -la home-soc-brief-*.html

# 4. Test executive brief
node home-soc-executive-brief.js
ls -la home-soc-executive-brief-*.html

# 5. Test ops brief
node home-soc-ops-brief.js
ls -la home-soc-ops-brief-*.html
```

All should complete without errors.

---

## PHASE 1 DEPLOYMENT STATUS

✅ Code: Ready
✅ Scripts: Tested and working
✅ Documentation: Complete
⏳ Deployment: Awaiting your execution on home network
⏳ Data Collection: 14 days needed

---

## NEXT: PHASE 2 DECISION POINT

After 14 days of Phase 1:

**If valuable (devices tracked, changes detected, risks identified):**
→ Proceed to Phase 2: XB7 Router API Integration
→ Use Windows Credential Manager for secure credential storage
→ Add deep router inventory (DHCP, DNS, port forwards)

**If not valuable (too many false positives, missed devices, no actionable data):**
→ Stop and reassess network architecture
→ Or adjust scoring/thresholds

**Decision made at: [Day 14 + 1]**

