# HOME SOC — Architecture

**Version:** 1.0 · **Frozen:** 2026-08-30

---

## The constraint that shaped everything

Claude Scheduled tasks run in Anthropic's cloud. They cannot reach a private
GitHub repository, and they cannot reach this machine. The GitHub Integration
connector serves Chat, Projects, and remote Claude Code sessions — it does not
give a scheduled cloud task repository tools.

Two ways out: make the private repo public, or publish a sanitized projection.

The private repo holds hardware addresses, internal addressing, router
configuration, and audit history — a map of the network. Publishing it would
hand an attacker the reconnaissance phase. So v1.0 publishes a projection: state
and verdicts, never identifiers and addresses. A reader can tell whether the
network is healthy and cannot tell which network it is.

Everything below follows from that single decision.

---

## Full pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCES                                                        │
│                                                                 │
│   Desktop (this host)   Laptop   WiFi   IoT devices             │
│         │                  │       │        │                   │
│         │                  └───────┴────────┘                   │
│         │                          │                            │
│         │                   (network-visible only)              │
└─────────┼──────────────────────────┼────────────────────────────┘
          │                          │
          ▼                          ▼
┌───────────────────────┐  ┌──────────────────────────┐
│ security-watch.js     │  │ iot-device-scanner.js    │
│                       │  │                          │
│ DNS resolvers         │  │ ARP enumeration          │
│ Firewall              │  │ Vendor-prefix ID         │
│ Real-time protection  │  │ Port probe               │
│ RDP listener          │  │ Banner verification      │
│ SSH listener          │  │                          │
│                       │  │ ~28 s                    │
│ vs approved baseline  │  │                          │
│ 4 h cooldown          │  │                          │
└───────────┬───────────┘  └────────────┬─────────────┘
            │                           │
            ▼                           ▼
  baseline.json                network-scan-*.json
  state.json
  alerts.json
            │                           │
            └─────────────┬─────────────┘
                          ▼
        ┌─────────────────────────────────────┐
        │  export-home-soc-reports.js         │
        │                                     │
        │  1. read newest of each artifact    │
        │  2. SANITIZE                        │
        │  3. derive alerts + risk level      │
        │  4. LEAK GUARD                      │
        │  5. git add -f · commit · push      │
        └─────────────────┬───────────────────┘
                          ▼
        ┌─────────────────────────────────────┐
        │  home-soc-reports  (PUBLIC)         │
        │                                     │
        │  ROUTER-SECURITY-AUDIT-LATEST.md    │
        │  BASELINE-LATEST.json               │
        │  DEVICE-SUMMARY.json                │
        └─────────────────┬───────────────────┘
                          │  raw.githubusercontent.com
                          │  anonymous, no credentials
                          ▼
        ┌─────────────────────────────────────┐
        │  Claude Scheduled — daily 20:10     │
        │  🏠 Home Security Bulletin          │
        └─────────────────┬───────────────────┘
                          ▼
                        Email
```

---

## Timing

```
19:45   HOME-SOC-Scan-And-Export fires
        └─ security-watch.js        ~2 s
        └─ iot-device-scanner.js   ~28 s
        └─ export-home-soc-reports.js + push  ~2 s

19:46   Public feed current

20:10   Claude Scheduled reads the feed, sends the bulletin
```

The 24-minute gap absorbs a slow scan, a retried push, and CDN propagation.

**This gap is not sufficient on its own.** `raw.githubusercontent.com` caches for
roughly five minutes, but the fetch layer used by the scheduled task was
observed serving a superseded copy for nearly three hours — see OPEN-001 in
[VALIDATION-REPORT.md](VALIDATION-REPORT.md). No schedule gap measured in
minutes defeats a cache measured in hours.

The bulletin therefore carries its own freshness validation: a cache-busting
parameter on each fetch, and an age check computed from the current time rather
than from the `stale` field inside the file. A file's own timestamp cannot tell
you whether that file is the newest one.

Chained with `cmd /c A && B && C`: a failing stage stops the chain rather than
publishing on partial data.

---

## Sanitization

Applied in `export-home-soc-reports.js` before anything is written.

| Source value | Published value | Function |
|---|---|---|
| private LAN address | `link: lan` | dropped |
| hardware address | `id: camera-01` | `classifyDevice` + counter |
| vendor string | discarded | `classifyDevice` |
| make / model / firmware | `firmware: current` | dropped |
| port number | `web-ui`, `video-stream`, `message-broker`, `remote-shell`, … | `classifyPort` |
| DNS resolvers | `isp_default`, `public_resolver`, `local_resolver`, `mixed_resolver` | `classifyDns` |
| WiFi network name | never emitted | passed to the leak guard as forbidden |

Device ids are assigned per category in scan order (`gateway-01`, `camera-01`).
They are stable within a scan and carry no information about the hardware.

---

## Leak guard

```
        build the three output strings
                    │
                    ▼
        ┌───────────────────────────┐
        │  sweep the exact bytes    │
        │                           │
        │  hardware address         │
        │  IPv4 · IPv6              │
        │  credential keywords      │
        │  private-key block        │
        │  vendor names (26)        │
        │  WiFi network name        │
        └───────────┬───────────────┘
                    │
         match ─────┴───── no match
           │                  │
           ▼                  ▼
      ABORT               write files
      write nothing       git add · commit · push
      push nothing
      exit 1
