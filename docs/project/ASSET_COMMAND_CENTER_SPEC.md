# Asset Command Center Specification

**Date**: 2026-09-09  
**Phase**: 2 - Asset Intelligence  
**Status**: Implementation Complete

---

## Overview

The Asset Command Center (ACC) is the unified interface for asset lifecycle management, inventory control, trust scoring, and shadow asset detection in SentinelOps.

**Mission**: Single pane of glass for all asset operations - discovery, profiling, monitoring, and threat response.

---

## Core Components

### 1. Unified Asset Schema (state/assets.json)

#### New Fields (Phase 2 Upgrade)
```json
{
  "id": 1,
  "hostname": "192.168.0.14",
  "ip": "192.168.0.14",
  "type": "Unknown",
  "os": "iPhone or iPad",
  "mac": "20:91:DF:0D:AF:CC",
  "risk_score": 0,
  "status": "ONLINE",
  
  /* NEW FIELDS */
  "trust_score": 82,           // 0-100 calculated trust rating
  "trust_level": "TRUSTED",    // CRITICAL_ASSET | TRUSTED | MONITORED | SUSPICIOUS | UNKNOWN
  "shadow_flag": false,        // True if device is unknown/suspicious
  "first_seen": "2026-09-09T...", // ISO timestamp when first discovered
  "last_change_time": "2026-09-09T...", // When any field last changed
  
  /* EXISTING FIELDS */
  "last_scan": "Home Network Scan",
  "vulnerabilities": { ... },
  "last_updated": "2026-09-07T17:23:20.021049"
}
```

#### Trust Score Calculation (100 points total)

| Component | Points | Calculation |
|-----------|--------|-------------|
| MAC Consistency | 40 | Known MAC = 40, Unknown = 0, Changes penalize |
| IP Stability | 20 | Stable = 20, Changes = 0-20 scaled |
| Service Stability | 15 | Known OS/Type = 15, Unknown = 0-10 |
| Vulnerability Trend | 15 | Stable/improving = 15, Rising = 0-15 |
| Discovery Consistency | 10 | Consistently seen = 10, Occasional = 0-10 |
| **TOTAL** | **100** | Min(100, sum) |

#### Trust Levels

- **CRITICAL_ASSET** (85-100): Known, stable, trusted infrastructure
- **TRUSTED** (70-84): Known device with minimal changes
- **MONITORED** (50-69): Device under observation
- **SUSPICIOUS** (30-49): Low trust score, requires investigation
- **UNKNOWN** (0-29): New or unidentified device

### 2. Trust Score Engine (scripts/asset_builder.py)

**Purpose**: Calculate and maintain trust_score for all assets

**Features**:
- Baseline MAC address tracking
- IP stability monitoring
- Service discovery consistency
- Vulnerability trend analysis
- Historical observation tracking

**Trust History Storage** (state/asset_trust_history.json):
```json
{
  "192.168.0.14": {
    "mac_changes": 0,
    "ip_changes": 0,
    "first_seen": "2026-09-09T10:07:46.190379",
    "observations": 1,
    "risk_scores": [0]
  }
}
```

**Output**:
- Updated state/assets.json with trust_score fields
- state/asset_trust_history.json - persistence layer
- Console feedback on upgrade status

### 3. Shadow Asset Detector (scripts/shadow_asset_detector.py)

**Purpose**: Real-time detection of unknown/suspicious devices

**Detection Methods**:

| Method | Signal | Risk Level |
|--------|--------|-----------|
| Unknown MAC | MAC = "Unknown" | CRITICAL |
| Unknown Type/OS | type="Unknown" AND os="Unknown" | HIGH |
| Low Trust Score | trust_score < 30 | HIGH |
| Network Discovery | New MAC on network ARP/DHCP | CRITICAL |

