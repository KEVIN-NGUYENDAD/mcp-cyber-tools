#!/usr/bin/env python3
"""Alert processor: Send queued Telegram alerts and GitHub issues.

Designed to run every 5 minutes via Windows Task Scheduler or cron.
Processes alert queues, sends Telegram messages, creates GitHub issues.

Usage:
    python scripts/process_alerts.py            # Process all queues
    python scripts/process_alerts.py --telegram # Telegram only
    python scripts/process_alerts.py --github   # GitHub only
    python scripts/process_alerts.py --stats    # Show statistics
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_telegram_sender, get_alert_engine, get_event_wiring
from utils.storage import get_storage


class AlertProcessor:
    """Process and deliver queued alerts."""

    def __init__(self):
        """Initialize alert processor."""
        self.storage = get_storage()
        self.telegram_sender = get_telegram_sender()
        self.alert_engine = get_alert_engine()
        self.event_wiring = get_event_wiring()
        self.log_file = Path('logs') / 'alert_processor.log'
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Ensure logs directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp."""
        timestamp = datetime.now().isoformat()
        # Replace Unicode for Windows compatibility
        message = message.replace('✅', '[OK]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]')
        log_entry = f'[{timestamp}] [{level}] {message}'

        try:
            print(log_entry)
        except UnicodeEncodeError:
            print(log_entry.encode('ascii', 'ignore').decode('ascii'))

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except:
            pass

    def process_telegram_queue(self, batch_size: int = 10) -> dict:
        """Process Telegram alert queue.

        Args:
            batch_size: Max messages to send per run

        Returns:
            Processing result
        """
        self.log('Processing Telegram queue...')

        try:
            result = self.telegram_sender.process_queue(batch_size=batch_size)

            self.log(f'Telegram queue processed: {result["sent"]} sent, {result["failed"]} failed, {result["deduped"]} deduped')

            return result

        except Exception as e:
            self.log(f'Telegram queue processing failed: {str(e)}', 'ERROR')
            return {'sent': 0, 'failed': 1, 'deduped': 0, 'error': str(e)}

    def process_github_queue(self, batch_size: int = 5) -> dict:
        """Process GitHub issue queue (stub for Phase 3).

        Currently logs queued items. Full GitHub API integration in next sprint.

        Args:
            batch_size: Max issues to create per run

        Returns:
            Processing result
        """
        self.log('Processing GitHub queue...')

        try:
            github_queue = self.storage.read_json('github_queue.json', default=[])

            result = {
                'timestamp': datetime.now().isoformat(),
                'queued': len(github_queue),
                'created': 0,
                'failed': 0,
            }

            self.log(f'GitHub queue: {len(github_queue)} issues pending (Phase 3 implementation coming)')

            return result

        except Exception as e:
            self.log(f'GitHub queue processing failed: {str(e)}', 'ERROR')
            return {'queued': 0, 'created': 0, 'failed': 1, 'error': str(e)}

    def process_all_queues(self) -> dict:
        """Process all alert queues.

        Returns:
            Combined processing result
        """
        self.log('=' * 60)
        self.log('ALERT PROCESSOR START')
        self.log('=' * 60)

        result = {
            'timestamp': datetime.now().isoformat(),
            'telegram': {},
            'github': {},
        }

        # Process Telegram queue
        result['telegram'] = self.process_telegram_queue()

        # Process GitHub queue
        result['github'] = self.process_github_queue()

        self.log('=' * 60)
        self.log('ALERT PROCESSOR COMPLETE')
        self.log('=' * 60)

        return result

    def show_statistics(self) -> dict:
        """Show current alert statistics.

        Returns:
            Statistics dict
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'telegram_queue': self.telegram_sender.get_queue_status(),
            'alert_stats': self.alert_engine.get_alert_stats(),
            'routing_stats': self.event_wiring.get_routing_stats(),
        }

        self.log('=' * 60)
        self.log('ALERT STATISTICS')
        self.log('=' * 60)

        self.log(f'Queued Telegram messages: {stats["telegram_queue"]["queued_count"]}')
        self.log(f'Sent Telegram messages: {stats["telegram_queue"]["sent_count"]}')
        self.log(f'Total alerts: {stats["alert_stats"]["total"]}')
        self.log(f'Critical: {stats["alert_stats"]["CRITICAL"]}')
        self.log(f'High: {stats["alert_stats"]["HIGH"]}')

        self.log('=' * 60)

        return stats

    def cleanup_old_data(self) -> dict:
        """Clean up old sent messages and logs.

        Returns:
            Cleanup result
        """
        self.log('Cleaning up old data...')

        result = {
            'sent_messages_removed': self.telegram_sender.clear_old_sent_messages(days=7),
            'timestamp': datetime.now().isoformat(),
        }

        self.log(f'Cleanup complete: {result["sent_messages_removed"]} old messages removed')

        return result


def main():
    """Main entry point."""
    processor = AlertProcessor()

    # Parse arguments
    if '--stats' in sys.argv:
        stats = processor.show_statistics()
        return 0

    elif '--telegram' in sys.argv:
        result = processor.process_telegram_queue()
        return 0 if result.get('failed', 1) == 0 else 1

    elif '--github' in sys.argv:
        result = processor.process_github_queue()
        return 0 if result.get('failed', 1) == 0 else 1

    elif '--cleanup' in sys.argv:
        processor.cleanup_old_data()
        return 0

    else:
        # Process all queues
        result = processor.process_all_queues()

        # Overall success: no failures in either queue
        success = (
            result.get('telegram', {}).get('failed', 1) == 0 and
            result.get('github', {}).get('failed', 0) == 0
        )

        return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
