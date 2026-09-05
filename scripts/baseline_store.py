"""Baseline Store for the SentinelOps Change Detection Engine (Phase A).

Persists the last-known snapshot per source/asset so a future Change
Detector (Phase B) can diff "previous" vs "current". This module only
stores and retrieves snapshot envelopes -- it does not diff, score, or
build events. Purely additive, same posture as Day 1's event_schema.py:
nothing else in the pipeline is touched.

Snapshot envelope:
    {
        "version": int,        # envelope schema version, bump on format change
        "source": str,         # e.g. "defender_status", "device_inventory"
        "asset_id": str,       # e.g. "desktop-primary"
        "captured_at": str,    # ISO 8601 UTC timestamp
        "state": dict,         # source-specific fields, opaque to this module
    }

Storage: one JSON file per source, under state\\, local only -- never
committed to the repo and never leaves this host (same rule as
alerts.json, which lives one directory up from state\\).
"""
import json
import os
from datetime import datetime, timezone

SNAPSHOT_VERSION = 1

# Sibling to security-watch.js's alerts.json -- local-only state, outside
# the git repo.
STATE_DIR = (
    r"C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\state"
)


def _path_for(source: str) -> str:
    return os.path.join(STATE_DIR, f"{source}.json")


def load_snapshot(source: str):
    """Return the last-known snapshot envelope for `source`, or None if no
    baseline exists yet (first run) or the file is missing/corrupt."""
    path = _path_for(source)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(
            f"Warning: could not read baseline for '{source}' ({exc}); "
            "treating as no baseline."
        )
        return None


def save_snapshot(source: str, asset_id: str, state: dict) -> dict:
    """Persist `state` as the new last-known snapshot for `source`/`asset_id`.

    Overwrites whatever load_snapshot(source) would have returned before
    this call. Atomic: writes to a temp file in the same directory, then
    renames into place, so a concurrent reader never sees a half-written
    file. On write failure, logs an error and returns None instead of
    raising -- a failed persist should not crash the caller's pipeline.
    """
    envelope = {
        "version": SNAPSHOT_VERSION,
        "source": source,
        "asset_id": asset_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
    }
    path = _path_for(source)
    tmp_path = path + ".tmp"
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        print(f"Error: could not write baseline for '{source}' ({exc}); continuing.")
        return None
    return envelope
