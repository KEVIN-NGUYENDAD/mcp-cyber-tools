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


def generate_html_brief(brief: dict, date: str = None) -> str:
    """Generate HTML version of brief for web display"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>SentinelOps Daily Brief - {}</title>".format(date),
        "  <style>",
        "    * { margin: 0; padding: 0; box-sizing: border-box; }",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }",
        "    .container { max-width: 900px; margin: 0 auto; padding: 20px; }",
        "    .header { background: linear-gradient(135deg, #1f2937 0%, #111827 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
        "    .header h1 { font-size: 28px; margin-bottom: 5px; }",
        "    .header p { font-size: 14px; opacity: 0.9; }",
        "    .section { background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }",
        "    .section h2 { font-size: 18px; color: #1f2937; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }",
        "    .score-display { font-size: 48px; font-weight: bold; color: #3b82f6; text-align: center; padding: 20px; }",
        "    .score-display.high { color: #dc2626; }",
        "    .score-display.medium { color: #f59e0b; }",
        "    .risk-level { font-size: 32px; text-align: center; padding: 20px; }",
        "    .risk-level.critical { color: #dc2626; }",
        "    .risk-level.high { color: #ea580c; }",
        "    .risk-level.medium { color: #f59e0b; }",
        "    .risk-level.low { color: #10b981; }",
        "    .item { padding: 12px; margin: 10px 0; background: #f9fafb; border-left: 4px solid #3b82f6; border-radius: 4px; }",
        "    .item.critical { border-left-color: #dc2626; background: #fef2f2; }",
        "    .item.high { border-left-color: #ea580c; background: #fff7ed; }",
        "    .item.medium { border-left-color: #f59e0b; background: #fffbeb; }",
        "    .item.low { border-left-color: #10b981; background: #f0fdf4; }",
        "    .severity { font-weight: bold; text-transform: uppercase; font-size: 12px; }",
        "    .severity.critical { color: #dc2626; }",
        "    .severity.high { color: #ea580c; }",
        "    .severity.medium { color: #f59e0b; }",
        "    .severity.low { color: #10b981; }",
        "    .empty { color: #9ca3af; font-style: italic; }",
        "    .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; }",
        "    @media (prefers-color-scheme: dark) {",
        "      body { background: #1f2937; color: #f3f4f6; }",
        "      .section { background: #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }",
        "      .section h2 { color: #f3f4f6; border-bottom-color: #4b5563; }",
        "      .item { background: #4b5563; }",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='container'>",
        "    <div class='header'>",
        "      <h1>📊 SentinelOps Daily Brief</h1>",
        "      <p>{}</p>".format(date),
        "    </div>",
    ]

    # Security Score
    html_lines.append("    <div class='section'>")
    html_lines.append("      <h2>Security Score</h2>")
    score = brief.get("security_score")
    if score is not None:
        score_class = "high" if score > 70 else "medium" if score > 40 else ""
        html_lines.append("      <div class='score-display {}'>{}/100</div>".format(score_class, score))
    else:
        html_lines.append("      <div class='score-display'>N/A</div>")
    html_lines.append("    </div>")

    # Today's Changes
    html_lines.append("    <div class='section'>")
    html_lines.append("      <h2>Today's Changes</h2>")
    changes = brief.get("todays_changes", [])
    if changes:
        for event in changes:
            severity = event.get("severity", "unknown").lower()
            title = event.get("title", "(untitled)")
            summary = event.get("summary", "")
            item_class = f"item {severity}"
            severity_class = f"severity {severity}"
            html_lines.append(f"      <div class='{item_class}'>")
            html_lines.append(f"        <span class='{severity_class}'>[{severity.upper()}]</span> {title}")
            if summary:
                html_lines.append(f"        <br><small>{summary}</small>")
            html_lines.append("      </div>")
    else:
        html_lines.append("      <div class='empty'>No changes detected today.</div>")
    html_lines.append("    </div>")

    # Current Risk
    html_lines.append("    <div class='section'>")
    html_lines.append("      <h2>Current Risk Level</h2>")
    risk = brief.get("current_risk", "unknown").lower()
    risk_emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    emoji = risk_emojis.get(risk, "⚪")
    risk_class = f"risk-level {risk}"
    html_lines.append(f"      <div class='{risk_class}'>{emoji} {risk.upper()}</div>")
    html_lines.append("    </div>")

    # Recommended Actions
    html_lines.append("    <div class='section'>")
    html_lines.append("      <h2>Recommended Actions</h2>")
    recommendations = brief.get("recommended_actions", [])
    if recommendations:
        for rec in recommendations:
            if isinstance(rec, dict):
                text = rec.get("recommendation") or rec.get("text") or "(no text)"
                priority = rec.get("action_priority", "").lower()
                html_lines.append(f"      <div class='item'><strong>[{priority.upper()}]</strong> {text}</div>")
            else:
                html_lines.append(f"      <div class='item'>{str(rec)}</div>")
    else:
        html_lines.append("      <div class='empty'>No recommendations at this time.</div>")
    html_lines.append("    </div>")

    # Footer
    html_lines.append("    <div class='footer'>")
    html_lines.append("      <p>SentinelOps Automated Daily Brief System</p>")
    html_lines.append("      <p style='margin-top: 5px; font-size: 11px;'>Generated at {} UTC</p>".format(datetime.now(timezone.utc).isoformat()))
    html_lines.append("    </div>")
    html_lines.append("  </div>")
    html_lines.append("</body>")
    html_lines.append("</html>")

    return "\n".join(html_lines)


def save_html_brief(brief: dict, date: str = None) -> bool:
    """Save HTML brief to daily_brief/YYYY-MM-DD.html and latest.html"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    html_content = generate_html_brief(brief, date)
    daily_brief_dir = Path(r"C:\GitHub\mcp-cyber-tools\daily_brief")

    try:
        # Save dated HTML
        dated_html_path = daily_brief_dir / f"{date}.html"
        with open(dated_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[BRIEF] Saved HTML to {dated_html_path}")

        # Save latest.html
        latest_html_path = daily_brief_dir / "latest.html"
        with open(latest_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[BRIEF] Updated latest.html")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to save HTML: {e}")
        return False


def send_daily_brief_telegram(date: str = None, web_url: str = None) -> bool:
    """Send Daily Brief via Telegram with link to web version"""
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

    # Save HTML version
    save_html_brief(brief, date)

    # Format and send with web link
    message = format_brief_message(brief, date)
    if web_url:
        message += f"\n\n<a href='{web_url}'>View full brief online →</a>"

    return send_via_telegram(message, bot_token, chat_id)


if __name__ == "__main__":
    import sys

    date = sys.argv[1] if len(sys.argv) > 1 else None
    success = send_daily_brief_telegram(date)
    sys.exit(0 if success else 1)
