# Nessus Pipeline - Quick Start Guide

## What is it?

The Nessus Pipeline connects Nessus vulnerability scanner directly to SentinelOps dashboard. No CSV exports, pure API-to-JSON transformation. Updates every 4 hours.

## File Structure

```
├── nessus_client.py         ← Connect to Nessus API
├── asset_builder.py         ← Discover and classify assets
├── risk_engine.py           ← Calculate risk scores
├── patch_queue.py           ← Manage patching priorities
├── nessus_pipeline.py       ← Orchestrator (main entry point)
├── NESSUS_PIPELINE.md       ← Complete documentation
├── requirements.txt         ← Python dependencies
└── state/                   ← Generated JSON files
    ├── assets.json          ← Asset inventory
    ├── risk_score.json      ← Risk metrics
    ├── patch_queue.json     ← Patch priorities
    ├── crypto_health.json   ← SSL/TLS audit
    └── pipeline_summary.json← Run metadata
```

## Installation (2 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Nessus credentials in .env
# Already set in project - check these values:
# NESSUS_URL=https://localhost:8834
# NESSUS_ACCESS_KEY=your_key
# NESSUS_SECRET_KEY=your_secret
```

## Usage

### Run Once (Test)
```bash
python nessus_pipeline.py
```

### Run Every 4 Hours (Production)
```bash
python nessus_pipeline.py --schedule
```

### Custom Schedule (e.g., Every 2 Hours)
```bash
python nessus_pipeline.py --schedule --interval 2
```

## How It Works

```
Nessus API
    ↓
nessus_client.py (connect + fetch scans)
    ↓
asset_builder.py (discover assets, auto-classify)
    ├→ Windows (servers, workstations)
    ├→ Camera (Reolink, Hikvision)
    ├→ Router (gateways, firewalls)
    ├→ NAS (Synology, QNAP)
    └→ Linux (servers, appliances)
    ↓
risk_engine.py (calculate scores 0-100)
    ↓
patch_queue.py (prioritize patches + crypto audit)
    ↓
state/*.json (saved to disk)
    ↓
web/server.js (REST API endpoints)
    ↓
Dashboard (displays metrics)
```

## Output Files

| File | What | Example |
|------|------|---------|
| `assets.json` | Device inventory | 11 devices, classified by type |
| `risk_score.json` | Overall risk | 45/100 (MEDIUM threat) |
| `patch_queue.json` | Patches needed | 269 patches, 8h to patch all |
| `crypto_health.json` | SSL/TLS status | 12 certs, 2 weak protocols |
| `pipeline_summary.json` | Last run info | Timestamp, file list |

## Dashboard Integration

Pipeline data automatically flows to:
- **Top Risk Hosts** widget
- **Patch Queue** display
- **Asset Types** breakdown
- **Risk Score** gauge
- **Crypto Health** status

All via REST API:
```
GET /api/state/assets.json
GET /api/state/risk_score.json
GET /api/state/patch_queue.json
GET /api/state/crypto_health.json
```

## Monitoring

### Check Logs
```bash
tail -f nessus_pipeline.log
```

### Check State Files
```bash
ls -lah state/*.json
cat state/pipeline_summary.json
```

### Check Git Commits
```bash
git log --oneline | grep "Nessus pipeline"
```

## Troubleshooting

### "Auth failed: 404"
- Nessus server not running on localhost:8834
- Check `.env` for correct URL/credentials
- Verify Nessus is accessible: `curl -k https://localhost:8834`

### "Assets file not found"
- First run hasn't completed yet
- Check `nessus_pipeline.log` for errors
- Verify Nessus has scans configured

### Empty asset list
- Nessus scans exist but haven't run yet
- Pipeline will populate once scans complete
- Run scans manually in Nessus UI

### Git commit errors
- Not critical - pipeline still completes
- Verify git is initialized: `git init`
- Check write permissions to repo

## Deployment

### Windows Task Scheduler
```powershell
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "C:\path\to\nessus_pipeline.py"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 4) `
  -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -Action $action -Trigger $trigger `
  -TaskName "NessusPipeline" -User "SYSTEM"
```

### Linux cron
```bash
0 */4 * * * cd /path/to/project && python nessus_pipeline.py
```

### Render.com
Add to `render.yaml`:
```yaml
services:
  - type: cron
    name: nessus-pipeline
    schedule: "0 */4 * * *"  # Every 4 hours
    command: "pip install -r requirements.txt && python nessus_pipeline.py"
```

## Key Features

✅ **Direct API** - No CSV exports, real-time data  
✅ **Auto-classification** - Windows/Camera/Router/NAS/Linux  
✅ **Risk scoring** - 0-100 scale with threat levels  
✅ **Patch priority** - Estimated remediation time  
✅ **Crypto audit** - SSL/TLS/cipher vulnerability scan  
✅ **Git integration** - Auto-commit on each run  
✅ **Scheduled runs** - Every 4 hours via schedule module  
✅ **Extensible** - Easy to add new data sources  

## Next Steps

1. Verify Nessus credentials in `.env`
2. Run `python nessus_pipeline.py` once to test
3. Schedule with `--schedule` flag for production
4. Monitor `nessus_pipeline.log` for issues
5. Check dashboard for Top Risk Hosts widget

## Documentation

Full details in `NESSUS_PIPELINE.md`:
- Architecture diagrams
- Module API reference
- Troubleshooting guide
- Future enhancements

## Questions?

- Check logs: `nessus_pipeline.log`
- Check state files: `state/*.json`
- Check Git: `git log`
- Read docs: `NESSUS_PIPELINE.md`

---

**Status**: ✅ Ready to Deploy  
**Tested**: Python 3.7+ on Windows  
**Dependencies**: requests, schedule, python-dotenv  
**Nessus Versions**: Professional, Essentials (API v6+)  
