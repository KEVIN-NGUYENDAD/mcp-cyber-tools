"""Telegram message sender with queuing, deduplication, and retry logic.

Consumes telegram_queue.json and sends alerts via Telegram Bot API.
Implements exponential backoff, message deduplication, and delivery tracking.
"""

import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path

from .storage import get_storage


class TelegramSender:
    """Send Telegram alerts with queueing and reliability features."""

    # Telegram API endpoint
    TELEGRAM_API = 'https://api.telegram.org'

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min

    # Deduplication: ignore duplicate messages within N seconds
    DEDUP_WINDOW = 300  # 5 minutes

    def __init__(self, state_dir: str = 'state', bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram sender.

        Args:
            state_dir: State directory for queue persistence
            bot_token: Telegram bot token (from env if not provided)
            chat_id: Telegram chat ID (from env if not provided)
        """
        self.storage = get_storage(state_dir)
        self.state_dir = state_dir

        # Load credentials from .env or parameters
        self.bot_token = bot_token or self._load_from_env('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or self._load_from_env('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            raise ValueError('Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env')

    def _load_from_env(self, key: str) -> Optional[str]:
        """Load value from .env file.

        Args:
            key: Environment variable name

        Returns:
            Value from .env or None
        """
        env_path = Path('.env')
        if not env_path.exists():
            return None

        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        return line.split('=', 1)[1]
        except Exception:
            pass

        return None

    def send_alert(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Send single alert to Telegram.

        Args:
            alert: Alert object with title, description, severity, etc.

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        # Format message
        message = self._format_alert_message(alert)

        # Send via API
        return self._send_message(message, alert_id=alert.get('id'))

    def process_queue(self, batch_size: int = 10) -> Dict[str, Any]:
        """Process telegram_queue.json, sending queued messages.

        Handles deduplication, retries, and status tracking.

        Args:
            batch_size: Max messages to send in one batch

        Returns:
            Processing result with sent, failed, deduped counts
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'sent': 0,
            'failed': 0,
            'deduped': 0,
            'errors': [],
        }

        # Read queue
        queue = self.storage.read_json('telegram_queue.json', default=[])

        if not queue:
            return result

        # Get sent messages for deduplication
        sent_messages = self.storage.read_json('telegram_sent.json', default=[])
        recent_sent = self._get_recent_messages(sent_messages, minutes=self.DEDUP_WINDOW // 60)
        dedup_hashes = {m['message_hash'] for m in recent_sent}

        # Process queue
        new_queue = []
        processed_count = 0

        for message_item in queue:
            if processed_count >= batch_size:
                # Keep remaining in queue
                new_queue.append(message_item)
                continue

            # Skip if already sent (deduplication)
            msg_hash = self._hash_message(message_item)
            if msg_hash in dedup_hashes:
                result['deduped'] += 1
                continue

            # Attempt to send
            success, error = self._send_queued_message(message_item)

            if success:
                result['sent'] += 1
                # Track sent message
                sent_record = {
                    'message_hash': msg_hash,
                    'alert_id': message_item.get('id'),
                    'sent_at': datetime.now().isoformat(),
                    'telegram_message_id': success if isinstance(success, int) else None,
                }
                sent_messages.append(sent_record)
                dedup_hashes.add(msg_hash)

            else:
                # Retry logic
                retries = message_item.get('retries', 0)
                if retries < self.MAX_RETRIES:
                    message_item['retries'] = retries + 1
                    message_item['last_error'] = error
                    message_item['last_retry'] = datetime.now().isoformat()
                    message_item['next_retry'] = (
                        datetime.now() + timedelta(seconds=self.RETRY_DELAYS[retries])
                    ).isoformat()
                    new_queue.append(message_item)
                else:
                    result['failed'] += 1
                    result['errors'].append(f"{message_item.get('id')}: {error}")

            processed_count += 1

        # Keep sent messages recent (last 1000)
        sent_messages = sent_messages[-1000:]

        # Persist queue and sent messages
        self.storage.write_json('telegram_queue.json', new_queue)
        self.storage.write_json('telegram_sent.json', sent_messages)

        return result

    def _send_queued_message(self, message_item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Send single queued message with retry delay check.

        Args:
            message_item: Item from telegram_queue

        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        # Check if ready to retry
        next_retry = message_item.get('next_retry')
        if next_retry and datetime.fromisoformat(next_retry) > datetime.now():
            return False, 'retry_delayed'

        # Format message
        message = self._format_queued_message(message_item)

        # Send
        return self._send_message(message, alert_id=message_item.get('id'))

    def _send_message(self, text: str, alert_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Send message via Telegram API.

        Args:
            text: Message text (supports HTML formatting)
            alert_id: Alert ID for tracking

        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        try:
            url = f'{self.TELEGRAM_API}/bot{self.bot_token}/sendMessage'

            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',  # Enable HTML formatting
                'disable_notification': False,  # Enable sound/vibration
            }

            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get('ok'):
                message_id = data.get('result', {}).get('message_id')
                return True, None

            else:
                error_msg = data.get('description', 'Unknown error')
                return False, error_msg

        except requests.exceptions.Timeout:
            return False, 'API timeout'
        except requests.exceptions.ConnectionError:
            return False, 'Connection error'
        except Exception as e:
            return False, str(e)

    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert as Telegram message.

        Args:
            alert: Alert object

        Returns:
            Formatted HTML message
        """
        severity_icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️',
        }

        icon = severity_icons.get(alert.get('severity', 'UNKNOWN'), '•')
        severity = alert.get('severity', 'UNKNOWN')
        title = alert.get('title', 'Alert')
        description = alert.get('description', 'No details')
        source = alert.get('source', 'unknown')
        entity_id = alert.get('entity_id', '-')

        message = f"""{icon} <b>SentinelOps Alert [{severity}]</b>

<b>Title:</b> {title}

<b>Description:</b> {description}

<b>Source:</b> {source}
<b>Entity:</b> {entity_id}

<i>Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"""

        return message

    def _format_queued_message(self, message_item: Dict[str, Any]) -> str:
        """Format queued message as Telegram text.

        Args:
            message_item: Item from telegram_queue

        Returns:
            Formatted HTML message
        """
        severity_icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️',
        }

        icon = severity_icons.get(message_item.get('severity', 'UNKNOWN'), '•')
        severity = message_item.get('severity', 'UNKNOWN')
        title = message_item.get('title', 'Alert')
        description = message_item.get('description', 'No details')
        source = message_item.get('source', 'unknown')
        entity_id = message_item.get('entity_id', '-')

        message = f"""{icon} <b>SentinelOps Alert [{severity}]</b>

<b>Title:</b> {title}

<b>Description:</b> {description}

<b>Source:</b> {source}
<b>Entity:</b> {entity_id}

<i>Queued: {message_item.get('queued_at', datetime.now().isoformat())[:19]}</i>"""

        return message

    def _hash_message(self, message_item: Dict[str, Any]) -> str:
        """Create hash of message for deduplication.

        Hashes title + description + source to detect duplicates.

        Args:
            message_item: Queue item

        Returns:
            SHA256 hex digest
        """
        key = f"{message_item.get('title')}|{message_item.get('description')}|{message_item.get('source')}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_recent_messages(self, messages: List[Dict[str, Any]], minutes: int = 5) -> List[Dict[str, Any]]:
        """Filter messages to only those sent in last N minutes.

        Args:
            messages: List of sent message records
            minutes: Look-back window

        Returns:
            Recent messages
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []

        for msg in messages:
            try:
                sent_at = datetime.fromisoformat(msg.get('sent_at', ''))
                if sent_at > cutoff:
                    recent.append(msg)
            except:
                pass

        return recent

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status.

        Returns:
            Queue stats
        """
        queue = self.storage.read_json('telegram_queue.json', default=[])
        sent = self.storage.read_json('telegram_sent.json', default=[])

        # Count by status
        status_counts = {}
        for item in queue:
            status = item.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'queued_count': len(queue),
            'sent_count': len(sent),
            'status_breakdown': status_counts,
            'queue_items': queue[:10],  # First 10 for inspection
        }

    def clear_old_sent_messages(self, days: int = 7) -> int:
        """Remove sent message records older than N days.

        Args:
            days: Age threshold

        Returns:
            Number of records removed
        """
        sent = self.storage.read_json('telegram_sent.json', default=[])
        cutoff = datetime.now() - timedelta(days=days)

        original_count = len(sent)
        sent = [
            msg for msg in sent
            if datetime.fromisoformat(msg.get('sent_at', datetime.now().isoformat())) > cutoff
        ]

        self.storage.write_json('telegram_sent.json', sent)

        return original_count - len(sent)


# Singleton instance
_telegram_sender = None

def get_telegram_sender(state_dir: str = 'state') -> TelegramSender:
    """Get or create singleton Telegram sender.

    Args:
        state_dir: State directory

    Returns:
        TelegramSender instance
    """
    global _telegram_sender
    if _telegram_sender is None:
        _telegram_sender = TelegramSender(state_dir=state_dir)
    return _telegram_sender
