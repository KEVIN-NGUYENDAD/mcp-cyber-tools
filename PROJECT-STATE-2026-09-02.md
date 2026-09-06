# PROJECT STATE — 2026-09-02

**Authoritative project reference.** A new chat should read this first and treat
it as current state. Everything here was verified against live systems on
2026-09-02, not recalled from conversation.

---

## Memory Compression Rules

This file is the record of what has already been proven. Re-deriving it costs
tokens and, worse, risks reaching a different conclusion from the same evidence.

**Treat as settled — do not re-investigate:**

- OPEN-001 history, cause, and four observations
- The 2026-09-01 stale feed incident
- The GitHub Contents API experiment and its rollback
- `publish_id` deployment
- Freshness validation findings
- Scanner, exporter, GitHub publish, Security Watch validation

Each is recorded in this file or the documents it links. Cite the section;
do not re-run the investigation.

**Investigate only evidence dated after 2026-09-02T21:06:58Z** — the timestamp
of the last verified publish (`acfc7eecba6d0412`).

**Workflow when starting new work:**

1. Read this file first.
2. State current status in under 10 lines.
3. Add net-new findings only.
4. Reference existing sections rather than repeating them.
5. Verify live systems only for facts that could have changed since the
   timestamp above.

**The one exception.** If a live check contradicts something recorded here, the
live system wins and this file is corrected. Settled means "not re-litigated
without cause", not "true regardless of evidence". Two entries in this file
already exist because a recorded claim turned out to be wrong.

---

## Executive summary

| Component | Status | Evidence |
|---|---|---|
| HOME-SOC v1.0 | Released, frozen, in observation | Tag `HOME-SOC-v1.0` → `5019334` |
| OPEN-001 | **ACCEPTED — detectable, not prevented** | Untested since rollback |
| Bulletin pipeline | Working | Delivers daily; freshness validation active |
| Scanner | Working | 3 devices, exit 0 |
| Security Watch | Working | 6/6 coverage, `unknown: 0` |
| Exporter | Working | Sanitized, leak guard passed, pushed |
| GitHub publishing | Working | `b5a900b` live and served |

**Observation period: reset to day 0.** 2026-09-01 had no collection run. Under
the [RUNBOOK.md](RUNBOOK.md) rule, the seven-day counter restarts.

**Two things are working but unproven.** The rolled-back OPEN-001 mitigation has
never run inside a scheduled bulletin. And the 19:45 chain has never completed
seven consecutive unattended days.

---

## OPEN-001 timeline

### 1 · Original symptom

A bulletin reported coverage **2/6** with **4 controls unknown**, while the
published feed carried 6/6 and `unknown: 0`. Repeated across four bulletins.

### 2 · Investigation

Every stale bulletin returned byte-identical content from commit `9d1e6e3`
(`source_scan_at 2026-08-30T21:55:53.899Z`, `unknown: 4`).

| Run | Bulletin read | Feed served | Lag |
|---|---|---|---|
| 1 | 21:55:53Z | 22:10:01Z | ≥ 14 min |
| 2 | 21:56Z | 22:10:01Z | ~2 h 51 m |
| 4 | 21:56:18Z | 22:10:01Z | ~5 h 01 m |

Run 4 was decisive: it returned the **older of two available versions**, five
hours after the newer was published. No time-based expiry produces that.

**Cause identified:** a snapshot pinned at the task's first successful fetch.
GitHub CDN ruled out — verified serving current data throughout, and 5 h exceeds
its ~5 min TTL by roughly 60×. Local fetches were correct at every point.

### 3 · API experiment

Implemented in commit `23e1159`:

- Exporter emits `publish_id`, a 16-char SHA-256 fingerprint over source data
- Bulletin resolves HEAD via `/commits?per_page=1`, then reads each file pinned
  to `?ref=<sha>`

A SHA-pinned URL is unique per publish, so a URL-keyed snapshot has nothing to
replay. Verified working against all four published versions.

### 4 · Why the API approach failed operationally

```
GitHub API unauthenticated : 60 requests/hour, per IP
Bulletin cost              : 4 requests/run
Scheduled task IP          : shared across tenants in Anthropic's cloud
```

Failure mode is HTTP 403 and **no bulletin at all**. That trades a bulletin
that is sometimes stale for one that is sometimes absent. For a daily unattended
monitor, absence is the worse failure: stale is wrong and detectable, missing is
silent.

### 5 · Rollback — commit `7fa1b9a`

Bulletin returned to `raw.githubusercontent.com` with a per-run cache-buster.
Unmetered, CDN-backed, no rate limit.

