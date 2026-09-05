# SENTINELOPS_DEEP_CONTEXT.md

Compiled 2026-09-04 for a full architectural handoff to another senior
AI architect/CTO. Read-only analysis — no code was changed, nothing
was implemented. Every claim below is sourced from repository
evidence: the local `mcp-cyber-tools` and `sentinelops-homepage`
checkouts, six additional GitHub repositories fetched read-only this
session (`home-soc-reports`, `network-security-audit-frontend`,
`cybersecurity-labs`, `kevin-cyber-security-copilot`,
`sentinelops-security-incidents`, the `KEVIN-NGUYENDAD` profile repo),
and this project's own prior work product
(`ARCHITECTURE_SUMMARY.md`, `SENTINELOPS_DISCOVERY_TIMELINE.md`,
`PROJECT_STATUS.md`, `NEXT_STEPS.md`, and every file in `docs/`).
Where evidence conflicts, both sides are shown — this document does
not resolve conflicts by picking the more flattering claim. Where no
evidence exists, it says so rather than filling the gap.

---

# 1. Executive Summary

**What SentinelOps actually is:** two things layered in the same
namespace, and they don't fully agree with each other. Layer one is a
real, working engineering project — a 95-tool MCP server
(`mcp-cyber-tools/modules/*.js`), a live alert→GitHub-incident
pipeline verified against real Windows Defender and firewall events
(`PROJECT_STATUS.md`, Issue #6), and a disciplined, evidence-driven
research track into a VNETWORK/WAAP integration that is still honestly
reporting itself as blocked. Layer two is a public portfolio site
(`sentinelops-homepage`, `sentinelops.fyi`) whose marketing copy
(`src/data/content.js`) makes specific, quantified operational claims
— a Wazuh SIEM processing ~40k events/day, 3/3 Suricata/Zeek sensors
online, a honeypot cluster, "100%" MCP tool-call auditing, a dated
threat report with exact block counts — that **this project's own
discovery documents directly disprove or cannot substantiate** (full
detail: §11, §17). Any operator picking this project up needs to know
both layers exist and that they diverge.

**Current maturity level:** Layer one (the engineering) is at a real,
verified MVP stage for its shipped scope, frozen as of 2026-09-04
(`PROJECT_STATUS.md`). Layer two (the public narrative) is
unverified-to-disproven in several specific, checkable claims.

**Current operational reality:**
- The Home-SOC alert pipeline is live, scheduled, and currently
  reporting a clean baseline (0 open alerts, GREEN) —
  `home-soc-reports/BASELINE-LATEST.json`.
- The 95-tool MCP server (`server.js`) is the confirmed active
  runtime; two other server files exist, byte-identical to each
  other, referenced by nothing (§6, §10).
- The GitHub incident pipeline has created and updated real issues
  against real events (`PROJECT_STATUS.md`, Issue #6).
- The WAAP integration is fully designed and **zero percent live** —
  every API call this project has made against it has been denied,
  including after completing WAAP onboarding
  (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §7–§8).
- The Healthcheck Webhook Receiver is fully planned and **zero
  percent implemented**, blocked on an undocumented HMAC spec and an
  unidentified deployment owner (`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`).

**What is working today:** MVP #1–#4 (fake-alert pipeline → Defender
pipeline → security-watch.js live telemetry → labeled/enriched
GitHub incidents), the Home-SOC sanitized publication pipeline to
`home-soc-reports`, and the 95-tool MCP server as a manually-invoked
Claude Desktop capability set.

**What is still blocked:** WAAP API access (root cause identified —
missing onboarding — but access remained denied after the fix was
applied, cause of *that* still open, §8); the Healthcheck Webhook
Receiver (two independent blockers, neither resolved); the Digital
Risk Twin (explicitly has had no discovery pass at all —
`NEXT_STEPS.md` §3).

---

# 2. Real Mission

**Why the platform exists**, stated directly by its own owner
(`sentinelops-homepage/src/data/content.js`, `profile.summary`):
*"I'm a cybersecurity student focused on SOC operations, DFIR, and AI
security, and I learn by building rather than just studying. That
means running a self-hosted home-SOC to practice detection engineering
and incident response against real traffic, and developing MCP
tooling that gives AI agents safe, auditable access to security
data."* This is corroborated by the actual codebase: the Home-SOC
pipeline runs against this operator's own real home network (real
firewall, real Defender, real controls), not a simulated one
(`PROJECT_STATUS.md`, MVP #3 verification against a real firewall
toggle).

SentinelOps is not, based on the evidence, a product being sold or a
company with customers — it is a **portfolio-as-working-system**: the
public site exists to demonstrate the engineering (`profile.role`:
*"Building an AI Security Operations Platform"*), and the engineering
exists to make the portfolio credible by being real rather than a mockup.
This dual purpose is exactly why the Layer 1 / Layer 2 divergence
flagged in §1 matters — it undermines the specific mechanism (proof of
real, working skill) the project is built to demonstrate.

**Long-term direction**, per the only forward-looking document with
any specificity (`NEXT_STEPS.md`): expand the alert pipeline's data
sources (WAAP edge logs, then Healthcheck push alerts), and eventually
synthesize all of them into a "Digital Risk Twin" — a standing,
queryable model of the organization's real exposure, explicitly
described as *"not a new alert type, but a standing answer to 'what do
we actually expose and what's its current state'"* that every
individual pipeline could enrich against. This is described as a
**working idea aggregating already-integrated sources**, not a new
platform.

