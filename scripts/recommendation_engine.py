"""Recommendation Engine for the SentinelOps Event Hub.

Turns a Change Detector event (Event Hub schema: source/severity/title/
summary/evidence) into a human-actionable recommendation + priority, and
stores it in the Daily Brief Store (daily_brief_store.add_recommendation())
so it surfaces under "Recommended Actions" / "what should I do next?"
(daily_brief_generator.py). Rule-based, matched on source + change type +
evidence -- no scoring, no diffing, no GitHub calls. Purely additive:
nothing in change_detector.py's detection logic, baseline_store.py, or
daily_brief_store.py's storage logic is touched.
"""
from daily_brief_store import add_recommendation

PRIORITY_BY_SEVERITY = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}

_DEFAULT_BY_SEVERITY = {
    "critical": "Investigate immediately.",
    "high": "Investigate as soon as possible.",
    "medium": "Review during the next check-in.",
    "low": "No action needed; monitor.",
}


def _evidence_get(evidence: list, key: str):
    for item in evidence or []:
        if item.get("key") == key:
            return item.get("value")
    return None


def _change_type(event: dict) -> str:
    title = event.get("title", "")
    if title.startswith("New entity detected"):
        return "new_entity"
    if title.startswith("Entity disappeared"):
        return "removed_entity"
    return "field_changed"


# Rules are checked in order; the first match wins. Each predicate gets
# (event, change_type, field, new_value) -- field/new_value come from the
# event's evidence list and are None when not applicable (e.g. new_entity).
_RULES = [
    (
        lambda e, ct, field, new_value: "firewall" in e["source"].lower() and ct == "field_changed" and new_value == "False",
        "Re-enable Windows Firewall.",
        "high",
    ),
    (
        lambda e, ct, field, new_value: (
            "defender" in e["source"].lower()
            and field and "realtimeprotection" in field.lower()
            and new_value == "False"
        ),
        "Re-enable Windows Defender real-time protection and run a full scan.",
        "high",
    ),
    (
        lambda e, ct, field, new_value: "website" in e["source"].lower() and ct == "field_changed" and new_value == "False",
        "Check the website hosting provider / server status.",
        "high",
    ),
    (
        lambda e, ct, field, new_value: "device_inventory" in e["source"].lower() and ct == "new_entity",
        "Verify ownership of the new device before trusting it on the network.",
        "medium",
    ),
    (
        lambda e, ct, field, new_value: "device_inventory" in e["source"].lower() and ct == "removed_entity",
        "Confirm whether the missing device was intentionally powered off or removed.",
        "low",
    ),
]


def build_recommendation(event: dict) -> dict:
    """Return {"recommendation": str, "action_priority": str} for a single
    change event, without persisting it."""
    change_type = _change_type(event)
    field = _evidence_get(event.get("evidence"), "field")
    new_value = _evidence_get(event.get("evidence"), "new_value")

    for predicate, recommendation, action_priority in _RULES:
        if predicate(event, change_type, field, new_value):
            return {"recommendation": recommendation, "action_priority": action_priority}

    severity = event.get("severity", "low")
    return {
        "recommendation": _DEFAULT_BY_SEVERITY.get(severity, _DEFAULT_BY_SEVERITY["low"]),
        "action_priority": PRIORITY_BY_SEVERITY.get(severity, "low"),
    }


def recommend_and_store(event: dict, date: str = None) -> dict:
    """Build a recommendation for `event` and persist it to the Daily
    Brief Store. Returns the stored entry, or None if the store write
    failed (logged by daily_brief_store, not raised here)."""
    rec = build_recommendation(event)
    entry = {
        "source": event.get("source"),
        "title": event.get("title"),
        "severity": event.get("severity"),
        "recommendation": rec["recommendation"],
        "action_priority": rec["action_priority"],
    }
    result = add_recommendation(entry, date)
    return entry if result is not None else None
