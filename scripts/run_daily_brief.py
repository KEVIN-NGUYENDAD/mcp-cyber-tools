"""Automation Layer: Daily Brief Run (8PM).

Generates and logs the Daily Brief (JSON + text) via
daily_brief_generator.py. Saves the JSON brief to daily_brief/YYYY-MM-DD.json
and prints the text output. Read-only against the Daily Brief Store --
does not call reset_daily_brief(), so a failed or duplicate run never
loses today's data.
"""
import json
import os
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

        # Save JSON brief to daily_brief/YYYY-MM-DD.json
        today = datetime.now(timezone.utc).date().isoformat()
        daily_brief_dir = r"C:\GitHub\mcp-cyber-tools\daily_brief"
        os.makedirs(daily_brief_dir, exist_ok=True)

        brief_path = os.path.join(daily_brief_dir, f"{today}.json")
        with open(brief_path, "w", encoding="utf-8") as f:
            json.dump(brief["json"], f, indent=2)
        print(f"[{timestamp}] Saved brief to {brief_path}")
    except Exception:
        traceback.print_exc()
        return 1
    print(f"[{timestamp}] Daily Brief run finished")
    return 0


if __name__ == "__main__":
    sys.exit(run())
