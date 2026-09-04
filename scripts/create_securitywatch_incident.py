#!/usr/bin/env python3
"""MVP #3: turn a real security-watch.js control-drift alert into an assigned
GitHub Issue, with 24-hour duplicate detection.

Flow this script proves:
    Real Alert (security-watch.js -> alerts.json)
    -> MCP (this script)
    -> Risk Score
    -> Duplicate Detection (24h window)
    -> GitHub Issue (new) OR occurrence update (duplicate)
    -> Assign KEVIN-NGUYENDAD
    -> GitHub Mobile push -> iPhone

This is MVP #1/#2 (scripts/create_test_incident.py,
scripts/create_defender_incident.py) with a third real alert source swapped
in. Everything past "get a real alert" -- scoring, issue formatting, GitHub
API calls, assignment -- is reused unchanged from create_test_incident.py.

Alert source: security-watch.js, the endpoint-control watcher already
running on this host via Task Scheduler (HOME-SOC-Scan-And-Export). It
polls 5 real Windows security controls (DNS, Firewall, Defender real-time
protection, RDP, SSH) every cycle and appends any transition away from the
approved baseline to its own alerts.json. No new alert source was built --
this reads whatever security-watch.js has already logged.

Duplicate detection: GitHub itself is the source of truth -- no separate
local state file. An open issue whose title matches this alert's title
(severity + event type + risk score, which are stable per alert type) and
whose "Last Seen" timestamp is within the last 24 hours counts as a
duplicate. Its occurrence count and Last Seen field are updated in place;
no new issue is created.

Usage:
    $env:GITHUB_TOKEN = "ghp_xxx"      # PowerShell, or: (gh auth token)
    python scripts/create_securitywatch_incident.py
    python scripts/create_securitywatch_incident.py --alerts-json path\\to\\alerts.json
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from create_test_incident import (
    ASSIGNEE,
    REPO_NAME,
    REPO_OWNER,
    assign_issue,
    build_issue,
    create_issue,
    github_request,
    score_alert,
)

# The live pipeline security-watch.js already runs on a schedule
# (HOME-SOC-Scan-And-Export) and writes here.
DEFAULT_ALERTS_JSON_PATH = (
    r"C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\alerts.json"
)

# security-watch.js's five rules are all CRITICAL today; mapped defensively
# in case that changes.
SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

DEDUP_WINDOW = timedelta(hours=24)


def load_alerts(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("alerts", [])


def to_alert(sw_alert: dict) -> dict:
    """Normalize a security-watch.js alert entry onto this pipeline's alert schema."""
    severity = SEVERITY_MAP.get(str(sw_alert.get("severity", "")).upper(), "low")

    # security-watch.js's own `control` field doesn't match its baseline/state key
    # for two of the five rules (control: 'firewall' vs. state key 'fw', and
    # 'defender' vs. 'def'), so baseline_value/current_value come back as
    # JSON `undefined` -- silently absent, not null -- for FIREWALL_DISABLED and
    # DEFENDER_DISABLED. Omit the field rather than print a misleading "None".
    baseline_value = sw_alert.get("baseline_value")
    current_value = sw_alert.get("current_value")
    control_diff = None
    if baseline_value is not None or current_value is not None:
        control_diff = f"baseline={baseline_value} current={current_value}"

    return {
        "source": "security_watch",
        "event_type": str(sw_alert.get("type", "unknown")).lower(),
        "severity": severity,
        "ip": "unknown",  # host control drift, no network IP involved
        "threat_signature": sw_alert.get("description"),
        "process": None,
        "file": control_diff,
        "detection_time": sw_alert.get("detected_at"),
    }


def find_open_issues(token: str) -> list:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=open&per_page=100"
    return github_request("GET", url, token)


def parse_tracking(body: str) -> dict:
    """Pull Occurrences / First Seen / Last Seen out of an issue body."""
    occ = re.search(r"\*\*Occurrences:\*\*\s*(\d+)", body or "")
    first = re.search(r"\*\*First Seen:\*\*\s*(\S+)", body or "")
    last = re.search(r"\*\*Last Seen:\*\*\s*(\S+)", body or "")
    return {
        "occurrences": int(occ.group(1)) if occ else 1,
        "first_seen": first.group(1) if first else None,
        "last_seen": last.group(1) if last else None,
    }


def with_tracking_block(body: str, occurrences: int, first_seen: str, last_seen: str) -> str:
    # Replace any existing tracking block rather than stacking a new one each update.
    base = re.split(r"\n## Occurrence Tracking\n", body or "")[0].rstrip() + "\n"
    block = (
        "\n## Occurrence Tracking\n\n"
        f"- **Occurrences:** {occurrences}\n"
        f"- **First Seen:** {first_seen}\n"
        f"- **Last Seen:** {last_seen}\n"
    )
    return base + block


def parse_timestamp(value: str):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def find_duplicate(issues: list, title: str, now: datetime):
    """An open issue with the same title, last seen within the dedup window."""
    for issue in issues:
        if issue["title"] != title:
            continue
        tracking = parse_tracking(issue.get("body") or "")
        last_seen = parse_timestamp(tracking["last_seen"]) or parse_timestamp(issue["created_at"])
        if last_seen is None:
            continue
        if now - last_seen <= DEDUP_WINDOW:
            return issue, tracking
    return None, None


def update_issue_body(token: str, issue_number: int, body: str) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}"
    return github_request("PATCH", url, token, {"body": body})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alerts-json",
        default=DEFAULT_ALERTS_JSON_PATH,
        help="Path to security-watch.js's alerts.json (default: the live host path)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit(
            "Missing GITHUB_TOKEN environment variable.\n"
            '  $env:GITHUB_TOKEN = "ghp_xxx"       # PowerShell\n'
            "  $env:GITHUB_TOKEN = (gh auth token)  # or reuse gh's token"
        )

    alerts = load_alerts(args.alerts_json)
    if not alerts:
        sys.exit(
            f"No alerts in {args.alerts_json} -- security-watch.js reports all "
            "5 controls at baseline. Nothing to process."
        )

    sw_alert = alerts[0]  # newest entry; security-watch.js prepends on each run
    alert = to_alert(sw_alert)
    risk_score = score_alert(alert)
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()

    issue_fields = build_issue(alert, risk_score, timestamp)
    print(f"Real alert source: security-watch.js ({alert['event_type']})")
    print(f"Signature: {alert['threat_signature']}")

    issues = find_open_issues(token)
    duplicate, tracking = find_duplicate(issues, issue_fields["title"], now)

    if duplicate:
        occurrences = tracking["occurrences"] + 1
        first_seen = tracking["first_seen"] or timestamp
        new_body = with_tracking_block(duplicate["body"], occurrences, first_seen, timestamp)
        update_issue_body(token, duplicate["number"], new_body)
        print(f"Duplicate within 24h -- not creating a new issue.")
        print(f"Updated Issue #{duplicate['number']}: occurrences={occurrences}, last_seen={timestamp}")
        print(f"Issue URL: {duplicate['html_url']}")
        return

    body = with_tracking_block(issue_fields["body"], 1, timestamp, timestamp)
    print(f"Creating issue: {issue_fields['title']}")

    issue = create_issue(token, issue_fields["title"], body)
    issue_number = issue["number"]
    print(f"Issue #{issue_number} created.")

    assign_issue(token, issue_number, ASSIGNEE)
    print(f"Assigned to {ASSIGNEE}.")

    print(f"Issue URL: {issue['html_url']}")


if __name__ == "__main__":
    main()