**Operational reliability preferred over API dependency.**

The API was not abandoned — it moved to the operator's manual runbook check,
one or two requests a day from a personal IP, where 60/hour is irrelevant.

### 6 · Current status

**ACCEPTED — DETECTABLE, NOT PREVENTED.**

The pinned snapshot can recur. What changed is that it no longer requires an API
call to notice. `publish_id` is served over the raw URL (verified), giving each
publish a stable identity.

> **The same `publish_id` on two consecutive days, with a chain run in between,
> is a stale read.** One string comparison against yesterday's email.

**Never tested since rollback.** No scheduled bulletin has yet read a publish
newer than the one before it. Until that happens, the GitHub API is
authoritative.

---

## Stale feed incident — 2026-09-01

| Field | Value |
|---|---|
| Age reported | 23.02 hours |
| Publish ID | `dc3b932c3b6ead0a` |
| Generated At | 2026-09-01T04:09:34.693Z |
| Source Scan At | 2026-09-01T04:08:54.033Z |
| Coverage | 6/6, `unknown: 0`, GREEN |

**Finding: the bulletin was correct and was not the problem.**

Verified against commit `5716a64` by direct fetch — byte-exact. At 20:10 MST on
09-01 that was the newest publish in existence. The bulletin read the newest
data available and reported its true age.

**This was NOT OPEN-001.** The defect is reading a *superseded* version. No
superseding version existed, so the fault had nothing to express — this incident
neither confirms nor clears it.

Full record: [INCIDENT-2026-09-01-STALE-FEED.md](INCIDENT-2026-09-01-STALE-FEED.md)

---

## Root cause analysis

### Scan artifacts on disk

```
2026-09-02 14:06:58   network-scan-1788383218343.json   ← manual run
2026-09-01            (no file)
2026-08-31 21:09:34   network-scan-1788235774594.json   ← published as 5716a64
2026-08-31 00:19:38   network-scan-1788160778430.json
```

### Publish gap

| Commit | Published (MST) | Gap |
|---|---|---|
| `5716a64` | 2026-08-31 21:09 | **41 hours** |
| `b5a900b` | 2026-09-02 14:06 | — |

**Immediate cause — identified.** The scan/publish chain did not execute on
2026-09-01. No artifact was produced, so nothing was published, so feed age grew.

**Underlying cause — unevidenced.** Why the 19:45 trigger did not fire, and why
`-StartWhenAvailable` did not catch up, cannot be determined. Power state is not
logged. The likely explanation is the machine being off or asleep across the
window, but that is inference.

**A single missed run costs two days.** The chain runs once daily; miss one and
the next bulletin reports day-old data and the one after reports two-day-old
data, all in GREEN.

---

## Verified working components

Each verified on 2026-09-02, not assumed.

| Component | Status | Verification |
|---|---|---|
| Security Watch | ✅ | 6/6 controls, `state.json` current |
| IoT Scanner | ✅ | 3 devices, exit 0 |
| Exporter | ✅ | Leak guard passed, committed, pushed |
| GitHub Publish | ✅ | `b5a900b` live |
| Bulletin | ✅ | Delivered |
| Freshness validation | ✅ | **Surfaced the 23-hour feed** |
| `publish_id` | ✅ | Changed across publishes as designed |

---

## Current verified feed

```
publish_id     : acfc7eecba6d0412
source_scan_at : 2026-09-02T21:06:18.225Z
generated_at   : 2026-09-02T21:06:58.431Z
coverage       : 6/6
unknown        : 0
risk           : GREEN
alerts         : 0
```

**Devices (3):**

| ID | Label | Category |
|---|---|---|
| `gateway-01` | Gateway | network |
| `camera-01` | Camera | iot |
| `computer-01` | Computer | computer |

**Controls (6/6):** DNS observed (`isp_default`) · Firewall enabled · Defender
enabled · RDP closed · SSH closed · Remote-access services none detected.

---

## Lessons learned

**Freshness validation exposed a fault it was not built for.** It was added for
OPEN-001. It caught a missed collection cycle — an unrelated failure.

Without it the bulletin would have reported:

```
GREEN · 6/6 · 0 alerts
```

Every figure accurate about the data held, and completely silent about that data
being a day old. A dead collector would have looked identical to a healthy one.

**The general lesson: a monitoring system's most dangerous output is a
confident green light over data it cannot vouch for.** Correctness about content
is not correctness about currency, and only the second one tells you the system
is still alive.

