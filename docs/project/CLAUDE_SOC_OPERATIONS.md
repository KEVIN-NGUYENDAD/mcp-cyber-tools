# Claude SOC Operations Framework

**Date**: 2026-09-09  
**Status**: Phase 2 Active  
**Framework Version**: 1.0.0

---

## Mục Tiêu (Objectives)

Xây dựng quy trình SOC tự động hóa cho SentinelOps sử dụng Claude AI, đảm bảo:
1. Real-time threat detection and response
2. Intelligent asset profiling
3. Automated incident routing
4. Continuous security monitoring
5. Data-driven decision making

---

## Roles & Responsibilities

### Claude AI as SOC Analyst
- **Capabilities**: Analyze assets, detect patterns, prioritize threats
- **Authority**: Execute configured responses automatically
- **Constraints**: Must follow approval policies for critical actions
- **Output**: Incidents, recommendations, daily briefs

### Security Team (Human Oversight)
- **Review**: High-severity alerts and decisions
- **Approve**: Remediation actions
- **Escalate**: Unusual patterns requiring investigation
- **Tune**: ML models and detection rules

---

## Automated Workflows

### Workflow 1: Asset Discovery & Profiling

```
Schedule: Continuous (on network changes)
Trigger: New device detected or MAC change

Steps:
1. Asset detected via network scan
2. Claude profiles asset:
   - OS identification
   - Service enumeration
   - Trust score calculation
   - Risk assessment
3. Add to inventory or update existing record
4. If shadow asset:
   - Flag for Nessus scan
   - Route to SOC dashboard
   - Send alert to team
5. Store in state/assets.json
```

**Tools Used**:
- `shadow_asset_detector.py` - Detection
- `asset_builder.py` - Profiling
- `asset_manager.py` - Inventory mgmt

---

### Workflow 2: Threat Detection & Prioritization

```
Schedule: Every 5 minutes (configurable)
Trigger: New vulnerability or incident detected

Steps:
1. Collect latest data:
   - Nessus scan results
   - Defender logs
   - Firewall alerts
   - Shadow asset reports
   
2. Claude analyzes:
   - Severity assessment
   - Asset criticality
   - Attack pattern recognition
   - Risk scoring
   
3. Prioritize threats:
   - CRITICAL → Immediate escalation
   - HIGH → SOC review queue
   - MEDIUM → Daily brief
   - LOW → Backlog
   
4. Route to response:
   - Create GitHub incident
   - Send Telegram alert
   - Log to daily brief
   - Archive for audit
```

**Input Sources**:
- state/risk_score.json
- state/defender_status.json
- state/incidents.json
- shadow_assets.json

**Output**:
- GitHub issues (critical/high)
- Daily brief entries
- Telegram alerts
- Audit trail

---

### Workflow 3: Shadow Asset Investigation

```
Schedule: On detection + hourly review
Trigger: Unknown MAC or low trust score

Steps:
1. Shadow asset flagged:
   - Unknown MAC or type
   - Trust score < 30
   - Unusual network behavior
   
2. Claude initiates investigation:
   - Query network history
   - Check ARP table
   - Review DHCP logs
   - Analyze traffic patterns
   
3. Generate Nessus targets:
   - Create scan task
   - Set scan policy (Full Network Audit)
   - Schedule execution
   
4. Document findings:
   - Add evidence to incident
   - Update asset record
   - Flag if rogue device
   
5. Route response:
   - If confirmed unknown:
     → CRITICAL incident
     → Network isolation review
   - If identified:
     → Add to inventory
     → Clear shadow flag
```

**Response Actions**:
- Trigger Nessus scan
- Create incident
- Notify security team
- Escalate if necessary

---

### Workflow 4: Daily Security Brief

```
Schedule: 09:00 UTC daily
Trigger: Scheduled task

Steps:
1. Collect 24-hour data:
   - Incidents (open + closed)
   - Shadow assets detected
   - Vulnerability trends
   - Risk score changes
   
2. Claude generates brief:
   - Executive summary (5 items)
   - Threat analysis
   - Asset health report
   - Top recommendations
   
3. Format and deliver:
   - Email to team
   - Slack notification
   - Dashboard update
   - Archive in brief store
```

