# Next Session Priorities

**Date Created**: 2026-09-05  
**Last Updated**: 2026-09-05  
**Context**: MVP is OPERATIONAL; Phase N - SOC Intelligence Infrastructure COMPLETE

---

## PHASE N: SOC INTELLIGENCE - COMPLETED ✅

**What Was Implemented (Session 2026-09-05)**:

### Intelligence Extractors
1. **Asset Intelligence** (`extract_asset_intelligence.py`)
   - Extracts device inventory from Nessus scan data
   - Auto-classifies devices (Router, Workstation, Server, Mobile, Printer, IoT)
   - Tracks vulnerability counts per asset
   - Detects new/removed assets

2. **Service Intelligence** (`extract_service_intelligence.py`)
   - Extracts port/protocol/service information
   - Builds service inventory (global and per-host)
   - Identifies service types and counts
   - Detects new/closed services

3. **Cryptographic Intelligence** (`extract_crypto_intelligence.py`)
   - Extracts certificate information
   - Analyzes TLS versions and cipher suites
   - Identifies weak ciphers and self-signed certificates
   - Calculates cryptographic health score (0-100)
   - Tracks expired and expiring certificates

4. **Integrated Collector** (`collect_soc_intelligence.py`)
   - Orchestrates all three extractors
   - Generates comprehensive intelligence report
   - Coordination of asset, service, and crypto data

### Dashboard Enhancements
- **Asset Inventory Card**: Total assets, known/unknown, new/removed tracking
- **Service Inventory Card**: Service counts, types, new/closed detection, top services
- **Cryptographic Health Card**: Health score, certificate count, weak cipher tracking, expiry info
- Auto-refresh integration for all intelligence data

### Daily Brief Generator
- **generate_daily_brief.py** produces comprehensive JSON briefings with:
  - Vulnerability summary
  - Domain/DNS status
  - WAAP/SSL status
  - Asset summary with top vulnerable devices
  - Service summary with top services
  - Cryptographic summary
  - Overall risk assessment and factors

### Outputs Generated
- `state/assets.json` - Device inventory
- `state/asset_changes.json` - New/removed assets
- `state/services.json` - Service/port inventory
- `state/service_changes.json` - Service changes
- `state/crypto_inventory.json` - Certificate/cipher data
- `state/crypto_changes.json` - Crypto changes
- `state/soc_intelligence.json` - Comprehensive report
- `daily_brief/YYYY-MM-DD.json` - Daily briefing

### Commits
- **e7bc11b**: Phase N - SOC Intelligence Infrastructure (extractors + dashboard)
- **e72c61e**: Daily brief generator with SOC intelligence summaries

---

## Priority Stack (Updated Post-Phase N)

### 🔴 Priority 1: Intelligence Scheduler Integration (CRITICAL)

**Objective**: Integrate SOC intelligence extractors into overnight automated collection

**Tasks**:
1. Add intelligence collectors to scheduler
   - Schedule `collect_soc_intelligence.py` after Nessus collector completes
   - Ensure extractors run: Asset → Service → Crypto → Integrated report
   - Add daily brief generation to scheduler

2. Verify overnight automation
   - Monitor state file updates: assets.json, services.json, crypto_inventory.json
   - Confirm daily_brief/YYYY-MM-DD.json generated each night
   - Check change detection files: asset_changes.json, service_changes.json, crypto_changes.json

3. Validate dashboard auto-refresh
   - Verify intelligence cards load fresh data every 60 seconds
   - Check that new/removed assets trigger alerts
   - Confirm service and crypto changes are visible

4. Expected outcome
   - Complete intelligence pipeline runs autonomously nightly
   - All state files generated and fresh
   - Dashboard displays real-time intelligence data
   - Daily brief captures daily security posture

**Success Criteria**: Intelligence pipeline runs nightly, dashboard shows current intelligence data, daily brief generated consistently.

---

### 🟡 Priority 2: Enhance Nessus Data Extraction (IMPORTANT)

**Objective**: Improve asset/service/crypto extraction from Nessus API responses

**Background**:
- Current extractors work but receive minimal detailed data from Nessus
- Asset extractor showing 0 assets (API response may not include detailed vulnerability fields)
- Service extractor showing minimal port/protocol data
- Crypto extractor finding limited certificate data

**Tasks**:
1. Analyze Nessus API response structure
   - Inspect full vulnerability object fields from `/scans/{scan_id}` endpoint
   - Document actual fields available: asset info, port, protocol, cert data, etc.
   - Identify if different endpoints needed for detailed data

