#!/usr/bin/env python3
"""MVP #2: turn a real Windows Defender detection into an assigned GitHub Issue.

Flow this script proves:
    Real Alert (Get-MpThreat / Get-MpThreatDetection)
    -> MCP (this script)
    -> Risk Score
    -> GitHub Issue
    -> Assign KEVIN-NGUYENDAD
    -> GitHub Mobile push -> iPhone

This is MVP #1 (scripts/create_test_incident.py) with a real alert source
swapped in for the static sample-events/test-alert.json. Everything past
"get a real alert" -- scoring, issue formatting, GitHub API calls,
assignment -- is reused unchanged from create_test_incident.py.

Alert source: Windows Defender, via PowerShell `Get-MpThreat` /
`Get-MpThreatDetection` (the same cmdlets already used by
modules/defender.js's defenderThreats tool). No new alert source was
built -- this reads whatever Defender has already detected on this host.

Usage:
    $env:GITHUB_TOKEN = "ghp_xxx"      # PowerShell
    python scripts/create_defender_incident.py

To generate a real, safe detection to test against, drop an EICAR test
string (https://en.wikipedia.org/wiki/EICAR_test_file) into any
non-excluded path and let Defender's real-time protection catch it:
    python -c "open(r'%TEMP%\\eicar_test.txt','w').write(
        'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')"
"""
import json
import subprocess
import sys

from create_test_incident import (
    ASSIGNEE,
    assign_issue,
    build_issue,
    create_issue,
    score_alert,
)
import os
from datetime import datetime, timezone

# Get-MpThreat SeverityID -> this pipeline's severity buckets.
# https://learn.microsoft.com/en-us/powershell/module/defender/get-mpthreat
DEFENDER_SEVERITY_MAP = {
    0: "low",     # Unknown
    1: "low",     # Low
    2: "medium",  # Moderate
    3: "high",    # (unused by Defender today, kept as a safe fallback)
    4: "high",    # High
    5: "critical",  # Severe
}

PS_SCRIPT = r"""
$d = Get-MpThreatDetection -ErrorAction SilentlyContinue |
    Sort-Object InitialDetectionTime -Descending |
    Select-Object -First 1
if (-not $d) { Write-Output '{}'; exit 0 }
$t = Get-MpThreat -ErrorAction SilentlyContinue |
    Where-Object { $_.ThreatID -eq $d.ThreatID } |
    Select-Object -First 1
[PSCustomObject]@{
    ThreatID      = $d.ThreatID
    ThreatName    = $t.ThreatName
    SeverityID    = $t.SeverityID
    ProcessName   = $d.ProcessName
    Resources     = ($d.Resources -join '; ')
    DetectionTime = if ($d.InitialDetectionTime) { $d.InitialDetectionTime.ToString('o') } else { $null }
    ActionSuccess = $d.ActionSuccess
} | ConvertTo-Json -Depth 5 -Compress
"""


def get_latest_defender_detection() -> dict:
    """Query Windows Defender for its most recent threat detection."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"PowerShell query failed:\n{result.stderr}")

    raw = result.stdout.strip()
    if not raw:
        raise SystemExit("No output from Get-MpThreatDetection.")

    detection = json.loads(raw)
    if not detection:
        raise SystemExit(
            "No Windows Defender detections found on this host.\n"
            "Trigger one first with a safe EICAR test file, e.g.:\n"
            '  python -c "open(r\'%TEMP%\\eicar_test.txt\', \'w\').write('
            "'X5O!P%@AP[4\\\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')\""
        )
    return detection


def to_alert(detection: dict) -> dict:
    """Normalize a raw Defender detection into this pipeline's alert schema."""
    severity_id = detection.get("SeverityID")
    severity = DEFENDER_SEVERITY_MAP.get(severity_id, "low")
    threat_name = detection.get("ThreatName") or "unknown_threat"

    return {
        "source": "windows_defender",
        "event_type": threat_name.replace(":", "_").replace("/", "_").lower(),
        "severity": severity,
        "ip": "unknown",  # host-based detection, no network IP involved
        "threat_signature": threat_name,
        "process": detection.get("ProcessName") or None,
        "file": detection.get("Resources") or None,
        "detection_time": detection.get("DetectionTime") or None,
    }


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit(
            "Missing GITHUB_TOKEN environment variable.\n"
            '  $env:GITHUB_TOKEN = "ghp_xxx"       # PowerShell'
        )

    detection = get_latest_defender_detection()
    alert = to_alert(detection)
    risk_score = score_alert(alert)
    timestamp = datetime.now(timezone.utc).isoformat()

    issue_fields = build_issue(alert, risk_score, timestamp)
    print(f"Real alert source: Windows Defender (Get-MpThreat / Get-MpThreatDetection)")
    print(f"Threat: {alert['threat_signature']}")
    print(f"Creating issue: {issue_fields['title']}")

    issue = create_issue(token, issue_fields["title"], issue_fields["body"])
    issue_number = issue["number"]
    print(f"Issue #{issue_number} created.")

    assign_issue(token, issue_number, ASSIGNEE)
    print(f"Assigned to {ASSIGNEE}.")

    print(f"Issue URL: {issue['html_url']}")


if __name__ == "__main__":
    main()
