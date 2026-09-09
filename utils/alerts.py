"""Alert routing and severity engine for SentinelOps.

Routes change_detector events to appropriate channels:
- CRITICAL → Telegram (immediate)
- HIGH → GitHub issue + Daily brief
- MEDIUM/LOW → Daily brief only

Supports severity overrides by event source.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .storage import get_storage


class Severity(Enum):
    """Alert severity levels."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class AlertChannel(Enum):
    """Delivery channels for alerts."""
    TELEGRAM = 'telegram'
    GITHUB = 'github'
    DAILY_BRIEF = 'daily_brief'
    ARCHIVE = 'archive'


class AlertEngine:
    """Routes alerts to appropriate channels based on severity and source."""

    # Default severity by change type
    SEVERITY_BY_CHANGE_TYPE = {
        'new_entity': Severity.MEDIUM,
        'removed_entity': Severity.MEDIUM,
        'field_toggled': Severity.HIGH,
        'value_changed': Severity.LOW,
    }

    # Source-specific severity overrides (source substring, change_type) → severity
    SEVERITY_OVERRIDES = {
        ('defender_threats', 'new_entity'): Severity.CRITICAL,  # Malware detected
        ('defender_status', 'field_toggled'): Severity.CRITICAL,  # Defender disabled
        ('device_inventory', 'new_entity'): Severity.HIGH,       # Unknown device
        ('firewall_status', 'field_toggled'): Severity.HIGH,     # Firewall changed
    }

    # Channels to route by severity
    CHANNEL_ROUTING = {
        Severity.CRITICAL: [AlertChannel.TELEGRAM, AlertChannel.GITHUB, AlertChannel.DAILY_BRIEF, AlertChannel.ARCHIVE],
        Severity.HIGH: [AlertChannel.GITHUB, AlertChannel.DAILY_BRIEF, AlertChannel.ARCHIVE],
        Severity.MEDIUM: [AlertChannel.DAILY_BRIEF, AlertChannel.ARCHIVE],
        Severity.LOW: [AlertChannel.DAILY_BRIEF, AlertChannel.ARCHIVE],
    }

    def __init__(self, state_dir: str = 'state'):
        """Initialize alert engine with storage.

        Args:
            state_dir: State directory for persistence
        """
        self.storage = get_storage(state_dir)
        self.state_dir = state_dir

    def determine_severity(self, source: str, change_type: str) -> Severity:
        """Determine alert severity based on source and change type.

        Checks severity overrides first, then uses default by change_type.

        Args:
            source: Event source (e.g., 'defender_threats')
            change_type: Type of change ('new_entity', 'field_toggled', etc.)

        Returns:
            Severity level
        """
        # Check overrides first
        for (substr, ct), severity in self.SEVERITY_OVERRIDES.items():
            if ct == change_type and substr in source.lower():
                return severity

        # Fall back to change_type default
        return self.SEVERITY_BY_CHANGE_TYPE.get(change_type, Severity.LOW)

    def create_alert(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert from change_detector event.

        Args:
            event: Event from change_detector with source, change_type, entity_id, etc.

        Returns:
            Alert object with metadata
        """
        source = event.get('source', 'unknown')
        change_type = event.get('change_type', 'value_changed')
        severity = self.determine_severity(source, change_type)

        alert = {
            'id': self._generate_alert_id(),
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'change_type': change_type,
            'severity': severity.name,
            'severity_level': severity.value,
            'entity_id': event.get('entity_id'),
            'title': self._generate_title(source, change_type, event),
            'description': self._generate_description(event),
            'channels': [c.value for c in self.CHANNEL_ROUTING[severity]],
            'original_event': event,
            'status': 'pending',  # pending, telegram_sent, github_created, archived
        }

        return alert

    def route_alert(self, alert: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Route alert to appropriate channels.

        Args:
            alert: Alert object created by create_alert()

        Returns:
            Tuple of (success: bool, routing_result: dict with channel results)
        """
        routing_result = {
            'alert_id': alert['id'],
            'timestamp': datetime.now().isoformat(),
            'channels_routed': [],
            'errors': [],
        }

        channels = alert.get('channels', [])

        for channel_str in channels:
            try:
                channel = AlertChannel(channel_str)

                if channel == AlertChannel.TELEGRAM:
                    success, error = self._route_telegram(alert)
                    if success:
                        routing_result['channels_routed'].append('telegram')
                    else:
                        routing_result['errors'].append(f'telegram: {error}')

                elif channel == AlertChannel.GITHUB:
                    success, error = self._route_github(alert)
                    if success:
                        routing_result['channels_routed'].append('github')
                    else:
                        routing_result['errors'].append(f'github: {error}')

                elif channel == AlertChannel.DAILY_BRIEF:
                    success, error = self._route_daily_brief(alert)
                    if success:
                        routing_result['channels_routed'].append('daily_brief')
                    else:
                        routing_result['errors'].append(f'daily_brief: {error}')

                elif channel == AlertChannel.ARCHIVE:
                    success, error = self._route_archive(alert)
                    if success:
                        routing_result['channels_routed'].append('archive')
                    else:
                        routing_result['errors'].append(f'archive: {error}')

            except ValueError:
                routing_result['errors'].append(f'unknown_channel: {channel_str}')

        overall_success = len(routing_result['errors']) == 0
        return overall_success, routing_result

    def _route_telegram(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Route CRITICAL alert to Telegram (queued for async sending).

        Args:
            alert: Alert object

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        try:
            # Queue for Telegram delivery (not sent immediately)
            telegram_queue = self.storage.read_json('telegram_queue.json', default=[])

            telegram_message = {
                'id': alert['id'],
                'queued_at': datetime.now().isoformat(),
                'alert_id': alert['id'],
                'severity': alert['severity'],
                'title': alert['title'],
                'description': alert['description'],
                'source': alert['source'],
                'entity_id': alert.get('entity_id'),
                'status': 'queued',  # queued, sent, failed, deduped
            }

            telegram_queue.append(telegram_message)

            # Keep queue size reasonable (last 1000 messages)
            if len(telegram_queue) > 1000:
                telegram_queue = telegram_queue[-1000:]

            success, error = self.storage.write_json('telegram_queue.json', telegram_queue)
            return success, error

        except Exception as e:
            return False, str(e)

    def _route_github(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Route HIGH+ alert to GitHub incident queue.

        Args:
            alert: Alert object

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        try:
            github_queue = self.storage.read_json('github_queue.json', default=[])

            github_issue = {
                'id': alert['id'],
                'queued_at': datetime.now().isoformat(),
                'alert_id': alert['id'],
                'severity': alert['severity'],
                'title': alert['title'],
                'description': alert['description'],
                'source': alert['source'],
                'status': 'queued',  # queued, created, failed
                'github_issue_id': None,  # Will be filled when issue created
            }

            github_queue.append(github_issue)

            success, error = self.storage.write_json('github_queue.json', github_queue)
            return success, error

        except Exception as e:
            return False, str(e)

    def _route_daily_brief(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Route alert to daily brief store.

        Args:
            alert: Alert object

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        try:
            # Get today's brief
            today = datetime.now().strftime('%Y-%m-%d')
            brief_file = f'daily_brief/{today}.json'

            def add_to_brief(brief_data):
                if 'changes' not in brief_data:
                    brief_data['changes'] = []

                change = {
                    'timestamp': alert['timestamp'],
                    'alert_id': alert['id'],
                    'severity': alert['severity'],
                    'title': alert['title'],
                    'description': alert['description'],
                    'source': alert['source'],
                }

                brief_data['changes'].append(change)

                # Keep changes recent (last 100)
                if len(brief_data['changes']) > 100:
                    brief_data['changes'] = brief_data['changes'][-100:]

                return brief_data

            default_brief = {
                'date': today,
                'changes': [],
                'created_at': datetime.now().isoformat(),
            }

            success, error = self.storage.write_json(brief_file, default_brief)
            if not success:
                return False, error

            # Now update it with the alert
            success, _, error = self.storage.read_and_modify(brief_file, add_to_brief)
            return success, error

        except Exception as e:
            return False, str(e)

    def _route_archive(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Archive alert for long-term storage.

        Args:
            alert: Alert object

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        try:
            archive = self.storage.read_json('alert_archive.json', default=[])

            archive.append(alert)

            # Keep archive size reasonable (last 10000 alerts)
            if len(archive) > 10000:
                archive = archive[-10000:]

            success, error = self.storage.write_json('alert_archive.json', archive)
            return success, error

        except Exception as e:
            return False, str(e)

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        return f'alert_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]}'

    def _generate_title(self, source: str, change_type: str, event: Dict[str, Any]) -> str:
        """Generate alert title from event data."""
        entity_id = event.get('entity_id', '?')

        if change_type == 'new_entity':
            return f'[NEW] {source}: {entity_id}'
        elif change_type == 'removed_entity':
            return f'[REMOVED] {source}: {entity_id}'
        elif change_type == 'field_toggled':
            field = event.get('field', '?')
            return f'[TOGGLE] {source}.{field} changed'
        else:
            field = event.get('field', '?')
            return f'[CHANGE] {source}.{field}'

    def _generate_description(self, event: Dict[str, Any]) -> str:
        """Generate alert description from event data."""
        parts = []

        if 'old_value' in event and 'new_value' in event:
            parts.append(f"Changed from {event['old_value']} to {event['new_value']}")

        if event.get('evidence'):
            evidence = event.get('evidence', [])
            if evidence:
                parts.append(f"Evidence: {evidence[0] if isinstance(evidence, list) else evidence}")

        return ' | '.join(parts) if parts else 'No additional details'

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve alert by ID from archive.

        Args:
            alert_id: Alert ID

        Returns:
            Alert object or None
        """
        archive = self.storage.read_json('alert_archive.json', default=[])

        for alert in archive:
            if alert.get('id') == alert_id:
                return alert

        return None

    def get_alerts_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get recent alerts by severity level.

        Args:
            severity: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'

        Returns:
            List of recent alerts matching severity
        """
        archive = self.storage.read_json('alert_archive.json', default=[])

        # Filter by severity (most recent first)
        filtered = [a for a in reversed(archive) if a.get('severity') == severity]

        return filtered[:100]  # Last 100

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics (counts by severity).

        Returns:
            Dict with severity counts
        """
        archive = self.storage.read_json('alert_archive.json', default=[])

        stats = {
            'total': len(archive),
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'last_alert': None,
        }

        for alert in archive:
            severity = alert.get('severity', 'UNKNOWN')
            if severity in stats:
                stats[severity] += 1

        if archive:
            stats['last_alert'] = archive[-1].get('timestamp')

        return stats


# Singleton instance for convenience
_alert_engine = None

def get_alert_engine(state_dir: str = 'state') -> AlertEngine:
    """Get or create singleton alert engine.

    Args:
        state_dir: State directory (only used on first call)

    Returns:
        AlertEngine instance
    """
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine(state_dir=state_dir)
    return _alert_engine
