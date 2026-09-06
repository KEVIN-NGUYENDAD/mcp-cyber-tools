#!/usr/bin/env python3
"""Send CRITICAL test alert via Telegram"""
import requests
import json
from datetime import datetime
from pathlib import Path

# Load credentials from .env
env_file = Path('C:\\Users\\tamng\\Projects\\mcp-cyber-tools\\.env')
bot_token = None
chat_id = None

with open(env_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            bot_token = line.split('=', 1)[1]
        elif line.startswith('TELEGRAM_CHAT_ID='):
            chat_id = line.split('=', 1)[1]

print(f"Bot Token: {bot_token[:8]}...{bot_token[-4:]}")
print(f"Chat ID: {chat_id}")
print()

# Read CRITICAL incidents from state/incidents.json
state_file = Path('state/incidents.json')
with open(state_file, 'r', encoding='utf-8') as f:
    state = json.load(f)

critical_alerts = [a for a in state.get('incidents', []) if a.get('severity') == 'CRITICAL']
print(f"Found {len(critical_alerts)} CRITICAL alerts")
print()

# Send first CRITICAL alert
if critical_alerts:
    alert = critical_alerts[0]

    message = f"""🚨 SENTINELOPS CRITICAL ALERT

Title: {alert.get('title')}
Incident: {alert.get('incident_id')}
Severity: {alert.get('severity')}
Status: {alert.get('status')}

Description: {alert.get('description')}

Recommended Action: {alert.get('recommended_action')}"""

    print(f"Sending incident: {alert.get('incident_id')}")
    print(f"Title: {alert.get('title')}")
    print()

    api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    response = requests.post(api_url, json=payload, timeout=10)
    data = response.json()

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")

    if response.status_code == 200 and data.get('ok'):
        print()
        print("✓ INCIDENT SENT SUCCESSFULLY")

        # Log to notification history
        history = {
            "sent_alerts": [{
                "incident_id": alert.get('incident_id'),
                "title": alert.get('title'),
                "severity": alert.get('severity'),
                "message_id": data.get('result', {}).get('message_id'),
                "sent_at": datetime.now().isoformat()
            }],
            "last_alert": {
                "incident_id": alert.get('incident_id'),
                "sent_at": datetime.now().isoformat()
            }
        }

        with open('state/notification_history.json', 'w') as f:
            json.dump(history, f, indent=2)

        print("Logged to state/notification_history.json")
