"""Automation Layer: Daily Brief Run (8PM).

Generates and logs the Daily Brief (JSON + text) via
daily_brief_generator.py. Read-only against the Daily Brief Store --
does not call reset_daily_brief(), so a failed or duplicate run never
loses today's data.
"""
import sys
import traceback
from datetime import datetime, timezone

from daily_brief_generator import generate_daily_brief


def run() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] Daily Brief run starting")
    try:
        brief = generate_daily_brief()
        print(brief["text"])
    except Exception:
        traceback.print_exc()
        return 1
    print(f"[{timestamp}] Daily Brief run finished")
    return 0


if __name__ == "__main__":
    sys.exit(run())
