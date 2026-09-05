"""Shared Event Schema for the SentinelOps Event Hub (Day 1).

Event Schema:
    {
        "source": str,      # e.g. "security_watch", "windows_defender"
        "severity": str,    # "critical" | "high" | "medium" | "low"
        "title": str,       # human-readable event label
        "summary": str,     # short description of what happened
        "evidence": list,   # [{"key": str, "value": str}, ...]
    }

This module only normalizes each source's existing internal alert dict
(source/event_type/severity/ip/threat_signature/process/file/
detection_time -- produced by each script's own to_alert()) into the
schema above. It does not replace or alter scoring, issue formatting,
or GitHub calls: score_alert(), build_issue(), create_issue(),
assign_issue() and github_request() keep consuming the original alert
dict unchanged.
"""
from create_test_incident import humanize_event_type

EVIDENCE_FIELDS = ("ip", "process", "file", "detection_time")


def make_event(source: str, severity: str, title: str, summary: str, evidence: list) -> dict:
    return {
        "source": source,
        "severity": severity,
        "title": title,
        "summary": summary,
        "evidence": evidence,
    }


def alert_to_event(alert: dict) -> dict:
    """Normalize this pipeline's internal alert dict into the shared Event Schema."""
    title = humanize_event_type(str(alert.get("event_type", "unknown")))
    summary = alert.get("threat_signature") or title
    evidence = [
        {"key": field, "value": alert[field]}
        for field in EVIDENCE_FIELDS
        if alert.get(field)
    ]
    return make_event(
        source=alert.get("source", "unknown"),
        severity=alert.get("severity", "unknown"),
        title=title,
        summary=summary,
        evidence=evidence,
    )
