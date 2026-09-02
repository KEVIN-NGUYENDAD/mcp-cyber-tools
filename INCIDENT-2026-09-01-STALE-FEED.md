# Incident 2026-09-01 — Stale Feed Observation

**Status:** CLOSED AS OBSERVATION
**Filed:** 2026-09-02 · **Classification revised during investigation**

---

## Summary

A Home Security Bulletin reported a data age of 23.02 hours.

**The bulletin was correct, and the bulletin was not the problem.** It read the
newest publish that existed, computed the true age, and flagged it. The feed was
23 hours old because **the collection chain did not run on 2026-09-01** — no
scan artifact exists for that date, and no publish occurred for 41 hours.

This is a **missed collection cycle**, not a stale read. It is not OPEN-001.

---

## Observed bulletin

| Field | Value |
|---|---|
| Publish ID | `dc3b932c3b6ead0a` |
| Generated At | 2026-09-01T04:09:34.693Z |
| Source Scan At | 2026-09-01T04:08:54.033Z |
| Age | 23.02 hours |
| Coverage | 6/6 |
| Unknown | 0 |
| Risk | GREEN |

All four identity fields verified against commit `5716a64` by direct fetch:

```
publish_id     : dc3b932c3b6ead0a
generated_at   : 2026-09-01T04:09:34.693Z
source_scan_at : 2026-09-01T04:08:54.033Z
unknown        : 0
```

Byte-exact. The bulletin reported precisely what the feed contained.

---

## Investigation

### Publish history

| Commit | Published (UTC) | Local | Gap to next |
|---|---|---|---|
| `b0548a5` | 2026-08-31 18:40:17 | 08-31 11:40 | 9.5 h |
| `5716a64` | 2026-09-01 04:09:34 | 08-31 21:09 | **41 h** |
| `b5a900b` | 2026-09-02 21:06:58 | 09-02 14:06 | — |

### Scan artifacts on disk

```
2026-09-02 14:06:58   network-scan-1788383218343.json   ← manual verification run
2026-08-31 21:09:34   network-scan-1788235774594.json   ← published as 5716a64
2026-08-31 00:19:38   network-scan-1788160778430.json
2026-08-30 15:10:26   network-scan-1788127826028.json
```

**No scan file exists for 2026-09-01.** The scanner did not execute that day, so
the exporter had nothing new to publish, so the feed did not advance.

At 20:10 local on 09-01 — when the bulletin ran — `5716a64` was the newest
publish in existence. There was no newer version for the bulletin to miss.

### Manual verification, 2026-09-02

| | Value |
|---|---|
| Task LastRunTime | 2026-09-02 14:06:09 local |
| Task LastResult | 0 |
| Local `state.json` | 2026-09-02 14:06:18 local |
| Feed `generated_at` | 2026-09-02T21:06:58.431Z |
| Feed `source_scan_at` | 2026-09-02T21:06:18.225Z |
| Feed `publish_id` | `acfc7eecba6d0412` |

> **Correction.** The initial report recorded the verification `publish_id` as
> `afcf7eecba6d0412`. The actual value is **`acfc7eecba6d0412`** — characters
> two and three transposed. Corrected here because `publish_id` is an
> exact-match detector: a wrong value in the log would silently break the
> day-over-day comparison it exists to support.

---

## Result

| Component | Status |
|---|---|
| Scanner | Functioning — produced a new scan on demand |
| Security-watch | Functioning — 6/6 coverage, `state.json` current |
| Exporter | Functioning — sanitized, leak guard passed, committed |
| GitHub publish | Functioning — `b5a900b` pushed and served |
| Bulletin freshness validation | **Functioning — this is what surfaced the incident** |
| OPEN-001 | Not reproduced |

**OPEN-001 could not have been reproduced by this event.** The defect is reading
a *superseded* version; on 09-01 no superseding version existed. This incident
neither confirms nor clears OPEN-001.

---

## Root cause

**Immediate cause — identified.** The collection chain did not execute on
2026-09-01. No scan artifact was produced, so no publish followed.

**Underlying cause — insufficient evidence.** Why the 19:45 trigger did not fire,
and why `-StartWhenAvailable` did not catch up before the manual run 18 hours
later, cannot be determined from available data. The most likely explanation is
that the machine was powered off or asleep across the window, but power state is
not logged, so this is inference rather than evidence.

The original assessment recorded root cause as "Unknown". That understates what
the artifacts show: the failure is located precisely at the collection stage on a
specific date. Only the reason for that stage not running is unknown.

---

## What this reveals

**1. The freshness validation earned its place.** Without it the bulletin would
have reported GREEN, 6/6, 0 alerts — accurate about the data it held, silent
about the data being a day old. The 23.02-hour figure is the only reason this
incident was noticed at all. That mitigation was added for OPEN-001 and caught an
unrelated fault.

**2. Limitation 9 manifested in production.** The system flagged staleness but did
not escalate it: 23-hour-old data still reported risk GREEN. A collector that
stopped for a day looked the same as a healthy one, apart from a number in the
header. See [RELEASE-NOTES-v1.0.md](RELEASE-NOTES-v1.0.md) limitation 9.

**3. A single missed run produces a 41-hour gap.** The chain runs once daily. Miss
one and the feed is stale for nearly two days — the next bulletin reports
day-old data, and the one after that reports two-day-old data, all in GREEN.

**4. The observation period resets.** 2026-09-01 had no chain run. Under the
[RUNBOOK.md](RUNBOOK.md) rule that a day counts only when both the chain and the
bulletin run unattended, the seven-day counter returns to zero.

---

## Actions

**Taken:** manual chain run on 2026-09-02, feed refreshed, all stages verified
functioning. `publish_id` correction recorded above.

**Not taken — deliberately.** No code, task, or scheduler change. v1.0 is frozen
and a single missed run is not yet evidence of a defect. Whether this recurs is
the question the observation period exists to answer.

**To watch:** if a second date passes with no scan artifact, the trigger
configuration becomes the suspect and this stops being an observation.

---

## Classification

**CLOSED AS OBSERVATION.**

Closed because every component was verified functioning and the immediate cause
is identified. An observation rather than a defect because one missed run under
unproven scheduling is expected behaviour for a system in its first week, not
evidence of a fault.

Reopened if a second collection cycle is missed.