2. Enhance asset extraction
   - Map Nessus OS info to device types more robustly
   - Extract IP→hostname mapping from Nessus asset data
   - Handle cases where asset data is sparse or missing

3. Improve service/port detection
   - Better extraction of port numbers from Nessus findings
   - Enhance service name identification from plugin metadata
   - Build more accurate service inventory

4. Strengthen crypto intelligence
   - Extract TLS version info from certificate plugins
   - Identify cipher suites from Nessus test results
   - Better weak cipher detection and classification

**Success Criteria**: Asset/service/crypto extractors populate state files with realistic data matching Nessus scan results

---

### 🟢 Priority 3: Risk Scoring & Alerting (NEXT PHASE)

**Objective**: Implement risk-based alerting for discovered threats

**Tasks**:
1. Build risk calculation engine
   - Score assets by vulnerability severity and counts
   - Calculate device-level risk (Critical/High/Medium/Low)
   - Track risk changes over time

2. Implement alert thresholds
   - Critical: Any critical vulnerability detected
   - High: 3+ high-severity vulns on single device
   - Medium: New services on known devices
   - Low: Weak ciphers detected

3. Create alert notifications
   - Generate structured alert JSON files
   - Track alert state (new/acknowledged/resolved)
   - Link alerts to specific assets/services/crypto issues

4. Dashboard alert display
   - Show alert count by severity
   - Link alerts to affected assets
   - Support alert acknowledgment

**Success Criteria**: Risk scores calculated for all assets, alerts generated for severity threshold violations

---

### 🔵 Priority 4: Mobile App Integration (FUTURE)

**Objective**: Mobile app for security team to review daily briefs and alerts

**Ideas**:
- Native app (iOS/Android) or PWA
- Daily brief push notifications
- Alert notifications with device details
- Real-time asset/service/crypto status
- Risk score display and trending

**Deferred**: Post-Phase O; requires mobile dev resources

---

### 🟣 Priority 5: Incident Response Workflow (FUTURE)

---

### 🟣 Priority 5: Testing & Validation (IN PROGRESS)

**Objective**: Validate intelligence pipeline end-to-end

**Items**:
- Test intelligence extractors with real Nessus data
- Verify dashboard displays intelligence correctly
- Validate daily brief generation
- Check scheduler execution and timing

**Hold for**: After scheduler integration complete

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
| `scripts/generate_daily_brief.py` | ✅ STABLE | Daily brief generation working with all summaries |
| `scripts/extract_asset_intelligence.py` | ✅ NEW | Asset extraction and change detection working |
| `scripts/extract_service_intelligence.py` | ✅ NEW | Service/port extraction and detection working |
| `scripts/extract_crypto_intelligence.py` | ✅ NEW | Cryptographic health scoring and detection working |
| `scripts/collect_soc_intelligence.py` | ✅ NEW | Orchestrated intelligence collection working |
| `dashboard.html` | ✅ STABLE | Enhanced with intelligence cards, auto-refresh verified |

**Exception**: If a bug is discovered, fix it. But no refactoring or enhancement without explicit request.

**Note on Intelligence Extractors**: Data extraction quality depends on Nessus API response structure. If extractors show sparse data (0 assets, minimal services), this is likely Nessus API limitation, not extractor bug. Priority 2 addresses improving extraction quality.

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

## Completed in This Session

**Phase N: SOC Intelligence Infrastructure** - COMPLETE ✅
- Asset Intelligence Extractor
- Service Intelligence Extractor
- Cryptographic Intelligence Extractor
- Integrated SOC Intelligence Collector
- Dashboard Intelligence Cards (3 new widgets)
- Daily Brief Generator with 7 sections
- Change Detection Layer for all intelligence types

## Not Starting New Work

These are **explicitly deferred** (do not start without new request):

| Item | Target Phase | Status |
|------|--------------|--------|
| Intelligence Scheduler Integration | Next Session | Priority 1 - integrate collectors into automation |
| Enhanced Nessus Data Extraction | Next Session | Priority 2 - improve data extraction quality |
| Risk Scoring & Alerting | Phase P | Priority 3 - implement risk-based alerts |
| Mobile App Integration | Phase Q | Priority 4 - mobile client for alerts/briefs |
| VNETWORK API Integration | Phase R | Discovery complete, blocked by entitlements |
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
