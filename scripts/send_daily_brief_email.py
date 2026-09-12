#!/usr/bin/env python3
"""Send Daily Brief via Email using SMTP."""
import json
import smtplib
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


def format_brief_html(brief: dict, date: str = None) -> str:
    """Format brief as HTML email"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<style>",
        "  body { font-family: Arial, sans-serif; color: #333; line-height: 1.6; }",
        "  .container { max-width: 600px; margin: 0 auto; padding: 20px; }",
        "  .header { background: #1f2937; color: white; padding: 15px; border-radius: 5px; }",
        "  .section { margin: 20px 0; padding: 15px; background: #f9fafb; border-left: 4px solid #3b82f6; }",
        "  .section h3 { margin-top: 0; color: #1f2937; }",
        "  .score { font-size: 24px; font-weight: bold; }",
        "  .critical { color: #dc2626; }",
        "  .high { color: #ea580c; }",
        "  .medium { color: #f59e0b; }",
        "  .low { color: #10b981; }",
        "  .item { margin: 10px 0; padding-left: 10px; }",
        "  .footer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; color: #666; font-size: 12px; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='container'>",
        f"<div class='header'>",
        f"  <h2>📊 SentinelOps Daily Brief</h2>",
        f"  <p>{date}</p>",
        f"</div>",
    ]

    # Security Score
    html_lines.append("<div class='section'>")
    html_lines.append("<h3>Security Score</h3>")
    score = brief.get("security_score")
    if score is not None:
        html_lines.append(f"<div class='score'>{score}/100</div>")
    else:
        html_lines.append("<div class='score'>N/A</div>")
    html_lines.append("</div>")

    # Today's Changes
    html_lines.append("<div class='section'>")
    html_lines.append("<h3>Today's Changes</h3>")
    changes = brief.get("todays_changes", [])
    if changes:
        for event in changes:
            severity = event.get("severity", "unknown").lower()
            title = event.get("title", "(untitled)")
            summary = event.get("summary", "")
            severity_class = f"class='{severity}'"
            html_lines.append(f"<div class='item'><span {severity_class}>[{severity.upper()}]</span> {title}")
            if summary:
                html_lines.append(f"<br><small>{summary}</small>")
            html_lines.append("</div>")
    else:
        html_lines.append("<div class='item'>No changes detected today.</div>")
    html_lines.append("</div>")

    # Current Risk
    html_lines.append("<div class='section'>")
    html_lines.append("<h3>Current Risk Level</h3>")
    risk = brief.get("current_risk", "unknown").lower()
    risk_emojis = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    emoji = risk_emojis.get(risk, "⚪")
    risk_class = f"class='{risk}'" if risk in risk_emojis else ""
    html_lines.append(f"<div class='item'><span {risk_class}>{emoji} {risk.upper()}</span></div>")
    html_lines.append("</div>")

    # Recommended Actions
    html_lines.append("<div class='section'>")
    html_lines.append("<h3>Recommended Actions</h3>")
    recommendations = brief.get("recommended_actions", [])
    if recommendations:
        for rec in recommendations:
            if isinstance(rec, dict):
                text = rec.get("recommendation") or rec.get("text") or "(no text)"
                priority = rec.get("action_priority", "").upper()
                if priority:
                    html_lines.append(f"<div class='item'><strong>[{priority}]</strong> {text}</div>")
                else:
                    html_lines.append(f"<div class='item'>{text}</div>")
            else:
                html_lines.append(f"<div class='item'>{str(rec)}</div>")
    else:
        html_lines.append("<div class='item'>No recommendations at this time.</div>")
    html_lines.append("</div>")

    # Footer
    html_lines.append("<div class='footer'>")
    html_lines.append("<p>SentinelOps Automated Daily Brief System</p>")
    html_lines.append("</div>")
    html_lines.append("</div>")
    html_lines.append("</body>")
    html_lines.append("</html>")

    return "\n".join(html_lines)


def send_via_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    smtp_server: str = "localhost",
    smtp_port: int = 25
) -> bool:
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = "sentinelops@localhost"
        msg['To'] = to_email

        # Attach HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Connect and send
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.sendmail("sentinelops@localhost", to_email, msg.as_string())

        print(f"[BRIEF] Email sent to {to_email}")
        return True

    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def send_daily_brief_email(date: str = None, to_email: str = None) -> bool:
    """Send Daily Brief via Email"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()

    # Use default email if not provided
    if not to_email:
        to_email = "security-team@localhost"

    print(f"[BRIEF] Sending Email to {to_email}: {date}")

    # Load brief
    brief = load_daily_brief(date)
    if not brief:
        return False

    # Format and send
    subject = f"SentinelOps Daily Brief - {date}"
    html_body = format_brief_html(brief, date)

    return send_via_smtp(to_email, subject, html_body)


if __name__ == "__main__":
    import sys

    date = sys.argv[1] if len(sys.argv) > 1 else None
    to_email = sys.argv[2] if len(sys.argv) > 2 else None
    success = send_daily_brief_email(date, to_email)
    sys.exit(0 if success else 1)
