"""Daily Brief Generator for the SentinelOps Event Hub (Phase D).

Reads a day's Daily Brief Store (daily_brief_store.load_daily_brief())
and renders it into the two outputs the 8PM report needs: a JSON brief
and a plain-text brief. This module only reads and formats -- it does
not score, detect changes, or mutate the store (reset_daily_brief() is
a separate, explicit call the caller makes once the brief has been
delivered). Purely additive, same posture as the rest of the pipeline.

Brief sections (both JSON and text):
    Security Score      -- latest score_delta's "current" value, or None
    Today's Changes      -- the store's "changes" list (Event Hub events)
    Current Risk         -- highest severity across changes/incidents today
    Recommended Actions  -- the store's "recommendations" list
"""
from daily_brief_store import load_daily_brief

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _security_score(store: dict):
    deltas = store.get("score_deltas") or []
    if not deltas:
        return None
    return deltas[-1].get("current")


def _current_risk(store: dict) -> str:
    severities = [c.get("severity") for c in store.get("changes") or []]
    severities += [i.get("severity") for i in store.get("incidents") or [] if isinstance(i, dict)]
    ranked = [s for s in severities if s in SEVERITY_RANK]
    if not ranked:
        return "low"
    return max(ranked, key=lambda s: SEVERITY_RANK[s])


def build_daily_brief(date: str = None) -> dict:
    """Return the JSON brief for `date` (default: today, UTC)."""
    store = load_daily_brief(date)
    return {
        "date": store["date"],
        "security_score": _security_score(store),
        "todays_changes": store.get("changes") or [],
        "current_risk": _current_risk(store),
        "recommended_actions": store.get("recommendations") or [],
    }


def render_text_brief(brief: dict) -> str:
    """Render a JSON brief (from build_daily_brief()) as plain text."""
    lines = [f"SentinelOps Daily Brief -- {brief['date']}", ""]

    lines.append("Security Score")
    score = brief["security_score"]
    lines.append(f"  {score if score is not None else 'N/A'}")
    lines.append("")

    lines.append("Today's Changes")
    changes = brief["todays_changes"]
    if changes:
        for event in changes:
            severity = str(event.get("severity", "unknown")).upper()
            lines.append(f"  - [{severity}] {event.get('title', '(untitled)')} -- {event.get('summary', '')}")
    else:
        lines.append("  No changes detected today.")
    lines.append("")

    lines.append("Current Risk")
    lines.append(f"  {brief['current_risk'].upper()}")
    lines.append("")

    lines.append("Recommended Actions")
    recommendations = brief["recommended_actions"]
    if recommendations:
        for rec in recommendations:
            text = rec.get("text") if isinstance(rec, dict) else str(rec)
            lines.append(f"  - {text}")
    else:
        lines.append("  No recommendations at this time.")

    return "\n".join(lines) + "\n"


def generate_daily_brief(date: str = None) -> dict:
    """Return {"json": <dict>, "text": <str>} -- the two Phase D outputs."""
    brief = build_daily_brief(date)
    return {"json": brief, "text": render_text_brief(brief)}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Daily Brief Generator CLI (for the MCP Interface, Phase E).")
    parser.add_argument("--date", default=None)
    parser.add_argument("--score-only", action="store_true", help="Print only the security score.")
    args = parser.parse_args()

    if args.score_only:
        print(json.dumps(build_daily_brief(args.date)["security_score"]))
    else:
        print(json.dumps(generate_daily_brief(args.date)))
