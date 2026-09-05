#!/usr/bin/env python3
"""MVP #3/#4: turn a real security-watch.js control-drift alert into an
assigned, enriched GitHub Issue, with 24-hour duplicate detection.

Flow this script proves:
    Real Alert (security-watch.js -> alerts.json)
    -> MCP (this script)
    -> Risk Score
    -> Duplicate Detection (24h window)
    -> GitHub Issue (new) OR occurrence update (duplicate)
    -> Auto Labels + MCP Analysis Comment
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

Enrichment (MVP #4): every processed alert -- new or duplicate -- gets auto
labels (subset of critical/high/defender/control-drift/firewall, chosen
from the alert's severity/source/event type) and an "MCP Analysis" comment
(risk score, reasons, recommendations) posted to the issue.

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
from event_schema import alert_to_event

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

# Reason / recommendation text per security-watch.js alert type. Scoped to
# the 5 control-drift rules it actually emits today; unknown types fall back
# to DEFAULT_ENRICHMENT.
ENRICHMENT_RULES = {
    "dns_change": {
        "reasons": [
            "DNS resolvers changed since baseline",
            "Possible DNS hijack or rogue resolver",
        ],
        "recommendations": [
            "Confirm the new DNS servers were an intentional change",
            "Revert to the approved DNS servers if unintended",
            "Check router/DHCP settings for tampering",
        ],
    },
    "firewall_disabled": {
        "reasons": [
            "Firewall disabled",
            "Security control drift detected",
        ],
        "recommendations": [
            "Re-enable firewall",
            "Check recent changes",
            "Review related events",
        ],
    },
    "defender_disabled": {
        "reasons": [
            "Real-time protection disabled",
            "Security control drift detected",
        ],
        "recommendations": [
            "Re-enable Windows Defender real-time protection",
            "Check recent changes",
            "Scan the host for threats once protection is restored",
        ],
    },
    "rdp_enabled": {
        "reasons": [
            "Remote Desktop started listening",
            "Increased remote-access attack surface",
        ],
        "recommendations": [
            "Confirm RDP was enabled intentionally",
            "Disable RDP if not required",
            "Review recent logon attempts",
        ],
    },
    "ssh_enabled": {
        "reasons": [
            "SSH started listening",
            "Increased remote-access attack surface",
        ],
        "recommendations": [
            "Confirm SSH was enabled intentionally",
            "Disable SSH if not required",
            "Review recent connection attempts",
        ],
    },
}
DEFAULT_ENRICHMENT = {
    "reasons": ["Security control drift detected"],
    "recommendations": ["Review recent changes", "Review related events"],
}


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


def compute_labels(alert: dict) -> list:
    """Subset of critical/high/defender/control-drift/firewall that applies
    to this specific alert."""
    labels = []
    if alert["severity"] == "critical":
        labels.append("critical")
    elif alert["severity"] == "high":
        labels.append("high")
    if alert["source"] == "windows_defender":
        labels.append("defender")
    if alert["source"] == "security_watch":
        labels.append("control-drift")
    if "firewall" in alert["event_type"]:
        labels.append("firewall")
    return labels


def build_analysis_comment(alert: dict, risk_score: int, occurrence_note: str = None) -> str:
    rules = ENRICHMENT_RULES.get(alert["event_type"], DEFAULT_ENRICHMENT)
    lines = ["## MCP Analysis", ""]
    if occurrence_note:
        lines += [occurrence_note, ""]
    lines += [f"**Risk Score:** {risk_score}", ""]
    lines += ["**Reason:**"]
    lines += [f"- {r}" for r in rules["reasons"]]
    lines += ["", "**Recommendation:**"]
    lines += [f"{i}. {r}" for i, r in enumerate(rules["recommendations"], 1)]
    return "\n".join(lines) + "\n"


def add_labels(token: str, issue_number: int, labels: list) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/labels"
    return github_request("POST", url, token, {"labels": labels})


def add_comment(token: str, issue_number: int, body: str) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments"
    return github_request("POST", url, token, {"body": body})


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

    # Event Hub Day 1: normalize into the shared Event Schema alongside the
    # existing pipeline. Purely additive -- scoring, issue text, and GitHub
    # calls below still consume `alert` unchanged.
    event = alert_to_event(alert)
    print(f"Event: {json.dumps(event)}")

    risk_score = score_alert(alert)
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()

    issue_fields = build_issue(alert, risk_score, timestamp)
    print(f"Real alert source: security-watch.js ({alert['event_type']})")
    print(f"Signature: {alert['threat_signature']}")

    labels = compute_labels(alert)

    issues = find_open_issues(token)
    duplicate, tracking = find_duplicate(issues, issue_fields["title"], now)

    if duplicate:
        occurrences = tracking["occurrences"] + 1
        first_seen = tracking["first_seen"] or timestamp
        new_body = with_tracking_block(duplicate["body"], occurrences, first_seen, timestamp)
        update_issue_body(token, duplicate["number"], new_body)
        issue_number = duplicate["number"]
        print(f"Duplicate within 24h -- not creating a new issue.")
        print(f"Updated Issue #{issue_number}: occurrences={occurrences}, last_seen={timestamp}")

        add_labels(token, issue_number, labels)
        print(f"Labels ensured: {', '.join(labels) if labels else '(none)'}")

        occurrence_note = f"_Recurrence detected -- occurrence #{occurrences}._"
        comment = build_analysis_comment(alert, risk_score, occurrence_note)
        add_comment(token, issue_number, comment)
        print("MCP analysis comment posted.")

        print(f"Issue URL: {duplicate['html_url']}")
        return

    body = with_tracking_block(issue_fields["body"], 1, timestamp, timestamp)
    print(f"Creating issue: {issue_fields['title']}")

    issue = create_issue(token, issue_fields["title"], body)
    issue_number = issue["number"]
    print(f"Issue #{issue_number} created.")

    assign_issue(token, issue_number, ASSIGNEE)
    print(f"Assigned to {ASSIGNEE}.")

    add_labels(token, issue_number, labels)
    print(f"Labels applied: {', '.join(labels) if labels else '(none)'}")

    comment = build_analysis_comment(alert, risk_score)
    add_comment(token, issue_number, comment)
    print("MCP analysis comment posted.")

    print(f"Issue URL: {issue['html_url']}")


if __name__ == "__main__":
    main()
