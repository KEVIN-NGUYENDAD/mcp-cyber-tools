# HOME SOC — Release Notes v1.0

**Tag:** `HOME-SOC-v1.0`
**Date:** 2026-08-30
**Status:** MVP complete — entering observation mode

---

## What this release does

Collects the security posture of a home network and endpoint, strips every
identifier from it, publishes the sanitized result to a public feed, and has
Claude read that feed to send a daily bulletin by email.

The problem it solves: Claude Scheduled tasks run in the cloud and cannot reach
a private repository or a local machine. v1.0 closes that gap with a sanitized
public projection instead of granting cloud access to private data.

---

## Major capabilities

### Endpoint control collection
`security-watch.js` reads five Windows security controls — DNS resolvers,
firewall, real-time protection, RDP listener, SSH listener — compares them
against an approved baseline, and records any divergence as a CRITICAL alert.

- One-shot, no daemon. Task Scheduler owns the cadence.
- No elevation required. All five probes verified working as a standard user.
- No email dependency. Delivery is downstream.
- Baseline is never created implicitly — `--approve-baseline` is an explicit act.
- 4-hour cooldown per alert type suppresses repeat notifications.

### Network inventory
`iot-device-scanner.js` enumerates devices on the LAN, identifies them by
hardware-address vendor prefix, probes open ports, and verifies services by
banner rather than assuming from the port number.

### Sanitizing exporter
`export-home-soc-reports.js` projects the private data into three public files.

| Input | Published as |
|---|---|
| private LAN address | `link: lan` |
| hardware address | `id: camera-01` |
| vendor, model, firmware | discarded |
| port number | service class (`web-ui`, `video-stream`, …) |
| DNS resolvers | provider class (`isp_default`, `public_resolver`, …) |

### Leak guard
Before any byte is written, the exact output is swept for hardware addresses,
IPv4/IPv6 addresses, credential keywords, private-key blocks, vendor names, and
the WiFi network name.

**It is a gate, not a filter.** It does not scrub — a single match aborts the
run before writing and before pushing. A partial or half-sanitized publish is
not a reachable state.

### Public feed
`home-soc-reports` holds exactly three files with fixed names, always
overwritten. A deny-by-default `.gitignore` means an unsanitized file cannot be
committed by accident.

### Daily bulletin
A Claude Scheduled task fetches the three raw URLs at 20:10 and emails a
Vietnamese bulletin: executive summary, devices, network status, findings, risk
assessment, recommended actions, changes since the previous bulletin.

---

## Architecture summary

```
endpoint + LAN
      ↓
security-watch.js        →  baseline.json · state.json · alerts.json
      ↓
iot-device-scanner.js    →  network-scan-*.json
      ↓
export-home-soc-reports.js
      ↓  sanitize
      ↓  LEAK GUARD  (abort on any match)
      ↓
home-soc-reports  (public, 3 files)
      ↓
Claude Scheduled 20:10   (anonymous fetch, no credentials)
      ↓
🏠 Home Security Bulletin  →  Email
```

Full detail in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Validation results

Nine capabilities proven against real data. Evidence and timestamps in
[VALIDATION-REPORT.md](VALIDATION-REPORT.md).

| Capability | Result |
|---|---|
| Scanner | PASS — 27.7 s, exit 0 |
| Exporter | PASS — commit pushed same second as scan |
| Leak guard | PASS — caught a real leak, aborted correctly |
| Sanitization | PASS — 0 identifiers across 5 tracked files |
| Public feed | PASS — 3/3 HTTP 200 anonymous |
| Alert engine | PASS — CRITICAL fired on simulated divergence |
| Cooldown | PASS — duplicate suppressed |
| Scheduled bulletin | PASS — generated and delivered |
| Control coverage | PASS — 6/6, `controls_unknown: 0` |

---

## Known limitations

These are real. None is a bug; all are boundaries of what v1.0 covers.

**1. The chain has never run unattended.**
Every execution so far was manually triggered. The 19:45 trigger fires for the
first time on the evening of 2026-08-30. Until it does, "fully automated" is a
design claim, not an observed fact.

**2. Endpoint coverage is one machine.**
`security-watch.js` reads the host it runs on. The laptop, phones, and tablet
have no endpoint agent — they appear only as network inventory, if the scanner
sees them at all.

**3. The scanner sees only what is in the ARP table.**
The last scan found 2 devices. An earlier manual audit listed 6. Devices that
are asleep, idle, or have not communicated recently are absent — and the
bulletin will report the smaller number without noting that devices went
missing. A device disappearing looks the same as a device that was never there.

