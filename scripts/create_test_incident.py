#!/usr/bin/env python3
"""MVP: turn a sample alert into an assigned GitHub Issue.

Flow this script proves:
    Alert -> MCP (this script) -> GitHub Issue -> Assign KEVIN-NGUYENDAD
    -> GitHub Mobile push -> iPhone

The last two hops (push notification -> iPhone) are handled entirely by
GitHub's own notification system once the issue is assigned -- this
script's job ends at "assign the issue and print its URL".

Usage:
    export GITHUB_TOKEN=ghp_xxx        # macOS / Linux
    $env:GITHUB_TOKEN = "ghp_xxx"      # PowerShell

    python scripts/create_test_incident.py
    python scripts/create_test_incident.py --alert sample-events/test-alert.json
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

REPO_OWNER = "KEVIN-NGUYENDAD"
REPO_NAME = "mcp-cyber-tools"
ASSIGNEE = "KEVIN-NGUYENDAD"

DEFAULT_ALERT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample-events",
    "test-alert.json",
)

SEVERITY_SCORES = {
    "critical": 95,
    "high": 75,
    "medium": 50,
    "low": 20,
}

# Words that should render as an acronym instead of Title Case.
ACRONYMS = {"sql", "xss", "ip", "rce", "csrf", "ssrf"}


def humanize_event_type(event_type: str) -> str:
    words = event_type.split("_")
    return " ".join(w.upper() if w.lower() in ACRONYMS else w.capitalize() for w in words)


def load_alert(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def score_alert(alert: dict) -> int:
    severity = str(alert.get("severity", "")).lower()
    if severity not in SEVERITY_SCORES:
        raise ValueError(
            f"Unknown severity '{severity}'. Expected one of: {', '.join(SEVERITY_SCORES)}."
        )
    return SEVERITY_SCORES[severity]


def build_issue(alert: dict, risk_score: int, timestamp: str) -> dict:
    severity = str(alert.get("severity", "unknown")).upper()
    event_label = humanize_event_type(str(alert.get("event_type", "unknown")))
    title = f"[{severity}] {event_label} | Risk {risk_score}"
    body = (
        "## Alert Details\n\n"
        f"- **Source:** {alert.get('source', 'unknown')}\n"
        f"- **Event Type:** {alert.get('event_type', 'unknown')}\n"
        f"- **IP:** {alert.get('ip', 'unknown')}\n"
        f"- **Risk Score:** {risk_score}\n"
        f"- **Timestamp:** {timestamp}\n"
    )
    return {"title": title, "body": body}


def github_request(method: str, url: str, token: str, payload: Optional[dict] = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise SystemExit(f"GitHub API error {e.code} on {method} {url}:\n{detail}")


def create_issue(token: str, title: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    return github_request("POST", url, token, {"title": title, "body": body})


def assign_issue(token: str, issue_number: int, assignee: str) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/assignees"
    return github_request("POST", url, token, {"assignees": [assignee]})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alert",
        default=DEFAULT_ALERT_PATH,
        help="Path to the alert JSON file (default: sample-events/test-alert.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit(
            "Missing GITHUB_TOKEN environment variable.\n"
            "Create a GitHub Personal Access Token with 'issues' write access "
            "(fine-grained) or the 'repo' scope (classic), then run:\n"
            '  export GITHUB_TOKEN="ghp_xxx"      # macOS / Linux\n'
            '  $env:GITHUB_TOKEN = "ghp_xxx"       # PowerShell'
        )

    alert = load_alert(args.alert)
    risk_score = score_alert(alert)
    timestamp = datetime.now(timezone.utc).isoformat()

    issue_fields = build_issue(alert, risk_score, timestamp)
    print(f"Creating issue: {issue_fields['title']}")

    issue = create_issue(token, issue_fields["title"], issue_fields["body"])
    issue_number = issue["number"]
    print(f"Issue #{issue_number} created.")

    assign_issue(token, issue_number, ASSIGNEE)
    print(f"Assigned to {ASSIGNEE}.")

    print(f"Issue URL: {issue['html_url']}")


if __name__ == "__main__":
    main()
