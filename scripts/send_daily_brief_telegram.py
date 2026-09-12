#!/usr/bin/env python3
"""Send Daily Brief via Telegram Bot API."""
import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path


def load_credentials():
    """Load TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from .env"""
    env_file = Path(r"C:\GitHub\mcp-cyber-tools\.env")
    bot_token = None
    chat_id = None

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    bot_token = line.split('=', 1)[1]
                elif line.startswith('TELEGRAM_CHAT_ID='):
                    chat_id = line.split('=', 1)[1]
    except FileNotFoundError:
        print(f"[ERROR] .env file not found: {env_file}")
        return None, None

    if not bot_token or not chat_id:
        print("[ERROR] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env")
        return None, None

    return bot_token, chat_id


def load_daily_brief(date: str = None) -> dict:
    """Load brief JSON from daily_brief/YYYY-MM-DD.json"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    brief_path = Path(r"C:\GitHub\mcp-cyber-tools\daily_brief") / f"{date}.json"

    try:
        with open(brief_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Brief file not found: {brief_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {brief_path}: {e}")
        return None


def format_brief_message(brief: dict, date: str = None) -> str:
    """Format brief as Telegram message"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    lines = [
        "📊 <b>SENTINELOPS DAILY BRIEF</b>",
        f"<i>{date}</i>",
        "",
    ]

    # Security Score
    lines.append("<b>Security Score:</b>")
    score = brief.get("security_score")
    if score is not None:
        lines.append(f"  {score}/100")
    else:
        lines.append("  N/A")
    lines.append("")

    # Today's Changes
    lines.append("<b>Today's Changes:</b>")
    changes = brief.get("todays_changes", [])
    if changes:
        for event in changes:
            severity = event.get("severity", "unknown").upper()
            title = event.get("title", "(untitled)")
            summary = event.get("summary", "")
            lines.append(f"  • [{severity}] {title}")
            if summary:
                lines.append(f"    {summary}")
    else:
        lines.append("  No changes detected today.")
    lines.append("")

    # Current Risk
    lines.append("<b>Current Risk:</b>")
    risk = brief.get("current_risk", "unknown").upper()
    if risk == "CRITICAL":
        lines.append(f"  🔴 {risk}")
    elif risk == "HIGH":
        lines.append(f"  🟠 {risk}")
    elif risk == "MEDIUM":
        lines.append(f"  🟡 {risk}")
    else:
        lines.append(f"  🟢 {risk}")
    lines.append("")

    # Recommended Actions
    lines.append("<b>Recommended Actions:</b>")
    recommendations = brief.get("recommended_actions", [])
    if recommendations:
        for rec in recommendations:
            if isinstance(rec, dict):
                text = rec.get("recommendation") or rec.get("text") or "(no text)"
                priority = rec.get("action_priority")
                if priority:
                    lines.append(f"  • [{priority.upper()}] {text}")
                else:
                    lines.append(f"  • {text}")
            else:
                lines.append(f"  • {str(rec)}")
    else:
        lines.append("  No recommendations at this time.")

    return "\n".join(lines)


def send_via_telegram(message: str, bot_token: str, chat_id: str) -> bool:
    """Send message to Telegram"""
    api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get('ok'):
            message_id = data.get('result', {}).get('message_id')
            print(f"[BRIEF] Telegram sent successfully (message_id: {message_id})")
            return True
        else:
            error_msg = data.get('description', 'Unknown error')
            print(f"[ERROR] Telegram API error: {error_msg}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")
        return False


def send_daily_brief_telegram(date: str = None) -> bool:
    """Send Daily Brief via Telegram"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    print(f"[BRIEF] Sending Telegram: {date}")

    # Load credentials
    bot_token, chat_id = load_credentials()
    if not bot_token or not chat_id:
        return False

    # Load brief
    brief = load_daily_brief(date)
    if not brief:
        return False

    # Format and send
    message = format_brief_message(brief, date)
    return send_via_telegram(message, bot_token, chat_id)


if __name__ == "__main__":
    import sys

    date = sys.argv[1] if len(sys.argv) > 1 else None
    success = send_daily_brief_telegram(date)
    sys.exit(0 if success else 1)
