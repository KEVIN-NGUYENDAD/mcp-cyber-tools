#!/usr/bin/env python3
"""Direct Telegram API test with real credentials"""
import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Step 1: Print environment
cwd = os.getcwd()
print(f"Current working directory: {cwd}")
print()

# Step 2: Load real .env
env_path = Path("C:\\Users\\tamng\\Projects\\mcp-cyber-tools\\.env")
print(f"Absolute path of loaded .env: {env_path.absolute()}")
print()

# Step 3: Read credentials
bot_token = None
chat_id = None

with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            bot_token = line.split('=', 1)[1]
        elif line.startswith('TELEGRAM_CHAT_ID='):
            chat_id = line.split('=', 1)[1]

# Step 4: Print masked credentials
print(f"Masked TELEGRAM_BOT_TOKEN: {bot_token[:8]}...{bot_token[-4:]}")
print(f"TELEGRAM_CHAT_ID: {chat_id}")
print()

# Step 5: Call Telegram getMe API
print("=" * 70)
print("TELEGRAM API TEST 1: getMe")
print("=" * 70)
print()

api_url_getme = f'https://api.telegram.org/bot{bot_token}/getMe'
try:
    response_getme = requests.get(api_url_getme, timeout=10)
    print(f"Status Code: {response_getme.status_code}")
    print(f"Response:")
    print(json.dumps(response_getme.json(), indent=2))
    print()
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# Step 6: Send test message
print("=" * 70)
print("TELEGRAM API TEST 2: sendMessage")
print("=" * 70)
print()

api_url_send = f'https://api.telegram.org/bot{bot_token}/sendMessage'
payload = {
    'chat_id': chat_id,
    'text': '🚨 SentinelOps Direct Test\n\nPhase N.12 Emergency Activation Test',
    'parse_mode': 'HTML'
}

print(f"Sending message to chat_id: {chat_id}")
print(f"Message: SentinelOps Direct Test")
print()

try:
    response_send = requests.post(api_url_send, json=payload, timeout=10)
    print(f"Status Code: {response_send.status_code}")
    print(f"Response:")
    response_data = response_send.json()
    print(json.dumps(response_data, indent=2))
    print()

    # Step 7: Check success
    if response_send.status_code == 200 and response_data.get('ok'):
        print("=" * 70)
        print("PASSED ✓")
        print("=" * 70)
        print()

        # Update notification history
        state_dir = Path("C:\\Users\\tamng\\Projects\\mcp-cyber-tools\\state")
        state_dir.mkdir(exist_ok=True)

        history_file = state_dir / 'notification_history.json'
        history = {
            "type": "telegram_direct_test",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message_id": response_data.get('result', {}).get('message_id'),
            "chat_id": chat_id
        }

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        print(f"Updated: state/notification_history.json")
        print()
    else:
        print("FAILED - API returned error")
        print(f"Error: {response_data.get('description', 'Unknown')}")

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
