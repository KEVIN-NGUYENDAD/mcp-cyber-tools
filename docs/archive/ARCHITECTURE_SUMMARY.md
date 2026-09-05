# ARCHITECTURE_SUMMARY.md

Compiled 2026-09-04. Sources: the `mcp-cyber-tools` repository (this
one, local), the `sentinelops-homepage` repository (local sibling
checkout), and five additional GitHub repositories under
`KEVIN-NGUYENDAD` fetched read-only for this pass (shallow-cloned into
a scratch directory, not merged into any working tree):
`home-soc-reports`, `network-security-audit-frontend`,
`cybersecurity-labs`, `kevin-cyber-security-copilot`,
`sentinelops-security-incidents`, plus the GitHub profile repo
`KEVIN-NGUYENDAD/KEVIN-NGUYENDAD`. Every statement below cites the
specific file it came from. Where a requested fact has no source in
these repositories, it is marked **Not documented** rather than
inferred. Full source list: §15.

## 1. Executive Summary

**What SentinelOps is:** a cybersecurity portfolio built around a
real, running toolchain rather than a static demo. Per
`sentinelops-homepage/PROJECT.md`, it is Kevin (Tam) Nguyen's
"Cybersecurity Portfolio," publicly presented at `sentinelops.fyi`
(`sentinelops-homepage/README.md`). Per
`mcp-cyber-tools/README.md`, the engine behind it is "a comprehensive
Model Context Protocol (MCP) server providing 90+ security analysis
tools for Windows incident response, threat hunting, and forensics."

**Primary mission:** per `sentinelops-homepage/PROJECT.md`, the stated
focus areas are SOC, DFIR, MCP, Home-SOC, and AI Security. The GitHub
profile repo (`KEVIN-NGUYENDAD/KEVIN-NGUYENDAD/README.md`) states the
same five areas plus "Security Automation," and self-describes as
"Cybersecurity Student | SOC | DFIR | AI Security."

