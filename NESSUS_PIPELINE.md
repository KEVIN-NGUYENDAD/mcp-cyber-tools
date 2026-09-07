# Nessus Pipeline Documentation

## Overview

The Nessus Pipeline integrates Nessus Professional/Essentials vulnerability scanner data directly into the SentinelOps dashboard. No CSV exports required—pure API-to-JSON transformation.

**Schedule**: Every 4 hours  
**Output**: 5 state files  
**Flow**: Nessus API → Assets → Risk Calc → Patch Queue → Dashboard

---

## Pipeline Architecture

```
┌─────────────────┐
│  Nessus API     │ ← Direct HTTPS connection
└────────┬────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  nessus_pipeline.py (Orchestrator)    │
    └────┬────────────┬──────────────┬──────┘
         │            │              │
    ┌────▼────────┐ ┌─▼────────────┐ ┌─▼─────────────────┐
    │ nessus_     │ │ asset_       │ │ risk_engine.py    │
    │ client.py   │ │ builder.py   │ │ patch_queue.py    │
    └────┬────────┘ └──────┬───────┘ └─────┬─────────────┘
         │                 │               │
    ┌────▼─────────────────▼───────────────▼────┐
    │  state/ (5 JSON files)                     │
    ├───────────────────────────────────────────┤
    │ • assets.json                             │
    │ • risk_score.json                         │
    │ • patch_queue.json                        │
    │ • crypto_health.json                      │
    │ • pipeline_summary.json                   │
    └────┬─────────────────────────────────────┘
         │
    ┌────▼──────────────┐
    │  web/server.js    │ ← Serves via REST API
    │  Express.js       │
    └─────┬─────────────┘
          │
    ┌─────▼──────────────┐
    │  SentinelOps       │
    │  Dashboard         │
    └───────────────────┘
```

---

## Installation

### 1. Dependencies

```bash
pip install -r requirements.txt
```

Requires:
- `requests` - HTTP client for Nessus API
- `schedule` - Job scheduling
- `python-dotenv` - Environment variable management

### 2. Environment Setup

Credentials in `.env`:
```env
NESSUS_URL=https://localhost:8834
NESSUS_ACCESS_KEY=your_api_key
NESSUS_SECRET_KEY=your_secret_key
```

---

## Modules

### nessus_client.py
**Direct Nessus API client**

```python
client = NessusClient()
scans = client.get_scans()
hosts = client.get_scan_hosts(scan_id)
details = client.get_host_details(scan_id, host_id)
```

Methods:
- `authenticate()` - Verify API credentials
- `get_scans()` - List all scans
- `get_scan_hosts(scan_id)` - Get hosts in scan
- `get_host_details()` - Full host info
- `get_vulnerabilities()` - Vulnerability details
- `get_plugin_details()` - Plugin/CVE info

### asset_builder.py
**Transform Nessus data → assets.json**

Auto-classifies assets:
- **Windows**: DOMAIN, DC, SERVER, WIN patterns
- **Camera**: REOLINK, HIKVISION, IP camera ranges
- **Router**: GATEWAY, EDGE, OPNSENSE, PFSENSE
- **NAS**: SYNOLOGY, QNAP, STORAGE, DS* patterns
- **Linux**: UBUNTU, DEBIAN, CENTOS patterns
- **Unknown**: Unmatched assets

Output: `state/assets.json`
```json
{
  "total_assets": 11,
  "assets_by_type": {
    "Windows": [...],
    "Camera": [...],
    "Router": [...],
    "NAS": [...],
    "Linux": [...]
  },
  "all_assets": [
    {
      "id": 1,
      "hostname": "WORKSTATION01",
      "ip": "192.168.1.10",
      "type": "Windows",
      "os": "Windows 11 Pro",
      "vulnerabilities": {
        "critical": 2,
        "high": 5,
        "medium": 12,
        "low": 8,
        "info": 45
      },
      "risk_score": 34,
      "status": "ONLINE",
      "last_updated": "2026-09-07T15:30:00Z"
    }
  ]
}
```

### risk_engine.py
**Calculate risk scores**

- Overall score: 0-100 (weighted by asset count)
- Threat level: LOW, MEDIUM, HIGH, CRITICAL
- Top risk hosts (top 5)
- Risk by asset type

Output: `state/risk_score.json`
```json
{
  "overall_score": 45,
  "threat_level": "MEDIUM",
  "risk_summary": {
    "critical_count": 3,
    "high_count": 18,
    "medium_count": 92,
    "low_count": 156,
    "total_vulnerabilities": 269
  },
  "top_risk_hosts": [
    {
      "hostname": "SERVER01",
      "risk_score": 78,
      "critical_count": 2
    }
  ],
  "risk_by_type": {
    "Windows": {"count": 5, "avg_risk": 42},
    "Linux": {"count": 2, "avg_risk": 28},
    "NAS": {"count": 1, "avg_risk": 15}
  }
}
```

### patch_queue.py
**Patch prioritization & crypto audit**

Builds queue by severity:
- CRITICAL patches (30 min each)
- HIGH patches (20 min each)
- MEDIUM patches (15 min each)
- LOW patches (tracked)

Estimates total patching time.

Output files:
- `state/patch_queue.json`
- `state/crypto_health.json`