**Brief Sections**:
- Incident Summary (count, severity)
- Critical Assets at Risk (top 5)
- Shadow Assets (new detections)
- Vulnerability Trends (top CVEs)
- Recommended Actions (prioritized)

---

### Workflow 5: Risk Scoring & Response

```
Schedule: Real-time (on event)
Trigger: Asset change, vulnerability, incident

Steps:
1. Event detected:
   - Shadow asset discovered
   - Vulnerability detected
   - Service change
   - Network anomaly
   
2. Claude calculates risk:
   - Event severity
   - Asset criticality
   - Environmental context
   - Historical patterns
   
3. Risk score assigned (0-100):
   - > 80: CRITICAL
   - 60-79: HIGH
   - 40-59: MEDIUM
   - 20-39: LOW
   - < 20: INFO
   
4. Automated response:
   - CRITICAL → GitHub incident + Telegram
   - HIGH → GitHub incident + daily brief
   - MEDIUM → Daily brief only
   - LOW/INFO → Archive
```

**Risk Factors**:
- Exploit availability (CVE data)
- Asset exposure (internet-facing?)
- Criticality (production vs. test)
- Trend (stable vs. worsening)
- Trust score (known vs. unknown device)

---

## Skills Integration (Phase 2)

### 5 Core Skills

#### 1. nessus-audit
**Purpose**: Vulnerability scanning orchestration

**Actions**:
- `launch_scan` - Start scan on target
- `target_asset` - Add asset to scan queue
- `generate_report` - Export scan results

**Trigger**: Shadow asset detected, risky asset identified

**Example**:
```python
nessus_skill.execute('launch_scan', 
                     target='192.168.0.51',
                     scan_type='full')
```

#### 2. waap-audit
**Purpose**: Web application firewall monitoring

**Actions**:
- `analyze_logs` - Parse WAF logs
- `detect_attacks` - Identify attack patterns
- `generate_report` - Security report

**Trigger**: High attack rate or unknown threat pattern

#### 3. asset-intelligence
**Purpose**: Asset profiling and trust analysis

**Actions**:
- `profile_asset` - Build device profile
- `calculate_trust_score` - Trust assessment
- `detect_anomalies` - Behavioral analysis
- `generate_report` - Asset intelligence report

**Trigger**: New asset discovered, trust score changes

#### 4. daily-soc
**Purpose**: SOC operations automation

**Actions**:
- `generate_brief` - Daily security brief
- `compile_threats` - Threat summary
- `prioritize_incidents` - Sort by severity
- `send_alerts` - Route notifications

**Trigger**: Scheduled (daily), on critical event

#### 5. git-governance
**Purpose**: Repository authority and policies

**Actions**:
- `enforce_policies` - Branch protection rules
- `manage_source_of_truth` - Version control
- `audit_access` - Access review
- `archive_branches` - Deprecate old branches

**Trigger**: Policy review, branch changes

---

## Decision Tree for Claude

### On Asset Discovery
```
Is MAC known?
├─ YES: Update trust score, check vulnerabilities
└─ NO: Mark as shadow
    ├─ Already in system?
    │  ├─ YES: Flag for re-scan
    │  └─ NO: Create incident, queue Nessus
    └─ Trigger asset-intelligence skill
```

### On Vulnerability
```
Is on CRITICAL_ASSET?
├─ YES: Immediate GitHub incident, Telegram alert
├─ NO: Is on TRUSTED asset?
│   ├─ YES: GitHub incident, daily brief
│   └─ NO: Daily brief only
└─ All: Trigger nessus-audit skill
```

### On Shadow Asset
```
Confidence level?
├─ HIGH (unknown MAC): 
│  ├─ Create CRITICAL incident
│  ├─ Trigger Nessus scan
│  └─ Escalate to team
├─ MEDIUM (low trust score):
│  ├─ Create HIGH incident
│  └─ Flag for investigation
└─ LOW: Monitor, log to brief
```

---

## Automated Incident Routing

### GitHub Incidents (critical/high)

