#!/usr/bin/env python3
"""Get correct chat ID from Telegram getUpdates"""
import requests
import json
import os
from pathlib import Path

# Load token from .env
env_path = Path('.env')
bot_token = None

if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('TELEGRAM_BOT_TOKEN='):
                bot_token = line.split('=', 1)[1].strip()

if not bot_token:
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

if not bot_token:
    print('[ERROR] TELEGRAM_BOT_TOKEN not found. Set it in .env or environment variable.')
    exit(1)

api_url = f'https://api.telegram.org/bot{bot_token}/getUpdates'

print("Fetching getUpdates...")
print()

response = requests.get(api_url, timeout=10)
data = response.json()

print('Full Response:')
print(json.dumps(data, indent=2))
print()

if data.get('result'):
    print("Found chat messages:")
    for update in data['result']:
        if 'message' in update:
            msg = update['message']
            chat = msg.get('chat', {})
            print(f"  Chat ID: {chat.get('id')}")
            print(f"  Chat Type: {chat.get('type')}")
            print(f"  From: {msg.get('from', {}).get('first_name')}")
            print(f"  Text: {msg.get('text', '')[:50]}")
            print()
else:
    print("No messages found. Please send a message to @sentinelops_kevin_bot first.")
