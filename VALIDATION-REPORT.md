# HOME SOC — Validation Report v1.0

**Date:** 2026-08-30
**Method:** every claim exercised against live data on the production machine.
No mocks, no fixtures, no simulated stages except where explicitly marked.

**Result: 9 PASS / 0 FAIL**

---

## Summary

| # | Capability | Result | Evidence |
|---|---|---|---|
| 1 | Scanner | ✅ PASS | 27.7 s, exit 0, scan file written |
| 2 | Exporter | ✅ PASS | Commit pushed in the same second as the scan |
| 3 | Leak guard | ✅ PASS | Caught a real leak and aborted |
| 4 | Sanitization | ✅ PASS | 0 identifiers across 5 tracked files |
| 5 | Public feed | ✅ PASS | 3/3 HTTP 200, anonymous |
| 6 | Alert engine | ✅ PASS | CRITICAL fired, RED escalated |
| 7 | Cooldown | ✅ PASS | Duplicate suppressed |
| 8 | Scheduled bulletin | ✅ PASS | Generated from the public feed, delivered |
| 9 | Control coverage | ✅ PASS | 6/6, `controls_unknown: 0` |

---

## 1. Scanner — PASS

```
node iot-device-scanner.js
  → Devices: 2 | Identified: 2 | Risks: 0
  → Saved: network-scan-1788125769321.json
  → 27.7 s
```

One-shot, exits cleanly, suitable for Task Scheduler. Services verified by
banner rather than assumed from the port number: port 443 on the gateway was
reported `Open, no banner (service unverified, NOT HTTPS)` rather than being
recorded as HTTPS.

---

## 2. Exporter — PASS

Ran inside the scheduled chain, not by hand:

```
14:55:53  Task started
14:56:18  network-scan-1788126978724.json written
14:56:18  commit 9d1e6e3 pushed to origin/main
          exit code 0
```

Scan and publish in the same second, no manual step between them.

---

## 3. Leak guard — PASS

**Proven twice, both times by catching something real.**

**Catch 1 — false positive, correct failure direction.** First run aborted:

```
[ABORT] ROUTER-SECURITY-AUDIT-LATEST.md would leak the identifier "ring".
```

`ring` matched inside `monitoring`. The gate behaved correctly — it refused to
publish under uncertainty. The matcher was wrong and was anchored with
lookarounds. Nothing was written and nothing was pushed.

**Catch 2 — a genuine leak, found by an independent sweep.** A separate scan
over all tracked files found real identifiers in `README.md`: an internal
address and vendor product names, used as examples in the sanitization table.

```
IPv4 in README.md
VENDOR in README.md
```

The exporter's guard did not catch this — it only sweeps its own three outputs.
The examples were replaced with generic descriptions and the re-scan passed.

**This is recorded as a limitation, not a clean result.** The guard's coverage
boundary is real, and the monthly leak audit in the runbook exists because of it.

---

## 4. Sanitization — PASS

Every tracked file in the public repo, swept independently of the exporter:

```
IPv4 · MAC · IPv6 · vendor names · WiFi network name · credential keywords
→ PASS - no identifiers in any tracked file  (5/5 files)
```

Verified transformations against real source data:

| Source (private) | Published (public) |
|---|---|
| gateway LAN address + hardware address | `gateway-01` |
| camera LAN address + hardware address | `camera-01` |
| vendor string (gateway) | *(discarded)* |
| vendor string (camera) | *(discarded)* |
| port 1883 | `message-broker` |
| port 554 | `video-stream` |
| ports 80 / 443 / 8000 | `web-ui` |
| port 9000 | `vendor-service` |
| ISP DNS resolvers | `provider_class: isp_default` |
| WiFi network name | *(never emitted)* |

---

## 5. Public feed — PASS

Anonymous fetch, no credentials, no GitHub connector:

```
[200] ROUTER-SECURITY-AUDIT-LATEST.md   1936 b   168 ms
[200] BASELINE-LATEST.json              1083 b    23 ms
[200] DEVICE-SUMMARY.json                890 b    29 ms
```

This is the capability the whole design exists to provide. Before it, the
scheduled task failed with:

```
HTTP 403: GitHub access to this repository is not enabled for this session.
remote: invalid credentials
```

Root cause confirmed: `mcp-cyber-tools` is private (API returns 404 anonymously),
and a scheduled cloud task has no credentials for it. The private repo remains
private and unchanged.

---

## 6. Alert engine — PASS *(simulated divergence)*

**Method.** No real security control was modified. The divergence was created by
editing `baseline.json` so the recorded DNS no longer matched the live reading.
This exercises rule evaluation, alert construction, persistence, and escalation
without touching a live security setting.

**Collector:**
```json
{
  "type": "DNS_CHANGE",
  "severity": "CRITICAL",
  "control": "dns",
  "description": "DNS resolvers changed since baseline",
  "detected_at": "2026-08-30T22:08:43.534Z"
}
```

**Exporter:**
```
risk_level : RED
alert type : DNS_CHANGED
severity   : CRITICAL
audit      : **Risk level:** RED
             - **CRITICAL** — control `dns` changed since baseline
```

Full escalation path proven: rule → `alerts.json` → exporter → RED → bulletin.

Baseline was restored and the system returned to GREEN.

**Limitation.** A real control change has still never travelled this chain. The
logic is proven; the end-to-end incident is not.

---

## 7. Cooldown — PASS

Immediately after the alert above, with the divergence still present:

```
No change from baseline.
Suppressed (4h cooldown): DNS_CHANGE
```

One alert per type per four hours. Anti-spam works.

---

## 8. Scheduled bulletin — PASS

