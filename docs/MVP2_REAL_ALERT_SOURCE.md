# MVP #2: Real Alert Source

MVP #1 (`docs/MVP_NOTIFICATION_FLOW.md`) proved the notification path using
a static, fake alert (`sample-events/test-alert.json`). This MVP replaces
that fake input with a real one — everything downstream (scoring, GitHub
Issue, assignment) is unchanged.

```
Real Alert (Windows Defender detection)
  |
  v
MCP  (scripts/create_defender_incident.py)
  |
  v
Risk Score
  |
  v
GitHub Issue
  |
  v
Assignment (KEVIN-NGUYENDAD)
```

## Alert source used

**Windows Defender**, via the `Get-MpThreat` / `Get-MpThreatDetection`
PowerShell cmdlets — the same cmdlets `modules/defender.js`'s
`defenderThreats` tool already queries. This was priority A on the
inspection list (Defender events / Windows Event Logs / Wazuh
`alerts.json` / Suricata `eve.json`) and was available immediately: the
host has Defender enabled with real-time protection on, and no exclusions
that would block a detection. Event Logs, Wazuh, and Suricata were not
needed.

No new alert source was built. The script reads whatever Defender has
already detected on the host — nothing is invented or simulated inside
the pipeline itself.

## How the real event was triggered

An EICAR test file (the industry-standard, harmless string used to test
antivirus alerting — not real malware) was written to a temp path.
Defender's real-time protection detected and quarantined it immediately:

```
ThreatName:  Virus:DOS/EICAR_Test_File
SeverityID:  5 (Severe)
Process:     powershell.exe
File:        C:\Users\<user>\AppData\Local\Temp\eicar_test.txt
ActionSuccess: true
```

## What changed vs. MVP #1

| | MVP #1 | MVP #2 |
|---|---|---|
| Alert input | `sample-events/test-alert.json` (static) | `Get-MpThreat` / `Get-MpThreatDetection` (live) |
| Script | `scripts/create_test_incident.py` | `scripts/create_defender_incident.py` |
| Scoring | `score_alert()` | same function, reused |
| Issue formatting | `build_issue()` | same function, reused (extended with optional evidence fields — see below) |
| GitHub Issue / assignment | `create_issue()`, `assign_issue()` | same functions, reused unchanged |

`create_defender_incident.py` imports `score_alert`, `build_issue`,
`create_issue`, `assign_issue`, and `ASSIGNEE` directly from
`create_test_incident.py` rather than duplicating them. The only new code
is `get_latest_defender_detection()` (runs the PowerShell query) and
`to_alert()` (maps a raw Defender detection onto the existing alert
schema: `source`, `event_type`, `severity`, `ip`, plus optional
`threat_signature` / `process` / `file` / `detection_time` fields).

`build_issue()` in `create_test_incident.py` was extended to append those
optional fields to the issue body **only when present** — the MVP #1 path
(`sample-events/test-alert.json`, no such keys) produces byte-identical
output to before this change.

## Severity mapping

Defender's `SeverityID` is mapped onto the same four buckets MVP #1 used:

| SeverityID | Meaning | Bucket | Score |
|---|---|---|---|
| 0, 1 | Unknown, Low | low | 20 |
| 2 | Moderate | medium | 50 |
| 3, 4 | High | high | 75 |
| 5 | Severe | critical | 95 |

## Scope

Same exclusions as MVP #1, still deliberately out of scope:

- No dashboard
- No database
- No Redis
- No PostgreSQL
- No Kubernetes
- No additional architecture beyond the two files this MVP added
  (`scripts/create_defender_incident.py`, this doc) plus one small,
  backward-compatible edit to `build_issue()` in
  `scripts/create_test_incident.py`

## Running it

```powershell
$env:GITHUB_TOKEN = "ghp_xxx"   # or: $env:GITHUB_TOKEN = (gh auth token)
python scripts/create_defender_incident.py
```

If Defender has no detections yet, the script exits with instructions for
generating a safe EICAR test detection.

## Result

Triggered one real Defender detection (EICAR test), which produced one
real GitHub Issue, assigned to KEVIN-NGUYENDAD:

**Issue #5** — `[CRITICAL] Virus Dos Eicar Test File | Risk 95`
https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/5

Stopping here per MVP #2 scope — first successful real alert achieved.
