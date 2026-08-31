# HOME SOC — Runbook

**Version:** 1.0 · **Audience:** the operator (you)

---

## Observation period

v1.0 is frozen until **seven consecutive days** of unattended operation.

| Day | Date | 19:45 chain | 20:10 bulletin | OPEN-001 fresh? | Notes |
|---|---|---|---|---|---|
| 1 | 2026-08-30 | ☐ | ☐ | ☐ | first unattended run |
| 2 | 2026-08-31 | ☐ | ☐ | ☐ | |
| 3 | 2026-09-01 | ☐ | ☐ | ☐ | |
| 4 | 2026-09-02 | ☐ | ☐ | ☐ | |
| 5 | 2026-09-03 | ☐ | ☐ | ☐ | |
| 6 | 2026-09-04 | ☐ | ☐ | ☐ | |
| 7 | 2026-09-05 | ☐ | ☐ | ☐ | |

A day counts only if both ran without you touching anything. A missed day resets
the count — the point is proving the system survives ordinary neglect.

**OPEN-001 column.** Tick only when the bulletin's `source_scan_at` is within
three hours of its own generation time *and* matches the GitHub API. Seven
consecutive ticks move OPEN-001 from MONITOR to RESOLVED. A single miss resets
that count independently of the other two columns — the defect can recur on a
day when everything else runs perfectly.

---

## Daily operations

**Effort: reading one email.**

The bulletin arrives at 20:10. Read four fields:

| Field | Expected | If not |
|---|---|---|
| Risk level | GREEN | → Incident response |
| Control coverage | 6/6 | → Playbook C |
| Data age | under 24 h | → Playbook B |
| Device count | steady | → Playbook D |
| `source_scan_at` vs bulletin time | under 3 h | → Playbook G |

**No bulletin at all** → Playbook A.

While OPEN-001 is in MONITOR, check the last row before acting on anything else
in the bulletin. A bulletin that read a superseded feed can report a coverage
gap that no longer exists, or miss a control change that already happened.

Do nothing else. A daily routine you actually keep beats a thorough one you
abandon in a week.

---

## Weekly checks

**Sunday, ~5 minutes.**

1. **Device list.** Open the latest bulletin. Does every device belong to you?
   A device you cannot account for is the single highest-value finding this
   system produces.

2. **Unidentified count.** `devices_unidentified` should be 0. Anything above
   that is a device whose vendor prefix is unknown — worth 60 seconds of
   attention.

3. **Chain health:**
   ```powershell
   Get-ScheduledTask -TaskName "HOME-SOC-Scan-And-Export" | Get-ScheduledTaskInfo
   ```
   `LastTaskResult` should be `0`. (`267009` means running; `267011` means never
   run.)

4. **Feed freshness:**
   ```powershell
   (Invoke-RestMethod "https://api.github.com/repos/KEVIN-NGUYENDAD/home-soc-reports/commits?per_page=1").commit.author.date
   ```
   Should be within 24 hours.

   Use the API, not the raw URL. `raw.githubusercontent.com` caches for about
   five minutes and can serve a superseded file that still reports
   `stale: false` — see limitation 10 in the release notes.

5. **No new port forwarding** on the router. The scanner cannot see router
   config — this one is manual.

---

## Monthly checks

**First Sunday, ~20 minutes.**

1. **Gateway firmware.** Check the ISP portal for updates.

2. **Baseline still correct.**
   ```powershell
   node security-watch.js --show
   ```
   Compare against `baseline.json`. If you have legitimately changed something
   (new DNS, RDP intentionally enabled), re-approve:
   ```powershell
   node security-watch.js --approve-baseline
   ```
   Do this deliberately. Re-approving hides whatever is currently divergent.

3. **Leak audit on the public repo.** The guard only checks the three generated
   files. Sweep everything:
   ```powershell
   cd "$env:APPDATA\Claude\Projects\home-soc-reports"
   foreach ($f in (git ls-files)) {
     $c = Get-Content $f -Raw
     if ($c -match '\b(?:\d{1,3}\.){3}\d{1,3}\b') { "IPv4 in $f" }
     if ($c -match '\b[0-9a-f]{2}([-:])[0-9a-f]{2}(?:\1[0-9a-f]{2}){4}\b') { "MAC in $f" }
     if ($c -match '(?i)(?<![\w-])(arris|reolink|commscope|cox|shenzhen|netgear)(?![\w-])') { "VENDOR in $f" }
   }
   ```
   Silence is a pass. This check exists because a real leak was once found in
   `README.md`, which the guard does not cover.

4. **Alert history.** Open `alerts.json`. Alerts you never investigated are
   worse than no alerts — they train you to ignore the system.

5. **Disk.** `network-scan-data/` grows one file per run. Prune below 100 MB.

---

## Annual checks

- Rotate WiFi passwords
- Full firewall rule audit
- Check IoT devices for end-of-life firmware support
- Re-read [ARCHITECTURE.md](ARCHITECTURE.md) — does it still describe reality?

---

## Incident response

### Playbook A — No bulletin arrived

```powershell
Get-ScheduledTask -TaskName "HOME-SOC-Scan-And-Export" | Get-ScheduledTaskInfo
```

| LastTaskResult | Meaning | Action |
|---|---|---|
| `0` | Chain succeeded | Problem is downstream → check the Claude Scheduled task in the Scheduled sidebar |
| `267009` | Still running | Wait, re-check |
| `267011` | Never ran | Machine was off at 19:45; `-StartWhenAvailable` runs it on next boot |
| anything else | A stage failed | Run the chain by hand (below) |

Run by hand:
```powershell
cd "$env:APPDATA\Claude\Projects\mcp-cyber-tools"; node security-watch.js; node iot-device-scanner.js; node export-home-soc-reports.js
```