**Corollary now visible in production — limitation 9.** Staleness is flagged but
does not escalate: 23-hour-old data still reported GREEN. The flag is a number in
a header, easy to skim past. Whether that should raise risk level is open, and
deliberately unresolved during the freeze.

---

## Bulletin Redesign v1

**Implemented 2026-09-02.** Presentation only — no collector, exporter, scanner,
or scheduler change. Full pasteable prompt:
[BULLETIN-PROMPT-v1.md](BULLETIN-PROMPT-v1.md)

### The problem being solved

Bulletins were technically correct and operationally misleading. Twice a
confident `GREEN · 6/6 · 0 alerts` sat above data that did not describe the
present — once from a stale read, once from a missed collection cycle. Both
times the age was recoverable from the report, and both times it was buried
below the reassurance.

**A reader who stops after the first line should stop on the right thing.**

### Layout

```
🏠 HOME SECURITY STATUS      ← header, before everything
   Last Scan · Last Publish · Data Age · Publish ID · Status

1. 🕒 DATA FRESHNESS
2. 💻 DESKTOP
3. 💻 LAPTOP
4. 📱 IPHONE
5. 📶 WIFI / NETWORK
6. 🚨 ALERTS
7. 📊 SYSTEM HEALTH
8. 🔍 OPEN-001 MONITOR

   Technical Details            ← only place UTC may appear
```

### Rules and why each exists

**Freshness outranks risk.** The header carries scan time, publish time, age and
`publish_id` before any assessment. Age is computed as *now minus
`source_scan_at`*, never from the file's own `stale` or `data_age_hours` — those
describe when the file was made, not when it was read, and trusting them is
precisely what failed.

**The 12-hour rule blocks the green light.** Past 12 hours the report opens with
`❌ STALE DATA` and the risk level may not appear above it. Graduated below that:
3–12 h renders `⚠️ DỮ LIỆU KHÔNG MỚI`, under 3 h renders `✅ DỮ LIỆU MỚI`. The
23-hour incident would have opened with a red banner instead of a green rating.

**Arizona time in front, UTC in back.** The system clock is already
`US Mountain Standard Time (UTC-07:00)` with DST off, so this is not a
conversion — it is removing UTC from where a homeowner reads. Format
`09/02/2026 02:06 PM`. UTC survives only in Technical Details, where an
investigator wants it.

**Absent means absent.** Sections 3 and 4 render `KHÔNG CÓ DỮ LIỆU` rather than
being omitted or inferred. There is one endpoint agent and it reads only its own
host; the scanner reads the ARP table, so a sleeping phone is missing and its
absence is indistinguishable from removal. An empty section states the gap. A
missing section would let the gap pass as coverage.

**OPEN-001 has three states and none of them is resolved.**

| State | Meaning |
|---|---|
| `NOT OBSERVED` | `publish_id` differs from yesterday — normal |
| `POSSIBLE STALE SNAPSHOT` | `publish_id` identical to yesterday |
| `MONITOR ALERT` | `publish_id` absent, or no prior value to compare |

`POSSIBLE STALE SNAPSHOT` is worded as two possibilities, not one: either the
bulletin re-read an old publish (OPEN-001) **or** the chain did not run so no
new publish exists. The feed alone cannot separate them — that ambiguity is
exactly what caused the 09-01 incident to be filed initially as a stale read
when it was a missed collection. The report now says so instead of guessing, and
points at Playbook G.

The prompt forbids the words RESOLVED, FIXED, and ĐÃ SỬA. Official status stays
**ACCEPTED — DETECTABLE, NOT PREVENTED**.

### Token-saving workflow

The redesign also fixes a cost problem. Every bulletin that buried its age forced
a manual investigation to establish whether the figures could be trusted — the
09-01 incident took several rounds of commit archaeology to answer "was this
data current?".

The header answers it in three fields. `Data Age`, `Publish ID`, and
`Last Scan Time` decide, without any tool call, whether the rest of the report
is worth reading:

| Header shows | Action |
|---|---|
| Age under 3 h, `publish_id` changed | Read normally. No verification needed |
| Age 3–12 h | Read, note the age |
| `❌ STALE DATA` | Stop. The body describes the past — Playbook B |
| `POSSIBLE STALE SNAPSHOT` | One API call to settle it — Playbook G |

Only the last row costs a request. The other three are decided by reading.

### What this does not change

No detection improves. No coverage increases. The same data produces the same
findings — a reader is simply told what the data is before being told what it
means. Sections 2–4 will render mostly empty until a second endpoint agent
exists, which is a v1.1 decision.

---