**4. The alert engine was proven by simulation, not by a real incident.**
The CRITICAL alert was triggered by editing `baseline.json`, not by a control
actually changing. The rule logic, alert write, cooldown, and RED escalation are
all proven — but no genuine security change has yet travelled the chain.

**5. The leak guard covers three files, not the repository.**
It sweeps the exporter's own output. It does not check `README.md` or anything
else committed by hand. A real leak was found in `README.md` by a separate
manual sweep, not by the guard.

**6. The public repo is public.**
The three files are sanitized, but they still publish a posture summary: how
many devices exist, what classes of service they run, whether the firewall is
on, and when the data was collected. That is a deliberate trade — it is the only
way a cloud task reads the feed without credentials — but it is not zero
disclosure.

**7. A 4-hour cooldown can hide a recurrence.**
Once an alert type fires, the same type is silent for four hours. A control that
is disabled, restored, and disabled again inside that window produces one alert,
not two.

**8. The machine must be on at 19:45.**
`-StartWhenAvailable` runs the task late if the machine was off, but a bulletin
generated at 20:10 will then read whatever data exists at that moment.

**9. Data staleness is flagged, not escalated.**
Past 48 hours the feed sets `stale: true` and the bulletin says so. It does not
raise the risk level. A collector that stopped a week ago still reports GREEN
with a staleness note.

**10. The bulletin can read a superseded copy of the feed, for hours.**
**→ Tracked as OPEN-001 · Status: MONITOR**

*Severity: this is the most serious open defect in v1.0.*

Full record, including the mitigation and its exit criteria, in
[VALIDATION-REPORT.md](VALIDATION-REPORT.md) § Open issues.

The freshness check reads the timestamp *inside* the fetched file, not whether
that file is the newest published version. A superseded copy carries its own
timestamp, so the bulletin cannot tell it is reading old data.

Observed twice on 2026-08-30/31:

| | Bulletin read | Feed actually served |
|---|---|---|
| Run 1 | `21:55:53Z`, `controls_unknown: 4` | `22:10:01Z`, `controls_unknown: 0` |
| Run 2, ~3 h later | `21:56Z`, `controls_unknown: 4` | `22:10:01Z`, `controls_unknown: 0` |

At the time of run 2 both `raw.githubusercontent.com` and the GitHub API served
the current file, and the newest commit was nearly three hours old. So this is
**not** the ~5-minute CDN window — the caching is in the fetch layer used by the
scheduled task, and it persisted for at least 2 h 51 m.

An earlier version of this note claimed the 24-minute gap between the 19:45
chain and the 20:10 bulletin made the scheduled path safe. **That was wrong.**
A cache lasting hours defeats any gap of minutes.

Consequence: after an incident is fixed and the chain re-run, the next bulletin
may still describe the pre-fix state — while reporting `stale: false`.

Mitigation applied (task prompt and documentation only, no code change): a
cache-busting query parameter per run, a mandatory age check computed against
the current time rather than the `stale` field, and a confidence warning printed
above all other content when the gap exceeds three hours.

Until OPEN-001 exits MONITOR, treat the bulletin's control states as advisory
and confirm from the source before acting on them:

```powershell
$a = Invoke-RestMethod "https://api.github.com/repos/KEVIN-NGUYENDAD/home-soc-reports/contents/BASELINE-LATEST.json?ref=main" -Headers @{"User-Agent"="v"}
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($a.content)) | ConvertFrom-Json | Select-Object source_scan_at, risk_level -ExpandProperty coverage
```

A proper fix belongs in the scheduled task prompt (cache-busting URL plus an
explicit age check against the current time), not in the pipeline.

---

## Operational status

| Component | Schedule | State |
|---|---|---|
| `HOME-SOC-Scan-And-Export` | Daily 19:45 | Registered, exit 0 on manual run |
| 🏠 Home Security Bulletin | Daily 20:10 | Active, delivered |
| Public feed | On each export | 4 commits, live |
| Private repo | — | Unchanged, still private |

**Current posture:** GREEN · 0 alerts · 6/6 controls · 2 devices · data 0 h old

---

## Freeze

v1.0 is frozen. Until seven consecutive days of successful unattended operation:

- No new features
- No architecture changes
- Bug fixes only

The counter starts on the first 19:45 run that completes without intervention.
Track it in [RUNBOOK.md](RUNBOOK.md).
