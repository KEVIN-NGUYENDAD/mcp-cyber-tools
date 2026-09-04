# SentinelOps Status

## Completed

✅ MVP #1 - Fake Alert Pipeline
✅ MVP #2 - Windows Defender Real Alert Pipeline
✅ MVP #3 (investigation) - Wazuh Verification
✅ MVP #3 - Live security-watch.js Telemetry Pipeline

## Architecture

```
Windows Defender ─┐
security-watch.js ┴→ alerts.json
                       ↓
                      MCP
                       ↓
                   Risk Score
                       ↓
              Duplicate Detection (24h)
                 ↓            ↓
         new alert      existing alert
              ↓                ↓
       GitHub Issue    Update occurrence
              ↓          count + last_seen
       Assign KEVIN-NGUYENDAD
              ↓
        GitHub Mobile
              ↓
            iPhone
```

## Commits

MVP #1:
d70a085

MVP #2:
8ec96f2

MVP #3:
(this commit) mvp3 live securitywatch telemetry

## Current State

Working:
- GitHub integration
- Issue creation
- Assignment
- Mobile visibility
- Risk scoring
- Live security-watch.js telemetry (real alert source)
- Duplicate detection (24h window, occurrence count + last_seen on the issue itself)

Not Yet Implemented:
- WAAP integration
- Labels automation
- MCP analysis comments

Ruled out (see investigation docs):
- Wazuh alerts.json — not installed, will not be built
- Suricata eve.json — not installed, will not be built

## MVP #3: Wazuh Verification

Wazuh verification completed.

Result:
No Wazuh installation found.

Do not build Wazuh integrations. Investigation frozen. No code changed.
See `docs/MVP3_WAZUH_INVESTIGATION.md` for full findings.

## Home-SOC Source Discovery

Completed 2026-09-04. Discovery/verification only, no code changed. See
`docs/HOME_SOC_SOURCE_DISCOVERY.md` for full findings.

Result, ranked (real + already running + closest fit to existing
scoring/GitHub pipeline):

1. **`security-watch.js` → `alerts.json`** (in
   `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`) —
   real, actively scheduled (`HOME-SOC-Scan-And-Export`, last run
   success 9/3/2026), clean alert schema, currently 0 open alerts (5/5
   controls match baseline). **Leading candidate for MVP #3 replacement.**
2. Windows Defender — already proven in MVP #2, still available
3. Windows Event Logs — real and live, but no process-creation telemetry
   without an auditpol change (out of scope)
4. `C:\mcp-cyber-tools\reports\home-soc-state` — a second, separate
   Home-SOC implementation on this host; dormant since 2026-08-29
5. Suricata — not installed, ruled out

## MVP #3: Live security-watch.js Telemetry

Built on the discovery above. Source: `security-watch.js`'s live
`alerts.json` at
`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\alerts.json`
— the endpoint-control watcher already running on this host via the
`HOME-SOC-Scan-And-Export` scheduled task. No new infrastructure was
built; Wazuh and Suricata remain out of scope, per the frozen
investigation.

New script: `scripts/create_securitywatch_incident.py`. Reuses
`score_alert`, `build_issue`, `create_issue`, `assign_issue`, `ASSIGNEE`,
`github_request`, `REPO_OWNER`, `REPO_NAME` from
`create_test_incident.py` unchanged, same pattern as MVP #2's
`create_defender_incident.py`. The only new logic is `to_alert()`
(maps a security-watch.js alert entry onto the existing alert schema)
and 24-hour duplicate detection.

**Duplicate detection:** GitHub itself is the source of truth — no
separate local state file. An open issue is a duplicate if its title
matches (title is stable per alert type: severity + event type + risk
score) and its "Last Seen" is within 24 hours. A duplicate gets its
body's `## Occurrence Tracking` block updated in place (`Occurrences`
+1, `Last Seen` refreshed) instead of a new issue.

**Finding — bug in security-watch.js (not fixed, out of scope):** its
`FIREWALL_DISABLED` and `DEFENDER_DISABLED` rules use
`control: 'firewall'` / `control: 'defender'`, but the actual
baseline/state object keys are `fw` / `def`. `baseline_value` /
`current_value` resolve to `undefined` and are silently dropped by
`JSON.stringify` for just those two rule types (DNS/RDP/SSH are
unaffected — their `control` names match). `to_alert()` in the new
script handles this defensively by omitting the field rather than
printing a misleading "None".

**Verification (2026-09-04):** Windows Firewall (Public profile) was
briefly disabled and immediately re-enabled (exposure window: a few
seconds, admin-run, single guarded command) to produce one real
detection:

```
Before: True → security-watch.js detects FIREWALL_DISABLED → alerts.json updated → After: True
```

Ran the pipeline twice against that one real alert:

| Run | Result |
|---|---|
| 1st | New issue created: **Issue #6** — `[CRITICAL] Firewall Disabled \| Risk 95`, assigned to KEVIN-NGUYENDAD |
| 2nd (same alert, still within 24h) | No new issue — Issue #6 updated: `Occurrences: 2`, `Last Seen` refreshed |

https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools/issues/6

Success criteria met: a real alert from security-watch.js created a
GitHub incident, and a repeat of the same real alert updated it instead
of duplicating it.

## Next Task

Not yet decided. Candidates from the "Not Yet Implemented" list:
labels automation, MCP analysis comments, WAAP integration.
