#!/usr/bin/env python3
"""
DATA FRESHNESS TRACKING (Phase N.10B)
Tai su dung logic tu Home SOC
Theo doi tuoi du lieu va phát canh báo STALE/EXPIRED
Outputs: state/data_freshness.json
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

class DataFreshnessTracker:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.brief_dir = Path(__file__).parent.parent / 'daily_brief'
        self.freshness_file = self.state_dir / 'data_freshness.json'

        # Files to track
        self.tracked_files = {
            'assets.json': 'Asset Intelligence',
            'services.json': 'Service Intelligence',
            'crypto_inventory.json': 'Crypto Inventory',
            'risk_score.json': 'Risk Score',
            'incidents.json': 'Incidents',
            'control_drift.json': 'Control Drift',
            'baseline_controls.json': 'Baseline Controls',
            'drift_events.json': 'Drift Events'
        }

    def get_file_age_minutes(self, filepath):
        """Tinh tuoi file (phut)"""
        if not filepath.exists():
            return None

        mtime = filepath.stat().st_mtime
        file_time = datetime.fromtimestamp(mtime)
        age = datetime.now() - file_time
        return int(age.total_seconds() / 60)

    def get_freshness_status(self, age_minutes):
        """Xac dinh trang thai du lieu"""
        if age_minutes is None:
            return 'MISSING'
        elif age_minutes < 60:
            return 'FRESH'
        elif age_minutes < 24 * 60:  # 24 hours
            return 'STALE'
        else:
            return 'EXPIRED'

    def get_freshness_severity(self, status):
        """Map status to severity for risk engine"""
        severity_map = {
            'FRESH': 0,      # No impact
            'STALE': 1,      # Minor confidence reduction
            'EXPIRED': 3,    # Major confidence reduction
            'MISSING': 4     # Critical - no data
        }
        return severity_map.get(status, 5)

    def track_all_files(self):
        """Theo doi tat ca cac file"""
        tracked_data = []
        freshness_summary = {}

        for filename, description in self.tracked_files.items():
            filepath = self.state_dir / filename
            age_minutes = self.get_file_age_minutes(filepath)
            status = self.get_freshness_status(age_minutes)
            severity = self.get_freshness_severity(status)

            # Xac dinh icon hien thi
            icon_map = {
                'FRESH': 'OK',
                'STALE': 'CAUTION',
                'EXPIRED': 'WARNING',
                'MISSING': 'ERROR'
            }

            tracked_data.append({
                'filename': filename,
                'description': description,
                'path': str(filepath),
                'exists': filepath.exists(),
                'age_minutes': age_minutes,
                'status': status,
                'severity': severity,
                'last_updated': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat() if filepath.exists() else None,
                'display_icon': icon_map.get(status, 'UNKNOWN')
            })

            freshness_summary[filename] = {
                'status': status,
                'age_minutes': age_minutes,
                'severity': severity
            }

        return tracked_data, freshness_summary

    def get_overall_freshness(self, freshness_summary):
        """Tinh trang thai tong the"""
        if not freshness_summary:
            return 'UNKNOWN'

        statuses = [data['status'] for data in freshness_summary.values()]

        # Neu co file EXPIRED
        if 'EXPIRED' in statuses:
            return 'EXPIRED'
        # Neu co file MISSING
        elif 'MISSING' in statuses:
            return 'MISSING'
        # Neu co file STALE
        elif 'STALE' in statuses:
            return 'STALE'
        # Tat ca FRESH
        else:
            return 'FRESH'

    def get_confidence_factor(self, overall_status):
        """Tinh confidence factor cho Risk Engine"""
        factor_map = {
            'FRESH': 1.0,      # 100% confidence
            'STALE': 0.8,      # 80% confidence
            'EXPIRED': 0.5,    # 50% confidence
            'MISSING': 0.2,    # 20% confidence
            'UNKNOWN': 0.5     # 50% confidence
        }
        return factor_map.get(overall_status, 0.5)

    def run(self):
        """Chay data freshness tracking"""
        tracked_data, freshness_summary = self.track_all_files()
        overall_status = self.get_overall_freshness(freshness_summary)
        confidence_factor = self.get_confidence_factor(overall_status)

        output = {
            'timestamp': datetime.now().isoformat(),
            'schema_version': '1.0',
            'overall_status': overall_status,
            'confidence_factor': confidence_factor,
            'tracked_files': tracked_data,
            'summary': {
                'total_files': len(tracked_data),
                'fresh_count': sum(1 for d in tracked_data if d['status'] == 'FRESH'),
                'stale_count': sum(1 for d in tracked_data if d['status'] == 'STALE'),
                'expired_count': sum(1 for d in tracked_data if d['status'] == 'EXPIRED'),
                'missing_count': sum(1 for d in tracked_data if d['status'] == 'MISSING'),
                'average_age_minutes': sum([d['age_minutes'] or 0 for d in tracked_data]) // len(tracked_data) if tracked_data else 0
            },
            'freshness_contract': {
                'fresh_threshold_minutes': 60,
                'stale_threshold_hours': 24,
                'check_frequency': 'Every pipeline run'
            }
        }

        # Luu freshness report
        with open(self.freshness_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=True)

        return {
            'status': 'success',
            'overall_status': overall_status,
            'confidence_factor': confidence_factor,
            'summary': output['summary']
        }

if __name__ == '__main__':
    tracker = DataFreshnessTracker()
    result = tracker.run()
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    sys.exit(0 if result.get('status') == 'success' else 1)