**Intended end-state**, as far as the documented evidence supports it:
a single operator (Kevin), triaging real security signal from
multiple real sources (host, edge, push) entirely through GitHub
Issues and GitHub Mobile — no dashboard, no database beyond what a
JSON file holds, explicitly stated as a constraint
(`NEXT_STEPS.md`: *"No dashboards, no databases, no new infrastructure
implied by default"*). Nothing in the reviewed sources describes an
end-state involving other users, a SaaS product, or infrastructure
beyond this operator's own home lab and personal cloud footprint.

---

# 3. Repository Inventory

| Repository | Purpose | Status | Dependencies | Relationship to others | Current usefulness |
|---|---|---|---|---|---|
| **mcp-cyber-tools** | MCP server (95 tools) + Home-SOC alert→incident pipeline + VNETWORK/WAAP discovery track | Private. MVP #1–#4 frozen/shipped; WAAP track blocked | `@modelcontextprotocol/sdk`, `zod`, Python 3 stdlib (`urllib`/similar for `github_request`), PowerShell | Hub of the ecosystem — everything else either feeds it or is downstream of it | **High** — the only repo with real, verified, running automation |
| **sentinelops-homepage** | Public portfolio at `sentinelops.fyi` | Public, static (Vite/React, no server) | React 18, Vite 5, Tailwind 3 | Narrates the ecosystem; contains claims not fully reconciled with `mcp-cyber-tools`'s verified state (§11, §17) | **Medium** — real hiring-facing asset, but its accuracy is currently a liability, not just an asset (§1) |
| **home-soc-reports** | One-way, sanitized publication surface, read by a scheduled task for a daily email bulletin | Public, actively updated (`BASELINE-LATEST.json` generated 2026-09-04T02:53:07Z) | `export-home-soc-reports.js` (documented as living in the private repo; **not found** in this session's local checkout — §17) | Downstream of `mcp-cyber-tools`'s private scan/baseline data; feeds a Claude Scheduled Task, not GitHub | **Medium** — genuinely live and current, but its producing script is unaccounted for locally |
| **sentinelops-security-incidents** | Unknown | Public, **empty** (0 bytes, no README, no commits) | None | Not referenced by any script; not the real incident destination (that's `mcp-cyber-tools` Issues) | **None currently** — a name that implies a role it doesn't fulfill |
| **kevin-cyber-security-copilot** | Standalone Flask/Groq "AI Cyber Security Assistant" demo | Public, deployed to Render | Flask, Groq API (`llama-3.1-8b-instant`), Gunicorn | Architecturally isolated — no integration with the MCP server or incident pipeline | **Low-Medium** — a portfolio demo app, not part of the operational system |
| **cybersecurity-labs** | Learning-lab modules (hashing, encryption, network, validation, tests) **plus** a near-duplicate copy of `kevin-cyber-security-copilot`'s app deployed as its own Render service | Public, deployed to Render | Same as above, plus `pytest`, `cryptography`/`pycryptodome` | Duplicates code from `kevin-cyber-security-copilot` (§10) | **Low-Medium** — real lab exercises with real tests, undermined by the duplicated app confusing the repo's identity |
| **network-security-audit-frontend** | Two-service (Flask backend + React frontend) network-audit demo tool | Public, deployed to Render (two services) | Flask 2.3.2, `flask-limiter`, `psutil`; React 18.2.0 | Architecturally isolated; its own `DEPLOYMENT.md` contains a leftover reference to an unrelated project's repo name (§17) | **Low-Medium** — functional demo, not integrated |
| **KEVIN-NGUYENDAD** (profile repo, discovered) | GitHub profile README | Public, single file | None | Its "Featured Projects" list disagrees with `sentinelops-homepage/PROJECT.md`'s list (§17) | **Low** — narrative only |

**Repositories reviewed and excluded as not SentinelOps-related:**
`TheWall` (confirmed GDScript/Godot game — `gh api
repos/KEVIN-NGUYENDAD/TheWall`'s `languages` endpoint returns
`{"GDScript":68401,"JavaScript":20542,"HTML":10878}` — despite being
described on the homepage as a live security-visualization tool, §17),
`Sass-ai-app` (pharmacy assistant), `uber-order-filter` (Uber driver
tool), `AZ-Transportation-Laws-` (private, unrelated).

---

# 4. System Architecture

**Domains:** `sentinelops.fyi` (static, no server —
`PROJECT_STATUS.md`), `audit.sentinelops.fyi` (real, live, CNAME→
VNETWORK CDN→Render origin, backend source repo **not found on this
machine** — `PROJECT_STATUS.md`, MVP #5 plan section),
`www.sentinelops.fyi` (WAAP-onboarded, Service ID `95743`, API access
still denied — `docs/WAAP_LOG_SEARCH_SCHEMA.md` §8).

**Render services (confirmed via `render.yaml`/`DEPLOYMENT.md`):**
`kevin-cyber-security-copilot`, `cybersecurity-labs`,
`network-security-audit-api`/`network-security-audit` (naming
inconsistent between that repo's own `README.md` and
`DEPLOYMENT.md`). The service behind `audit.sentinelops.fyi` is
**not documented anywhere found**.

**MCP:** `server.js`, 95 tools, 11 modules, stdio transport via
`@modelcontextprotocol/sdk`, invoked through Claude Desktop
(`claude_desktop_config.json.example`). Full detail: §6.

**Home-SOC:** two independent pipelines under one name — an
alert→GitHub-incident pipeline and a sanitized public-publication
pipeline. Full detail: §5.

**GitHub:** the system of record for incidents
(`KEVIN-NGUYENDAD/mcp-cyber-tools` Issues) and the host for every
repository in §3.

**Incident flows:** see §7.

**WAAP:** designed, not live. See §8.

**Healthchecks:** planned, not built. VNETWORK Healthcheck & Alerting
is a real product (beta) with native webhooks but no REST API
(`docs/VNETWORK_PRODUCT_DISCOVERY.md`); the receiver design is in
`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`.

**External integrations:** GitHub (issues, hosting), VNETWORK
(`openapi.vnetwork.vn`, planned), Groq (LLM API, the two Flask demo
apps), Render (hosting).

### ASCII architecture diagram (verified components solid-lined in prose; planned/unverified marked explicitly)

```
┌───────────────────────────── Windows host ─────────────────────────────┐
│                                                                          │
│  Windows Defender ──┐                                                   │
│  security-watch.js ─┴─→ alerts.json ──→ create_securitywatch_incident.py│
│  (Task Scheduler:                              │                        │
│   HOME-SOC-Scan-And-Export)                    ▼                        │
│                                    score_alert / 24h dup-detect /       │
│                                    compute_labels / analysis comment     │
│                                                 │                        │
│  [MCP server: server.js — 95 tools, 11 modules]│                        │
│  (Claude Desktop client, stdio) — NOT wired     │                        │
│  into the incident scripts above (§17)          ▼                        │
└─────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                          GitHub Issues — KEVIN-NGUYENDAD/mcp-cyber-tools
                                                  │
                                                  ▼
                                          GitHub Mobile → phone


┌── separate export pipeline ──────────────────────────────────────────┐
│ private scan/baseline data → export-home-soc-reports.js (script       │
│ location: NOT FOUND in local checkout, §17) → leak-guard →            │
│ PUBLIC home-soc-reports repo → daily Claude Scheduled Task → email    │
└─────────────────────────────────────────────────────────────────────┘


┌── WAAP: fully designed, ZERO live access (§8) ────────────────────────┐
│  VNETWORK openapi.vnetwork.vn POST /v1/bsearch                        │
│  Bearer token — authenticates, but 403/404/401 on every product       │
│  tested, unchanged by completing WAAP onboarding for                  │
│  www.sentinelops.fyi                                                  │
│  (planned) scripts/create_waap_incident.py → same GitHub-Issue chain  │
└─────────────────────────────────────────────────────────────────────┘

┌── Healthcheck: fully planned, ZERO implementation ─────────────────────┐
│  VNETWORK Healthcheck & Alerting → webhook (HMAC spec undocumented)    │
│  (planned) POST /api/webhooks/vnetwork-healthcheck on                 │
│  audit.sentinelops.fyi (backend owner: unknown, §17)                  │
└─────────────────────────────────────────────────────────────────────┘


┌── PUBLIC NARRATIVE (sentinelops.fyi) — claims not reconciled with the │
│    verified state above (§11, §17):                                   │
│  - "Home-SOC SIEM (Wazuh)" ~40k events/day  ←→ Wazuh confirmed NOT     │
│    installed anywhere on this host (docs/MVP3_WAZUH_INVESTIGATION.md) │
│  - "Suricata / Zeek Sensors" 3/3 online     ←→ Suricata confirmed NOT  │
│    installed (same doc + HOME_SOC_SOURCE_DISCOVERY.md); Zeek never    │
│    checked in any discovery doc                                       │
│  - "TheWall" described as a live attacker-traffic visualization       │
│    ←→ TheWall's own GitHub repo is 68KB of GDScript (a Godot game)    │
│  - Threat Report #001 (6 blocked requests, audit.sentinelops.fyi)     │
│    ←→ this project has never had working WAAP API access to verify   │
│    or reproduce such a report                                         │
└─────────────────────────────────────────────────────────────────────┘

  Standalone, unconnected demo apps: kevin-cyber-security-copilot,
  cybersecurity-labs, network-security-audit-frontend (+backend) —
  each its own Render deployment, no documented integration with
  anything above.
```

---

# 5. Home-SOC Deep Dive

**Actual alert sources.** Per `docs/HOME_SOC_SOURCE_DISCOVERY.md`, the
project explicitly searched for and ranked every real, available
telemetry source on the host — this is the single most important
document for understanding what Home-SOC actually is versus what it's
described as elsewhere. Windows Defender (proven, MVP #2) and
`security-watch.js` (chosen, MVP #3) are the only two sources
integrated into the alert pipeline. Windows Event Logs were evaluated
and rejected for this purpose (no process-creation telemetry without
an `auditpol` change). Wazuh and Suricata were both confirmed **not
installed** (`docs/MVP3_WAZUH_INVESTIGATION.md`,
`docs/HOME_SOC_SOURCE_DISCOVERY.md`).

**`security-watch.js`.** A small, already-working endpoint-control
watcher. Every scheduled run it reads 5 real Windows security controls
(DNS servers, Windows Firewall, Defender real-time protection, RDP
listening, SSH listening), diffs against an explicitly-approved
`baseline.json`, and appends any transition to `alerts.json`
(`docs/HOME_SOC_SOURCE_DISCOVERY.md`). Scheduled via Windows Task
Scheduler as `HOME-SOC-Scan-And-Export`
(`cmd /c node security-watch.js && node iot-device-scanner.js && node
export-home-soc-reports.js`), verified actually running (`LastRunTime
9/3/2026 7:51:48 PM`, `LastTaskResult 0`). **The script's own source
was not found in the local `mcp-cyber-tools` checkout reviewed this
session** — only its output (`alerts.json`) and its documented
behavior (via `docs/HOME_SOC_SOURCE_DISCOVERY.md`'s description) were
available; it apparently lives at
`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`, a
separate tree from the local project directory used for this review.

**`alerts.json`.** Schema example, captured directly:
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
Current state (`state.json`, 2026-09-04T02:52:27Z): all 5 controls
match baseline, 0 open alerts — the correct/expected reading for a
clean host, not a stale one.

**Alert generation → scoring:** `alerts.json` →
`scripts/create_securitywatch_incident.py`'s `to_alert()` mapper →
`score_alert()` (risk scoring, function confirmed present by direct
source inspection) → 24-hour duplicate detection (GitHub issue title +
"Last Seen" timestamp is the only state — no separate local state
file) → `create_issue()` (new) or `update_issue_body()` (duplicate) →
`compute_labels()` → `build_analysis_comment()` → `assign_issue()`.

**Existing automation:** the `HOME-SOC-Scan-And-Export` scheduled
task (host-side collection) and the daily-20:10 Claude Scheduled Task
(publication-side, reading `home-soc-reports`'s raw GitHub URLs).
Neither is confirmed to invoke the GitHub incident scripts
automatically on its own schedule — `PROJECT_STATUS.md`'s
verification narrative describes manual runs of
`create_securitywatch_incident.py` against real toggled events, not
an automatic trigger chain from the scheduled task straight through to
GitHub. **This distinction (automated collection vs. manually-run
incident creation) is not explicit anywhere and is worth confirming
directly with the operator before assuming full automation exists.**

**Real-world validated detections:** one, fully documented — a
Windows Firewall (Public profile) toggle, briefly disabled and
immediately re-enabled under a single guarded admin command, produced
a real `FIREWALL_DISABLED` alert, a real GitHub Issue (#6,
`[CRITICAL] Firewall Disabled | Risk 95`), and a real duplicate-update
on a second run (`Occurrences: 2`, then `3` after MVP #4 enrichment)
(`PROJECT_STATUS.md`).

**Current limitations / remaining gaps:**
- A confirmed, unfixed bug: `FIREWALL_DISABLED`/`DEFENDER_DISABLED`
  rules reference control keys `firewall`/`defender` that don't match
  the actual baseline/state object's `fw`/`def` keys, silently
  dropping `baseline_value`/`current_value` for those two alert types
  only (DNS/RDP/SSH unaffected) — `PROJECT_STATUS.md`.
- A second, unrelated, **dormant** Home-SOC implementation exists at
  `C:\mcp-cyber-tools\reports\home-soc-state`, last written
  2026-08-29, with a failing scheduled task
  (`HOME-SOC-MCP-Server`, `LastTaskResult: 1`) and a
  never-run second task (`HOME-SOC-Startup-Scan-AutoPush`) —
  explicitly not chosen, not deleted (§10, §17).
- A previously-closed reliability incident
  (`INCIDENT-2026-09-01-STALE-FEED.md`) documented a ~41-hour missed
  collection cycle, root-caused as a scheduling gap, not a script bug
  — closed as an observation, not currently blocking.
- The `export-home-soc-reports.js` script and its listed private-repo
  data sources (`network-scan-data/*.json`,
  `laptop-collection-data/*.json`, `baseline/BASELINE-*.json`) were
  **not found** in the local `mcp-cyber-tools` checkout — only
  described in `home-soc-reports/README.md` and confirmed live only by
  their published output.

**Telemetry pipeline (actual, as verified):**

```
security-watch.js (schedule: HOME-SOC-Scan-And-Export)
   reads: DNS servers, Windows Firewall, Defender RTP, RDP listen, SSH listen
   diffs against: baseline.json
        │
        ▼
   alerts.json  (schema above)
        │
        ▼ (manual run, per PROJECT_STATUS.md's own verification narrative)
   create_securitywatch_incident.py
        │  to_alert() → score_alert() → 24h duplicate check
        ▼
   GitHub Issue (create or update) → labels + analysis comment → assign
        │
        ▼
   GitHub Mobile
```

---

# 6. MCP Deep Dive

**Tools discovered / tool count:** **95**, counted directly from
`server.tool(...)` calls in every `modules/*.js` file (not merely
trusted from `README.md`'s "90+" prose claim, which the direct count
is consistent with).

**Tool categories (11 modules):**

| Module | Count | Category focus |
|---|---|---|
| `host.js` | 10 | User/system identity and enumeration |
| `network.js` | 10 | Network configuration, connections, DNS |
| `process.js` | 10 | Process listing, metrics, trees |
| `services.js` | 5 | Windows service status |
| `eventlogs.js` | 10 | Security/System/Application/RDP/USB event logs |
| `firewall.js` | 5 | Firewall status and rules |
| `defender.js` | 5 | Windows Defender status and threats |
| `persistence.js` | 10 | Startup items, Registry Run keys, WMI, DLL hijack |
| `forensics.js` | 10 | Hashing, file metadata, ADS, recycle bin |
| `hunting.js` | 10 | Encoded PowerShell, LOLBins, credential dumping, beacons |
| `incident.js` | 10 | Evidence collection, timeline, security-audit report |

**Full per-tool inventory:** already produced and verified in
`ARCHITECTURE_SUMMARY.md` §5 (95-row table, `module | tool | description`)
— not reproduced a third time here; treat that table as canonical.

**Production-ready tools:** all 95, in the sense that they are wired
into the active `server.js` and follow one consistent, working
implementation pattern (`zod` schema → `runPowerShell()` →
`formatResponse()`, both in `modules/shared.js`). No tool is marked
experimental/beta in source or docs.

**Experimental tools:** none flagged as such within `server.js`'s
tool set. The genuinely experimental/orphaned code is the **entire
alternate server** described below, not any individual tool.

**Core capabilities:** host/network/process/service introspection,
event-log querying, firewall/Defender status, persistence and
forensic-artifact detection, threat-hunting heuristics, and
incident-response evidence collection/timeline/audit-report
generation — all read-only, all PowerShell-backed, all local to the
Windows host running the server.

**Current active runtime:** `server.js` — confirmed via
`package.json`'s `"main": "server.js"` and the example Claude Desktop
config (`claude_desktop_config.json.example`), which points at
`server.js` specifically. `server_v2.js` and `server_backup_v1.js` are
byte-for-byte identical to each other (confirmed via `diff`), a
separate 410-line, single-file, monolithic MCP server (not using the
`modules/` pattern), registering a 12-tool subset by name
(`readLogFile`, `checkHash`, `scanPort`, `nslookup`, `ping`, `tracert`,
`ipconfig`, `netstat`, `tasklist`, `servicesChecker`, `eventLogs`,
`processMonitor`) of what `server.js` also provides. Neither is
referenced anywhere else in the repo. **Why both exist is not
documented anywhere — treat them as orphaned prototypes, not a fallback
or dev/prod split**, unless the operator says otherwise.

**Most important MCP capabilities** (by evidence of actual use):
`incident.js`'s `collectEvidence`/`timeline`/`securityAudit` (the
closest thing to a report-generation capability the server has,
matching `README.md`'s "Report Generation" feature claim) and
`defender.js`'s tools (the one telemetry source proven end-to-end into
a real GitHub incident, MVP #2).

**Underused MCP capabilities:** all 10 `hunting.js` tools
(`huntEncodedPowerShell`, `huntPersistence`, `huntCredentialDumping`,
etc.) — real, implemented, and not referenced by any script or
scheduled automation found in this review. They are only reachable by
a human manually invoking them through Claude Desktop, never by the
automated pipeline. The same is true of most of `forensics.js` and
`persistence.js` — powerful, unused outside ad-hoc manual queries.

**Missing MCP capabilities:**
- No tool exists yet for VNETWORK/WAAP (planned:
  `vnetworkWaapSearch`, `docs/WAAP_LOG_SEARCH_SCHEMA.md` §6, not
  built).
- `README.md`'s own unchecked roadmap items: remote system analysis
  support, ML-based anomaly detection, historical-report database
  storage, a web dashboard, MITRE ATT&CK mapping, threat-intel feed
  integration — all listed, none implemented (`README.md`,
  "Roadmap").
- **No audit-logging/tool-call-tracking mechanism was found in
  `modules/shared.js` or anywhere else in the server** — relevant
  because the public site's "Live Infrastructure" panel claims "100%"
  tool-call auditing for `mcp-cyber-tools API` (§11, §17); nothing in
  the reviewed source substantiates that specific claim.
- The incident-creation Python scripts (§7) are **not invoked through
  MCP at all** — they are standalone scripts run directly, with their
  own `argparse` `main()` — meaning the MCP layer and the incident
  pipeline are two separate code paths that happen to live in the
  same repo, not one integrated system.

---

# 7. Incident Pipeline Deep Dive

**Current alert-to-incident workflow** (verified by direct function
listing in every script):

```
alert (source-specific dict)
   │
   ▼
to_alert()                 ← per-source mapper (only in
                              create_securitywatch_incident.py;
                              create_defender_incident.py and
                              create_test_incident.py build the alert
                              dict inline instead)
   │
   ▼
score_alert()               ← risk scoring (create_test_incident.py,
                               reused unchanged by the other two)
   │
   ▼
build_issue()                ← formats title/body
   │
   ▼
github_request() / create_issue() / assign_issue()
   │
   ▼
(new)                         (duplicate, within 24h)
   │                                │
   ▼                                ▼
GitHub Issue created      find_open_issues() → find_duplicate()
                           → update_issue_body() (Occurrences +1,
                             Last Seen refreshed)
   │                                │
   └────────────────┬───────────────┘
                     ▼
        compute_labels() → add_labels()
        build_analysis_comment() → add_comment()
                     │
                     ▼
              assign_issue() (KEVIN-NGUYENDAD)
```

**`create_test_incident.py`** — the base script. Defines
`score_alert`, `build_issue`, `github_request`, `create_issue`,
`assign_issue`, and the hardcoded constants `REPO_OWNER =
"KEVIN-NGUYENDAD"`, `REPO_NAME = "mcp-cyber-tools"`, `ASSIGNEE =
"KEVIN-NGUYENDAD"` — reused, unmodified, by both scripts below. This
is the actual, confirmed destination of every incident in the system —
**not** `sentinelops-security-incidents` (empty, unreferenced).

**`create_defender_incident.py`** — MVP #2. Same reuse pattern,
Windows Defender as the alert source.

**`create_securitywatch_incident.py`** — MVP #3/#4. Adds
`to_alert()` (maps a `security-watch.js` alert onto the shared
schema), the full 24h duplicate-detection chain
(`find_open_issues`, `parse_tracking`, `with_tracking_block`,
`parse_timestamp`, `find_duplicate`, `update_issue_body`), and MVP
#4's enrichment layer (`compute_labels`, `build_analysis_comment`,
`add_labels`, `add_comment`). This is the most fully-developed script
and the template every future integration is planned to copy
(`docs/WAAP_LOG_SEARCH_SCHEMA.md` §6,
`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` §6).

**`create_waap_incident.py`** — **does not exist.** Confirmed absent
by directory listing of `scripts/` this session. Planned only.

**Authentication:** all three existing scripts read `GITHUB_TOKEN`
from the environment (`os.environ.get("GITHUB_TOKEN")`), with a
guarded error message if missing, and call the GitHub REST API
directly — no SDK dependency.

**Implemented vs. planned:**

| Piece | Status |
|---|---|
| Fake-alert pipeline (MVP #1) | Implemented |
| Defender pipeline (MVP #2) | Implemented |
| security-watch.js pipeline (MVP #3) | Implemented, verified against a real event |
| Labels + analysis comments (MVP #4) | Implemented, verified against a real recurrence |
| WAAP pipeline | **Planned only** — schema/mapper design complete, script does not exist, blocked on API access (§8) |
| Healthcheck webhook receiver | **Planned only** — HTTP receiver, HMAC verification, and mapper all designed, nothing built |
| Digital Risk Twin | **Idea only** — no design, no discovery pass |

---

# 8. WAAP Investigation Deep Dive

**Why WAAP matters strategically:** across three independent VNETWORK
discovery passes (`docs/VNETWORK_API_DISCOVERY.md`,
`docs/VNETWORK_PRODUCT_DISCOVERY.md`,
`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`), `POST /v1/bsearch` was
ranked the single highest-ROI capability every time — the only real
security-log source (client IP, URI, status code, user agent,
mitigation result) anywhere in VNETWORK's 106-endpoint API. It is the
only planned integration that adds genuinely new *edge*-layer signal
to a pipeline that is currently 100% host-layer (Defender,
security-watch.js).

## Discovery phases (full detail: `SENTINELOPS_DISCOVERY_TIMELINE.md`
Phases 3–10; condensed here)

1. **API catalog** (Phase 3) — 106 endpoints, `bsearch` identified as
   the only log source, no native alerting anywhere in the API.
2. **Product discovery** (Phase 4) — confirmed Healthcheck & Alerting
   and Object Storage exist as separate products; re-confirmed no
   hidden alert/webhook API exists.
3. **Capability assessment** (Phase 5) — Partner Portal unreachable,
   assessment built from public docs; surfaced the unscoped-API-key
   risk (later realized in practice, below) and Multi-CDN
   Orchestration as an additional high-ROI item.
4. **Schema deep dive** (Phase 7) — full request/response schema,
   sample payloads, MCP plan; found the undocumented
   `mitigation_result` field and a real docs-vs-template contradiction
   (`domains` mandatory vs. optional).
5. **Live verification** (Phase 8) — first actual calls to
   `openapi.vnetwork.vn`: `403` (Compute), `404` (CDN, traced to an
   unresolved `{{URL}}` template variable in VNETWORK's own published
   Postman collection), `401` (WAAP), reproduced across a token
   rotation prompted by an accidental exposure of the token in the
   session transcript (handled correctly — treated as compromised,
   rotated, retested).
6. **Root cause** (Phase 9) — Kevin's direct Partner Portal check
   found WAAP onboarding Step 2 (Domain & Origin) empty. No WAAP site
   had ever been onboarded.
7. **Post-onboarding re-verification** (Phase 10) — after Kevin
   onboarded `www.sentinelops.fyi` (Service ID `95743`), the identical
   three checks returned **byte-for-byte identical** results. Access
   remained denied.

## Confirmed facts

- The endpoint, auth scheme, and full schema (§3/§5 of
  `docs/WAAP_LOG_SEARCH_SCHEMA.md`) are correct and well-formed — no
  call in this entire investigation was ever rejected as malformed
  (`400`), only as unauthorized/denied.
- The token is live and authenticates (differentiated,
  service-specific error codes, not a uniform failure).
- The 5 originally-requested fields (source IP, URI, status code,
  user agent, mitigation result) all exist at the documentation level.
- VNETWORK's own published Postman collection has a real, confirmed
  gap: 3 of 106 endpoints use an unresolved `{{URL}}` template
  variable instead of the hardcoded host every other endpoint uses.

## Rejected hypotheses (for the "still denied after onboarding"
question — ranked by probability, evidence detailed in this
session's prior analysis turn)

1. **Account/token scope mismatch — leading hypothesis, not rejected**
   (see below).
2. **Onboarding incomplete beyond Step 2** — plausible for the WAAP
   `401` specifically, but does not explain the parallel, unchanged
   Compute `403`/CDN `404`, which have no dependency on WAAP
   onboarding at all.
3. **Domain-string mismatch** — plausible, but weakened by Kevin
   citing a specific Service ID (`95743`) alongside the domain,
   implying direct portal confirmation rather than a guess; also
   doesn't explain Compute/CDN.
4. **Propagation delay** — weakest: no VNETWORK documentation asserts
   such a delay exists, and it likewise doesn't explain Compute/CDN.

## Entitlement findings

The account's API token returns `403 Service.AccessDenied` on
Compute and `404 Service.NotFound` on CDN — **entirely unrelated
products to WAAP**, denied in the exact same unchanged pattern before
and after WAAP-specific onboarding. This is the central evidence
behind the leading hypothesis.

## Verification results

See Phase 8/10 above and `docs/WAAP_LOG_SEARCH_SCHEMA.md` §7–§8 for
full request/response bodies, byte-for-byte.

## Portal findings

Confirmed directly by Kevin (not by this project's own tooling, which
has no Partner Portal access): WAAP onboarding Step 2 was empty as of
the root-cause check, and has since been filled in (`www.sentinelops.fyi`,
Service ID `95743`).

## DNS findings

`audit.sentinelops.fyi` — CNAME → `edge.vnetwork.gslb.veloceed.com` →
`95715.cdn.vncdn.net` (VNETWORK's own CDN), Render origin behind it
(confirmed via HTTP `rndr-id` header) —
`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md` §3. **This is a different domain
than the one onboarded to WAAP during this investigation
(`www.sentinelops.fyi`)** — see §17 for why this matters.

## API findings

Full catalog: §3 of this document / `docs/VNETWORK_API_DISCOVERY.md`.

## Current primary blocker

WAAP API access remains denied for this token/account across every
product tested, unchanged by completing WAAP onboarding for
`www.sentinelops.fyi`.

## Current leading hypothesis

**Account/token scope mismatch** — this token/account was never
granted API-layer entitlement to Compute, CDN, or WAAP, independent of
whatever is visible or configured in the console. It is the only
hypothesis consistent with the full evidence set (all three products
denied identically, unaffected by a domain-specific console action).

## Evidence supporting it

The identical `403`/`404`/`401` spread, reproduced across two
different tokens and across a completed WAAP onboarding action that
had no effect on any of the three results. Fastest validation
(recorded, not yet performed): check, via Partner Portal or VNETWORK
support, which products this specific API key/account is actually
entitled to call at the `openapi.vnetwork.vn` layer.

---

# 9. Discovery Timeline Review

Every phase from `SENTINELOPS_DISCOVERY_TIMELINE.md`, none skipped.

## Phase 1 — MVP #3 Input Verification: Wazuh Investigation
- **Goal:** confirm `Wazuh alerts.json` exists before building
  against it.
- **Evidence:** no Wazuh service/directory/listening port anywhere;
  `sc query WazuhSvc` → `1060: service does not exist`; two
  unrelated files happen to be named `alerts.json`, neither Wazuh's.
- **Discovery:** the entire originally-scoped input doesn't exist.
- **Result:** investigation closed, no code changed.
- **Architecture impact:** none built.
- **Why next phase started:** the disqualified input left MVP #3
  without a data source, forcing a search for a real replacement.

## Phase 2 — Home-SOC Source Discovery
- **Goal:** pick a real, already-running replacement input.
- **Evidence:** two separate Home-SOC implementations found (one
  dormant, one live); `security-watch.js`'s schema is clean and
  close to the existing pipeline's shape.
- **Discovery:** `security-watch.js` ranked #1 of five candidates.
- **Result:** chosen as MVP #3's real data source.
- **Architecture impact:** MVP #3's actual implementation replaced the
  original Wazuh-based diagram.
- **Why next phase started:** this closed the MVP #3 question; Phase
  3 began independently, as the start of the separate VNETWORK/WAAP
  track ("MVP #4 Discovery").

## Phase 3 — VNETWORK OpenAPI Discovery
- **Goal:** catalog VNETWORK's API and rank by ROI.
- **Evidence:** 106 endpoints read from the public Postman collection.
- **Discovery:** `bsearch` is the only real log source; no native
  alerting anywhere in the API.
- **Result:** `bsearch` ranked #1 of 106 endpoints.
- **Architecture impact:** set the reference priority order every
  later pass inherited.
- **Why next phase started:** the collection had no trace of
  Healthcheck & Alerting or Object Storage, raising the question
  Phase 4 answered.

## Phase 4 — VNETWORK Product Discovery
- **Goal:** determine whether Healthcheck & Alerting and Object
  Storage exist as separate products.
- **Evidence:** VNETWORK's public docs site; a targeted keyword
  re-search of the Phase-3 collection JSON.
- **Discovery:** both products real; Healthcheck has native webhooks
  but no API; zero keyword matches confirming no hidden alerting
  surface.
- **Result:** `bsearch` reconfirmed as WAAP's only programmatic
  surface.
- **Architecture impact:** seeded Phase 6's plan; no code.
- **Why next phase started:** the original brief's authenticated
  Partner Portal exploration was still unattempted — Phase 5 took it
  on.

## Phase 5 — VNETWORK Capability Assessment
- **Goal:** the originally-requested 17-category Partner Portal
  exploration.
- **Evidence:** an unauthenticated fetch returned only a bare
  login-wall page title — confirmed, not assumed.
- **Discovery:** assessment built from public docs instead;
  Multi-CDN Orchestration surfaced as high-ROI; API keys confirmed
  account-wide/unscoped/no rotation.
- **Result:** 18 services assessed, each fact marked
  CONFIRMED/NOT DOCUMENTED.
- **Architecture impact:** none — a documentation observation at this
  point (the key-scoping risk was later realized in practice, Phase
  8).
- **Why next phase started:** with WAAP and Healthcheck both scoped,
  the project moved to planning the Healthcheck receiver specifically.

## Phase 6 — MVP #5 Healthcheck Webhook Receiver Plan
- **Goal:** design a receiver and pick a deployment target.
- **Evidence:** a previously-unfetched VNETWORK docs page; direct
  DNS/HTTP checks of both `sentinelops.fyi` and
  `audit.sentinelops.fyi`.
- **Discovery:** webhook mechanics confirmed but HMAC
  algorithm/signing base/payload schema undocumented anywhere;
  `audit.sentinelops.fyi` real and live but its backend source not
  found on this machine; an earlier project assumption (that the
  homepage's WAF case-study copy was "just marketing") was corrected
  — DNS/HTTP independently confirms the *infrastructure* claims.
- **Result:** `audit.sentinelops.fyi` recommended, `sentinelops.fyi`
  ruled out; endpoint path and HMAC strategy designed defensively.
- **Architecture impact:** established the project's second
  integration shape (push vs. poll) — design only.
- **Why next phase started:** this closed the Healthcheck track's
  planning; the higher-priority WAAP track resumed post-freeze at a
  deeper level (Phase 7).

## Phase 7 — WAAP Log Search Schema & MCP Plan
- **Goal:** capture `bsearch`'s full schema and an MCP integration
  design.
- **Evidence:** the `Bsearch Aggs` Postman item's request template and
  field-reference table, read in full.
- **Discovery:** the undocumented `mitigation_result` field; a real
  docs-vs-template contradiction on `domains`.
- **Result:** full schema, payloads, and MCP plan produced —
  explicitly flagged as doc-sourced, not live-verified.
- **Architecture impact:** none built.
- **Why next phase started:** at the user's explicit direction, this
  same document proceeded directly into a live test.

## Phase 8 — WAAP Live Verification Pass
- **Goal:** verify Phase 7's schema against real API responses.
- **Evidence:** three live calls, each denied with a distinct,
  structured error; a token exposure incident, handled by immediate
  rotation and retest.
- **Discovery:** the account has zero working access despite a
  correct, well-formed request schema; a real `{{URL}}` routing gap
  in VNETWORK's published collection.
- **Result:** `403`/`404`/`401`, reproduced identically after
  rotation.
- **Architecture impact:** none — the integration stayed blocked
  before any code was written.
- **Why next phase started:** the denials couldn't be diagnosed
  further from outside the API, forcing a ground-truth check against
  the Partner Portal.

## Phase 9 — WAAP Root Cause Identification
- **Goal:** determine why Phase 8 was denied, via direct portal
  evidence.
- **Evidence:** Kevin's direct check of the WAAP onboarding wizard.
- **Discovery:** Step 2 (Domain & Origin) was empty — no WAAP site had
  ever been onboarded.
- **Result:** root cause found, explaining every Phase 8 result
  without further API debugging.
- **Architecture impact:** reclassified the blocker as a specific
  console action item.
- **Why next phase started:** once Kevin completed the missing
  onboarding, verifying the fix actually worked was the natural next
  step rather than assuming it did.

## Phase 10 — WAAP Post-Onboarding Re-Verification
- **Goal:** re-run Phase 8's checks after onboarding completion.
- **Evidence:** the identical three calls, same token file, correct
  domain this time.
- **Discovery:** all three results byte-for-byte identical to
  Phase 8 — onboarding did not unlock access.
- **Result:** corrects, not merely reconfirms, Phase 9's root cause.
- **Architecture impact:** none — WAAP remains fully designed,
  entirely unbuilt.
- **Why next phase started:** no Phase 11 exists yet — four
  unconfirmed explanations were recorded and ranked in this
  session's follow-up analysis (§8 above), leaving this the current,
  unresolved end state.

---

# 10. Technical Debt

## Critical

- **Public-narrative/verified-reality divergence** (`sentinelops-homepage/src/data/content.js` vs. `docs/MVP3_WAZUH_INVESTIGATION.md`, `docs/HOME_SOC_SOURCE_DISCOVERY.md`, and the TheWall repo's actual language stats). Why it exists: the marketing copy appears to have been written aspirationally or for a different intended setup and never reconciled against the engineering reality this project's own discovery work later established. Impact: this is the operator's hiring-facing portfolio — its core value proposition is "real, not simulated" work; specific, falsifiable claims (a SIEM that doesn't exist, sensors that aren't installed, a game project described as a security tool) directly undermine that proposition the moment anyone checks. Risk: reputational, immediate, zero technical cost to have prevented. Recommended priority: fix before any new feature work — this is a content edit, not an engineering task.
- **VNETWORK API key exposure** (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §7). Why it exists: a live token was pasted into a chat transcript while being passed into a shell. Impact: full account compromise for the exposure window (mitigated — rotated immediately). Risk: this is a realized security event, not a hypothetical; the same unscoped-key architecture (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`) means it can happen again with the same blast radius. Recommended priority: adopt a stricter secret-handling procedure (file-based, never typed inline) as standard practice going forward — this session already started doing so after the incident.

## High

- **WAAP integration fully designed, zero percent live** (§8). Why it exists: entitlement gap, root cause still open. Impact: blocks `NEXT_STEPS.md`'s #1 priority and the highest-ROI data source identified across the whole VNETWORK research track. Risk: continued engineering investment (threshold decisions, mapper code) would be premature until access is confirmed. Recommended priority: resolve the single entitlement-check validation step (§8) before any further design work on this track.

## Medium

- **`sentinelops-security-incidents` repo, empty, unreferenced, purpose undetermined** (§3). Why it exists: unknown — possibly an abandoned early idea. Impact: a name that strongly implies it's the incident destination, when it isn't — a real trap for the next person (or AI) who assumes it based on the name alone. Risk: low technical risk, moderate confusion risk. Recommended priority: resolve with a one-line decision (delete, repurpose, or document its intended future role) — trivial effort.
- **`security-watch.js` control-key bug** (§5). Why it exists: a naming mismatch between rule definitions (`firewall`/`defender`) and the baseline/state object's actual keys (`fw`/`def`), introduced when the two were written and never reconciled. Impact: two of five alert types silently lose their `baseline_value`/`current_value` fields (the alert itself still fires correctly — only the evidence detail is dropped). Risk: low-medium — a real investigator working an alert has slightly less context than intended. Recommended priority: a small, contained fix once `security-watch.js`'s source is located (it wasn't found in the local checkout, §5).
- **Healthcheck Webhook Receiver's two independent blockers** (§7). Why they exist: VNETWORK hasn't published the HMAC/payload spec, and the `audit.sentinelops.fyi` backend owner was never identified on this machine. Impact: blocks `NEXT_STEPS.md`'s #2 priority entirely. Risk: low — nothing is built yet, so nothing is at risk of being built wrong; the risk is purely opportunity cost. Recommended priority: capture one real test delivery (cheap, well-scoped) and get a direct answer on `audit.sentinelops.fyi` ownership.
- **`export-home-soc-reports.js` and its data sources not found locally** (§5). Why it exists: the script apparently lives in a different local tree (`AppData\Roaming\Claude\Projects\mcp-cyber-tools`) than the one reviewed for this document. Impact: Pipeline B (§5) cannot be verified end-to-end from source, only from its documented behavior and live output. Risk: low today (the pipeline is visibly working), but means any bug in that script is currently unauditable from this checkout. Recommended priority: confirm the canonical location and reconcile the two trees, or document why two trees exist.

## Low

- **`server_v2.js`/`server_backup_v1.js`, byte-identical, orphaned** (§6). Why it exists: unknown — likely superseded prototypes never removed. Impact: minor — dead code, but could confuse a future contributor into extending the wrong file. Risk: low. Recommended priority: delete or clearly mark deprecated, whenever convenient.
- **Dormant `home-soc-state` pipeline** (§5). Why it exists: an earlier, separate Home-SOC implementation, superseded by `security-watch.js` but never decommissioned. Impact: minor confusion risk, same class as the two server files. Risk: low. Recommended priority: archive or document its retirement.
- **`cybersecurity-labs` containing a near-duplicate of `kevin-cyber-security-copilot`'s app** (§3). Why it exists: apparent copy-paste during setup, never diverged or removed. Impact: minor — makes the repo's actual identity (learning labs vs. another copilot demo) ambiguous. Risk: low. Recommended priority: low, cosmetic.
- **`network-security-audit-frontend/DEPLOYMENT.md`'s leftover reference to `huong-pharmacy-ai-copilot`** (§17). Why it exists: a copy-pasted deployment guide from an unrelated template, never edited for this project. Impact: cosmetic, momentarily confusing to a new reader. Risk: none. Recommended priority: low.

---

# 11. Hidden Risks

Categorized; every entry cites its evidence, none is speculative.

**Documentation / Operational (the largest category, and the one most
likely to be missed by reading only the top-level status docs):**
- The public portfolio's `content.js` makes a series of specific,
  falsifiable operational claims that this project's own discovery
  documents contradict or cannot substantiate:
  - *"Home-SOC SIEM (Wazuh)... ~40k events/day"* — directly
    contradicted by `docs/MVP3_WAZUH_INVESTIGATION.md`'s exhaustive,
    multi-method confirmation that Wazuh is not installed anywhere on
    this host.
  - *"Suricata / Zeek Sensors... 3/3 online"* — Suricata confirmed
    not installed by the same investigation and independently by
    `docs/HOME_SOC_SOURCE_DISCOVERY.md`; Zeek is never mentioned or
    checked in any discovery document reviewed.
  - *"Honeypot Cluster... 860+ sessions logged (7d)"* — no honeypot
    infrastructure appears anywhere in any repository or discovery
    document reviewed this session.
  - *"TheWall... Public-facing visualization of blocked attacker
    traffic... 2.4k+ events streamed (7d)"* — `TheWall`'s own GitHub
    repository is confirmed (via `gh api`'s `languages` endpoint) to
    be 68KB of GDScript plus supporting JS/HTML — the language and
    file-size signature of a Godot game project, not a security data
    visualization tool.
  - *"mcp-cyber-tools API... Tool calls audited: 100%"* — no
    audit-logging or call-tracking code was found anywhere in
    `modules/shared.js` or any other module reviewed for this
    document.
  - *Threat Report #001* — a dated, specific incident report (6
    malicious requests, injection classification, blocked at the
    edge, `audit.sentinelops.fyi`) that this project has never had
    the working WAAP API access needed to generate, verify, or
    reproduce through its own tooling (the entire WAAP investigation,
    contemporaneous with this report's dated content, found zero
    working access to WAAP log data for any domain).
  - **Note on what this does *not* prove:** it does not prove these
    systems are fabricated — some (a manually-configured WAAP rule
    set, a console-only-viewed report) could be real but simply
    outside this project's own tooling's visibility. What it *does*
    establish is that **none of these specific claims are
    corroborated by anything in the codebase or discovery record
    reviewed**, and at least three (Wazuh, Suricata, TheWall) are
    directly and confidently contradicted by direct, methodical
    checks this project already performed for other reasons.
- **Domain mismatch in the WAAP narrative:** the homepage's
  `wafCaseStudy` describes full WAAP protection specifically for
  `audit.sentinelops.fyi` (*"100% Public traffic routed through
  VNetwork WAAP," "0 Direct-to-origin requests reaching Render"*).
  The WAAP onboarding actually completed during this investigation
  (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §8) was for a **different
  domain**, `www.sentinelops.fyi`. Either `audit.sentinelops.fyi` has
  a separate, older WAAP configuration never touched or documented by
  this discovery track, or the case study's claims were written ahead
  of the actual provisioning work — which, per this project's own
  evidence, only started being done (and for the wrong domain) during
  this very investigation. This is not resolvable from the evidence
  available; it is flagged as a real open question, not asserted
  either way.

**Ownership:**
- The source repo/Render service behind `audit.sentinelops.fyi` is
  unknown — searched across every local tree available and not found
  (`PROJECT_STATUS.md`, MVP #5 section). This blocks the Healthcheck
  receiver and means nobody reviewing this codebase can currently
  modify or audit that live service's code.
- `sentinelops-security-incidents`'s intended owner/purpose is
  undetermined (§3, §10).

**Security:**
- The account-wide, unscoped VNETWORK API key
  (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`) already had one real
  exposure incident this session (§10, Critical). The underlying
  architectural condition (no per-service scoping, no documented
  rotation/audit API) has not changed and cannot be changed from this
  project's side — it's a VNETWORK platform limitation, not something
  fixable in the codebase.

**Dependency:**
- Two demo apps (`kevin-cyber-security-copilot`, `cybersecurity-labs`)
  depend on the Groq API with no documented fallback, rate-limit
  handling beyond Flask defaults, or cost-monitoring visible in the
  reviewed source.
- The entire WAAP/Healthcheck integration track depends on a single
  vendor (VNETWORK) whose own published API documentation has a
  confirmed gap (`{{URL}}` template variable, §8) — meaning even
  VNETWORK's own reference material isn't fully self-consistent.

**Architectural:**
- The MCP server (95 tools) and the incident-creation pipeline are
  two separate code paths (§6) that happen to coexist in one repo —
  a future contributor could reasonably assume the incident scripts
  run *through* MCP and be wrong.
- Two "shadow" implementations exist that look production-like but
  aren't: `home-soc-state` (superseded, dormant) and
  `server_v2.js`/`server_backup_v1.js` (superseded, orphaned) — both
  are real risk for a future contributor (human or AI) who globs for
  matching filenames without checking which one is actually wired in.

---

# 12. Architectural Constraints

Rules this project already follows in practice, evidenced by
repeated behavior across every phase, not stated as a formal policy
document (except where noted):

- **Reuse the existing incident pipeline unconditionally.** Every new
  alert source (Defender, `security-watch.js`, and every planned one
  — WAAP, Healthcheck) adds only a `to_alert()` mapper and calls the
  same `score_alert`/`build_issue`/`create_issue`/`assign_issue`/
  `compute_labels`/`build_analysis_comment` chain, unchanged. Never a
  parallel pipeline.
- **GitHub Issues as the sole incident state — no separate database.**
  Duplicate detection reads GitHub itself (title match + "Last Seen"
  timestamp) rather than maintaining a local state file
  (`PROJECT_STATUS.md`, MVP #3).
- **JSON files, not databases, for local state.**
  `security-watch.js`'s `baseline.json`/`state.json`,
  `home-soc-reports`'s three fixed-name published files — no SQL/NoSQL
  database anywhere in the reviewed system.
- **No dashboards.** Explicitly stated as a constraint for the Digital
  Risk Twin (`NEXT_STEPS.md`) and consistent with the "GitHub Mobile
  as the SOC console" idea already recorded
  (`docs/VNETWORK_CAPABILITY_ASSESSMENT.md`, "Crazy But Realistic
  Ideas").
- **Poll-and-diff over push, until a real push mechanism exists.**
  `security-watch.js` polls and diffs against baseline; VNETWORK's API
  has no native alerting, so the same shape was adopted for the
  planned WAAP integration.
- **Verify before building — the project's strongest working
  discipline.** Every discovery pass in the reviewed record
  re-checked a claim against live evidence rather than trusting
  documentation or assumption: the Wazuh check (multi-method,
  exhaustive), the Suricata check (repeated independently), the DNS/
  HTTP check on both `sentinelops.fyi` and `audit.sentinelops.fyi`
  rather than assuming from names, the token-rotation-and-retest
  habit after the exposure incident, and the post-onboarding
  re-verification pass (which caught that the "fix" hadn't actually
  worked).
- **Credentials never committed; environment variables only.**
  `GITHUB_TOKEN`, and (after this session's incident) VNETWORK's token
  read from a local, non-committed file — consistent pattern across
  every script.
- **Documentation-only discovery passes are explicitly labeled as
  such**, with an "Explicitly not done in this pass" section in every
  `docs/*.md` file, distinguishing research from implementation at the
  document level.

---

# 13. Asset Utilization Review

| Asset | Current use | Potential use | Underutilization | ROI opportunity |
|---|---|---|---|---|
| `sentinelops.fyi` | Static portfolio narrative; contains unreconciled/unverifiable operational claims (§11) | Could become the true public face of the real system — a "Live Infrastructure" panel sourced from actual GitHub API issue counts and `home-soc-reports`'s real published JSON, instead of hardcoded figures | **High** — currently a liability as much as an asset | Very high, near-zero cost: reconcile content with reality using data the project already produces |
| `audit.sentinelops.fyi` | Real, live, DNS-confirmed WAAP-fronted Render service; backend source unknown | The confirmed target for the Healthcheck webhook receiver (§7) and, per the homepage's own case study, the intended WAAP-protected surface | **High** — its own backend can't currently be extended by anyone reviewing this codebase | High once ownership is resolved — a single conversation, not engineering work |
| `contact@sentinelops.fyi` / `kevin@sentinelops.fyi` | Contact-form `mailto:` links only (`content.js`) | Could be a destination for an automated digest (e.g. weekly Home-SOC/incident summary) | **High** — no automation targets either address today | Medium — a small addition to existing scripts |
| Home-SOC | Live, working, low current signal volume (0 open alerts) | Feed into the Digital Risk Twin once WAAP/Healthcheck exist (`NEXT_STEPS.md`) | **Low** — genuinely used as designed | Already realized; future value is additive, not corrective |
| WAAP | Fully designed, zero live integration | The highest-ranked data source across every VNETWORK discovery pass | **Very high** — fully designed capability sitting entirely idle | Highest of any single item in this table once the access blocker clears |
| MCP | 95 tools, manually invoked via Claude Desktop | Could directly power incident enrichment (currently the Python scripts duplicate logic MCP tools could supply) | **Medium** — a real, working capability set mostly used ad hoc, not by automation | Medium — would tighten the architecture, not add new capability |
| GitHub | The incident system's entire backbone (issues, labels, assignment, mobile) | Already close to fully utilized for its role | **Low** | Already realized |
| GitHub Mobile / iPhone | The de facto SOC console, per the project's own stated idea | Same — already the intended end-state | **Low** | Already realized |
| `sentinelops-security-incidents` | Unused, empty | Undetermined — could be repurposed or retired | **Total (100%)** | Zero until a decision is made; currently pure overhead/confusion |

---

# 14. Current State Assessment

**Truly complete** (built and verified against real events):
- MVP #1–#4 pipeline: fake-alert → Defender → `security-watch.js`
  live telemetry → labeled/enriched GitHub incidents
  (`PROJECT_STATUS.md`, Issue #6, real occurrences 1→2→3).
- The 95-tool MCP server (`server.js`) as a Claude Desktop capability
  set (directly counted from source, §6).
- The Home-SOC sanitized publication pipeline to `home-soc-reports`
  (live output confirmed, `BASELINE-LATEST.json` current as of
  2026-09-04).

**Partially complete:**
- WAAP integration — schema, auth, payloads, and MCP plan 100%
  designed (`docs/WAAP_LOG_SEARCH_SCHEMA.md` §1–§6); live access 0%
  (§8).
- Healthcheck Webhook Receiver — plan 100% designed
  (`docs/MVP5_WEBHOOK_RECEIVER_PLAN.md`); implementation 0%.

**Blocked:**
- WAAP live API access (leading hypothesis identified, not yet
  validated, §8).
- Healthcheck implementation (HMAC spec + deployment owner both
  unresolved, §7, §10).

**Experimental / orphaned** (not "in progress," genuinely unmaintained
per the evidence):
- `server_v2.js`/`server_backup_v1.js` — byte-identical, unreferenced
  (§6).
- The dormant `home-soc-state` pipeline (§5).
- The Digital Risk Twin — explicitly "a concept sketch only,"
  `NEXT_STEPS.md`'s own words, no discovery pass performed.

---

# 15. CTO Strategy

Constraints as given: no new paid services, no Kubernetes, no Redis,
no unnecessary databases, no unnecessary dashboards, use existing
assets first. `sentinelops.fyi` at the center.

**1. Fix the narrative-vs-reality gap before anything else.** This is
the only item in this entire review that is simultaneously the
highest-impact and the lowest-cost — it is a content edit to
`content.js`, not an engineering task, and it directly protects the
one asset (the portfolio's credibility) every other piece of work in
this project exists to build toward (§2). Doing new engineering work
before this is fixed means building on top of a foundation that
actively contradicts the work's own purpose.

**2. Make `sentinelops.fyi` genuinely central by making it *read
from* the real system instead of describing it from memory.** The
`home-soc-reports` repo already publishes real, current, sanitized
JSON on a schedule (§5) — the homepage's static site could fetch and
render that data directly (client-side, no new backend, no new
service) instead of hardcoding numbers. This uses an asset that
already exists (`home-soc-reports`) to solve a problem (§11's
credibility gap) with zero new infrastructure — directly satisfying
"use existing assets first."

**3. Resolve WAAP access with the cheapest possible step before
spending any more design time on it.** The schema and MCP plan are
already complete (§8) — the only remaining work is a single
entitlement-verification conversation (Partner Portal or VNETWORK
support), not more engineering. Do not build
`scripts/create_waap_incident.py` until that step confirms access,
per this project's own "verify before building" discipline (§12).

**4. Once WAAP access is confirmed, build it exactly per the existing
plan — no new infrastructure.** `scripts/create_waap_incident.py`
reusing the unchanged pipeline (§7), one new label, one new
`ENRICHMENT_RULES` entry — this is additive to what already exists,
matching every constraint given.

**5. Treat GitHub Issues + GitHub Mobile as the permanent dashboard.**
This is not a compromise — it's already the project's own stated
ideal (§12), and it satisfies "no unnecessary dashboards" by
construction rather than by restraint.

**6. Resolve `audit.sentinelops.fyi` ownership before touching the
Healthcheck receiver.** This is a single question to the operator, not
work — but it blocks real engineering (§7, §10) until answered.

**7. Build the Digital Risk Twin, if and when built, as a JSON
state-file diff — the same pattern `security-watch.js` already uses,
generalized.** `NEXT_STEPS.md` already specifies this constraint
explicitly ("No dashboards, no databases, no new infrastructure
implied by default") — the CTO strategy here is simply: do not deviate
from the project's own already-stated design intent when this becomes
buildable (after #3–#4 and the Healthcheck receiver both exist).

**8. Retire or repurpose the two "shadow" implementations
(`server_v2.js`/`server_backup_v1.js`, `home-soc-state`) and decide
`sentinelops-security-incidents`'s fate.** Zero cost, removes real
confusion risk for whoever operates this system next (§11).

This strategy adds no new services, no new infrastructure, and no new
paid dependencies — every recommended action either fixes an existing
asset's accuracy, unblocks an already-designed integration via a
verification step (not new engineering), or removes dead weight.
`sentinelops.fyi` becomes the center of the architecture not by adding
a dashboard to it, but by making it the one place that actually,
verifiably reflects what `mcp-cyber-tools` is really doing.

---

# 16. Immediate Priorities

Top 10, ranked by impact, each with Benefit / Effort / Risk /
Dependency.

1. **Reconcile `sentinelops.fyi`'s claims with verified reality.**
   Benefit: high (protects the portfolio's core credibility). Effort:
   low (content edit only). Risk: none. Dependency: none.
2. **Resolve the WAAP account/token entitlement question (§8's
   leading hypothesis).** Benefit: high (unblocks the #1-ranked
   integration). Effort: low (one verification step, not engineering).
   Risk: none. Dependency: VNETWORK Partner Portal or support access.
3. **Decide the WAAP alert-worthy threshold and confirm the `domains`
   list.** Benefit: medium-high. Effort: low (a decision, not
   discovery — `NEXT_STEPS.md` already frames it this way). Risk:
   none. Dependency: #2.
4. **Build `scripts/create_waap_incident.py` and the
   `vnetworkWaapSearch` MCP tool.** Benefit: high (adds the first
   edge-layer signal to the pipeline). Effort: medium. Risk: low
   (reuses proven pipeline code). Dependency: #2, #3.
5. **Capture one real Healthcheck webhook delivery** (temporary
   Monitor against a logging-only endpoint). Benefit: medium. Effort:
   low. Risk: none. Dependency: a VNETWORK Monitor configured to fire.
6. **Resolve `audit.sentinelops.fyi` backend ownership.** Benefit:
   medium (unblocks the Healthcheck receiver). Effort: low (one
   question to the operator). Risk: none. Dependency: none.
7. **Make `sentinelops.fyi` read `home-soc-reports`'s real published
   JSON instead of hardcoded figures.** Benefit: high (directly closes
   §11's largest hidden risk, no new backend). Effort: low-medium
   (client-side fetch against an already-public URL). Risk: none.
   Dependency: none.
8. **Clarify `sentinelops-security-incidents`'s fate** (repurpose or
   retire). Benefit: low-medium (removes a real trap for future
   maintainers, §11). Effort: very low. Risk: none. Dependency: none.
9. **Fix `security-watch.js`'s control-key bug** (`firewall`/
   `defender` vs. `fw`/`def`). Benefit: low-medium (restores dropped
   evidence fields on 2 of 5 alert types). Effort: very low, once the
   script's canonical location is confirmed (§5, §10). Risk: low.
   Dependency: locating the script.
10. **Decide the fate of the dormant `home-soc-state` pipeline and the
    orphaned `server_v2.js`/`server_backup_v1.js`.** Benefit: low
    (removes confusion risk for future contributors, §11). Effort:
    very low. Risk: none. Dependency: none.

---

# 17. Knowledge Another AI Would Miss

Everything here is either absent from, or not connected together in,
`PROJECT_STATUS.md`, `NEXT_STEPS.md`, `ARCHITECTURE_SUMMARY.md`, or
`SENTINELOPS_DISCOVERY_TIMELINE.md` alone.

**1. The public site and the verified engineering tell different
stories, and no existing top-level document says so.** This is the
single biggest thing a fresh reader would miss. `PROJECT_STATUS.md`
and the timeline both live entirely inside `mcp-cyber-tools`'s
backend investigation — neither one cross-references
`sentinelops-homepage/src/data/content.js`'s specific marketing claims
against what the backend investigation itself proved. Only by reading
both together (as this document does, §11) does the gap become
visible: a claimed Wazuh SIEM the project's own investigation
proved doesn't exist; claimed Suricata/Zeek sensors likewise
disproven; a claimed security-visualization tool (TheWall) that is
actually a Godot game by its own repository's language statistics; a
claimed "100%" audit-logging capability with no corresponding code
anywhere; and a dated threat report describing WAAP protection this
project has never had working API access to verify.

**2. The WAAP onboarding domain doesn't match the case-study
domain.** The homepage's `wafCaseStudy` is specifically about
`audit.sentinelops.fyi`. The WAAP onboarding actually completed
during this investigation was for `www.sentinelops.fyi`. These are
different domains. Nothing in `PROJECT_STATUS.md` or `NEXT_STEPS.md`
flags this mismatch — you have to read the homepage content and the
WAAP schema doc side by side to see it. It's genuinely unclear from
the evidence whether `audit.sentinelops.fyi` has its own separate,
older, undocumented WAAP setup, or whether the case study describes
work that — per this project's own investigation — has in fact never
been completed for that domain.

**3. "Verify before building" is this project's actual working
culture, not just a one-off habit.** It shows up identically in
completely unrelated investigations: exhaustively checking Wazuh
absence by five different methods rather than trusting a "not
installed" assumption; checking both candidate domains by DNS/HTTP
rather than reasoning from their names; re-testing WAAP access after
the fix instead of assuming the fix worked (which is exactly what
caught that it hadn't). A future contributor — human or AI — should
match this discipline, not treat it as this project being unusually
cautious for no reason.

**4. Two "shadow" implementations exist that look real but aren't
current.** `home-soc-state` (a dormant, separate Home-SOC pipeline,
superseded by `security-watch.js` but never deleted) and
`server_v2.js`/`server_backup_v1.js` (an orphaned, byte-identical
alternate MCP server, superseded by the modular `server.js` but never
deleted). Someone exploring the codebase by filename pattern alone —
rather than checking `package.json`'s `main` field or the scheduled
task names — could easily build on the wrong one.

**5. `sentinelops-security-incidents` is a name-based trap.** It
sounds exactly like where incidents should live. It's empty. The real
destination, confirmed by hardcoded constants in
`scripts/create_test_incident.py`, is GitHub Issues on
`mcp-cyber-tools` itself.

**6. `mcp-cyber-tools`'s root directory also contains an entirely
separate, unrelated historical initiative** — `EXECUTION_DISCIPLINE.md`,
`BUG_TRACKER.md`, and a dozen `TIER1`/`TIER2`/`TIER3`/`QA`-prefixed
files describing a "v1.0.2 QA phase" (Aug 21–Sep 11, 2026) for testing
the 95 MCP tools themselves, with its own strict "NO SCOPE CHANGES"
rule. This is a **different, earlier, time-boxed sprint effort**, not
a currently-binding constraint on the SentinelOps/WAAP discovery work
documented elsewhere in this same repo. A future AI glancing at
`EXECUTION_DISCIPLINE.md`'s "🚨 RULE #1: NO SCOPE CHANGES" could
mistakenly conclude the WAAP research (which has clearly continued
well past that sprint's dates) is out of policy. It isn't — the two
efforts are separate tracks that happen to share a repository.

**7. `cybersecurity-labs` isn't just lab exercises — it also secretly
runs a near-duplicate of `kevin-cyber-security-copilot`'s app as its
own separate Render deployment.** A future contributor treating
`cybersecurity-labs` as "the labs repo" might miss that it's also
independently serving a live copilot demo under its own domain.

**8. `network-security-audit-frontend/network-security-audit/DEPLOYMENT.md`
contains a leftover instruction to "Select repository
`huong-pharmacy-ai-copilot`"** — a copy-pasted deployment guide from
an entirely unrelated template project, never edited for this repo.
Harmless, but would confuse anyone following the doc literally.

**9. The portfolio's own "featured projects" lists don't agree with
each other.** `sentinelops-homepage/PROJECT.md` lists `mcp-cyber-tools`,
`home-soc-reports`, `network-security-audit-frontend`, and
`kevin-cyber-security-copilot`. The GitHub profile README
(`KEVIN-NGUYENDAD/KEVIN-NGUYENDAD/README.md`) lists those same four
plus `TheWall` and `Sass AI App` — both unrelated to security. There
is no single canonical answer, anywhere in the reviewed evidence, to
"what counts as part of SentinelOps."

**10. The credential-exposure incident this session is a real,
lived example of the unscoped-API-key risk `docs/VNETWORK_CAPABILITY_ASSESSMENT.md`
predicted in the abstract.** That document flagged, purely as a
documentation finding, that a leaked VNETWORK key would be a
full-account compromise with no available scoping or rotation API.
Weeks (in document-time) later, in this same investigation, exactly
that class of event happened for real — a token was briefly exposed
and had to be rotated. The response (immediate rotation, retest before
trusting the new token, moving to file-based credential handling) is
the correct playbook and is worth preserving as institutional memory,
not just as a line item in the timeline.

**11. `security-watch.js` and `export-home-soc-reports.js` — two of
the most load-bearing scripts in the entire Home-SOC pipeline —
were never found in the local `mcp-cyber-tools` checkout used for this
and the prior discovery documents.** Their *output* and *documented
behavior* are confirmed live and correct; their *source code* is not
present in this tree. They apparently live in a separate local path
(`C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\`).
Any future audit or bug fix targeting these scripts needs to locate
the correct tree first — assuming they're in this repository (as their
GitHub-hosted documentation implies) would be wrong.
