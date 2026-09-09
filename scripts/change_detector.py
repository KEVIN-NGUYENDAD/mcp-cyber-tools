"""Change Detector for the SentinelOps Change Detection Engine (Phase B).

Diffs a previous baseline snapshot (from baseline_store.load_snapshot())
against a current snapshot (from baseline_store.save_snapshot()) and
emits Event Hub compatible events (event_schema.make_event()) for what
changed. This module only detects and describes changes -- it does not
score, correlate, or persist anything. Purely additive: nothing in
event_schema.py or baseline_store.py is touched.

Snapshot "state" shapes this module understands:
    Flat fields (e.g. defender_status):
        {"AntivirusEnabled": true, "RealTimeProtectionEnabled": true, ...}
    Entity map (e.g. device_inventory):
        {"192.168.1.5": {"hostname": "desktop", "vendor": "Dell"}, ...}

Change types:
    new_entity      -- a key present in current's entity map but not previous's
    removed_entity  -- a key present in previous's entity map but not current's
    field_toggled   -- a field whose value is bool in both snapshots and differs
    value_changed   -- any other field whose value differs between snapshots

First run (no previous snapshot yet) produces no events: there is
nothing to diff against, so the current snapshot is just the new
baseline, not a change.

Wiring (Phase: pipeline completion): process_snapshot() ties this
together end to end -- Snapshot -> Baseline Store -> Change Detector ->
Risk Scoring -> Critical?-branch -> GitHub Incident / Daily Brief
Store -- reusing score_alert()/build_issue()/create_issue()/
assign_issue() unchanged from create_test_incident.py, the same
primitives create_securitywatch_incident.py and
create_defender_incident.py already reuse for their own alert sources.
"""
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for Alert Engine
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_alert_engine

from baseline_store import load_snapshot, save_snapshot
from create_test_incident import ASSIGNEE, assign_issue, build_issue, create_issue, score_alert
from daily_brief_store import add_change, add_incident
from event_schema import make_event
from recommendation_engine import recommend_and_store

# Provisional severities for Risk Scoring (a later stage, reusing
# score_alert()) to refine -- these are just enough to satisfy the Event
# Schema's required "severity" field.
SEVERITY_BY_CHANGE_TYPE = {
    "new_entity": "medium",
    "removed_entity": "medium",
    "field_toggled": "high",
    "value_changed": "low",
}

# Source-specific severity escalation (GitHub Incident Auto Routing sprint):
# overrides SEVERITY_BY_CHANGE_TYPE's generic default for named high-impact
# scenarios. (source substring, change_type) -> severity; first match wins.
SEVERITY_OVERRIDES = {
    ("defender_threats", "new_entity"): "critical",  # Malware Detected
    ("device_inventory", "new_entity"): "high",      # Unknown Device
}


def _severity_for(source: str, change_type: str) -> str:
    for (substr, ct), severity in SEVERITY_OVERRIDES.items():
        if ct == change_type and substr in source.lower():
            return severity
    return SEVERITY_BY_CHANGE_TYPE[change_type]


def _is_entity_map(state: dict) -> bool:
    return bool(state) and all(isinstance(v, dict) for v in state.values())


def _evidence_from_fields(fields: dict) -> list:
    return [{"key": str(k), "value": str(v)} for k, v in fields.items()]


def _new_entity_event(source: str, entity_id: str, fields: dict) -> dict:
    return make_event(
        source=source,
        severity=_severity_for(source, "new_entity"),
        title=f"New entity detected: {entity_id}",
        summary=f"{source}: a new entity '{entity_id}' was not present in the previous baseline.",
        evidence=[{"key": "entity_id", "value": str(entity_id)}] + _evidence_from_fields(fields),
    )


def _removed_entity_event(source: str, entity_id: str, fields: dict) -> dict:
    return make_event(
        source=source,
        severity=_severity_for(source, "removed_entity"),
        title=f"Entity disappeared: {entity_id}",
        summary=f"{source}: entity '{entity_id}' was present in the previous baseline but is now missing.",
        evidence=[{"key": "entity_id", "value": str(entity_id)}] + _evidence_from_fields(fields),
    )


def _field_change_event(source: str, entity_id, field: str, old_value, new_value) -> dict:
    change_type = (
        "field_toggled"
        if isinstance(old_value, bool) and isinstance(new_value, bool)
        else "value_changed"
    )
    label = f"{entity_id}.{field}" if entity_id is not None else field
    evidence = [
        {"key": "field", "value": str(field)},
        {"key": "old_value", "value": str(old_value)},
        {"key": "new_value", "value": str(new_value)},
    ]
    if entity_id is not None:
        evidence.insert(0, {"key": "entity_id", "value": str(entity_id)})
    return make_event(
        source=source,
        severity=_severity_for(source, change_type),
        title=f"{label} changed",
        summary=f"{source}: '{label}' changed from {old_value!r} to {new_value!r}.",
        evidence=evidence,
    )


