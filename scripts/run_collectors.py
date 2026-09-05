"""Automation Layer: Collector Run (every 15 minutes).

Runs every real collector, saves through baseline_store.py, and routes
any detected changes through change_detector.py (Risk Scoring ->
Recommendation Engine -> Critical?-branch -> GitHub Incident / Daily
Brief Store). One process, no new infrastructure -- scheduled the same
way security-watch.js already is, via Windows Task Scheduler. A single
collector failing (e.g. host offline, PowerShell error) is logged and
skipped; it does not stop the others.
"""
import socket
import sys
import traceback
from datetime import datetime, timezone

from change_detector import process_snapshot
from collect_defender_snapshot import collect_defender_status
from collect_defender_threats_snapshot import collect_defender_threats
from collect_device_inventory_snapshot import collect_device_inventory
from collect_firewall_snapshot import collect_firewall_status
from collect_website_snapshot import DEFAULT_HOST, collect_website_status

HOST_ASSET_ID = socket.gethostname()

COLLECTORS = [
    ("defender_status", HOST_ASSET_ID, collect_defender_status),
    ("defender_threats", HOST_ASSET_ID, collect_defender_threats),
    ("firewall_status", HOST_ASSET_ID, collect_firewall_status),
    ("device_inventory", HOST_ASSET_ID, collect_device_inventory),
    ("website_status", DEFAULT_HOST, lambda: collect_website_status(DEFAULT_HOST)),
]


def run() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] Collector run starting (host_asset_id={HOST_ASSET_ID})")
    exit_code = 0
    for source, asset_id, collect in COLLECTORS:
        try:
            state = collect()
            results = process_snapshot(source, asset_id, state)
            print(f"[{source}] snapshot saved, {len(results)} change event(s): {results}")
        except Exception:
            exit_code = 1
            print(f"[{source}] ERROR:")
            traceback.print_exc()
    print(f"[{timestamp}] Collector run finished (exit_code={exit_code})")
    return exit_code


if __name__ == "__main__":
    sys.exit(run())
