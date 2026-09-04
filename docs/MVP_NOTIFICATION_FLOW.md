# MVP: Alert-to-Mobile Notification Flow

This is the smallest possible proof of one specific flow: a raw alert
becomes an assigned, mobile-notified GitHub Issue.

```
Alert
  |
  v
MCP  (scripts/create_test_incident.py)
  |
  v
GitHub Issue
  |
  v
Assignment (KEVIN-NGUYENDAD)
  |
  v
GitHub Mobile Push
  |
  v
iPhone
```

## What each hop is

| Step | What it is | What proves it |
|---|---|---|
| Alert | A raw security event, as JSON | `sample-events/test-alert.json` |
| MCP | Reads the alert, scores its severity, formats it | `scripts/create_test_incident.py` |
| GitHub Issue | The scored alert, created via the GitHub REST API | Issue title/body produced by the script |
| Assignment | The issue is assigned to `KEVIN-NGUYENDAD` | `POST /issues/{n}/assignees` call in the script |
| GitHub Mobile Push | GitHub's own notification system pushes an alert for the new assignment | Handled entirely by GitHub — not by this script |
| iPhone | The push notification arrives via the GitHub Mobile app | Requires GitHub Mobile installed and notifications enabled for this repo |

The script's responsibility stops at "assign the issue and print its
URL." Everything from that point on — the push notification and its
delivery to an iPhone — is standard GitHub Mobile behavior, not
something this MVP implements or controls.

## Risk scoring

| Severity | Score |
|---|---|
| critical | 95 |
| high | 75 |
| medium | 50 |
| low | 20 |

## Issue format

```
Title: [SEVERITY] Event Type | Risk <score>

Body:
## Alert Details

- Source
- Event Type
- IP
- Risk Score
- Timestamp
```

`Timestamp` is the time the script processed the alert (UTC, ISO 8601)
— the sample alert JSON does not carry its own timestamp field.

## Scope of this MVP

Deliberately excluded, per the brief this MVP was scoped to:

- No dashboard
- No database
- No PostgreSQL
- No Redis
- No Kubernetes
- No additional architecture beyond the three files added here

This proves the notification path exists and works end-to-end. It is
not a production alert pipeline.

## Files added

- `sample-events/test-alert.json` — one sample alert
- `scripts/create_test_incident.py` — reads the alert, scores it,
  creates the GitHub Issue, assigns it, prints the Issue URL
- `docs/MVP_NOTIFICATION_FLOW.md` — this document

## Running it

```bash
export GITHUB_TOKEN="ghp_xxx"                # a PAT with issues write access
python scripts/create_test_incident.py
```

See the repo root README for general setup; this script has no
dependency beyond the Python 3 standard library.
