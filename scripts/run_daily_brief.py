"""Automation Layer: Daily Brief Run (3:00 PM).

Generates and logs the Daily Brief (JSON + text + HTML) via
daily_brief_generator.py. Saves JSON to daily_brief/YYYY-MM-DD.json and
HTML to daily_brief/YYYY-MM-DD.html and latest.html, sends Telegram with
web link to https://sentinelops-soc.onrender.com/.
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

        # Determine web URL (production or local)
        # Production: https://sentinelops-soc.onrender.com/
        # Local: http://localhost:3000/
        env_mode = os.getenv("ENV", "local").lower()
        if env_mode == "production":
            web_url = "https://sentinelops-soc.onrender.com/"
        else:
            web_url = "http://localhost:3000/"

        # Send via Telegram with web link
        print("[BRIEF] Sending via Telegram...")
        telegram_ok = send_daily_brief_telegram(today, web_url=web_url)
        if telegram_ok:
            print("[BRIEF] Telegram delivery successful")
            print(f"[BRIEF] View brief online: {web_url}")
        else:
            print("[ERROR] Telegram delivery failed")

        # Note: Email delivery removed - using web-based delivery instead
        print(f"[BRIEF] Daily Brief available at: {web_url}latest")
        print(f"[BRIEF] Daily Brief run finished at {timestamp}")
        return 0 if telegram_ok else 1

    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run())