**Current maturity/status:** per `mcp-cyber-tools/PROJECT_STATUS.md`,
a build milestone (MVP #1–#4) is **frozen as of 2026-09-04**: a live
alert pipeline (Windows Defender / `security-watch.js` → MCP → risk
scoring → GitHub Issue → labels/analysis comment → GitHub Mobile) is
built, verified against real events, and working. A parallel discovery
track (VNETWORK/WAAP integration research) is documentation-only and,
as of the most recent verification pass, **blocked on live API
access** (`mcp-cyber-tools/PROJECT_STATUS.md`, "WAAP Log Search —
Post-Onboarding Re-Verification"). The `sentinelops-security-incidents`
repository, seemingly intended as an incident-record destination,
exists but is **empty** (0 bytes, confirmed via `gh api
repos/KEVIN-NGUYENDAD/sentinelops-security-incidents` — size 0,
`created_at` == `pushed_at`) — the pipeline's actual, real incident
destination is `KEVIN-NGUYENDAD/mcp-cyber-tools`'s own Issues, per the
`REPO_OWNER`/`REPO_NAME` constants in
`mcp-cyber-tools/scripts/create_test_incident.py`.

**Key objectives**, per `mcp-cyber-tools/NEXT_STEPS.md`, in stated
priority order: (1) WAAP Log Search Integration, (2) Healthcheck
Webhook Receiver, (3) Digital Risk Twin (explicitly "a concept sketch
only" pending its own discovery pass).

## 2. Repository Inventory

Repo list and visibility confirmed via `gh repo list KEVIN-NGUYENDAD`
(2026-09-04).

| Name | Purpose | Status | Key technologies | Source references |
|---|---|---|---|---|
| **mcp-cyber-tools** | Windows SOC/DFIR MCP server (95 tools, see §5) plus the Home-SOC alert→GitHub-incident pipeline and the VNETWORK/WAAP discovery track | Private repo. MVP #1–#4 frozen/shipped; VNETWORK/WAAP work documentation-only and access-blocked | Node.js 18+ (ESM), `@modelcontextprotocol/sdk` `^1.30.0`, `zod`, Python 3 (incident scripts), PowerShell | `README.md`, `package.json`, `server.js`, `PROJECT_STATUS.md`, `NEXT_STEPS.md` |
| **sentinelops-homepage** | Public portfolio site at `sentinelops.fyi` | Public repo. Confirmed static — no server component | React 18, Vite 5, Tailwind CSS 3 | `sentinelops-homepage/README.md`, `PROJECT.md`, `package.json` |
| **home-soc-reports** | "Sanitized Home SOC status feed" — a one-way, sanitization-gated publication surface read by a scheduled task to generate a daily email bulletin | Public repo, actively updated (latest commit 2026-09-03, `BASELINE-LATEST.json` `generated_at` 2026-09-04T02:53:07Z) | Plain JSON/Markdown data files, written by `export-home-soc-reports.js` (that script lives in the private `mcp-cyber-tools` repo, per its own README, and was not found in this repo — see §11) | `home-soc-reports/README.md`, `BASELINE-LATEST.json`, `DEVICE-SUMMARY.json` |
| **sentinelops-security-incidents** | Unknown — no README, no commits, no files | Public repo, **empty** (`size: 0`, confirmed via `gh api`) | Not documented | `gh api repos/KEVIN-NGUYENDAD/sentinelops-security-incidents` |
| **kevin-cyber-security-copilot** | "AI-powered Cyber Security Assistant" — a Flask web app (Q&A, code review, SOC-analysis demo) calling the Groq API | Public repo. Deployed to Render per its own `render.yaml` | Python, Flask, Groq API (`llama-3.1-8b-instant`), Gunicorn | `kevin-cyber-security-copilot/README.md`, `agent.py`, `app.py`, `render.yaml`, `requirements.txt` |
| **cybersecurity-labs** | "Cybersecurity learning labs covering hashing, encryption, networking, validation and Python testing" (`gh repo list` description) — contains real lab modules (`hashing.py`, `encryption.py`, `network.py`, `validation.py`, `tests/`) **and** a near-duplicate copy of the `kevin-cyber-security-copilot` Flask/Groq app (`app.py`, `agent.py`) deployed as its own Render service | Public repo, deployed to Render (`render.yaml`: service name `cybersecurity-labs`) | Python, `pytest`, `cryptography`/`pycryptodome`, Flask, Groq API | `cybersecurity-labs/README.md`, `render.yaml`, `hashing.py`, `encryption.py`, `network.py`, `validation.py`, `agent.py`, `app.py`, `requirements.txt` |
| **network-security-audit-frontend** | "React UI - Network Security Scanner" (`gh repo list` description) — a Flask backend (port scan, password strength, WiFi security, network info) plus a React frontend, deployed as two separate Render services | Public repo | Backend: Python, Flask 2.3.2, Flask-CORS, `flask-limiter`, `psutil`, Gunicorn. Frontend: React 18.2.0, `react-scripts` 5.0.1 | `network-security-audit-frontend/README.md`, `network-security-audit/backend/app.py`, `security_scanner.py`, `requirements.txt`, `frontend/package.json` |
| **KEVIN-NGUYENDAD** (profile repo, discovered, not in the requested list) | GitHub profile README | Public repo, single file | Markdown only | `KEVIN-NGUYENDAD/README.md` |

**Repositories reviewed and excluded as not SentinelOps-related**
(found via `gh repo list`, confirmed off-topic by their own
descriptions, not deep-dived): `TheWall` (no description given — a
separate, unrelated project per the local filesystem, which also
contains an unrelated Godot game tree at `C:\Users\tamng\Projects\`),
`Sass-ai-app` ("AI-powered Pharmacy Assistant"), `uber-order-filter`
("Manual Decision Support System for Uber Drivers"), and
`AZ-Transportation-Laws-` (private, no description).

## 3. System Architecture

**Major components**, each already documented individually:

1. **`mcp-cyber-tools` MCP server** (`server.js`) — 95 read-only
   Windows analysis tools across 11 modules (§5).
2. **Home-SOC alert pipeline** (`security-watch.js` →
   `alerts.json` → `scripts/create_securitywatch_incident.py` →
   GitHub Issues in `KEVIN-NGUYENDAD/mcp-cyber-tools`) — built, live,
   verified (`PROJECT_STATUS.md`, §6/§7 below).
3. **Home-SOC publication pipeline** (`export-home-soc-reports.js`,
   in the private repo → `home-soc-reports` public repo → a Claude
   Scheduled Task → email) — a **separate, one-way, sanitized**
   export, distinct from #2 (`home-soc-reports/README.md`).
4. **VNETWORK/WAAP integration** (planned, not built) — a future
   `scripts/create_waap_incident.py` would feed the same GitHub
   pipeline as #2 (`WAAP_LOG_SEARCH_SCHEMA.md` §6). Currently blocked
   on live API access (§9, §11).
5. **`sentinelops-homepage`** — the public portfolio site; a static
   consumer of the ecosystem's story, not a live integration point.
6. **Standalone demo apps** (`kevin-cyber-security-copilot`,
   `cybersecurity-labs`, `network-security-audit-frontend`) — each an
   independently deployed Render app, not wired into the MCP server or
   the GitHub-incident pipeline. **Not documented** as sharing any
   runtime dependency with components #1–#4.

**Relationships between components:** #2 and #3 both originate from
data produced on the same Windows host but are architecturally
**separate pipelines with separate destinations** — #2 writes to
GitHub Issues (incident-shaped, un-sanitized, private-repo-adjacent
since the issues live in the private `mcp-cyber-tools` repo's issue
tracker), #3 writes to a public repo through an explicit "leak
guard" gate (`home-soc-reports/README.md`). Nothing in the reviewed
sources merges these two pipelines.

**Data flows:** see the diagram below and §6/§7.

**Trust boundaries**, as documented:
- Between the private `mcp-cyber-tools` repo (raw data, tooling,
  credentials) and the public `home-soc-reports` repo (sanitized
  output only) — enforced by the "leak guard" regex sweep described in
  `home-soc-reports/README.md`, which aborts the export rather than
  redacting on a match.
- Between `openapi.vnetwork.vn`'s Bearer token (account-wide, unscoped
  — `VNETWORK_CAPABILITY_ASSESSMENT.md`) and everything that token can
  reach — a single leaked key is a full-account compromise, a finding
  from that same doc, and one realized in practice during this
  project's own WAAP verification work (`WAAP_LOG_SEARCH_SCHEMA.md`
  §7: a token was briefly exposed and was rotated in response).
- Object Storage (OSS) uses a **separate credential model** (Access
  Key/Secret) from the rest of the VNETWORK API surface
  (`VNETWORK_PRODUCT_DISCOVERY.md`).

**External dependencies:** GitHub (issue tracking, both repos and the
API), VNETWORK `openapi.vnetwork.vn` (planned WAAP integration), Groq
API (the two Flask copilot demo apps), Render (hosting for
`audit.sentinelops.fyi`'s backend — source repo **Not documented**
per `PROJECT_STATUS.md` — and for the three standalone demo apps),
Claude Desktop / a Claude Scheduled Task (both the MCP server host and
the daily Home-SOC bulletin trigger).

### ASCII architecture diagram

```
┌───────────────────────────── Windows host ─────────────────────────────┐
│                                                                          │
│  Windows Defender ──┐                                                   │
│  security-watch.js ─┴─→ alerts.json ──→ scripts/                        │
│  (Task Scheduler:                       create_securitywatch_incident.py│
│   HOME-SOC-Scan-                              │                         │
│   And-Export)                                 ▼                         │
│                                    score_alert / build_issue /          │
│                                    24h duplicate detection /            │
│                                    compute_labels /                     │
│                                    build_analysis_comment               │
│                                                │                        │
│  [mcp-cyber-tools MCP server: server.js]      │                        │
│  95 read-only tools, 11 modules                │                        │
│  (Claude Desktop client, stdio)                │                        │
│                                                 ▼                        │
└─────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                          GitHub Issues — KEVIN-NGUYENDAD/mcp-cyber-tools
                          (labels, MCP analysis comment, assignee)
                                                  │
                                                  ▼
                                          GitHub Mobile → phone


┌── separate export pipeline (documented in home-soc-reports/README.md) ──┐
│                                                                          │
│  network-scan-data/*.json, laptop-collection-data/*.json,               │
│  baseline/BASELINE-*.json, state.json/baseline.json                     │
│  (all in the private mcp-cyber-tools repo)                              │
│                     │                                                   │
│                     ▼                                                   │
│         export-home-soc-reports.js  (script itself: location            │
│                     │                 not found in either repo          │
│                     │                 reviewed — see §11)               │
│         classify → derive risk → LEAK GUARD (abort on any match)        │
│                     │                                                   │
└─────────────────────┼────────────────────────────────────────────────────┘
                       ▼
      PUBLIC repo: home-soc-reports
      (ROUTER-SECURITY-AUDIT-LATEST.md, BASELINE-LATEST.json,
       DEVICE-SUMMARY.json — always overwritten, never appended)
                       │
                       ▼
         Claude Scheduled Task, daily 20:10
         (fetches the 3 raw.githubusercontent.com URLs)
                       │
                       ▼
              🏠 Home Security Bulletin → Email


┌── planned, not built (WAAP_LOG_SEARCH_SCHEMA.md §6; blocked, §9/§11) ───┐
│  VNETWORK openapi.vnetwork.vn — POST /v1/bsearch                        │
│  (Bearer token; access currently denied — see §9)                       │
│                     │ (planned)                                         │
│                     ▼                                                   │
│  scripts/create_waap_incident.py → same GitHub-Issue chain above        │
└───────────────────────────────────────────────────────────────────────┘


  Public site: sentinelops.fyi (sentinelops-homepage repo, static
  React/Vite, no server) — links to audit.sentinelops.fyi, whose own
  backend source repo is Not documented (PROJECT_STATUS.md).

  Standalone, independently deployed demo apps (no documented
  integration with the above): kevin-cyber-security-copilot.onrender.com,
  cybersecurity-labs.onrender.com, network-security-audit-frontend
  (+ -backend).onrender.com.
```

## 4. Infrastructure

| Item | Status | Source |
|---|---|---|
| `sentinelops.fyi` | Confirmed static (Vite/React, no server) | `mcp-cyber-tools/PROJECT_STATUS.md` |
| `audit.sentinelops.fyi` | Confirmed real and live, CNAME'd to VNETWORK's CDN with a Render origin behind it; source repo/service running there **Not documented** — not found in any repository reviewed | `mcp-cyber-tools/PROJECT_STATUS.md` |
| `www.sentinelops.fyi` | WAAP onboarding completed by Kevin in the VNETWORK Partner Portal, Service ID `95743`; API-level access not yet confirmed working (§9) | `mcp-cyber-tools/PROJECT_STATUS.md` |
| DNS provider(s) for any domain | Not documented | — |
| Render services (named, confirmed) | `kevin-cyber-security-copilot` (web), `cybersecurity-labs` (web), `network-security-audit-api`/`network-security-audit` (per `DEPLOYMENT.md`, though its live-URL section instead names `network-security-audit-frontend`/`-backend`, an inconsistency in that repo's own docs, not resolved here) | `kevin-cyber-security-copilot/render.yaml`, `cybersecurity-labs/render.yaml`, `network-security-audit-frontend/README.md` + `DEPLOYMENT.md` |
| Render service behind `audit.sentinelops.fyi` | Not documented | `mcp-cyber-tools/PROJECT_STATUS.md` (explicitly states it "was not found anywhere on this machine") |
| External platforms | GitHub (issue tracking + hosting all repos), Render (app hosting), Groq (LLM API for the two copilot demo apps), VNETWORK (planned WAAP integration) | See repo-specific citations above |
| Hosting providers | Render (confirmed for 3 demo apps); `audit.sentinelops.fyi`'s host is Render per DNS/HTTP inspection but the specific service is unidentified | `PROJECT_STATUS.md`; `render.yaml` files |
| Security platforms | VNETWORK (Compute, CDN, WAAP, Object Storage — see §10); Windows Defender (host-level, `mcp-cyber-tools/modules/defender.js`) | `VNETWORK_PRODUCT_DISCOVERY.md`; `modules/defender.js` |
| Monitoring systems | VNETWORK Healthcheck & Alerting (beta; console-only, no REST API documented) | `VNETWORK_PRODUCT_DISCOVERY.md` |

## 5. MCP Architecture

**Server design:** `server.js` (`mcp-cyber-tools/server.js`) is the
active entry point (`package.json`: `"main": "server.js"`), built on
`@modelcontextprotocol/sdk`'s `McpServer` over
`StdioServerTransport`, server metadata `{name: "cyber-tools",
version: "1.0.0"}`. It imports and calls 11 `register*Tools(server)`
functions from `modules/`, one per phase-grouped file
(`server.js`).

**`server_v2.js` and `server_backup_v1.js`:** confirmed **byte-for-
byte identical** to each other (`diff` produced no output), each a
separate, 410-line, single-file, monolithic MCP server (not using the
`modules/` pattern) registering 12 tools (`readLogFile`, `checkHash`,
`scanPort`, `nslookup`, `ping`, `tracert`, `ipconfig`, `netstat`,
`tasklist`, `servicesChecker`, `eventLogs`, `processMonitor`) — a
strict subset, by name, of tools also present in the modular
`server.js`. Neither file is referenced by `package.json`'s `main`
field or by the example Claude Desktop config
(`claude_desktop_config.json.example`, which points at `server.js`).
**Not documented:** why both files exist or which one (if either) is
still in active use — no README or comment in either file explains
their relationship to `server.js`.

**Tool categories and counts** (verified by parsing every
`server.tool(...)` call in each module file, not by trusting the
README's prose count):

| Module | Registered tools (counted) | README's stated count |
|---|---|---|
| `host.js` | 10 | 10 |
| `network.js` | 10 | 10 |
| `process.js` | 10 | 10 |
| `services.js` | 5 | 5 |
| `eventlogs.js` | 10 | 10 |
| `firewall.js` | 5 | 5 |
| `defender.js` | 5 | 5 |
| `persistence.js` | 10 | 10 |
| `forensics.js` | 10 | 10 |
| `hunting.js` | 10 | 10 |
| `incident.js` | 10 | 10 |
| **Total** | **95** | "90+" |

Counted total (95) is consistent with the README's "90+" claim.
Source: direct parse of `modules/*.js` in this session.

**Inputs and outputs:** every tool follows the same shape (verified in
`modules/host.js` and consistent with `README.md`'s example module):
a `zod` input schema (often `{}` for no-argument tools), an `async`
handler that runs a PowerShell command via `runPowerShell()`
(`modules/shared.js`), and a response built by `formatResponse()`
(`modules/shared.js`) — i.e. structured PowerShell-backed system
introspection, not external network calls (with the sole planned
exception of the not-yet-built `vnetworkWaapSearch` tool, §9).

**Current capabilities:** all 95 tools above — host/user enumeration,
network/process/service inspection, event-log queries, firewall/
Defender status, persistence and forensic artifact checks, threat-
hunting heuristics (encoded PowerShell, LOLBins, credential dumping
indicators, etc.), and incident-response evidence collection/timeline/
audit-report generation (`README.md` Tool Categories section;
`modules/incident.js`).

**Planned capabilities:** one new tool, `vnetworkWaapSearch`, plus a
new script `scripts/create_waap_incident.py` — both design-only, not
implemented (`WAAP_LOG_SEARCH_SCHEMA.md` §6).

### Full MCP tool table (95 tools, extracted directly from `modules/*.js`)

| Module | Tool | Description (as registered) |
|---|---|---|
| host.js | `whoami` | Get current user identity |
| host.js | `hostname` | Get computer hostname |
| host.js | `systemInfo` | Get detailed system information |
| host.js | `localUsers` | List all local user accounts |
| host.js | `localAdmins` | List all local administrators |
| host.js | `installedSoftware` | List installed software |
| host.js | `sharedFolders` | List shared network resources |
| host.js | `environmentVars` | Get environment variables |
| host.js | `userProfiles` | List all user profiles on system |
| host.js | `loggedOnUsers` | Get currently logged on users |
| network.js | `ipconfig` | Display network configuration |
| network.js | `netstat` | Display network connections and statistics |
| network.js | `arp` | Display ARP cache |
| network.js | `routePrint` | Display routing table |
| network.js | `dnsCache` | Display DNS resolver cache |
| network.js | `ping` | Ping a host |
| network.js | `tracert` | Trace route to host |
| network.js | `nslookup` | DNS lookup |
| network.js | `scanPort` | Check if TCP port is open |
| network.js | `activeConnections` | Get active network connections with process info |
| process.js | `tasklist` | List all running processes |
| process.js | `processMonitor` | Monitor process metrics |
| process.js | `processDetails` | Get detailed info for a specific process |
| process.js | `processTree` | Display process tree (parent-child relationships) |
| process.js | `processByPid` | Get process info by PID |
| process.js | `runningProcesses` | Get summary of running processes |
| process.js | `cpuUsage` | Get CPU usage by process |
| process.js | `memoryUsage` | Get memory usage by process |
| process.js | `topProcesses` | Get top processes by various metrics |
| process.js | `suspiciousProcesses` | Find potentially suspicious processes |
| services.js | `servicesChecker` | List all services |
| services.js | `runningServices` | List running services only |
| services.js | `stoppedServices` | List stopped services |
| services.js | `autoStartServices` | List services set to autostart |
| services.js | `disabledServices` | List disabled services |
| eventlogs.js | `eventLogs` | Get recent Event Logs |
| eventlogs.js | `securityLogs` | Get Security Event Logs |
| eventlogs.js | `systemLogs` | Get System Event Logs |
| eventlogs.js | `applicationLogs` | Get Application Event Logs |
| eventlogs.js | `failedLogons` | Get failed login attempts |
| eventlogs.js | `successfulLogons` | Get successful login events |
| eventlogs.js | `powershellLogs` | Get PowerShell event logs |
| eventlogs.js | `rdpLogs` | Get RDP connection logs |
| eventlogs.js | `usbLogs` | Get USB device connection logs |
| eventlogs.js | `serviceLogs` | Get service start/stop logs |
| firewall.js | `firewallStatus` | Get Windows Firewall status |
| firewall.js | `firewallRules` | List firewall rules |
| firewall.js | `inboundRules` | List inbound firewall rules |
| firewall.js | `outboundRules` | List outbound firewall rules |
| firewall.js | `disabledFirewallRules` | List disabled firewall rules |
| defender.js | `defenderStatus` | Get Windows Defender status |
| defender.js | `defenderThreats` | Get detected threats |
| defender.js | `defenderHistory` | Get Defender scan history |
| defender.js | `defenderExclusions` | List Defender exclusions |
| defender.js | `defenderQuickScan` | Get Defender quick scan info |
| persistence.js | `startupPrograms` | List startup programs |
| persistence.js | `startupFolders` | List files in startup folders |
| persistence.js | `scheduledTasks` | List scheduled tasks |
| persistence.js | `registryRunKeys` | List Registry Run keys |
| persistence.js | `registryRunOnce` | List Registry RunOnce keys |
| persistence.js | `wmiPersistence` | Check WMI persistence mechanisms |
| persistence.js | `servicePersistence` | Check service persistence |
| persistence.js | `browserPersistence` | Check browser extensions and plugins |
| persistence.js | `dllHijackLocations` | List potential DLL hijacking locations |
| persistence.js | `persistenceAudit` | Audit all persistence mechanisms |
| forensics.js | `checkHash` | Calculate SHA256 hash of file |
| forensics.js | `readLogFile` | Read content of log file |
| forensics.js | `fileMetadata` | Get file metadata (timestamps, size, permissions) |
| forensics.js | `recentFiles` | Get recently accessed files |
| forensics.js | `downloadsFolder` | List files in Downloads folder |
| forensics.js | `desktopFiles` | List files on Desktop |
| forensics.js | `tempFiles` | List files in TEMP directory |
| forensics.js | `recycleBin` | List files in Recycle Bin |
| forensics.js | `alternateDataStreams` | Find alternate data streams (ADS) |
| forensics.js | `suspiciousExecutables` | Find potentially suspicious executables |
| hunting.js | `huntEncodedPowerShell` | Hunt for encoded PowerShell commands |
| hunting.js | `huntPersistence` | Hunt for persistence mechanisms |
| hunting.js | `huntSuspiciousServices` | Hunt for suspicious services |
| hunting.js | `huntSuspiciousTasks` | Hunt for suspicious scheduled tasks |
| hunting.js | `huntCredentialDumping` | Hunt for credential dumping attempts |
| hunting.js | `huntLateralMovement` | Hunt for lateral movement indicators |
| hunting.js | `huntRemoteDesktop` | Hunt for RDP activity and anomalies |
| hunting.js | `huntNetworkBeacons` | Hunt for network beacon indicators |
| hunting.js | `huntLivingOffTheLand` | Hunt for Living off the Land Binaries (LOLBins) |
| hunting.js | `huntIndicators` | Hunt for various IOCs (Indicators of Compromise) |
| incident.js | `collectEvidence` | Collect forensic evidence for incident |
| incident.js | `collectProcesses` | Collect all running processes snapshot |
| incident.js | `collectServices` | Collect all services snapshot |
| incident.js | `collectNetworkState` | Collect network connections snapshot |
| incident.js | `collectStartupItems` | Collect startup items and persistence mechanisms |
| incident.js | `collectFirewall` | Collect firewall configuration |
| incident.js | `collectDefender` | Collect Windows Defender status and threats |
| incident.js | `collectLogs` | Collect relevant event logs |
| incident.js | `timeline` | Generate incident timeline |
| incident.js | `securityAudit` | Generate comprehensive security audit report |

## 6. Home SOC Architecture

Two distinct, separately-documented pipelines share the "Home SOC"
name — treated separately per the evidence (see §3's diagram):

**A. The alert → GitHub-incident pipeline** (`PROJECT_STATUS.md`,
"Home-SOC Source Discovery" and "MVP #3" sections):

- **Data sources considered:** `security-watch.js` → `alerts.json`
  (chosen — "real, actively scheduled ... clean alert schema"),
  Windows Defender (already integrated, MVP #2), Windows Event Logs
  (ruled out — "no process-creation telemetry without an auditpol
  change"), a second dormant Home-SOC implementation at
  `C:\mcp-cyber-tools\reports\home-soc-state` (inactive since
  2026-08-29), Wazuh and Suricata (both ruled out — not installed,
  `MVP3_WAZUH_INVESTIGATION.md`).
- **Alert source, confirmed live:** `security-watch.js`'s
  `alerts.json`, produced by a Windows Task Scheduler job
  (`HOME-SOC-Scan-And-Export`).
- **Telemetry flow / detection workflow:** `alerts.json` →
  `scripts/create_securitywatch_incident.py`'s `to_alert()` mapper →
  `score_alert()` (risk scoring) → 24-hour duplicate detection
  (GitHub issue title + "Last Seen" timestamp, no separate state
  file) → either `create_issue()` (new) or `update_issue_body()`
  (duplicate, increments `Occurrences`) → `compute_labels()` (subset
  of `critical`/`high`/`defender`/`control-drift`/`firewall`) →
  `build_analysis_comment()` (Risk Score/Reason/Recommendation, from
  an `ENRICHMENT_RULES` table covering 5 known alert types) →
  `assign_issue()` (`KEVIN-NGUYENDAD`) → GitHub Mobile.
- **Report generation:** none in this pipeline — the GitHub Issue
  itself is the report artifact.
- **Verified live** (`PROJECT_STATUS.md`): a real, briefly-toggled
  Windows Firewall event produced Issue #6; a repeat within 24h
  updated it (`Occurrences: 2`, then `3` after MVP #4) instead of
  duplicating.
- **Known bug, not fixed (documented, out of scope):**
  `security-watch.js`'s `FIREWALL_DISABLED`/`DEFENDER_DISABLED` rules
  reference control keys `firewall`/`defender` that don't match the
  actual baseline/state object's `fw`/`def` keys, silently dropping
  two fields (`PROJECT_STATUS.md`, MVP #3 section).

**B. The sanitized publication pipeline** (`home-soc-reports/README.md`):

- **Data sources:** `network-scan-data/network-scan-*.json`,
  `laptop-collection-data/*.json`, `baseline/BASELINE-*.json`, and
  optionally `state.json`/`baseline.json` — all described as living in
  the private `mcp-cyber-tools` repo, per that README; **not found**
  in this session's local checkout of `mcp-cyber-tools` (see §11).
- **Processing:** `export-home-soc-reports.js` — classifies addresses
  into non-identifying labels (MAC → device id, vendor/model/firmware
  → discarded, port → service class), derives alerts and a
  GREEN/YELLOW/RED risk level, then runs a **leak-guard regex sweep**
  (MAC, IPv4/IPv6, credential keywords, private-key blocks, vendor
  names, SSID) over the exact output bytes — "any hit → abort, write
  nothing, push nothing" (`home-soc-reports/README.md`). This script
  itself was likewise **not found** in the local `mcp-cyber-tools`
  checkout (§11).
- **Output, confirmed live:** `ROUTER-SECURITY-AUDIT-LATEST.md`,
  `BASELINE-LATEST.json`, `DEVICE-SUMMARY.json` — always overwritten,
  never appended. Latest data (`BASELINE-LATEST.json`,
  `generated_at: 2026-09-04T02:53:07.000Z`): `risk_level: "GREEN"`,
  0 alerts, 6/6 controls reported and unchanged from baseline;
  (`DEVICE-SUMMARY.json`): 3 devices, all identified, 0 total risks.
- **Consumer:** a Claude Scheduled Task, daily at 20:10, fetching the
  three files via `raw.githubusercontent.com` and producing a "🏠 Home
  Security Bulletin" email.
- **Freshness contract:** if the newest timestamp is more than 48
  hours old, the bulletin must report stale data rather than presenting
  it as current (`home-soc-reports/README.md`).

**Integration with MCP and SentinelOps:** Pipeline A is triggered by
data the MCP server's own host produces and lands in the same private
repo the MCP server lives in (`mcp-cyber-tools`), but the MCP tools
themselves (§5) are read-only introspection tools, separate from the
Python incident scripts that do the actual GitHub posting — **not
documented** as being invoked through the MCP protocol itself (the
scripts are standalone, run directly, per their own `argparse`-based
`main()` functions). Pipeline B explicitly states it "is not edited by
hand" and is generated entirely by `export-home-soc-reports.js`
(`home-soc-reports/README.md`).

## 7. Incident Management Architecture

**Incident creation flow** (per `mcp-cyber-tools/PROJECT_STATUS.md`
and direct inspection of `scripts/*.py`):

```
alert (source-specific) → to_alert() mapper → score_alert()
   → build_issue() → github_request() → create_issue() → assign_issue()
```

For a repeat alert within 24h: `find_open_issues()` →
`find_duplicate()` → `update_issue_body()` (via `parse_tracking()` /
`with_tracking_block()`) instead of `create_issue()`, then
`compute_labels()` / `add_labels()` and `build_analysis_comment()` /
`add_comment()` run on both the new-issue and duplicate-update paths
(`scripts/create_securitywatch_incident.py`, confirmed by direct
function listing).

**Incident repositories:** issues are created against
`KEVIN-NGUYENDAD/mcp-cyber-tools` — confirmed by the hardcoded
constants `REPO_OWNER = "KEVIN-NGUYENDAD"`, `REPO_NAME =
"mcp-cyber-tools"`, `ASSIGNEE = "KEVIN-NGUYENDAD"` in
`scripts/create_test_incident.py`, used unchanged by the other two
scripts. The separate `sentinelops-security-incidents` repository is
**not referenced by any script reviewed** and is empty (§1, §2) —
whether it is an intended future destination is **Not documented**.

**Automation scripts, discovered and confirmed present:**

| Script | Present? | Role |
|---|---|---|
| `scripts/create_test_incident.py` | Yes | Original/base script — defines `score_alert`, `build_issue`, `github_request`, `create_issue`, `assign_issue`, the `REPO_OWNER`/`REPO_NAME`/`ASSIGNEE` constants |
| `scripts/create_defender_incident.py` | Yes | Windows Defender alert source (MVP #2), same reuse pattern |
| `scripts/create_securitywatch_incident.py` | Yes | `security-watch.js` alert source (MVP #3/#4) — adds `to_alert()`, 24h duplicate detection, `compute_labels()`, `build_analysis_comment()` |
| `scripts/create_waap_incident.py` | **No — not present** | Planned only, per `WAAP_LOG_SEARCH_SCHEMA.md` §6; confirmed absent by directory listing of `scripts/` in this session |

**GitHub integration mechanics:** all three existing scripts
authenticate via a `GITHUB_TOKEN` environment variable (checked with
`os.environ.get("GITHUB_TOKEN")`, with a guarded error message
pointing to `$env:GITHUB_TOKEN = "ghp_xxx"` / `export
GITHUB_TOKEN=ghp_xxx` if missing) and call the GitHub REST API
directly via `github_request()` — no GitHub SDK/library dependency
documented.

**Alert-to-incident workflow:** see §6.A above — identical for every
source integrated so far (Defender, `security-watch.js`) and the same
shape planned for WAAP (`WAAP_LOG_SEARCH_SCHEMA.md` §6:
`to_alert()` → `score_alert` → `build_issue` → `create_issue` →
`assign_issue` → `compute_labels` → `build_analysis_comment` →
duplicate-detection chain, "unchanged").

## 8. Security Telemetry Sources

| Source | Status | Integration level | Evidence | Limitations |
|---|---|---|---|---|
| Microsoft Defender | Live, integrated (MVP #2) | Full — `modules/defender.js` (5 MCP tools) plus `scripts/create_defender_incident.py` feeding the GitHub pipeline | `PROJECT_STATUS.md` "Completed" list; `modules/defender.js` | Not documented beyond the 5 tools listed in §5 |
| `security-watch.js` (endpoint control watcher: firewall, Defender, DNS, RDP, SSH) | Live, integrated (MVP #3/#4), verified against a real event | Full — feeds `scripts/create_securitywatch_incident.py` | `PROJECT_STATUS.md`, Issue #6 verification | One confirmed bug (control-key mismatch, §6); the tool itself was not found in either repo reviewed this session — its output (`alerts.json`) was, but its source was not |
| WAAP (`POST /v1/bsearch` on `openapi.vnetwork.vn`) | Schema/plan complete; **live API access currently denied** | None yet — design-only (`vnetworkWaapSearch`, `scripts/create_waap_incident.py`, neither built) | `WAAP_LOG_SEARCH_SCHEMA.md` §1–§8 | 403/404/401 across Compute/CDN/WAAP even after WAAP onboarding — see §9, §11 |
| VNETWORK (general, `openapi.vnetwork.vn`) | Documented (106 endpoints catalogued), **not integrated**, current token denied for Compute/CDN too | None | `VNETWORK_API_DISCOVERY.md` | No native alert/webhook endpoint exists anywhere in this API — polling/diffing is the only shape (`VNETWORK_API_DISCOVERY.md`) |
| VNETWORK Healthcheck & Alerting | Documented (beta product, real native webhooks) | None — **no REST API exists to integrate against** | `VNETWORK_PRODUCT_DISCOVERY.md`; plan doc `MVP5_WEBHOOK_RECEIVER_PLAN.md` | Console/Partner-Portal only; HMAC algorithm/signing base/payload schema all undocumented anywhere published |
| Windows Event Logs | Reviewed as a candidate, **not chosen** for the alert pipeline | None for alerting; used read-only via `modules/eventlogs.js` (10 MCP tools) | `PROJECT_STATUS.md`, "Home-SOC Source Discovery" | "No process-creation telemetry without an auditpol change (out of scope)" |
| Network Monitoring (this repo's `modules/network.js`) | Live, read-only MCP tools only | 10 MCP tools, not wired into any alert pipeline | `modules/network.js` (§5 table) | Not an alert source — introspection only |
| Wazuh | Investigated, **ruled out** | None — not installed | `MVP3_WAZUH_INVESTIGATION.md` | "No Wazuh installation found... Do not build Wazuh integrations" |
| Suricata | Investigated, **ruled out** | None — not installed | `PROJECT_STATUS.md` | Same as above |
| A second, dormant Home-SOC implementation (`C:\mcp-cyber-tools\reports\home-soc-state`) | Discovered, **not chosen**, inactive | None | `PROJECT_STATUS.md`, "Home-SOC Source Discovery" | Dormant since 2026-08-29 |

## 9. WAAP Discovery Findings

Full detail: `WAAP_LOG_SEARCH_SCHEMA.md` (8 sections),
`VNETWORK_API_DISCOVERY.md`, `VNETWORK_PRODUCT_DISCOVERY.md`,
`VNETWORK_CAPABILITY_ASSESSMENT.md`.

**Discovery work completed:** four passes, all in
`mcp-cyber-tools/docs/` and cross-referenced from `PROJECT_STATUS.md`:
(1) full 106-endpoint OpenAPI catalog and ROI ranking
(`VNETWORK_API_DISCOVERY.md`), (2) product-level discovery confirming
Healthcheck/WAAP/Object Storage exist as separate products
(`VNETWORK_PRODUCT_DISCOVERY.md`), (3) a 17-category capability
assessment built from public docs after Partner Portal access proved
unavailable (`VNETWORK_CAPABILITY_ASSESSMENT.md`), (4) a
schema-and-payload-level deep dive plus live verification
(`WAAP_LOG_SEARCH_SCHEMA.md`).

**Confirmed findings — the endpoint itself:** `POST
https://openapi.vnetwork.vn/v1/bsearch`, Bearer-token auth, the only
read-only log/analytics surface in the whole 106-endpoint API
(`VNETWORK_API_DISCOVERY.md`). Full request/response schema and
verbatim sample payloads captured (`WAAP_LOG_SEARCH_SCHEMA.md` §3,
§5). The 5 originally-requested fields — source IP
(`http_x_forwarded_for`), URI (`uri.keyword`), status code (`status`/
`upstream_status`), user agent (`http_user_agent`), and attack
indicators (`mitigation_result`, undocumented in prose but present in
the request template) — are all identified at the documentation level
(`WAAP_LOG_SEARCH_SCHEMA.md` §1, §4).

**API test results (live verification, §7–§8 of the schema doc):**
three read-only calls, reproduced twice (before and after a token
rotation, and again after WAAP onboarding):

| Check | Result | Changed after onboarding `www.sentinelops.fyi` (Service ID 95743)? |
|---|---|---|
| `GET /v3/instances` (Compute) | `403 Service.AccessDenied` | No |
| `GET /v3/cdn/domains` (CDN) | `404 Service.NotFound` | No |
| `POST /v1/bsearch` (WAAP) | `401 Request.Unauthorized` | No |

**Entitlements:** the token authenticates (structured, service-
specific errors, not a uniform failure) but this account currently has
no live, working access to WAAP, CDN, or Compute from this token, even
after WAAP onboarding was completed in the console
(`WAAP_LOG_SEARCH_SCHEMA.md` §8). Four unconfirmed explanations are
recorded (propagation delay, onboarding incomplete beyond "Domain &
Origin," a domain-string mismatch, or an account/token scope
mismatch) — none resolved as of this pass.

**Schema work:** complete and verbatim — request schema, response
envelope (both success and error shapes), and a documented
contradiction (docs table says `domains` is mandatory; the request
template says it defaults to all domains if omitted) — flagged, not
resolved (`WAAP_LOG_SEARCH_SCHEMA.md` §3).

**Log search research:** the `mitigation_result` field (attack
indicator) has exactly one confirmed value, `"ACL-WHITE"`; no other
value, and no separate "attack type"/"rule ID"/"CVE" field, is
documented anywhere (`WAAP_LOG_SEARCH_SCHEMA.md` §4).

**Current blockers:** see §11 (consolidated across all sections).

## 10. UNETWORK (VNETWORK) Discovery Findings

*(The task instruction spells this "UNETWORK"; the vendor's actual
name throughout every source document reviewed is **VNETWORK** —
reported under the vendor's documented name, not a variant spelling
introduced by this project.)*

**Product discovery:** four products confirmed to exist:
**Compute/Storage/Network/Security/Monitoring/CDN/WAAP** (all under
one unified `openapi.vnetwork.vn` REST API, 106 endpoints,
Bearer-token auth — `VNETWORK_API_DISCOVERY.md`), **Healthcheck &
Alerting** (beta; console-only, no REST API — `VNETWORK_PRODUCT_DISCOVERY.md`),
**Object Storage** (S3-compatible, separate Access Key/Secret
credential, no VNETWORK-specific REST API —
`VNETWORK_PRODUCT_DISCOVERY.md`), and **Multi-CDN Orchestration**
(confirmed rich metrics API via the same `openapi.vnetwork.vn`
surface — `VNETWORK_CAPABILITY_ASSESSMENT.md`).

**API discovery:** 106 total endpoints — 39 read-only (37 `GET` + the
1 read-only `POST /v1/bsearch` query), 67 mutating (excluded from
ROI ranking). No "Projects" category exists as an API resource — it
is an Organizations-console concept only. No native alert/webhook
endpoint exists anywhere in this API
(`VNETWORK_API_DISCOVERY.md`).

**Capability assessment:** 18 services assessed across 17 requested
categories, each fact marked `CONFIRMED (docs)` or `NOT DOCUMENTED`
(`VNETWORK_CAPABILITY_ASSESSMENT.md`). Notable confirmed findings:
API keys are account-wide and unscoped with no documented rotation or
usage-audit API (a finding this project's own WAAP verification work
later realized in practice, §9); Kubernetes, Databases, Container
Registry, Serverless Functions, and Usage & Cost Management are each
either "coming soon"/early-access or use a non-Bearer-token
integration shape (e.g. `kubectl`), so none are buildable today.

**Current status:** documentation and schema work is complete; live
integration is blocked (§9, §11). No VNETWORK API endpoint has been
called for any purpose other than the specific read-only verification
calls logged in `WAAP_LOG_SEARCH_SCHEMA.md` §7–§8.

**Open questions:** the four unconfirmed explanations in §9's
entitlement table; whether `{{URL}}` (an unresolved template variable
on the 3 "CDN > Domains" endpoints in VNETWORK's own published Postman
collection, versus the hardcoded `openapi.vnetwork.vn` host on the
other 103 endpoints) is a routing bug or simply an unpublished
environment variable (`WAAP_LOG_SEARCH_SCHEMA.md` §7.1); whether
`mitigation_result` and the once-seen `mitigate_result` are the same
field (`WAAP_LOG_SEARCH_SCHEMA.md` §4).

## 11. Current Confirmed Blockers

Only blockers with direct evidence in the reviewed repositories are
listed.

| Blocker | Impact | Evidence | Source files |
|---|---|---|---|
| WAAP API access not live despite completed onboarding | Cannot build/verify the WAAP integration (§9) against real data | Identical `403`/`404`/`401` before and after onboarding `www.sentinelops.fyi` | `WAAP_LOG_SEARCH_SCHEMA.md` §7–§8, `PROJECT_STATUS.md` |
| `GET /v3/cdn/domains` unusable to enumerate authorized domains | Cannot programmatically determine which domain(s) this account can query | `404 Service.NotFound`, traced to an unresolved `{{URL}}` template variable in VNETWORK's own published Postman collection (3 of 106 endpoints affected) | `WAAP_LOG_SEARCH_SCHEMA.md` §7.1 |
| Alert-worthy threshold for WAAP integration undecided | Cannot finalize `scripts/create_waap_incident.py`'s thresholding logic | Three candidate shapes recorded, none chosen | `NEXT_STEPS.md`, `WAAP_LOG_SEARCH_SCHEMA.md` §6 |
| `mitigation_result` vs `mitigate_result` field-name ambiguity | Cannot trust attack-indicator filtering/exclusion logic until resolved | Both names appear once each in the same request template, never both confirmed live | `WAAP_LOG_SEARCH_SCHEMA.md` §4 |
| Healthcheck Webhook Receiver — HMAC spec undocumented | Cannot implement signature verification safely | "The HMAC algorithm, the signing base, and the payload schema" are confirmed absent from VNETWORK's published docs | `MVP5_WEBHOOK_RECEIVER_PLAN.md`, `NEXT_STEPS.md` |
| Healthcheck Webhook Receiver — deployment target unknown | Cannot decide "add a route" vs. "stand up a new service" | Source repo/Render service behind `audit.sentinelops.fyi` "was not found anywhere on this machine" | `PROJECT_STATUS.md`, `NEXT_STEPS.md` |
| Digital Risk Twin has had no discovery pass | Cannot scope or plan; depends on the two blockers above being resolved first | Explicitly stated "unlike #1 and #2, this has not gone through a discovery pass" | `NEXT_STEPS.md` |
| `security-watch.js` control-key bug | `FIREWALL_DISABLED`/`DEFENDER_DISABLED` alerts silently drop `baseline_value`/`current_value` | Confirmed root cause (key mismatch `firewall`/`defender` vs. `fw`/`def`), explicitly "not fixed, out of scope" | `PROJECT_STATUS.md`, MVP #3 section |
| `export-home-soc-reports.js` and its private-repo data sources not found | Cannot verify Pipeline B (§6.B) end-to-end from source — only its documented behavior and live output are confirmed | `home-soc-reports/README.md` describes the script as living in the private `mcp-cyber-tools` repo; not present in this session's local checkout of that repo | `home-soc-reports/README.md`; absence confirmed by directory search of the local `mcp-cyber-tools` checkout |
| `sentinelops-security-incidents` repo's purpose is undetermined | Unclear whether it is a stale/abandoned idea or an intended future destination | Empty repo (0 bytes), no README, not referenced by any script | `gh api repos/KEVIN-NGUYENDAD/sentinelops-security-incidents` |

## 12. Active Workstreams

| Workstream | Type | Status | Source |
|---|---|---|---|
| WAAP Log Search Integration | Development (blocked) | Schema/plan complete; live API access blocked | `NEXT_STEPS.md` #1, `WAAP_LOG_SEARCH_SCHEMA.md` |
| VNETWORK API access troubleshooting | Investigation | Root cause (no WAAP onboarding) identified and addressed; a second, distinct access issue remains open post-fix | `PROJECT_STATUS.md`, "WAAP Log Search — Root Cause Identified" and "— Post-Onboarding Re-Verification" |
| Healthcheck Webhook Receiver | Research/plan | Plan complete; two blocking open items (HMAC spec, deployment target) | `MVP5_WEBHOOK_RECEIVER_PLAN.md`, `NEXT_STEPS.md` #2 |
| Digital Risk Twin | Research (not started) | Concept sketch only, explicitly not yet a plan | `NEXT_STEPS.md` #3 |
| Home-SOC alert pipeline | Maintenance / stable | Live, verified, milestone-frozen | `PROJECT_STATUS.md` |
| Home-SOC sanitized publication pipeline | Live, actively updated | Latest publish 2026-09-04T02:53Z | `home-soc-reports/BASELINE-LATEST.json` |

## 13. Next Priorities

Per `NEXT_STEPS.md`'s explicit, numbered priority order:

1. **WAAP Log Search Integration** — schema/plan are complete;
   resolve the live-access blocker (§9/§11) and decide the
   alert-threshold and `domains`-list questions, which the doc
   explicitly frames as "decisions for Kevin, not discovery gaps."
2. **Healthcheck Webhook Receiver** — capture a real webhook
   delivery's HMAC details (needs a temporary Monitor against a
   logging-only endpoint, per the plan doc) and decide the deployment
   target for `audit.sentinelops.fyi`.
3. **Digital Risk Twin** — run its own discovery pass; explicitly
   deferred until #1 and #2 exist to feed it.

## 14. 30-Day Roadmap

**Caveat, stated plainly:** none of the reviewed source documents
contain a dated roadmap or calendar commitment — `NEXT_STEPS.md`
provides a **priority order**, not a schedule, and `PROJECT_STATUS.md`
records what happened on 2026-09-04 without projecting forward dates.
The Immediate/Near-term/Future buckets below map directly onto that
documented priority order; no specific day-counts are asserted because
none exist in the source material.

**Immediate** (documented priority #1, currently blocked — the next
concrete step is unblocking, not building): resolve why WAAP API
access remains denied post-onboarding (`WAAP_LOG_SEARCH_SCHEMA.md`
§8's four unconfirmed explanations); once unblocked, decide the
alert-worthy threshold and confirm the `domains` list, then build
`scripts/create_waap_incident.py` and the `vnetworkWaapSearch` MCP
tool per the existing plan (`WAAP_LOG_SEARCH_SCHEMA.md` §6).

**Near-term** (documented priority #2): capture one real Healthcheck
webhook delivery to determine the HMAC algorithm/signing base/payload
schema; resolve the `audit.sentinelops.fyi` deployment-target question;
then implement `POST /api/webhooks/vnetwork-healthcheck`
(`MVP5_WEBHOOK_RECEIVER_PLAN.md`).

**Future** (documented priority #3, no plan yet — explicitly a
hypothesis): run a discovery pass for the Digital Risk Twin once #1
and #2 exist to feed it (`NEXT_STEPS.md` §3).

## 15. Source Reference Index

| File | Purpose |
|---|---|
| `mcp-cyber-tools/PROJECT_STATUS.md` | Primary project status log — every completed MVP, discovery pass, and verification result, in chronological sections |
| `mcp-cyber-tools/NEXT_STEPS.md` | Prioritized build order and open decisions for the next 3 workstreams |
| `mcp-cyber-tools/README.md` | MCP server overview, tool-category counts, architecture tree, setup instructions |
| `mcp-cyber-tools/package.json` | Confirms `server.js` as the active entry point, dependency versions |
| `mcp-cyber-tools/server.js` | Active MCP server — module registration order |
| `mcp-cyber-tools/server_v2.js` | Alternate, monolithic 12-tool MCP server (identical to `server_backup_v1.js`) |
| `mcp-cyber-tools/server_backup_v1.js` | Byte-identical to `server_v2.js` |
| `mcp-cyber-tools/modules/*.js` (11 files) | Source of the full 95-tool MCP inventory (§5) |
| `mcp-cyber-tools/scripts/create_test_incident.py` | Base incident-creation functions and GitHub repo/assignee constants |
| `mcp-cyber-tools/scripts/create_defender_incident.py` | Defender-sourced incident script |
| `mcp-cyber-tools/scripts/create_securitywatch_incident.py` | `security-watch.js`-sourced incident script, duplicate detection, enrichment |
| `mcp-cyber-tools/claude_desktop_config.json.example` | Confirms `server.js` as the configured MCP entry point |
| `mcp-cyber-tools/docs/VNETWORK_API_DISCOVERY.md` | Full 106-endpoint VNETWORK OpenAPI catalog and ROI ranking |
| `mcp-cyber-tools/docs/VNETWORK_PRODUCT_DISCOVERY.md` | Healthcheck/WAAP/Object Storage product-level discovery |
| `mcp-cyber-tools/docs/VNETWORK_CAPABILITY_ASSESSMENT.md` | 17-category, 18-service capability assessment |
| `mcp-cyber-tools/docs/WAAP_LOG_SEARCH_SCHEMA.md` | Full WAAP `bsearch` schema, sample payloads, MCP plan, and live verification (§1–§8) |
| `mcp-cyber-tools/docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` | Healthcheck webhook receiver plan and open blockers |
| `mcp-cyber-tools/docs/MVP3_WAZUH_INVESTIGATION.md` | Wazuh investigation — ruled out |
| `mcp-cyber-tools/docs/HOME_SOC_SOURCE_DISCOVERY.md` | Home-SOC alert-source ranking |
| `sentinelops-homepage/README.md` | Portfolio site tech stack and structure |
| `sentinelops-homepage/PROJECT.md` | Stated mission/focus areas for the portfolio |
| `home-soc-reports/README.md` | Sanitized publication pipeline — full architecture, sanitization rules, freshness contract |
| `home-soc-reports/BASELINE-LATEST.json` | Latest published control-state baseline |
| `home-soc-reports/DEVICE-SUMMARY.json` | Latest published device inventory summary |
| `kevin-cyber-security-copilot/README.md`, `agent.py`, `app.py`, `render.yaml`, `requirements.txt` | Standalone Flask/Groq demo app — architecture and deployment |
| `cybersecurity-labs/README.md`, `render.yaml`, `hashing.py`, `encryption.py`, `network.py`, `validation.py`, `agent.py`, `app.py`, `requirements.txt` | Learning-lab modules plus a near-duplicate copilot app, deployed separately |
| `network-security-audit-frontend/README.md`, `network-security-audit/DEPLOYMENT.md`, `backend/app.py`, `backend/security_scanner.py`, `backend/requirements.txt`, `frontend/package.json` | Two-service (Flask + React) network-audit demo app |
| `gh api repos/KEVIN-NGUYENDAD/sentinelops-security-incidents` (live GitHub API query) | Confirmed the repo is empty (0 bytes) |
| `gh repo list KEVIN-NGUYENDAD` (live GitHub API query) | Full repository inventory and visibility used to build §2 |
| `KEVIN-NGUYENDAD/KEVIN-NGUYENDAD/README.md` | GitHub profile README — mission statement, featured-projects list |
