# SentinelOps Recovery Guide

**Purpose**: If project context is lost or unclear, follow these steps to restore operational visibility  
**Time to Recovery**: ~10 minutes  
**Success Criteria**: Dashboard loads with live data from all 4 collectors

---

## Step 1: Restore Context (2 minutes)

### Read Core Documentation
1. Open `docs/SENTINELOPS_MVP_STATUS.md`
   - Current operational status
   - Component inventory
   - Validation results

2. Open `docs/NEXT_SESSION.md`
   - Current priorities
   - Known limitations
   - Stable components (do not modify)

3. Review `.env` and `.env.example`
   - Confirm credentials are configured
   - Verify required API keys present
   - Check no credentials committed to git

### Git Status Check
```bash
git status
git log --oneline -10
```

Should show:
- Branch: `learning-factory-v2` or `develop`
- Recent commits: Collectors working, dashboard implemented
- No uncommitted changes (or only state/daily_brief changes, which are expected)

---

## Step 2: Verify Collectors (5 minutes)

### Run Nessus Collector
```bash
python scripts/collect_nessus_snapshot.py
```

**Expected output**:
```json
{
  "timestamp": "2026-09-05T...",
  "scanner_status": "running",
  "hosts": 11,
  "findings": [
    {
      "severity": 2,  // medium
      "description": "...",
      "asset": {"ip": "192.168.0.51"}
    },
    ...
  ]
}
```

**File created**: `state/nessus_status.json`

### Run Domain Collector
```bash
python scripts/collect_domain_snapshot.py
```

**Expected output**:
```json
{
  "timestamp": "2026-09-05T...",
  "domain": "sentinelops.fyi",
  "spf": "v=spf1 include:_spf.porkbun.com ~all",
  "dmarc": "CNAME pixie.porkbun.com.",
  "nameservers": ["curitiba.ns.porkbun.com.", ...],
  "dns_complete": {
    "has_spf": true,
    "has_dmarc": true,
    "has_nameservers": true,
    "has_a_records": true,
    "has_mx_records": true
  }
}
```

**File created**: `state/domain_status.json`

### Run WAAP Collector
```bash
python scripts/collect_waap_snapshot.py
```

**Expected output**:
```json
{
  "timestamp": "2026-09-05T...",
  "domain": "audit.sentinelops.fyi",
  "ssl_status": "valid",
  "ssl_expiry_date": "2026-11-22",
  "days_until_expiry": 87,
  "certificate_issuer": "Let's Encrypt"
}
```

**File created**: `state/waap_status.json`

### Run Health Score Calculator
```bash
python scripts/calculate_waap_score.py
```

**Expected output**:
```json
{
  "timestamp": "2026-09-05T...",
  "health_score": 80,
  "grade": "B",
  "recommendations": [
    {
      "category": "Security Headers",
      "action": "Add HSTS header",
      "impact": "Prevents SSL stripping attacks"
    },
    ...
  ]
}
```

**File created**: `state/waap_score.json`

### Verify State Files Exist
```bash
ls -la state/
```

Should show:
- `nessus_status.json` (recent timestamp)
- `domain_status.json` (recent timestamp)
- `waap_status.json` (recent timestamp)
- `waap_score.json` (recent timestamp)
- Timestamps should be within last 5 minutes

**If any file is missing or old**: Run the corresponding collector again

---

## Step 3: Start Dashboard Server (1 minute)

### Option A: Python HTTP Server (Recommended)
```bash
python -m http.server 8080
```

Output:
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

### Option B: Alternative Server
```bash
# Node.js (if available)
npx http-server -p 8080

# Or use system Python directly
cd C:\Users\tamng\Projects\mcp-cyber-tools
python -m http.server 8080
```

**Leave the server running** in this terminal window

---

## Step 4: Verify Dashboard (2 minutes)

### Open Dashboard in Browser

**Local access**:
```
http://localhost:8080/dashboard.html
```

