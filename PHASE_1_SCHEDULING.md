# PHASE 1 HARDENED SCHEDULING
## Lightweight Continuous Monitoring

**Architecture:**
```
Desktop Runtime (When machine is on)
  ↓
Every 30 minutes → network-collector.js
  - ARP table snapshot
  - Camera presence check
  - Change detection
  - Store in device-history.json
  ↓
Accumulated Evidence (30+ data points/day)
  ↓
8:00 PM → home-soc-brief.js
  - Generates reports FROM accumulated evidence
  - NO expensive nmap scans
  - NO full discovery runs
  - Fast analysis of collected data
```

---

## SCHEDULING

### Option A: Cron (Linux/macOS) - Recommended

```bash
# Edit crontab
crontab -e

# Add these lines:

# Lightweight collection every 30 minutes (when desktop is on)
*/30 * * * * cd /path/to/mcp-cyber-tools && node network-collector.js >> logs/collector.log 2>&1

# Generate reports once daily at 8 PM
0 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-brief.js >> logs/brief.log 2>&1

# Generate executive brief at 8:05 PM
5 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-executive-brief.js >> logs/executive.log 2>&1

# Generate ops brief at 8:10 PM
10 20 * * * cd /path/to/mcp-cyber-tools && node home-soc-ops-brief.js >> logs/ops.log 2>&1

# Create logs directory first
mkdir -p /path/to/mcp-cyber-tools/logs
```

### Option B: Windows Task Scheduler

**Task 1: Network Collector (every 30 min)**
- Action: `node network-collector.js`
- Working directory: `C:\path\to\mcp-cyber-tools`
- Trigger: Every 30 minutes
- Condition: Only if user is logged in

**Task 2: Reports Generation (8 PM)**
- Action: `node home-soc-brief.js && node home-soc-executive-brief.js && node home-soc-ops-brief.js`
- Working directory: `C:\path\to\mcp-cyber-tools`
- Trigger: Daily at 8:00 PM

### Option C: Docker Container (Background Service)

```dockerfile
FROM node:22-alpine

WORKDIR /app
COPY . .

# Install dependencies
RUN npm install || true

# Collector runs in foreground, reports via cron inside container
CMD ["sh", "-c", "while true; do node network-collector.js; sleep 1800; done"]
```

---

## DATA FLOW

### Continuous Collection (Every 30 Minutes)

```bash
network-collector.js runs:
  1. arp -a (2-5 seconds)
  2. ping camera IPs (3-5 seconds)
  3. Compare to previous state
  4. Detect changes
  5. Store in JSON files
  6. Total: ~10 seconds
```

**Output files updated:**
- `device-history.json` — Current devices + camera status
- `changes.json` — Change log (new/offline devices)
- `network-history.json` — Historical snapshots

### Report Generation (Once at 8 PM)

```bash
home-soc-brief.js reads from:
  1. device-history.json (just read, no scan)
  2. changes.json (accumulated evidence)
  3. network-history.json (trends)
  4. Generates report in ~1 second
  5. No expensive scans
```

---

## EVIDENCE ACCUMULATION

### Per Day (if desktop on 24/7):

- **48 collections** (every 30 min)
- **48 ARP snapshots** (current network state)
- **48 camera ping checks** (online/offline)
- **Change events** (new devices, offline devices)

### Over 14 Days:

- **~672 ARP snapshots** (good coverage of network changes)
- **~672 camera checks** (camera reliability data)
- **Change log** (exactly what happened)
- **Network history** (trends and averages)

### Report Quality:

Based on 48+ data points per day, reports show:
- Accurate device count (multiple confirmations)
- Reliable camera status (48 checks/day)
- Real change detection (not one-time snapshot)
- Network trends (average devices, patterns)

---

## MONITORING COLLECTION PERFORMANCE

### Check collector output:

```bash
# View latest collection
tail -20 logs/collector.log

# Expected output:
# 📡 Network Collector - Lightweight Collection
# 📋 Reading ARP table...
#    Found: 8 devices
#    Previous: 8 devices
# 📹 Checking camera presence...
#    Online: 2/3
# ✅ Collection complete
```

