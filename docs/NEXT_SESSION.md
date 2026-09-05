# Next Session Priorities

**Date Created**: 2026-09-05  
**Context**: MVP is OPERATIONAL, ready for validation and operational hardening

---

## Priority Stack

### 🔴 Priority 1: Overnight Scheduler Validation (CRITICAL)

**Objective**: Verify that automated collectors run on schedule without manual intervention

**Tasks**:
1. Check cron jobs / Task Scheduler configuration
   - Verify Nessus collector scheduled
   - Verify Domain collector scheduled
   - Verify WAAP collector scheduled
   - Verify health score calculation scheduled
   - Verify daily brief generation scheduled

2. Monitor one full overnight cycle
   - Check state files update with fresh timestamps
   - Verify timestamps are close (within 5 minutes) of expected schedule
   - Verify no error files or exceptions logged

3. Validate daily brief generation
   - Confirm `daily_brief/YYYY-MM-DD.json` created with latest date
   - Verify content is populated (findings, recommendations)

4. Expected outcome
   - All collectors run autonomously
   - State files refresh on schedule
   - No manual intervention required
   - MVP validated as production-ready

**Success Criteria**: All 4 collectors + health score + daily brief all run within 15-minute window, zero manual intervention required.

---

### 🟡 Priority 2: Asset Intelligence - Build `state/assets.json`

**Objective**: Create device/asset inventory from Nessus scan results

**Background**:
- Nessus scan discovers 11 hosts
- Hosts have IP addresses but no device names
- Example Nessus data: `{"ip": "192.168.0.51", "os": "Windows 11", ...}`

**Tasks**:
1. Extract unique IPs from `state/nessus_status.json`
   - Field: `findings[*].asset.ip`
   - Expected: ~11 unique IPs

2. Create baseline `state/assets.json` structure
   ```json
   {
     "timestamp": "2026-09-05T15:05:54Z",
     "assets": [
       {
         "ip": "192.168.0.51",
         "hostname": "Kevin-PC",
         "device_type": "Desktop",
         "os": "Windows 11",
         "first_seen": "2026-09-05",
         "last_seen": "2026-09-05",
         "vulnerability_count": 3,
         "highest_severity": "medium"
       },
       ...
     ]
   }
   ```

3. Populate manually from known devices
   - 192.168.0.1 → Router (Network device)
   - 192.168.0.51 → Kevin-PC (Desktop)
   - 192.168.0.21 → TBD (Query user or leave blank)

4. Link to Nessus findings
   - Count vulnerabilities per IP
   - Highest severity per IP
   - Update `last_seen` on each scan

**Expected output**: `state/assets.json` with 11-15 entries, device names populated for known devices

---

### 🟢 Priority 3: Asset Intelligence - IP-to-Device Name Mapping

**Objective**: Automatically resolve IP → hostname for better visibility

**Tasks**:
1. Create `scripts/map_assets.py` (new)
   - Input: Nessus IPs from `state/nessus_status.json`
   - Output: `state/assets.json` (merge with manual mappings)

2. Mapping strategies (in order):
   - **DNS reverse lookup**: `reverse_dns(ip)` → hostname
   - **DHCP lease inspection**: Check local DHCP server for IP/hostname bindings
   - **Nessus hostname field**: Some Nessus findings include hostname
   - **Manual mapping**: `assets_manual.json` (user-maintained fallback)

3. Run as part of nightly schedule
   - Hook into `calculate_waap_score.py` flow
   - Run after Nessus collector completes
   - Output: Updated `state/assets.json`

4. Handle edge cases
   - Unknown IPs → Leave hostname blank, flag as "TBD"
   - Offline hosts → Keep last-known hostname
   - Conflicts → Prefer DNS over Nessus, prefer manual over DNS

**Expected outcome**: 90%+ of IPs mapped to hostnames

---

### 🔵 Priority 4: Dashboard Enhancement - Top Vulnerable Devices Widget

**Objective**: Add "Top Vulnerable Devices" section to live dashboard

**Requirements**:
- Pure HTML/CSS/JavaScript (no framework changes)
- Data source: `state/assets.json` + `state/nessus_status.json`
- Sort by: severity (critical/high first), then vulnerability count
- Display top 5 devices
- Format:
  ```
  Device Name          Severity   Findings   Status
  ────────────────────────────────────────────────
  Kevin-PC             Medium     3          ⚠️
  Unknown (192.0.21)   Low        1          ℹ️
  Router               Info       58         ℹ️
  ```