**Mobile/Remote access**:
```
http://192.168.0.51:8080/dashboard.html
```
(Replace 192.168.0.51 with your machine's IP)

### Check Dashboard Display

Should display:

1. **Nessus Card**
   - Hosts: 11
   - Critical: 0
   - High: 0
   - Medium: 3
   - Low: 2
   - Info: 58

2. **Domain Card**
   - SPF: ✅ Present
   - DMARC: ✅ Present
   - Nameservers: 4 entries
   - A Records: 2 entries
   - MX Records: 2 entries

3. **WAAP Card**
   - SSL Status: Valid
   - Days Until Expiry: 87
   - Health Score: 80/100
   - Grade: B
   - Health Status: Healthy

4. **Recommendations Section**
   - Lists action items
   - Sorted by impact
   - Each includes rationale

5. **Refresh Indicator**
   - Shows last update time
   - Auto-refreshes every 60 seconds
   - Shows "Loading data..." briefly during refresh

### Test Auto-Refresh
- Wait 60 seconds
- Verify "Last Updated" time changes
- Verify data is still current

### Test Mobile/Responsive
- Resize browser to mobile width (~375px)
- Verify layout stacks vertically
- Verify all cards still readable
- Verify no horizontal scrolling

---

## Step 5: Verify Overnight Scheduler (Optional)

### Check If Scheduler Is Configured
```bash
# Windows Task Scheduler
tasklist | findstr sentinelops
# or
Get-ScheduledTask | Select-String sentinelops

# Linux/Mac cron
crontab -l
```

**Expected**: Cron jobs or scheduled tasks for collectors + calculator

### If Scheduler Is Not Running
1. Review `docs/NEXT_SESSION.md` Priority 1
2. Set up automated collection (see "Set Up Scheduler" section below)
3. This is important for MVP validation

---

## Step 6: Troubleshooting

### Dashboard Shows "Loading data..." But Doesn't Update
1. Check browser console for errors: F12 → Console tab
2. Verify state files exist: `ls -la state/`
3. Verify file timestamps are recent (within 5 min)
4. Check HTTP server is running (terminal shows requests)
5. Try hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Collectors Return Errors
1. **"Missing dependencies"**: Install required packages
   ```bash
   pip install dnspython requests python-dotenv
   ```

2. **"401 Unauthorized"** (Nessus): Check credentials in `.env`
   ```bash
   cat .env | grep NESSUS
   # Verify NESSUS_ACCESS_KEY and NESSUS_SECRET_KEY are set
   ```

3. **"403 Access Denied"** (Porkbun): Optional credential, can be skipped
   ```bash
   # Domain collector works without Porkbun API (uses DNS only)
   # Expiration date will be null
   ```

4. **"Connection refused"** (WAAP): Check network connectivity
   ```bash
   ping audit.sentinelops.fyi
   # If fails, check DNS settings or VPN
   ```

### State Files Are Empty or Null
1. Run collector with verbose output:
   ```bash
   python scripts/collect_nessus_snapshot.py 2>&1 | head -50
   ```
2. Check for errors in output
3. Verify API credentials are correct
4. Verify network access (ping, nslookup)

---

## Set Up Scheduler (If Not Configured)

### Option A: Windows Task Scheduler

**Create task for each collector**:

1. Open Task Scheduler
2. Create Basic Task → Name: "SentinelOps Nessus Collector"
3. Trigger: Daily at 23:00 (11 PM)
4. Action: `python.exe`
   - Path: `C:\Users\tamng\Projects\mcp-cyber-tools\scripts\collect_nessus_snapshot.py`
5. Repeat for other collectors + calculator

### Option B: Windows PowerShell (Easier)

```powershell
# Create a scheduled task
$trigger = New-ScheduledTaskTrigger -Daily -At 23:00
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Users\tamng\Projects\mcp-cyber-tools\scripts\collect_nessus_snapshot.py" -WorkingDirectory "C:\Users\tamng\Projects\mcp-cyber-tools"
Register-ScheduledTask -TaskName "SentinelOps-Nessus" -Trigger $trigger -Action $action -Description "Nessus vulnerability collector"
```

### Option C: Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add lines (runs at 23:00 daily):
0 23 * * * cd /path/to/mcp-cyber-tools && python scripts/collect_nessus_snapshot.py
0 23 * * * cd /path/to/mcp-cyber-tools && python scripts/collect_domain_snapshot.py
0 23 * * * cd /path/to/mcp-cyber-tools && python scripts/collect_waap_snapshot.py
5 23 * * * cd /path/to/mcp-cyber-tools && python scripts/calculate_waap_score.py
```

**Verify cron is running**:
```bash
crontab -l  # List jobs
sudo journalctl -u cron | tail  # Check logs
```

---

## Post-Recovery Checklist

- [ ] Read `docs/SENTINELOPS_MVP_STATUS.md`
- [ ] Read `docs/NEXT_SESSION.md`
- [ ] Ran all 4 collectors successfully
- [ ] State files are fresh (timestamps < 5 min old)
- [ ] Dashboard loads without errors
- [ ] All data cards display correctly
- [ ] Auto-refresh works (60s cycle)
- [ ] Mobile/responsive layout verified
- [ ] Server process running (terminal shows requests)
- [ ] (Optional) Scheduler configured for nightly runs

**If all boxes checked**: System is OPERATIONAL ✅

---

## Emergency Recovery

### Complete Wipe & Restore (Worst Case)

If something is broken and you need to start fresh:

1. **Backup current state** (just in case)
   ```bash
   cp -r state/ state.backup/
   cp -r daily_brief/ daily_brief.backup/
   ```

2. **Clear state files**
   ```bash
   rm -f state/*.json
   rm -rf daily_brief/
   ```

3. **Re-run collectors** (Step 2 above)
   ```bash
   python scripts/collect_nessus_snapshot.py
   python scripts/collect_domain_snapshot.py
   python scripts/collect_waap_snapshot.py
   python scripts/calculate_waap_score.py
   ```

4. **Start dashboard** (Step 3 above)
   ```bash
   python -m http.server 8080
   ```

5. **Verify** (Step 4 above)
   - Open `http://localhost:8080/dashboard.html`

**Expected time**: ~2 minutes from zero to operational

---

## Contact & Documentation

### Key Contacts
- **Owner**: Cyber Tools Team (tamngankevin@gmail.com)
- **Repository**: C:\Users\tamng\Projects\mcp-cyber-tools

### Reference Documents
- `docs/SENTINELOPS_MVP_STATUS.md` — Status & validation
- `docs/NEXT_SESSION.md` — Next priorities
- `docs/PHASE_V_VNETWORK_DISCOVERY.md` — Phase 2 roadmap
- `README.md` — Original project overview

### Key Scripts
- `scripts/collect_nessus_snapshot.py` — Fetch vulnerabilities
- `scripts/collect_domain_snapshot.py` — Fetch DNS/domain status
- `scripts/collect_waap_snapshot.py` — Fetch SSL/TLS status
- `scripts/calculate_waap_score.py` — Calculate health score
- `dashboard.html` — Live web dashboard

---

## Version History

| Date | Status | Notes |
|------|--------|-------|
| 2026-09-05 | CREATED | Initial recovery guide for MVP handoff |

---

**Last Updated**: 2026-09-05  
**Verified**: All steps tested and confirmed working  
**Ready For**: Production use & next session continuation
