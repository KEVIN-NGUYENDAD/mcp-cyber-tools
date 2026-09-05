"""Daily Brief Store for the SentinelOps Event Hub (Phase C).

Accumulates the non-critical output of a day's Change Detector runs --
changes, incidents, recommendations, score deltas -- so the Daily Brief
Generator (Phase D) has something to read at 8PM. This module only
appends to and reads/reset a local JSON store; it does not decide what
is critical, score anything, or generate the brief itself. Purely
additive, same posture as baseline_store.py: nothing else in the
pipeline is touched.

Daily store shape (one JSON file per calendar date):
    {
        "date": str,               # "YYYY-MM-DD"
        "changes": list,           # Event Hub events (event_schema.make_event())
        "incidents": list,         # entries describing incidents opened that day
        "recommendations": list,  # AI-generated recommendation entries
        "score_deltas": list,      # risk-score-change entries
    }

Storage: one JSON file per date, under daily_brief\\, local only --
never committed to the repo and never leaves this host (same rule as
alerts.json and baseline_store.py's state\\).
"""
import json
import os
from datetime import datetime, timezone

# Sibling to baseline_store.py's state\\ and security-watch.js's
# alerts.json -- local-only state, outside the git repo.
DAILY_BRIEF_DIR = (
    r"C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\daily_brief"
)

CATEGORIES = ("changes", "incidents", "recommendations", "score_deltas")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _path_for(date: str) -> str:
    return os.path.join(DAILY_BRIEF_DIR, f"{date}.json")


def _empty_store(date: str) -> dict:
    return {"date": date, "changes": [], "incidents": [], "recommendations": [], "score_deltas": []}


def load_daily_brief(date: str = None) -> dict:
    """Return the store for `date` (default: today, UTC), or an empty
    store if none exists yet (first entry of the day) or the file is
    missing/corrupt."""
    date = date or _today()
    path = _path_for(date)
    if not os.path.exists(path):
        return _empty_store(date)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(
            f"Warning: could not read daily brief store for '{date}' ({exc}); "
            "treating as empty."
        )
        return _empty_store(date)


def _save_daily_brief(store: dict) -> dict:
    """Atomic write: temp file in the same directory, then rename into
    place. On write failure, logs an error and returns None instead of
    raising -- a failed persist should not crash the caller's pipeline."""
    path = _path_for(store["date"])
    tmp_path = path + ".tmp"
    try:
        os.makedirs(DAILY_BRIEF_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        print(f"Error: could not write daily brief store for '{store['date']}' ({exc}); continuing.")
        return None
    return store


def _append(category: str, entry: dict, date: str = None) -> dict:
    date = date or _today()
    store = load_daily_brief(date)
    store[category].append(entry)
    return _save_daily_brief(store)


def add_change(event: dict, date: str = None) -> dict:
    return _append("changes", event, date)


def add_incident(incident: dict, date: str = None) -> dict:
    return _append("incidents", incident, date)


def add_recommendation(recommendation: dict, date: str = None) -> dict:
    return _append("recommendations", recommendation, date)


def add_score_delta(score_delta: dict, date: str = None) -> dict:
    return _append("score_deltas", score_delta, date)


def reset_daily_brief(date: str = None) -> dict:
    """Overwrite `date`'s store with an empty one -- called after the
    Daily Brief Generator (Phase D) has consumed a day's store, so the
    next day starts clean."""
    date = date or _today()
    return _save_daily_brief(_empty_store(date))


def recent_incidents(days: int = 7) -> list:
    """Return the concatenated "incidents" lists from the last `days`
    calendar dates (today back `days - 1` days), oldest first."""
    from datetime import timedelta

    today = datetime.now(timezone.utc).date()
    incidents = []
    for offset in range(days - 1, -1, -1):
        date = (today - timedelta(days=offset)).isoformat()
        incidents.extend(load_daily_brief(date).get("incidents") or [])
    return incidents


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daily Brief Store CLI (for the MCP Interface, Phase E).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="Print a date's daily brief store.")
    load_parser.add_argument("--date", default=None)

    incidents_parser = subparsers.add_parser("recent-incidents", help="Print incidents from the last N days.")
    incidents_parser.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    if args.command == "load":
        print(json.dumps(load_daily_brief(args.date)))
    elif args.command == "recent-incidents":
        print(json.dumps(recent_incidents(args.days)))