```

Two properties that matter:

**It aborts rather than scrubs.** Scrubbing invites a subtly-wrong regex to
publish a partially redacted value. Aborting means the only two outcomes are
"fully sanitized" or "nothing happened".

**Whole-word matching.** An early version matched substrings and blocked the
word `monitoring` because it contains `ring`, a camera vendor. The gate worked —
it failed toward refusing to publish — but the matcher was wrong, and it is now
anchored with lookarounds.

---

## Unknown is reported as unknown

A control with no collector output is published as `state: "unknown"` and
rendered `NO DATA`, never as a pass. `BASELINE-LATEST.json` carries an explicit
coverage block:

```json
"coverage": {
  "controls_reported": 6,
  "controls_unknown": 0,
  "note": "All controls reported by a collector."
}
```

This exists because the failure mode of a monitoring system is not a false
alarm — it is a green light over a blind spot. Before `security-watch.js` ran,
the feed reported GREEN with four controls unknown, and the bulletin said so
rather than implying the network was clean.

---

## Baseline approval

`baseline.json` is never created implicitly. Running the collector without one
prints the current readings and exits non-zero.

Approving an insecure state as "normal" blinds every future comparison — if the
firewall is already off when the baseline is taken, it can never be detected as
having been turned off. So approval stays an explicit human act:

```
node security-watch.js --approve-baseline
```

v1.0 changed the mechanism (an interactive `yes` became a flag, so the collector
runs unattended) but not the property.

---

## Data flow guarantees

| Guarantee | Enforced by |
|---|---|
| No identifier reaches the public repo | Leak guard abort |
| No unsanitized file is committed | `.gitignore` deny-by-default + `git add -f` of exactly 3 names |
| A blind control is never reported as passing | `state: "unknown"` + coverage block |
| An insecure state is never silently normalized | Baseline requires `--approve-baseline` |
| Partial data is never published | `&&` chaining stops on failure |
| Alert spam is bounded | 4-hour cooldown per alert type |
| Stale data is visible | `data_age_hours` + `stale` flag at 48 h |
| A superseded read is visible | Cache-buster + age check against current time (OPEN-001, MONITOR) |

The last row is a mitigation under observation, not a proven guarantee. Until
OPEN-001 exits MONITOR, the bulletin's control states are advisory and the
GitHub API is authoritative.

---

## Files

**Private — `mcp-cyber-tools`**

| File | Role |
|---|---|
| `security-watch.js` | Endpoint control collector |
| `iot-device-scanner.js` | LAN inventory scanner |
| `export-home-soc-reports.js` | Sanitizer, leak guard, publisher |
| `baseline.json` | Approved control state |
| `state.json` | Latest reading |
| `alerts.json` | Alert history, newest first, capped at 100 |
| `cooldown.json` | Per-alert-type suppression timestamps |
| `network-scan-data/` | Raw scan history |

**Public — `home-soc-reports`**

| File | Role |
|---|---|
| `ROUTER-SECURITY-AUDIT-LATEST.md` | Human-readable audit |
| `BASELINE-LATEST.json` | Control states, alerts, coverage, risk level |
| `DEVICE-SUMMARY.json` | Device counts and per-device status |
| `.gitignore` | Deny-by-default allowlist |
| `README.md` | Pipeline and sanitization policy |

---

## What this architecture does not do

It does not monitor endpoints other than the host running the collector. It does
not detect a device that has left the network — only devices currently in the
ARP table are counted. It does not act on findings; every recommendation is for
a human. And it does not treat stale data as an incident.

Those are v1.1 and beyond. See [ROADMAP.md](ROADMAP.md).
