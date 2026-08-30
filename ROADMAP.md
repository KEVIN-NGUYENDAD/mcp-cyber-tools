# HOME SOC — Roadmap

**Current:** v1.0, frozen 2026-08-30, in observation.

Nothing here is scheduled and nothing here is approved. This is a record of
which gap each future version would close, so that a decision to build can be
made against evidence rather than enthusiasm.

**Entry condition for any work below:** seven consecutive days of successful
unattended v1.0 operation. Until then the only permitted changes are bug fixes.

---

## v1.1 — Close the gaps v1.0 documented

Every item exists because [VALIDATION-REPORT.md](VALIDATION-REPORT.md) named it
as unproven or missing. No new capability — only making v1.0's own claims true.

**Device-departure detection.**
The scanner reads the ARP table, so a sleeping device and a removed device look
identical. v1.0 reports the smaller number without comment. v1.1 would track
devices across scans and distinguish *absent* from *gone*.

**Staleness escalates.**
Past 48 hours the feed sets `stale: true` but the risk level stays GREEN. A
collector that died a week ago still reports green with a footnote. Staleness
should raise risk, because unknown is not the same as safe.

**Leak guard covers the repository.**
The guard sweeps three generated files. A real leak was found in `README.md` by a
manual sweep. The guard should run as a pre-commit gate over every tracked file.

**Second endpoint.**
`security-watch.js` covers the host it runs on. The laptop has no agent and
appears only as network inventory.

**A real incident, deliberately caused.**
Alerting was proven by editing a baseline, not by changing a control. A
controlled test — disable the firewall, confirm the bulletin goes RED, restore —
would close the last simulated step. This is an operator action, not code.

---

## v1.2 — Make the data mean more over time

Only after v1.1's gaps are closed and the system has run long enough to have a
history worth reading.

**Trend rather than snapshot.**
Each bulletin describes one moment. "Third new device this week" is a different
statement from "one new device", and only history can make it.

**Alert acknowledgement.**
`alerts.json` accumulates. Nothing records that a human looked. Unreviewed
alerts silently train the reader to ignore the system — the failure mode that
kills monitoring long before a bug does.

**Per-device baselines.**
Controls are baselined; devices are not. A camera that starts serving a new
service class is invisible today.

**Retention.**
`network-scan-data/` grows one file per run forever. Currently handled by a
manual monthly note in the runbook.

---

## v2.0 — Only if the evidence demands it

Each of these is a genuine expansion, and each carries a cost that v1.0
deliberately refused. None should be built because it is interesting.

**Continuous collection.**
Daily means a change at 20:15 is found 23 hours later. Faster detection costs
constant CPU, larger history, and more chances to alert on noise. Build only if
the observation period shows daily cadence actually missing something.

**Router configuration monitoring.**
Port forwarding, UPnP, and remote management are checked by hand in the runbook —
the highest-value unmonitored surface. Requires router credentials, which is a
significant new secret to hold and a new thing to leak. The reason v1.0 does not
do this is not difficulty; it is that holding router credentials to protect a
router is a trade worth making deliberately.

**Correlation.**
"New device appeared, then firewall was disabled" is a stronger signal than
either alone. Requires the trend data from v1.2 first.

**Response actions.**
Re-enabling a firewall automatically is technically small and operationally
serious. A monitoring system that acts can also act wrongly, and it removes the
human check that currently catches false positives. Build only with an explicit
approval step, and only after the alert engine has a long clean record on real
incidents.

---

## Explicitly not planned

**A dashboard.** The bulletin is one email a day and is read. A dashboard is a
thing to visit, and unvisited dashboards are worse than no dashboard because
they create a feeling of coverage.

**More detections for their own sake.** v1.0 watches six controls and reports
honestly when it cannot see one. Twelve controls with four silently broken is
strictly worse than six that are trustworthy.

**Making the private repo public**, or widening what the public feed publishes.
The current projection is the minimum that makes cloud reading possible.

**Cloud-hosted collection.** The collector must run where the endpoint is.

---

## Decision record

| Version | Entry condition |
|---|---|
| v1.1 | 7 consecutive days of unattended v1.0 operation |
| v1.2 | v1.1 stable and enough history to make trends meaningful |
| v2.0 | Observed evidence that a specific v2.0 item is needed |

The strongest argument against building any of this is that v1.0 has not yet run
unattended for a single full day. Everything above is speculation until that
number is seven.
