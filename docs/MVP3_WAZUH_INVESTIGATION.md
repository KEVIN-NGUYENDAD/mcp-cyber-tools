# MVP #3: Wazuh Investigation (pre-build findings)

Before writing any new integration code, the target `PROJECT_STATUS.md`
next-step diagram calls for:

```
Wazuh alerts.json
  |
  v
MCP
  |
  v
GitHub Issue
  |
  v
Assign KEVIN-NGUYENDAD
  |
  v
GitHub Mobile
```

This required first checking whether that first box (`Wazuh alerts.json`)
actually exists on this host. It does not. Findings below.

## Is Wazuh installed?

**No.** Checked on the Home-SOC Windows host (`C:\mcp-cyber-tools`, the
running Phase 1 deployment) and confirmed with:

- `Get-Service` — no service matching `wazuh` or `ossec`
- `C:\Program Files` / `C:\Program Files (x86)` — no `wazuh`/`ossec`
  install directories
- `C:\ossec-agent`, `C:\wazuh-agent` — do not exist
- `sc query WazuhSvc` — `1060: service does not exist`
- No listening ports for Wazuh manager (`1514`, `1515`, `55000`)
- No WSL distro installed (Wazuh manager doesn't run natively on
  Windows — only the agent does; a manager would need WSL, a Linux VM,
  or Docker)
- No Docker installed either, so no containerized manager

## Is alerts.json present?

Two files named `alerts.json` exist on the host, but **neither is
Wazuh's**:

| Path | Content | What it actually is |
|---|---|---|
| `C:\mcp-cyber-tools\reports\home-soc-state\alerts.json` | `{"alerts":[]}` | This project's own Home-SOC alert store — written by the ARP/network-collector + baseline-analyzer pipeline described in `home-soc-phase1-package\docs\ARCHITECTURE.md`, read by the `getAlerts` MCP tool in `home-soc-mcp-server.js` |
| `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\alerts.json` | `{"schema_version":"1.0","alerts":[],"updated_at":"2026-09-04T02:52:27.028Z","open_alert_count":0}` | Claude Desktop project-scope state file, same custom schema, unrelated to Wazuh |

Real Wazuh alert output is JSON-Lines (one alert object per line, each
with `rule`, `agent`, `data`, `full_log`, etc.) written by the **manager**
at `/var/ossec/logs/alerts/alerts.json` — a Linux path that doesn't exist
here at all, on a component (the manager) that isn't installed.

A repo-wide grep for `wazuh`/`ossec` across `C:\mcp-cyber-tools` turns up
exactly one incidental string match (in `ios-security-assessor.js`,
unrelated to this pipeline) — confirming no prior Wazuh wiring or stub
exists to build on.

## What actually exists today

The current alerting on this host comes entirely from the custom
Home-SOC stack (`network-collector.js` → `baseline-analyzer.js` →
`home-soc-state/*.json` → `home-soc-mcp-server.js`), plus the Windows
Defender path already proven in MVP #2. Neither of those is Wazuh.

## Conclusion

MVP #3 as scoped (`Wazuh alerts.json` as the input) cannot start from
"read the file" — the file, and the service that produces it, don't
exist yet. Standing up a real Wazuh manager (Linux VM/WSL/Docker) is a
new piece of infrastructure, not a config change, and is out of scope
for this verification pass per instruction ("do not write new
integrations yet").

No code changed in this pass — investigation only.

## Options for actually reaching MVP #3

1. Install a real Wazuh manager (Docker container is the fastest path
   on Windows) and point it at this host or a test agent, so
   `alerts.json` is genuinely produced by Wazuh — highest fidelity to
   the original architecture diagram, most setup work.
2. Re-scope MVP #3 to use the alert source that already exists and is
   real today — the Home-SOC `alerts.json` at
   `C:\mcp-cyber-tools\reports\home-soc-state\alerts.json` — following
   the exact MVP #2 pattern (reuse `score_alert`/`build_issue`/
   `create_issue`/`assign_issue`, add one new `to_alert()`-style mapper
   for this schema).
3. Defer Wazuh, pull forward Suricata `eve.json` from the "Not Yet
   Implemented" list instead — same problem: not installed either,
   would need the same verification pass first.

No option was chosen or implemented here; this is a decision for the
next MVP #3 planning step.
