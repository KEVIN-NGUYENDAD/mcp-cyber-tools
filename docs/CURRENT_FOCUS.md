# CURRENT FOCUS - PHASE G: Nessus Integration

## 📌 Objective
Integrate Nessus vulnerability scanner into SentinelOps baseline tracking and change detection.

## 🎯 What to Collect (from Nessus API)

```json
{
  "timestamp": "2026-09-05T16:00:00Z",
  "scanner_status": "ready|running|error",
  "last_scan": "2026-09-05T12:30:00Z",
  "scan_age_hours": 3.5,
  "critical": 0,
  "high": 2,
  "medium": 5,
  "low": 12,
  "info": 45
}
```

## 📝 Implementation Plan

### Step 1: Create Nessus Collector Script
**File**: `scripts/collect_nessus_snapshot.py`

Requirements:
- Read Nessus API credentials from config
- Query scanner status
- Get latest scan results
- Save to `state/nessus_status.json`
- Output JSON only (no logging to console)

### Step 2: Integrate with Baseline Store
- Add `nessus` section to baseline.json
- Track: critical count, high count, scan age

### Step 3: Change Detection
- Compare current nessus state vs baseline
- Detect: New critical/high vulns, Stale scans

### Step 4: Recommendation Engine
- IF critical > 0 → HIGH severity recommendation
- IF high > 5 → MEDIUM severity recommendation
- IF scan_age_hours > 24 → INFO recommendation

### Step 5: Daily Brief Integration
- Add nessus section to daily_brief/*.json
- Show latest scan status + recommendations

## 🔧 Tech Stack
- Python 3.8+ (requests library)
- Nessus REST API v2
- JSON for data exchange

## ✅ Validation Checklist
- [ ] Script creates valid JSON output
- [ ] Handles missing API key gracefully
- [ ] Integrates with state/*.json
- [ ] Change detector identifies vulnerabilities
- [ ] Recommendations generated correctly
- [ ] Daily brief includes Nessus data

## 🚫 Constraints
- NO new architecture
- NO hardcoded data
- NO duplicate logic from existing collectors
- Use real Nessus API only
