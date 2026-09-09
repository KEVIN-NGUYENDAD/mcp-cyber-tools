"""Event wiring: Connect change_detector events to alert routing.

This module bridges change_detector output to the alert engine,
creating the automation pipeline:

  change_detector → events → AlertEngine → telegram_queue + github_queue

Designed to be called from change_detector.py after emitting events.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .alerts import get_alert_engine, Severity
from .storage import get_storage


class EventWiring:
    """Wire events to alert engine and route to appropriate channels."""

    def __init__(self, state_dir: str = 'state'):
        """Initialize event wiring.

        Args:
            state_dir: State directory for persistence
        """
        self.alert_engine = get_alert_engine(state_dir=state_dir)
        self.storage = get_storage(state_dir=state_dir)
        self.state_dir = state_dir

    def process_event(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Process single change_detector event through alert engine.

        Args:
            event: Event from change_detector with source, change_type, etc.

        Returns:
            Tuple of (success: bool, routing_result: dict)
        """
        try:
            # Create alert from event
            alert = self.alert_engine.create_alert(event)

            # Route alert to channels
            success, routing_result = self.alert_engine.route_alert(alert)

            # Log the routing
            self._log_event_routing(event, alert, routing_result)

            return success, routing_result

        except Exception as e:
            return False, {'error': str(e)}

    def process_events_batch(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple events in batch.

        Args:
            events: List of events from change_detector

        Returns:
            Batch processing result
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_events': len(events),
            'processed': 0,
            'failed': 0,
            'alerts_created': 0,
            'telegram_queued': 0,
            'github_queued': 0,
            'daily_brief_updated': 0,
            'archived': 0,
            'errors': [],
        }

        for event in events:
            try:
                alert = self.alert_engine.create_alert(event)
                success, routing_result = self.alert_engine.route_alert(alert)

                if success:
                    result['processed'] += 1
                    result['alerts_created'] += 1

                    # Count by channel
                    for channel in routing_result.get('channels_routed', []):
                        if channel == 'telegram':
                            result['telegram_queued'] += 1
                        elif channel == 'github':
                            result['github_queued'] += 1
                        elif channel == 'daily_brief':
                            result['daily_brief_updated'] += 1
                        elif channel == 'archive':
                            result['archived'] += 1

                    self._log_event_routing(event, alert, routing_result)
                else:
                    result['failed'] += 1
                    for error in routing_result.get('errors', []):
                        result['errors'].append(f"Event {event.get('source')}: {error}")

            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"Event processing failed: {str(e)}")

        return result

    def _log_event_routing(self, event: Dict[str, Any], alert: Dict[str, Any], routing_result: Dict[str, Any]):
        """Log event routing decision for auditing.

        Args:
            event: Original change_detector event
            alert: Created alert object
            routing_result: Routing result from alert engine
        """
        try:
            # Append to event log (rotates every 1000 entries)
            event_log = self.storage.read_json('event_routing_log.json', default=[])

            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_id': event.get('id'),
                'alert_id': alert.get('id'),
                'source': event.get('source'),
                'change_type': event.get('change_type'),
                'severity': alert.get('severity'),
                'channels_routed': routing_result.get('channels_routed', []),
                'errors': routing_result.get('errors', []),
            }

            event_log.append(log_entry)

            # Keep log size reasonable
            if len(event_log) > 1000:
                event_log = event_log[-1000:]

            self.storage.write_json('event_routing_log.json', event_log)

        except Exception:
            pass  # Logging failure should not block processing

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get event routing statistics.

        Returns:
            Stats about routing decisions
        """
        log = self.storage.read_json('event_routing_log.json', default=[])

        stats = {
            'total_events_routed': len(log),
            'by_severity': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0,
            },
            'by_source': {},
            'by_change_type': {},
            'channel_usage': {
                'telegram': 0,
                'github': 0,
                'daily_brief': 0,
                'archive': 0,
            },
        }

        for entry in log:
            severity = entry.get('severity', 'UNKNOWN')
            if severity in stats['by_severity']:
                stats['by_severity'][severity] += 1

            source = entry.get('source', 'unknown')
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

            change_type = entry.get('change_type', 'unknown')
            stats['by_change_type'][change_type] = stats['by_change_type'].get(change_type, 0) + 1

            for channel in entry.get('channels_routed', []):
                if channel in stats['channel_usage']:
                    stats['channel_usage'][channel] += 1

        return stats

    def get_critical_alerts_queue(self) -> List[Dict[str, Any]]:
        """Get queued CRITICAL alerts awaiting Telegram delivery.

        Returns:
            List of queued CRITICAL telegram messages
        """
        telegram_queue = self.storage.read_json('telegram_queue.json', default=[])

        critical = [m for m in telegram_queue if m.get('severity') == 'CRITICAL']
        return critical

    def get_routing_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event routing log entries.

        Args:
            limit: Max entries to return

        Returns:
            Recent routing log entries
        """
        log = self.storage.read_json('event_routing_log.json', default=[])

        # Return most recent entries
        return log[-limit:] if log else []


def wire_change_detector_to_telegram(event_data: Dict[str, Any], state_dir: str = 'state') -> Dict[str, Any]:
    """Convenience function for change_detector.py integration.

    Called after change_detector emits an event.

    Args:
        event_data: Event dict from change_detector
        state_dir: State directory

    Returns:
        Routing result
    """
    wiring = EventWiring(state_dir=state_dir)
    success, result = wiring.process_event(event_data)

    return {
        'success': success,
        'routing': result,
        'timestamp': datetime.now().isoformat(),
    }


# Singleton instance
_event_wiring = None

def get_event_wiring(state_dir: str = 'state') -> EventWiring:
    """Get or create singleton event wiring.

    Args:
        state_dir: State directory

    Returns:
        EventWiring instance
    """
    global _event_wiring
    if _event_wiring is None:
        _event_wiring = EventWiring(state_dir=state_dir)
    return _event_wiring