```json
{
  "queue_by_priority": {
    "CRITICAL": [
      {
        "asset": "WORKSTATION01",
        "ip": "192.168.1.10",
        "type": "Windows",
        "count": 2,
        "priority": 1,
        "estimated_time_minutes": 30
      }
    ],
    "HIGH": [...],
    "MEDIUM": [...],
    "LOW": [...]
  },
  "total_patches_pending": 269,
  "estimated_time": "8h"
}
```

### nessus_pipeline.py
**Orchestrator**

Coordinates all modules and schedules.

**Run once:**
```bash
python nessus_pipeline.py
```

**Run with scheduling (every 4 hours):**
```bash
python nessus_pipeline.py --schedule
```

**Run with custom interval (e.g., 2 hours):**
```bash
python nessus_pipeline.py --schedule --interval 2
```

Output:
- Logs to console + `nessus_pipeline.log`
- Creates `state/pipeline_summary.json`
- Commits changes to git

---

## State Files Generated

| File | Purpose | Updated | Consumers |
|------|---------|---------|-----------|
| `assets.json` | Asset inventory with vulns | Per run | Dashboard, Risk engine |
| `risk_score.json` | Overall risk metrics | Per run | Risk display, KPIs |
| `patch_queue.json` | Patching priorities | Per run | Patch manager |
| `crypto_health.json` | SSL/TLS/cipher audit | Per run | Security dashboard |
| `pipeline_summary.json` | Last run metadata | Per run | Monitoring |

All files include:
- `timestamp`: ISO 8601 when generated
- `last_updated`: ISO 8601 modification time
- Complete data snapshots

---

## Dashboard Integration

### API Endpoints

```
GET /api/state/assets.json
GET /api/state/risk_score.json
GET /api/state/patch_queue.json
GET /api/state/crypto_health.json
GET /api/state/pipeline_summary.json
```

### Dashboard Widgets

The following dashboard cards auto-refresh from pipeline output:

**Top Risk Hosts**
- Shows top 5 highest-risk assets
- Source: `risk_score.json → top_risk_hosts`

**Patch Queue**
- Displays pending patches by priority
- Estimated time to remediate
- Source: `patch_queue.json`

**Asset Types**
- Breakdown by classification
- Source: `assets.json → assets_by_type`

**Crypto Health**
- SSL/TLS certificate inventory
- Vulnerable protocols/ciphers
- Source: `crypto_health.json`

**Overall Risk Score**
- Threat level indicator
- Risk timeline graph
- Source: `risk_score.json`

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run once
python nessus_pipeline.py

# Check output
cat state/assets.json
cat state/risk_score.json
```

### Production (Render.com)

Add to `render.yaml`:
```yaml
services:
  - type: cron
    name: nessus-pipeline
    schedule: "0 */4 * * *"  # Every 4 hours
    command: "pip install -r requirements.txt && python nessus_pipeline.py"
```

Or as background service:
```bash
nohup python nessus_pipeline.py --schedule > nessus.log 2>&1 &
```

### Windows Task Scheduler

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\nessus_pipeline.py"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "NessusPipeline"
```

### Linux cron

```bash
0 */4 * * * cd /path/to/project && python nessus_pipeline.py
```

---

## Logging

Pipeline logs to:
1. **Console**: Real-time output
2. **`nessus_pipeline.log`**: Persistent file log

```
[2026-09-07T15:30:00+00:00] [START] NESSUS PIPELINE START
[2026-09-07T15:30:02+00:00] [INFO] Step 1: Discovering assets from Nessus...
[2026-09-07T15:30:15+00:00] [SUCCESS] ✅ Discovered 11 assets
[2026-09-07T15:30:16+00:00] [INFO] Step 2: Calculating risk scores...
[2026-09-07T15:30:18+00:00] [SUCCESS] ✅ Risk score: 45 (MEDIUM)
[2026-09-07T15:30:19+00:00] [INFO] Step 3: Building patch queue...
[2026-09-07T15:30:21+00:00] [SUCCESS] ✅ Patch queue: 269 pending
[2026-09-07T15:30:22+00:00] [SUCCESS] PIPELINE COMPLETE - 22.3s
```

---

## Troubleshooting

### "Connection refused" to Nessus

- Verify Nessus is running on `https://localhost:8834`
- Check firewall allows HTTPS to Nessus
- Confirm `.env` has correct credentials

### Empty assets

- Ensure scans exist in Nessus
- Check Nessus API credentials
- Verify network access to Nessus server
- Run `nessus_client.py` directly to test auth

### Git commit fails

- Ensure git is initialized: `git init`
- Check working directory permissions
- Git commit errors are logged but don't fail pipeline

### Patch queue estimates are wrong

- Algorithm uses 20 min average per host
- Adjust multiplier in `patch_queue.py` line ~110
- Estimates are rough guidance only

---

## Future Enhancements

- [ ] Store historical trends (delta tracking)
- [ ] Integrate with ticketing system (JIRA, Linear)
- [ ] Email/Slack alerts on new CRITICALs
- [ ] Compliance scoring (CIS, NIST)
- [ ] Patch status tracking (% patched)
- [ ] Asset audit trails (discovered/removed)
- [ ] MCP integration for advanced threat hunting

---

## Git Integration

Pipeline auto-commits after each successful run:

```
Auto: Nessus pipeline run 2026-09-07T15:30:21+00:00
```

Includes all updated state files. Configure `.gitignore`:

```
nessus_pipeline.log
state/history/  # Optional history directory
```

---

**Status**: 🟢 Pipeline Ready  
**Last Updated**: 2026-09-07  
**Maintenance**: Check Nessus connection weekly
