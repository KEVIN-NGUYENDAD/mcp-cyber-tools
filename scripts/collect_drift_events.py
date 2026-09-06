#!/usr/bin/env python3
"""
DRIFT EVENT COLLECTOR (Phase N.10A)
Tích hợp Control Drift vào Timeline
Tạo sự kiện cho Incident Engine
Outputs: state/drift_events.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class DriftEventCollector:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.drift_file = self.state_dir / 'control_drift.json'
        self.events_file = self.state_dir / 'drift_events.json'

    def load_drift_report(self):
        """Tải drift report từ baseline_controls.py"""
        if self.drift_file.exists():
            try:
                return json.load(open(self.drift_file, encoding='utf-8'))
            except:
                return None
        return None

    def convert_drifts_to_events(self):
        """Chuyển drift detections thành timeline events"""
        drift_report = self.load_drift_report()
        if not drift_report:
            return []

        drifts = drift_report.get('drifts', [])
        events = []

        for drift in drifts:
            # Tạo event cho timeline
            event = {
                'type': f"CONTROL_DRIFT_{drift['control'].upper()}",
                'severity': drift.get('severity', 'MEDIUM'),
                'timestamp': drift.get('detected_at', datetime.now().isoformat()),
                'title': f"Control Drift: {drift['control']}",
                'description': drift.get('description', ''),
                'control': drift['control'],
                'change_type': drift.get('type', 'UNKNOWN'),
                'old_value': drift.get('old_value'),
                'new_value': drift.get('new_value'),
                'delta': drift.get('delta'),
                'details': {
                    'baseline_value': drift.get('old_value'),
                    'current_value': drift.get('new_value'),
                    'detected_at': drift.get('detected_at'),
                    'severity': drift.get('severity')
                }
            }
            events.append(event)

        return events

    def generate_summary(self):
        """Tạo summary cho Daily Brief"""
        drift_report = self.load_drift_report()
        if not drift_report:
            return None

        return {
            'drifts_detected': drift_report.get('drifts_detected', 0),
            'has_critical': drift_report.get('has_critical_drift', False),
            'by_severity': drift_report.get('by_severity', {}),
            'control_status': drift_report.get('control_status_summary', {})
        }

    def run(self):
        """Chạy drift event collection"""
        events = self.convert_drifts_to_events()
        summary = self.generate_summary()

        output = {
            'timestamp': datetime.now().isoformat(),
            'schema_version': '1.0',
            'total_drift_events': len(events),
            'events': events,
            'summary': summary or {}
        }

        # Lưu drift events
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return {
            'status': 'success',
            'drift_events': len(events),
            'critical_count': sum(1 for e in events if e.get('severity') == 'CRITICAL'),
            'control_status': summary.get('control_status', {}) if summary else {}
        }

if __name__ == '__main__':
    collector = DriftEventCollector()
    result = collector.run()
    # Avoid unicode encoding issues on Windows
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    sys.exit(0 if result.get('status') == 'success' else 1)
