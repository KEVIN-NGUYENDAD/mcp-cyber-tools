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
from daily_brief_store import load_daily_brief, recent_incidents

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
            if isinstance(rec, dict):
                text = rec.get("recommendation") or rec.get("text") or "(no recommendation text)"
                priority = rec.get("action_priority")
                text = f"[{str(priority).upper()}] {text}" if priority else text
            else:
                text = str(rec)
            lines.append(f"  - {text}")
    else:
        lines.append("  No recommendations at this time.")

    return "\n".join(lines) + "\n"


def generate_daily_brief(date: str = None) -> dict:
    """Return {"json": <dict>, "text": <str>} -- the two Phase D outputs."""
    brief = build_daily_brief(date)
    return {"json": brief, "text": render_text_brief(brief)}


def render_incidents_text(incidents: list) -> str:
    """Render a recent_incidents() list as a short, iPhone/iPad-readable
    answer to "what incidents are active?"."""
    if not incidents:
        return "No active incidents.\n"
    lines = ["Active Incidents", ""]
    for inc in incidents:
        severity = str(inc.get("severity", "unknown")).upper()
        title = inc.get("title", "(untitled)")
        line = f"  - [{severity}] {title}"
        if inc.get("issue_url"):
            line += f" -- {inc['issue_url']}"
        lines.append(line)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Daily Brief Generator CLI (for the MCP Interface, Phase E).")
    parser.add_argument("--date", default=None)
    parser.add_argument("--score-only", action="store_true", help="Print only the security score.")
    parser.add_argument("--incidents", action="store_true", help="Print recent incidents instead of the daily brief.")
    parser.add_argument("--days", type=int, default=7, help="Window size (days) for --incidents.")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format for the daily brief or --incidents (default: text, optimized for Claude iPhone/iPad).",
    )
    args = parser.parse_args()

    if args.score_only:
        print(json.dumps(build_daily_brief(args.date)["security_score"]))
    elif args.incidents:
        incidents = recent_incidents(args.days)
        if args.format == "json":
            print(json.dumps(incidents))
        else:
            print(render_incidents_text(incidents))
    else:
        brief = generate_daily_brief(args.date)
        if args.format == "json":
            print(json.dumps(brief))
        else:
            print(brief["text"])
