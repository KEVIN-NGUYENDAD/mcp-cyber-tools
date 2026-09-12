"""Automation Layer: Daily Brief Run (3:00 PM).

Generates and logs the Daily Brief (JSON + text) via
daily_brief_generator.py. Saves the JSON brief to daily_brief/YYYY-MM-DD.json,
prints the text output, and sends via Telegram + Email.
Read-only against the Daily Brief Store -- does not call reset_daily_brief(),
so a failed or duplicate run never loses today's data.
"""
import json
import os
import sys
import traceback
from datetime import datetime, timezone

from daily_brief_generator import generate_daily_brief
from send_daily_brief_telegram import send_daily_brief_telegram
from send_daily_brief_email import send_daily_brief_email


def run() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[BRIEF] Daily Brief run starting at {timestamp}")
    try:
        brief = generate_daily_brief()
        print("[BRIEF] Generated daily brief")
        print(brief["text"])

        # Save JSON brief to daily_brief/YYYY-MM-DD.json
        today = datetime.now(timezone.utc).date().isoformat()
        daily_brief_dir = r"C:\GitHub\mcp-cyber-tools\daily_brief"
        os.makedirs(daily_brief_dir, exist_ok=True)

        brief_path = os.path.join(daily_brief_dir, f"{today}.json")
        with open(brief_path, "w", encoding="utf-8") as f:
            json.dump(brief["json"], f, indent=2)
        print(f"[BRIEF] Saved to {brief_path}")

        # Send via Telegram
        print("[BRIEF] Sending via Telegram...")
        telegram_ok = send_daily_brief_telegram(today)
        if telegram_ok:
            print("[BRIEF] Telegram delivery successful")
        else:
            print("[ERROR] Telegram delivery failed")

        # Send via Email
        print("[BRIEF] Sending via Email...")
        email_ok = send_daily_brief_email(today)
        if email_ok:
            print("[BRIEF] Email delivery successful")
        else:
            print("[ERROR] Email delivery failed")

        # Overall status
        if telegram_ok or email_ok:
            print(f"[BRIEF] Daily Brief run finished at {timestamp}")
            return 0
        else:
            print(f"[ERROR] All delivery methods failed")
            return 1

    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run())