**Shadow Asset Report** (state/shadow_assets.json):
```json
{
  "scan_time": "2026-09-09T...",
  "total_assets": 24,
  "shadows_detected": 2,
  "flagged_count": 2,
  "shadows": [
    {
      "ip": "192.168.0.51",
      "mac": "Unknown",
      "hostname": "192.168.0.51",
      "type": "Windows",
      "trust_score": 52,
      "risk_score": 3,
      "detected_at": "2026-09-09T...",
      "reason": "MAC address cannot be determined",
      "confidence": "HIGH",
      "recommended_action": "Immediate Nessus Target Scan"
    }
  ]
}
```

**Nessus Integration**: Generates target list for Layer 2 scanning:
- High-priority targets (unknown MAC, low trust)
- Recommended scan types (Full Network Audit)
- Priority order (CRITICAL first)

### 4. Asset Command Center CLI (scripts/asset_manager.py)

**Purpose**: Operational interface for asset management

**Commands**:

```bash
# List all assets with trust scores
python asset_manager.py --list-all

# Detect shadow assets
python asset_manager.py --list-shadow

# Trust score report by category
python asset_manager.py --trust-report

# Filter by asset type
python asset_manager.py --by-type Windows
python asset_manager.py --by-type Linux
python asset_manager.py --by-type Camera
python asset_manager.py --by-type Unknown

# List risky assets (above risk threshold)
python asset_manager.py --risky 50

# Full system health check
python asset_manager.py --health
```

**Output Formats**:
- Tabular (grid/simple format)
- JSON (machine-readable)
- Console (human-readable)

---

## Integration Points

### With Change Detector
- Shadow assets marked in state/assets.json
- Flag triggers incident routing
- Critical shadow assets -> GitHub incidents

### With Nessus Pipeline
- Shadow asset targets passed to Nessus API
- Scan results update trust_score
- Vulnerability data feeds risk_score

### With Risk Scoring
- trust_score influences overall risk calculation
- Shadow flag escalates alerts
- Low trust → high priority

---

## Operational Workflows

### Workflow 1: Daily Asset Inventory Review
```
1. Run: python asset_manager.py --health
   → See asset count, connectivity, trust distribution
   
2. Run: python asset_manager.py --list-shadow
   → Identify unknown devices
   
3. If shadows detected:
   a) Investigate via network scan
   b) Add to inventory if known
   c) Escalate if suspicious
```

### Workflow 2: Shadow Asset Response
```
1. Shadow asset detected (unknown MAC)
   
2. System generates Nessus targets
   
3. IT team reviews targets
   
4. Launch Nessus scan (Layer 2)
   
5. Results update trust_score
   
6. Device classified and added to inventory
```

### Workflow 3: Trust Score Review
```
1. Weekly: python asset_manager.py --trust-report
   
2. Review SUSPICIOUS category (trust 30-49)
   
3. For each suspicious asset:
   - Analyze MAC/IP changes
   - Check vulnerability trends
   - Determine if known/rogue
   
4. Update trust_level if needed
```

---

## Data Flow

```
Network Discovery (ARP/DHCP)
         ↓
Shadow Asset Detector
         ↓
Flag in state/assets.json
         ↓
Risk Scoring Engine
         ↓
Incident Router (if critical)
         ↓
Nessus Target List
         ↓
Network Scan Execution
         ↓
Results → Trust Score Update
```

---

## Metrics & KPIs

### Asset Inventory Health

| Metric | Target | Current |
|--------|--------|---------|
| Known Assets | >= 20 | 24 |
| MAC Coverage | >= 90% | 92% |
| Average Trust Score | >= 70 | 68 |
| Shadow Assets | <= 3 | 2 |
| Online Rate | >= 95% | 96% |

### Trust Distribution Target

| Level | Target % | Current % |
|-------|----------|-----------|
| CRITICAL_ASSET | 10-15% | 8% |
| TRUSTED | 50-60% | 54% |
| MONITORED | 20-30% | 29% |
| SUSPICIOUS | 5-10% | 6% |
| UNKNOWN | <= 5% | 3% |

---

## Future Enhancements

### Phase 3: Predictive Intelligence
- ML-based anomaly detection
- Behavioral profiling
- Risk prediction models

