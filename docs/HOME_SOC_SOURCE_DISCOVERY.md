# Home-SOC Source Discovery

Follow-up to `docs/MVP3_WAZUH_INVESTIGATION.md`. Wazuh is not installed
and that investigation is frozen. This pass checks the four priority
sources for real, already-available security telemetry on this host, to
pick the next real alert source for MVP #3's replacement. Discovery and
verification only — no code changed.

## 1. Windows Defender — real, already proven

Real-time protection is on (`RealTimeProtectionEnabled: True`), engine
and signatures current (updated 9/2/2026). `Get-MpThreat` /
`Get-MpThreatDetection` return real detection history — this is exactly
the source MVP #2 already used and shipped. Nothing new to discover
here; it's the one proven source in the pipeline today.

## 2. Windows Event Logs — real, live, partially useful

| Log | RecordCount | Notes |
|---|---|---|
| Security | 34,376 | Live, growing. Logon events (4624) present. **No** failed-logon (4625) or process-creation (4688) events — process-creation auditing is off by default on this host, so no command-line/process telemetry is available from this log without an auditpol change (a config change, out of scope here) |
| Microsoft-Windows-Windows Defender/Operational | 7,956 | Live. Same underlying detections as `Get-MpThreat`, in Event Log form instead of the cmdlet form |
| System | 45,041 | Live, generic OS events |
| Application | 35,748 | Live, generic app events |

No Sysmon installed (no service, no `Microsoft-Windows-Sysmon/Operational`
log) — so no rich process/network telemetry beyond what's listed above.

## 3. Existing Home-SOC reports — two separate pipelines found, one of them live

This is the most important finding of this pass. There are **two
distinct, unrelated Home-SOC implementations** on this machine, not one:

### 3a. `C:\mcp-cyber-tools\reports\home-soc-state\*.json` (per `home-soc-phase1-package/docs/ARCHITECTURE.md`)

Stale. All files (`device-history.json`, `network-history.json`,
`baseline.json`, `changes.json`, `alerts.json`) last written
**2026-08-29 19:18 UTC** — one single collection, six days old at time
of writing. Its scheduled tasks:

- `HOME-SOC-MCP-Server` — last run 8/29, `LastTaskResult: 1` (failure), not currently running
- `HOME-SOC-Startup-Scan-AutoPush` — has never run (`LastRunTime` shows the scheduler's epoch default)

This pipeline is effectively dormant.

### 3b. `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\` — active

This is a separate, much larger project tree with its own git repo,
scheduled independently as **`HOME-SOC-Scan-And-Export`**
(`cmd /c node security-watch.js && node iot-device-scanner.js && node
export-home-soc-reports.js`). Verified actually running:
`LastRunTime 9/3/2026 7:51:48 PM`, `LastTaskResult 0` (success),
`NextRunTime 9/4/2026 7:45:00 PM`.

Its `security-watch.js` is a small, already-working endpoint-control
watcher: every scheduled run it reads 5 real Windows security controls
(DNS servers, Windows Firewall, Defender real-time protection, RDP
listening, SSH listening), diffs against an explicitly-approved
`baseline.json`, and appends any transition to `alerts.json` in a clean,
consistent schema:

```json
{
  "type": "DEFENDER_DISABLED",
  "severity": "CRITICAL",
  "control": "defender",
  "description": "Real-time protection was turned off",
  "baseline_value": true,
  "current_value": false,
  "detected_at": "2026-09-04T02:52:27.028Z"
}
```

Current state (`state.json`, 2026-09-04T02:52:27Z): DNS, firewall,
Defender, RDP, SSH all match baseline — 0 open alerts, which is the
correct/expected reading, not a stale one. `alerts.json` is currently
`{"alerts":[],"open_alert_count":0}`.

One known reliability caveat, already investigated and closed by this
project's own team: `INCIDENT-2026-09-01-STALE-FEED.md` documents a
missed collection cycle on 2026-09-01 (the scheduled task didn't fire
for ~41 hours) — root-caused as a scheduling gap, not a bug in the
scripts, and closed as an observation. Worth knowing about, not
currently blocking.

This schema (`type`/`severity`/`description`/plus optional fields) is
structurally very close to the alert shape MVP #1/#2 already score and
post to GitHub Issues with — closer than raw Defender or raw Event Log
output.

## 4. Suricata — not installed

Same result as the Wazuh check: no `Suricata` service, no
`C:\Program Files\Suricata`. Confirmed absent, not a usable source.

## Conclusion

Ranked by "real + already running + easy to map onto the existing
`score_alert`/`build_issue` pipeline":

1. **`security-watch.js`'s `alerts.json`** (path 3b above) — real,
   actively scheduled, clean schema, zero new code needed to *produce*
   the data (only a mapper, same shape as MVP #2's `to_alert()`)
2. **Windows Defender** — already proven in MVP #2, still available as
   a second/parallel source
3. Windows Event Logs (Security/Defender-Operational logs) — real and
   live, but no process-creation telemetry without an auditpol change
4. `C:\mcp-cyber-tools\reports\home-soc-state` (path 3a) — dormant,
   would need its own scheduled tasks fixed before it's usable
5. Suricata — not installed, ruled out

No integration was built in this pass. This is a discovery finding for
the next MVP decision, not an implementation.