**Template**:
```markdown
Title: [THREAT] Asset vulnerability on {hostname}
Description:
- Asset: {ip} ({type})
- Vulnerability: {cve}
- Severity: {level}
- Risk Score: {score}
- Recommendation: {action}
Labels: [security, {severity}, {asset_type}]
Assignee: Security team
```

### Telegram Alerts (critical only)

**Format**:
```
🚨 CRITICAL: {threat_title}
Asset: {ip} ({hostname})
Type: {asset_type}
Risk: {score}/100
Action: {recommendation}
```

### Daily Brief Entries (all levels)

**Format**:
```json
{
  "incident": "{title}",
  "severity": "{level}",
  "asset": "{ip}",
  "timestamp": "{iso_time}",
  "status": "{open|resolved}",
  "risk_score": {score}
}
```

---

## Configuration & Tuning

### Response Thresholds

| Parameter | Value | Tuning |
|-----------|-------|--------|
| CRITICAL threshold | 80 | Adjust in risk_score.py |
| HIGH threshold | 60 | Adjust in risk_score.py |
| Shadow detection confidence | HIGH | Edit change_detector.py |
| MAC change penalty | 5 points | Edit asset_builder.py |
| Trust score floor | 0 | Minimum score possible |

### Skill Scheduling

```yaml
nessus-audit:
  frequency: on_shadow_detected
  parallel: false
  timeout: 3600

asset-intelligence:
  frequency: on_asset_change
  parallel: true
  timeout: 300

daily-soc:
  frequency: "0 9 * * *"  # 09:00 UTC daily
  parallel: false
  timeout: 600

git-governance:
  frequency: "0 0 * * 0"  # Weekly Sunday
  parallel: false
  timeout: 300
```

---

## Monitoring & Observability

### Key Metrics

```
Assets Monitored: {count}
Shadow Assets: {count}
Average Trust Score: {score}/100
Critical Vulnerabilities: {count}
Open Incidents: {count}
Daily Incidents: {count}
Response Time (avg): {minutes}
False Positive Rate: {percent}
```

### Health Checks

```bash
# Run every hour
python asset_manager.py --health

# Outputs:
- Asset count and distribution
- Trust score statistics
- Shadow asset count
- Online/offline status
- MAC coverage percentage
```

### Audit Trail

All Claude SOC operations logged to:
- `docs/SOC_AUDIT.log` - Action history
- `state/incidents.json` - Incident tracking
- GitHub issues - Decision records
- Daily briefs - Summary reports

---

## Approval Workflows

### For CRITICAL Incidents
```
1. Claude detects threat
2. Create GitHub incident (auto)
3. Send Telegram alert (auto)
4. Wait for team approval
5. Execute remediation (on approval)
```

### For Policy Changes
```
1. Claude proposes change
2. Document in PR
3. Team review (48 hour window)
4. Merge if approved
5. Deploy configuration
```

---

## Training & Feedback Loop

### Continuous Improvement

```
1. Analyze false positives weekly
2. Tune thresholds based on patterns
3. Update risk scoring models
4. Retrain anomaly detection
5. Document lessons learned
```

### Performance Metrics

Track and improve:
- Detection accuracy (TP/FP rate)
- Response time to critical threats
- Asset profiling completeness
- Trust score stability
- User satisfaction

---

## Compliance & Governance

- **SOX**: Audit trail maintained for all decisions
- **ISO27001**: Risk-based incident response documented
- **GDPR**: Asset data retention policy enforced
- **Internal**: Weekly review of automated decisions

---

## Rollout Plan (Phase 2)

**Week 1**: Asset profiling + shadow detection (LIVE)  
**Week 2**: Nessus integration + automated scanning  
**Week 3**: Risk scoring + incident routing  
**Week 4**: Daily briefs + team notifications  
**Week 5**: Performance tuning + threshold optimization  

---

## Success Criteria

✓ All network assets profiled within 24 hours  
✓ Shadow assets detected within 5 minutes  
✓ Critical incidents routed within 1 minute  
✓ 95%+ false positive filtering  
✓ Team confidence in automated decisions  
✓ Audit trail complete for all actions  

---

**Framework Version**: 1.0.0  
**Last Updated**: 2026-09-09  
**Status**: Implementation Phase  
**Next Review**: 2026-09-16