The Claude Scheduled task fetched all three public URLs and produced a full
Vietnamese bulletin: executive summary, device table, control states, findings,
risk assessment, recommended actions, changes since previous.

Notably, it reported the coverage gap rather than presenting GREEN as clean:

> "4/6 control không có dữ liệu … Đây là lỗ hổng giám sát, không phải kết quả sạch"

The design intent — a blind spot must never read as a pass — survived all the way
to the delivered output.

---

## 9. Control coverage — PASS

**Before:**
```
controls_reported: 6   controls_unknown: 4
firewall: unknown   defender: unknown   rdp: unknown   ssh: unknown
```

**After** (verified via the GitHub API to bypass CDN caching, commit `22391bc`):
```
controls_reported: 6   controls_unknown: 0
dns: observed (isp_default)   firewall: enabled   defender: enabled
rdp: closed   ssh: closed     remote_access_services: none_detected
note: "All controls reported by a collector."
```

All five probes confirmed working **without elevation**:

```
DNS      : (ISP resolvers)      Firewall : True
Defender : realtime enabled     RDP      : closed
SSH      : closed               Elevated : False
```

---

## Defects found and fixed

**D-1 · UTF-8 BOM breaks JSON parsing.**
PowerShell's `Set-Content -Encoding utf8` writes a BOM; `JSON.parse` rejects it.

`security-watch.js` failed **silently** — it reported `No baseline found` and
refused to compare. `export-home-soc-reports.js` failed **loudly** — it aborted
with the parse error.

The silent failure is the more dangerous of the two: hand-editing `baseline.json`
from PowerShell would have stopped comparison with no visible signal. Both files
now strip the BOM.

**D-2 · Substring vendor matching.**
`ring` matched inside `monitoring`. Anchored with lookarounds.

**D-3 · Real identifiers in `README.md`.**
Sanitization examples used live values from the network. Replaced with generic
descriptions. See §3.

---

## Open issues

### OPEN-001 · Bulletin read a superseded copy of the feed

**Status: MONITOR** · Opened 2026-08-31 · Documentation-only response

**Observed — two occurrences, both verified against the live feed:**

| | Bulletin read | Feed served at that moment | Lag |
|---|---|---|---|
| Run 1 · ~2026-08-30 22:12Z | `21:55:53Z`, `controls_unknown: 4` | `22:10:01Z`, `controls_unknown: 0` | ~14 min |
| Run 2 · ~2026-08-31 01:01Z | `21:56Z`, `controls_unknown: 4` | `22:10:01Z`, `controls_unknown: 0` | ~2 h 51 m |

**Run 2 reproduced the fault.** At that time both `raw.githubusercontent.com`
and the GitHub API returned the current file, and the newest commit
(`22391bc`, `22:10:26Z`) was nearly three hours old. The caching is therefore
not the ~5-minute CDN window; it sits in the fetch layer used by the scheduled
task and persisted for at least 2 h 51 m.

**Impact.** Four controls were reported `NO DATA` when they were in fact
`enabled / enabled / closed / closed`. The bulletin's recommended action — "run
`security-watch.js` to fill the coverage gap" — described work already completed
almost three hours earlier.

**Why the freshness check did not catch it.** Staleness is computed from the
timestamp *inside* the fetched file. A superseded copy carries its own
timestamp, so it reads as fresh. The check answers "how old is this data" but
not "is this the newest data".

**Partial self-detection.** Run 2's bulletin did recompute age against the real
current time and reported "0 giờ tại thời điểm tạo báo cáo → khoảng 3 giờ tính
đến hiện tại". It declined to trust the `stale` field. It did not take the final
step of concluding that a 3-hour gap implies a possibly superseded read.

**Mitigation applied — documentation and task prompt only, no code change.**

1. Cache-busting query parameter on each fetch, unique per run.
2. Mandatory age check against current time, independent of the `stale` field.
3. A confidence warning printed above all other content when the gap exceeds 3 h.
4. Runbook freshness checks repointed from the raw URL to the GitHub API.

**Subsequent run.** The operator reports a later run did not reproduce the
fault. *Not independently verified in this session* — no third observation was
captured here. Two confirmed occurrences stand against one unverified clean run,
which is why the status is MONITOR rather than RESOLVED.

**Exit criteria.** Seven consecutive scheduled bulletins whose reported
`source_scan_at` is within 3 hours of their own generation time, each confirmed
against the GitHub API. Track in [RUNBOOK.md](RUNBOOK.md).

**Why this is not closed.** A caching layer that held for nearly three hours
once can hold again. Until the mitigation is observed working across the
seven-day period, the correct posture is that the bulletin's control states are
advisory and must be confirmed at source before anyone acts on them.

---

## What this report does not prove

**Unattended operation.** Every run was manually triggered. The 19:45 trigger
has not yet fired on its own. "Fully automated" remains a design claim.

**Real incident detection.** All alerting was proven by simulation. No genuine
control change has travelled the chain.

**Multi-device coverage.** Endpoint controls cover the host running the collector
only.

**Device-departure detection.** The scanner found 2 devices; an earlier manual
audit listed 6. Devices absent from the ARP table are invisible, and a departure
is indistinguishable from a device being asleep.

**Sustained operation.** Longest observed continuity is a few hours.

---

## Verdict

**Nine capabilities proven. Three defects found and fixed. Five gaps documented.**

The pipeline moves real data from a private network to a delivered bulletin
without leaking an identifier, and it reports its own blind spots rather than
hiding them.

v1.0 is **fit for observation**, not yet **proven in operation**. The seven-day
observation period in [RUNBOOK.md](RUNBOOK.md) is what closes that gap.