**Implementation**:
1. Read `state/assets.json` and Nessus status
2. Create sortable device list (severity desc, count desc)
3. Render as new section in dashboard
4. Update auto-refresh to include asset data
5. Test on mobile (ensure responsive)

**Expected outcome**: Dashboard shows "Top 5 Most Vulnerable Devices" ranked by risk

---

### 🟣 Priority 5: Dashboard Enhancement - Recommendations by Device

**Objective**: Link recommendations to specific devices (optional, lower priority)

**Ideas**:
- Show "Patch Windows 11" on Kevin-PC specifically
- Show "Update firmware" on Router
- Filter recommendations by device

**Hold for**: After Priority 4 completes

---

## Do NOT Rebuild

These components are **OPERATIONAL and STABLE**. Do not refactor, enhance, or modify:

| Component | Status | Reason |
|-----------|--------|--------|
| `scripts/collect_nessus_snapshot.py` | ✅ STABLE | Working correctly, severity mapping verified |
| `scripts/collect_domain_snapshot.py` | ✅ STABLE | SPF/DMARC/DNS detection working, parsing fixed |
| `scripts/collect_waap_snapshot.py` | ✅ STABLE | SSL/TLS cert fetch working, expiry calculation verified |
| `scripts/calculate_waap_score.py` | ✅ STABLE | Health score algorithm proven, weighting correct |
| `scripts/event_hub.py` | ✅ STABLE | Change tracking working, dedup logic verified |
| `scripts/generate_daily_brief.py` | ✅ STABLE | Brief generation working, event schema stable |
| `dashboard.html` | ✅ STABLE | Live data binding working, mobile tested |

**Exception**: If a bug is discovered, fix it. But no refactoring or enhancement without explicit request.

---

## Context Preservation

### Key Files to Read If Context Lost
- `docs/SENTINELOPS_MVP_STATUS.md` — Current status & validation results
- `docs/RECOVERY_GUIDE.md` — Step-by-step recovery procedures
- `docs/PHASE_V_VNETWORK_DISCOVERY.md` — Phase 2 integration roadmap

### Key Branches
- **Main work branch**: `learning-factory-v2`
- **Main branch**: `develop`
- **Latest stable commit**: See git log

### State Files (Real-time Data)
- `state/nessus_status.json` — Vulnerability findings
- `state/domain_status.json` — DNS/domain configuration
- `state/waap_status.json` — SSL/TLS certificate data
- `state/waap_score.json` — Health score + recommendations
- `state/assets.json` — Device inventory (to be created)

---

## Not Starting New Work

These are **explicitly deferred** (do not start without new request):

| Item | Target Phase | Status |
|------|--------------|--------|
| VNETWORK API Integration | Phase 2 | Discovery complete, blocked by entitlements |
| Incident Posting to GitHub | Phase 2 | Pattern proven in MVP #3/#4, integration deferred |
| Asset Compliance Scoring | Phase 3+ | Complex, requires more baseline data |
| Predictive Risk Modeling | Phase 3+ | Requires 30 days of baseline collection |
| React Dashboard UI | Never | Explicitly excluded (Phase 1 constraint) |

---

## Session Checklist

When continuing next session:
- [ ] Read `docs/SENTINELOPS_MVP_STATUS.md`
- [ ] Read `docs/RECOVERY_GUIDE.md` (just in case)
- [ ] Review this file (`docs/NEXT_SESSION.md`)
- [ ] Verify collectors still running: `ls -la state/` (check timestamps)
- [ ] Check dashboard is live: Open `dashboard.html` in browser
- [ ] Start work on Priority 1 (scheduler validation)

---

## Session End State

**When this session ends**:
1. One or more priorities completed (Priority 1 is critical)
2. All new code committed to `learning-factory-v2`
3. No uncommitted changes
4. Dashboard still operational
5. State files fresh and valid

**Next session starts**: Review what was done, pick next priority from this list

---

**Last Updated**: 2026-09-05  
**Prepared By**: Claude Code  
**Status**: Ready for continuation