def _diff_fields(source: str, entity_id, previous_fields: dict, current_fields: dict) -> list:
    previous_fields = previous_fields or {}
    current_fields = current_fields or {}
    events = []
    for field in sorted(set(previous_fields) | set(current_fields)):
        old_value = previous_fields.get(field)
        new_value = current_fields.get(field)
        if old_value == new_value:
            continue
        events.append(_field_change_event(source, entity_id, field, old_value, new_value))
    return events


def _diff_entities(source: str, previous_state: dict, current_state: dict) -> list:
    events = []
    for entity_id, fields in current_state.items():
        if entity_id not in previous_state:
            events.append(_new_entity_event(source, entity_id, fields))
        else:
            events.extend(_diff_fields(source, entity_id, previous_state[entity_id], fields))
    for entity_id, fields in previous_state.items():
        if entity_id not in current_state:
            events.append(_removed_entity_event(source, entity_id, fields))
    return events


def detect_changes(previous_snapshot, current_snapshot: dict) -> list:
    """Diff two baseline_store snapshot envelopes and return a list of
    Event Hub compatible events describing what changed.

    `previous_snapshot` is whatever baseline_store.load_snapshot(source)
    returned (None on first run -- returns [] in that case).
    `current_snapshot` is the envelope just produced by
    baseline_store.save_snapshot(source, asset_id, state).
    """
    if previous_snapshot is None:
        return []

    source = current_snapshot["source"]
    current_state = current_snapshot.get("state") or {}
    previous_state = previous_snapshot.get("state") or {}

    if _is_entity_map(current_state) or _is_entity_map(previous_state):
        return _diff_entities(source, previous_state, current_state)
    return _diff_fields(source, None, previous_state, current_state)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "change"


def _event_to_alert(event: dict) -> dict:
    """Adapt a Change Detector event (Event Hub schema: source/severity/
    title/summary/evidence) into the alert shape score_alert()/
    build_issue() expect (source/event_type/severity/ip/threat_signature/
    process/file/detection_time) -- the same shape every other alert
    source in this pipeline already normalizes into."""
    return {
        "source": event["source"],
        "event_type": _slugify(event["title"]),
        "severity": event["severity"],
        "ip": "unknown",
        "threat_signature": event["summary"],
        "process": None,
        "file": None,
        "detection_time": datetime.now(timezone.utc).isoformat(),
    }


def route_change_event(event: dict) -> dict:
    """Score a change event and route it.

    critical/high -> open a GitHub Incident, reusing build_issue()/
    create_issue()/assign_issue()/score_alert() unchanged. If
    GITHUB_TOKEN isn't set, logs a warning and falls back to the Daily
    Brief Store instead of raising -- a missing token shouldn't crash
    the caller's pipeline.

    everything else -> Daily Brief Store (daily_brief_store.add_change()).
    """
    risk_score = score_alert(event)
    recommend_and_store(event)

    if event["severity"] in ("critical", "high"):
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            alert = _event_to_alert(event)
            timestamp = alert["detection_time"]
            issue_fields = build_issue(alert, risk_score, timestamp)
            issue = create_issue(token, issue_fields["title"], issue_fields["body"])
            assign_issue(token, issue["number"], ASSIGNEE)
            add_incident({
                "title": event["title"],
                "severity": event["severity"],
                "risk_score": risk_score,
                "issue_url": issue["html_url"],
                "detected_at": timestamp,
            })
            return {"routed_to": "github_incident", "risk_score": risk_score, "issue_url": issue["html_url"]}
        print(
            f"Warning: GITHUB_TOKEN not set; skipping GitHub incident for "
            f"'{event['title']}' ({event['severity']}); routing to Daily Brief Store instead."
        )

    add_change(event)
    return {"routed_to": "daily_brief_store", "risk_score": risk_score}


def send_alerts_for_events(events: list) -> int:
    """Send alerts to Alert Engine for detected changes.

    Args:
        events: List of change events from detect_changes()

    Returns:
        Number of alerts sent
    """
    if not events:
        return 0

    try:
        engine = get_alert_engine()
        alerts_sent = 0

        for event in events:
            try:
                # Event already has compatible format from _new_entity_event, etc.
                alert = engine.create_alert(event)
                success, routing_result = engine.route_alert(alert)

                if success:
                    alerts_sent += 1
                # Failed alerts are logged by route_alert

            except Exception as e:
                pass  # Non-blocking: one failed alert doesn't stop others

        return alerts_sent

    except Exception as e:
        pass  # Non-blocking: Alert Engine unavailable


def process_snapshot(source: str, asset_id: str, state: dict) -> list:
    """Full pipeline wiring: Snapshot -> Baseline Store -> Change Detector
    -> Risk Scoring -> Critical?-branch -> GitHub Incident / Daily Brief
    Store -> Alert Engine for Telegram. Returns one route_change_event() result
    per detected change (empty on a source's first run -- nothing to diff against yet)."""
    previous = load_snapshot(source)
    current = save_snapshot(source, asset_id, state)
    events = detect_changes(previous, current)

    # Send alerts for detected changes (non-blocking)
    if events:
        send_alerts_for_events(events)

    return [route_change_event(event) for event in events]
