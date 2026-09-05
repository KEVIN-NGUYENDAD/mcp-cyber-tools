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
"""
from event_schema import make_event

# Provisional severities for Risk Scoring (a later stage, reusing
# score_alert()) to refine -- these are just enough to satisfy the Event
# Schema's required "severity" field.
SEVERITY_BY_CHANGE_TYPE = {
    "new_entity": "medium",
    "removed_entity": "medium",
    "field_toggled": "high",
    "value_changed": "low",
}


def _is_entity_map(state: dict) -> bool:
    return bool(state) and all(isinstance(v, dict) for v in state.values())


def _evidence_from_fields(fields: dict) -> list:
    return [{"key": str(k), "value": str(v)} for k, v in fields.items()]


def _new_entity_event(source: str, entity_id: str, fields: dict) -> dict:
    return make_event(
        source=source,
        severity=SEVERITY_BY_CHANGE_TYPE["new_entity"],
        title=f"New entity detected: {entity_id}",
        summary=f"{source}: a new entity '{entity_id}' was not present in the previous baseline.",
        evidence=[{"key": "entity_id", "value": str(entity_id)}] + _evidence_from_fields(fields),
    )


def _removed_entity_event(source: str, entity_id: str, fields: dict) -> dict:
    return make_event(
        source=source,
        severity=SEVERITY_BY_CHANGE_TYPE["removed_entity"],
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
        severity=SEVERITY_BY_CHANGE_TYPE[change_type],
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