## Report redesign request (original)

Future bulletins to be organised as:

```
1. Desktop
2. Laptop
3. iPhone
4. WiFi / Network
5. Alerts
6. System Health
7. OPEN-001 Monitor
```

**Timestamps:** Arizona time (MST) in user-facing sections; UTC only under
Technical Details.

> Note: the system clock is already `US Mountain Standard Time (UTC-07:00)` with
> DST off — Arizona time. No conversion is needed; the change is to stop
> surfacing UTC outside Technical Details.

### What the data can and cannot fill today

**This structure asks for sections the pipeline does not produce.** Recorded so a
future chat does not build them against data that is not there.

| Section | Available data |
|---|---|
| 1 · Desktop | Partial — `computer-01` from network scan, plus the 6 endpoint controls, which come from whichever host runs the collector |
| 2 · Laptop | **None.** No endpoint agent. Would appear only as a scanned device, and the scanner cannot label which computer is which |
| 3 · iPhone | **None.** Absent from recent scans entirely |
| 4 · WiFi / Network | Full — gateway, camera, control states |
| 5 · Alerts | Full — `alerts` array |
| 6 · System Health | Full — coverage, freshness, publish identity |
| 7 · OPEN-001 Monitor | Full — `publish_id` day-over-day |

Two structural facts behind this:

- `security-watch.js` reads **only the host it runs on**. There is one endpoint
  agent, so per-machine sections cannot be populated from it.
- The scanner reads the **ARP table**. A sleeping phone is absent, and its
  absence is indistinguishable from removal — device counts have already varied
  between 2 and 3 for this reason.

Building sections 1–3 requires either a second endpoint agent or accepting that
they render as "no data" most days. That is a v1.1 decision, not a formatting
one.

---

## Repository state

```
HEAD           : b47a8fb  docs: record stale feed observation and verification
origin         : 7fa1b9a  (b47a8fb and 5d504d2 unpushed)
Tag            : HOME-SOC-v1.0 → 5019334  (unchanged since release)
Private repo   : KEVIN-NGUYENDAD/mcp-cyber-tools, branch learning-factory-v2
Public feed    : KEVIN-NGUYENDAD/home-soc-reports, branch main
```

**Note:** `state.json`, `alerts.json`, and `baseline.json` became tracked in
commit `5d504d2` (not part of the OPEN-001 work). The tracked `state.json`
contains real DNS resolver addresses. The repo is private, so this is not a
leak, but operational data is no longer local-only. `git rm --cached` reverses
it if unintended.

---

## Key documents

| File | Purpose |
|---|---|
| [RELEASE-NOTES-v1.0.md](RELEASE-NOTES-v1.0.md) | Capabilities, 10 known limitations, validation results |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Pipeline, sanitization, leak guard, data-flow guarantees |
| [RUNBOOK.md](RUNBOOK.md) | Daily/weekly/monthly checks, playbooks A–G, observation tracker |
| [VALIDATION-REPORT.md](VALIDATION-REPORT.md) | 9 capabilities proven, 3 defects fixed, gaps documented |
| [OPEN-001-INVESTIGATION.md](OPEN-001-INVESTIGATION.md) | Full defect investigation, rollback rationale, bulletin prompt |
| [INCIDENT-2026-09-01-STALE-FEED.md](INCIDENT-2026-09-01-STALE-FEED.md) | Missed collection cycle |
| [ROADMAP.md](ROADMAP.md) | v1.1 / v1.2 / v2.0, and what is explicitly not planned |

---

## Handoff to a future chat

Read this file first and treat it as authoritative.

**Standing constraints:**

1. **v1.0 is frozen.** Bug fixes and documentation only until seven consecutive
   unattended days. Counter is at **0** — 09-01 broke it.
2. **The tag `HOME-SOC-v1.0` does not move.**
3. **The GitHub API is authoritative** over the bulletin while OPEN-001 is
   ACCEPTED. Bulletin control states are advisory.
4. **Do not use the API in the bulletin.** Rate limits caused the rollback.
5. **`publish_id` is the detector.** Compare day over day before anything else.

**Open questions, in priority order:**

1. Does OPEN-001 recur after the rollback? Untested.
2. Will the 19:45 chain run unattended? Once in three days so far, and late.
3. Should stale data escalate risk level? Limitation 9, unresolved.
4. Do sections 1–3 of the report redesign get real data, or get dropped?

**What would be a mistake:** treating GREEN as safe without checking the age and
`publish_id` first. Both failures so far produced a confident GREEN over data
that did not describe the present.