---

### Playbook B — Data is stale

`stale: true` means the newest scan is over 48 hours old. The bulletin still
reports a risk level, but that level describes a network as it was two days ago.

1. Was the machine off? That is the usual answer.
2. Run the chain by hand.
3. If the scan produces no new file, run the scanner alone and read its output.

**Treat a stale GREEN as unknown, not as safe.** v1.0 flags staleness but does
not escalate it — that judgement is yours.

---

### Playbook C — Controls report NO DATA

Coverage below 6/6 means a control has no collector output.

```powershell
cd "$env:APPDATA\Claude\Projects\mcp-cyber-tools"
node security-watch.js --show
```

- Readings print correctly → `state.json` is not reaching the exporter. Check
  the file exists and parses.
- A reading shows `unknown` → that probe failed. Run its PowerShell command
  directly to see the error.
- `No baseline found` → `baseline.json` is missing or unreadable. A UTF-8 BOM
  was historically the cause; both scripts now strip it.

**Do not ignore a coverage gap because the risk level is GREEN.** GREEN with
four unknown controls means "nothing found in the part still being watched".

---

### Playbook D — Device count changed

**Count went up.** A new device joined. Identify it. If `devices_unidentified`
increased, an unknown-vendor device is on your network — investigate before
dismissing.

**Count went down.** v1.0 cannot distinguish "device removed" from "device
asleep". The scanner reads the ARP table; an idle device vanishes from it. Check
whether the missing device is simply off before assuming anything.

---

### Playbook E — CRITICAL alert / risk level RED

The bulletin reports which control changed, from what, to what, and when.

1. **Did you do it?** A DNS change after switching VPN, RDP after enabling
   remote help — legitimate changes trigger the same alert as hostile ones.
   Legitimate → re-approve the baseline. Then the alert stops.

2. **Not you** — act by control:

   | Control | Immediate action |
   |---|---|
   | DNS changed | Check router DNS settings; change the router password |
   | Firewall disabled | Re-enable now; then find what disabled it |
   | Defender disabled | Re-enable; run a full scan |
   | RDP listening | Disable; check Event Viewer for logons |
   | SSH listening | Stop the service; check SSH logs |

3. **After acting:** run the chain by hand so the feed reflects the fix, and
   confirm the next bulletin returns to GREEN.

4. **Cooldown.** The same alert type stays silent for four hours after firing.
   To re-arm immediately:
   ```powershell
   Remove-Item "$env:APPDATA\Claude\Projects\mcp-cyber-tools\cooldown.json"
   ```

---

### Playbook F — Leak guard aborted the export

Output ends with `[ABORT] ... would leak ...`. **This is the system working.**
Nothing was written and nothing was pushed.

1. Read what it caught. The message names the file and the matched text.
2. **Genuine leak** — a sanitizer missed a case. Fix the classifier in
   `export-home-soc-reports.js`. Do not weaken the guard.
3. **False positive** — a vendor word appearing innocently, as `ring` inside
   `monitoring` once did. Fix the matcher, not the policy.

Never disable the guard to get an export through. An abort costs one bulletin.
A leak cannot be recalled — the public repo has a permanent history.

---

### Playbook G — Bulletin may have read stale data (OPEN-001)

Trigger: the bulletin's `source_scan_at` is more than three hours older than the
bulletin's own generation time, or it prints the confidence warning.

1. **Read the source directly.** This bypasses every cache between you and the
   published file:
   ```powershell
   $a = Invoke-RestMethod "https://api.github.com/repos/KEVIN-NGUYENDAD/home-soc-reports/contents/BASELINE-LATEST.json?ref=main" -Headers @{"User-Agent"="v"}
   $j = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($a.content)) | ConvertFrom-Json
   "source_scan_at   : $($j.source_scan_at)"
   "risk_level       : $($j.risk_level)"
   "controls_unknown : $($j.coverage.controls_unknown)"
   "alerts           : $($j.alerts.Count)"
   ```

2. **Compare.** If the API disagrees with the bulletin, the bulletin read a
   superseded copy. **The API is authoritative.** Act on it, not on the email.

3. **Record the miss.** Leave the OPEN-001 column unticked for that day and note
   both timestamps. The gap size is the useful measurement — 14 minutes and
   2 h 51 m have both been observed.

4. **Do not re-run the chain to "fix" the bulletin.** Publishing again does not
   change what the next fetch is served, and it discards a data point about how
   long the cache actually holds.

**Direction of error.** A stale read can hide a real alert as easily as it can
invent a phantom coverage gap. Both observed occurrences happened to be
harmless — reporting a gap that had already been closed. The reverse, reporting
GREEN over a control that has since been disabled, is the same defect pointed
the dangerous way.

---

## Command reference

```powershell
# Current readings, write nothing
node security-watch.js --show

# Collect and compare
node security-watch.js

# Approve current state as baseline (deliberate act)
node security-watch.js --approve-baseline

# Scan the network
node iot-device-scanner.js

# Preview the export, write nothing
node export-home-soc-reports.js --dry-run

# Export and commit, do not push
node export-home-soc-reports.js --no-push

# Full export and push
node export-home-soc-reports.js

# Run the whole chain now
Start-ScheduledTask -TaskName "HOME-SOC-Scan-And-Export"

# Chain status
Get-ScheduledTask -TaskName "HOME-SOC-Scan-And-Export" | Get-ScheduledTaskInfo
```

All commands run from `%APPDATA%\Claude\Projects\mcp-cyber-tools`.

---

## Change policy during observation

**Allowed:** bug fixes, documentation corrections, baseline re-approval.

**Not allowed:** new detections, new outputs, new schedules, refactors, schema
changes.

A system under observation must not move, or the observation measures nothing.