### Monitor history file size:

```bash
# Should grow slowly over time
watch -n 300 'du -h reports/home-soc-state/*.json'

# device-history.json: ~1-2 KB (current state)
# changes.json: ~2-5 KB (change log, kept at 1000 entries)
# network-history.json: ~5-10 KB (snapshots, kept at 1000 entries)
```

### Verify reports are using history:

```bash
# Check brief was fast (no scan)
tail logs/brief.log

# Should show:
# Generating Home SOC Brief from accumulated evidence...
#   (using device history from collector)
# ✓ Home SOC Brief generated (fast, <2 seconds)
```

---

## FIRST RUN BEHAVIOR

**First time you run the system:**

1. Run manual discovery once (establishes baseline):
   ```bash
   node home-network-discovery.js
   ```

2. Start collector:
   ```bash
   node network-collector.js
   ```

3. At 8 PM, reports will use collected evidence

**After first week:**
- History is established
- Reports use accumulated data
- No full discovery needed (unless manual reset)

---

## LIGHTWEIGHT CHARACTERISTICS

### Collection performance:
- ✅ **Fast:** 10 seconds per collection
- ✅ **Lightweight:** No nmap, no port scanning
- ✅ **Frequent:** Can run every 30 minutes
- ✅ **Low CPU:** Simple ARP + ping
- ✅ **Low Network:** Minimal traffic

### Report generation:
- ✅ **Fast:** <2 seconds (reads history, doesn't scan)
- ✅ **Accurate:** Based on 48+ data points
- ✅ **No scanning:** All data pre-collected
- ✅ **Stable:** Same method every day

### Storage:
- ✅ **Compact:** ~10 KB total history
- ✅ **Retained:** Last 1000 entries per file
- ✅ **Clean:** Old entries auto-purged

---

## TROUBLESHOOTING

### Collection not running

```bash
# Test collector manually
node network-collector.js

# Check it creates history files
ls -la reports/home-soc-state/device-history.json
```

### Reports still doing scans

This means device-history.json doesn't exist yet.

```bash
# First run collector to create history
node network-collector.js

# Then reports will use it
node home-soc-brief.js
```

### History file getting too large

The system auto-limits to last 1000 entries:
- device-history.json: Current state (always small)
- changes.json: Limited to 1000 changes
- network-history.json: Limited to 1000 snapshots

### Camera pings not working

Some networks block ping. Edit network-collector.js to check SSH/HTTP instead:

```javascript
// Replace ping with SSH check to camera
execSync(`ssh admin@${ip} 'echo'`, { stdio: 'ignore' })
// Or HTTP
execSync(`curl -s http://${ip}/status`, { stdio: 'ignore' })
```

---

## PERFORMANCE IMPACT

### Desktop machine impact:

**Collector (every 30 min):**
- CPU: <1% for 10 seconds
- Memory: <10 MB
- Network: ~100 bytes (ARP traffic)
- Disk: 1 KB per run

**Reports (once at 8 PM):**
- CPU: <1% for 1 second
- Memory: <20 MB
- Network: None
- Disk: <100 KB

**Total daily impact:** Minimal

---

## PHASE 1 HARDENING SUMMARY

| Aspect | Before | After |
|--------|--------|-------|
| Report generation | Full nmap scan | Read from history |
| Report time | 30-60 seconds | 1-2 seconds |
| Collection frequency | Once daily | Every 30 min |
| Data points per day | 1-2 | 48+ |
| Evidence quality | Single snapshot | 48 confirmations |
| CPU usage | High during scan | Low, distributed |
| Network impact | High (nmap traffic) | Low (ARP + ping) |

---

## NEXT STEPS

1. **Install collector:**
   ```bash
   cp network-collector.js /your/path/
   ```

2. **Schedule collection:**
   - Every 30 minutes (or hourly)

3. **Schedule reports:**
   - Once daily at 8 PM

4. **Monitor:**
   - Check logs/collector.log daily
   - Verify reports use history (not scans)

5. **After 14 days:**
   - Evaluate if Phase 1 adds value
   - Decide on Phase 2 (router integration)