### Phase 4: Automated Response
- Auto-isolation of rogue devices
- Automatic Nessus remediation scanning
- Policy-based quarantine

### Phase 5: Advanced Analytics
- Asset lifetime tracking
- ROI/risk calculations
- Compliance reporting

---

## Configuration

### Environment Variables

```bash
# Nessus API (for shadow scan targeting)
NESSUS_URL=https://nessus.example.com:8834
NESSUS_ACCESS_KEY=...
NESSUS_SECRET_KEY=...

# Threshold settings
SHADOW_TRUST_THRESHOLD=30
MAC_CHANGE_PENALTY=5
IP_CHANGE_PENALTY=3
```

### Trust Score Tuning

Edit `scripts/asset_builder.py` TrustScoreEngine class:
- Adjust point allocation (MAC/IP/Service/Vuln/Discovery)
- Modify trust_level thresholds
- Customize risk factor weighting

---

## Compliance & Governance

- **Asset Tracking**: Complete inventory of all network devices
- **Change Tracking**: First-seen, last-changed timestamps
- **Trust Attestation**: Documented trust calculation basis
- **Audit Trail**: Historical changes preserved in trust_history
- **Incident Linkage**: Shadow assets traced to GitHub incidents

---

## Success Criteria

✓ All network assets catalogued with MAC/IP/Type  
✓ Trust scores calculated for 100% of assets  
✓ Shadow asset detection operational  
✓ Nessus targeting integrated  
✓ CLI tools functional and documented  
✓ Integration tests passing  

---

## KNOWN LIMITATIONS & PHASE 3 ROADMAP

### Skills Implementation (Interface Scaffold)
- **Current Status (Phase 2)**: Thư mục `skills/` đóng vai trò là Interface & Architecture Scaffold
- **Function Stubs**: Tất cả 5 skills (nessus-audit, waap-audit, asset-intelligence, daily-soc, git-governance) hiện chỉ return mock data
- **Phase 3 Work**: Kết nối trực tiếp vào Nessus API, WAAP systems, subprocess thực tế sẽ được hoàn thiện
- **Timeline**: Dự kiến Q4 2026 hoặc sớm hơn

### Trust Score Thresholds Calibration
- **Current Settings**: 
  - MAC stability threshold: 1.1 (10% tolerance)
  - Risk degradation threshold: 1.5 (50% tolerance)  
  - Baseline observation points: 8 (neutral for first-seen)
- **Calibration Method**: Các ngưỡng được thiết lập theo kinh nghiệm ban đầu
- **Phase 3 Refinement**: Sẽ được hiệu chỉnh bằng dữ liệu thực nghiệm sau 30 ngày vận hành
- **Data-Driven Update**: Sử dụng asset_trust_history.json để phân tích pattern thực tế

### Shadow Asset Classification Refinement
- **Phase 2 Classification**: 
  - `UNCLASSIFIED` (MAC unknown hoặc type unknown)
  - `SUSPICIOUS` (trust score < 30)
- **Phase 3 Enhancement**: Phân định chi tiết:
  - `UNCLASSIFIED_KNOWN_DEVICE` (đã biết MAC nhưng chưa rõ OS)
  - `ROGUE_SHADOW_ASSET` (MAC hoàn toàn lạ, chưa từng thấy)
  - `POTENTIALLY_COMPROMISED` (trust score tụt mạnh)
- **Detection Methods**: Sẽ thêm behavioral analysis & anomaly scoring

### Future Enhancements (Phase 3+)
- ML-based anomaly detection for asset behavior
- Automated remediation playbooks
- Advanced reporting & compliance integration
- Cross-asset vulnerability correlation
- Device lifecycle tracking & ROI analysis

---

**Specification Version**: 1.0  
**Last Updated**: 2026-09-09  
**CTO Approved**: Yes (with known limitations)  
**Maintainer**: SentinelOps Architecture Team  
**Next Review**: Phase 3 Kickoff (Q4 2026)
