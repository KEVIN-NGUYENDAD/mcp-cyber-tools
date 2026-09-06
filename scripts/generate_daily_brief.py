#!/usr/bin/env python3
"""
DAILY BRIEF GENERATOR (Phase N)
Generates comprehensive daily intelligence brief from collected data
Populates: daily_brief/ directory

Inputs:
- state/assets.json
- state/services.json
- state/crypto_inventory.json
- state/waap_score.json
- state/nessus_status.json
- state/domain_status.json

Outputs:
- daily_brief/<date>.json (daily brief report)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class DailyBriefGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.brief_dir = Path(__file__).parent.parent / 'daily_brief'
        self.brief_dir.mkdir(exist_ok=True)

    def load_state_file(self, filename):
        filepath = self.state_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def generate_brief(self):
        brief = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': {},
            'top_risks': [],
            'asset_intelligence': {},
            'service_intelligence': {},
            'crypto_posture': {},
            'waap_posture': {},
            'recommendations': []
        }

        assets_data = self.load_state_file('assets.json')
        services_data = self.load_state_file('services.json')
        crypto_data = self.load_state_file('crypto_inventory.json')
        waap_data = self.load_state_file('waap_score.json')

        if assets_data and isinstance(assets_data, dict):
            assets = assets_data.get('assets', [])
            brief['asset_intelligence'] = {
                'total_assets': len(assets),
                'by_type': self.count_by_type(assets, 'device_type'),
                'by_os': self.count_by_type(assets, 'os'),
                'top_vulnerable': self.get_top_items(assets, 'vulnerability_count', 5)
            }
            brief['summary']['assets'] = len(assets)

        if services_data and isinstance(services_data, dict):
            services = services_data.get('services', [])
            brief['service_intelligence'] = {
                'total_services': len(services),
                'by_type': self.count_by_type(services, 'service_type'),
                'top_services': self.get_top_items(services, 'vulnerability_count', 5)
            }
            brief['summary']['services'] = len(services)

        if crypto_data and isinstance(crypto_data, dict):
            brief['crypto_posture'] = {
                'score': crypto_data.get('score', 0),
                'status': 'good' if crypto_data.get('score', 0) >= 70 else 'needs_improvement',
                'critical_findings': crypto_data.get('severity_breakdown', {}).get('CRITICAL', 0),
                'high_findings': crypto_data.get('severity_breakdown', {}).get('HIGH', 0)
            }
            brief['summary']['crypto_score'] = crypto_data.get('score', 0)

        if waap_data and isinstance(waap_data, dict):
            brief['waap_posture'] = {
                'score': waap_data.get('score', 0),
                'status': waap_data.get('status', 'unknown'),
                'threats_detected': waap_data.get('threat_summary', {}).get('threats_detected', 0),
                'blocked_requests': waap_data.get('threat_summary', {}).get('blocked_requests', 0)
            }
            brief['summary']['waap_score'] = waap_data.get('score', 0)

        scores = [brief['crypto_posture'].get('score', 50), brief['waap_posture'].get('score', 50)]
        avg_score = sum(scores) / len(scores) if scores else 50

        if avg_score >= 80:
            risk_level = 'LOW'
        elif avg_score >= 60:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'

        brief['summary']['risk_level'] = risk_level

        # Add Control Baseline status (Phase N.10A)
        drift_data = self.load_state_file('control_drift.json')
        if drift_data:
            brief['control_baseline'] = {
                'status': drift_data.get('control_status_summary', {}),
                'has_drift': drift_data.get('has_critical_drift', False),
                'drifts_detected': drift_data.get('drifts_detected', 0)
            }

        # Add Data Freshness status (Phase N.10B)
        freshness_data = self.load_state_file('data_freshness.json')
        if freshness_data:
            brief['data_freshness'] = {
                'overall_status': freshness_data.get('overall_status', 'UNKNOWN'),
                'confidence_factor': freshness_data.get('confidence_factor', 0.5),
                'summary': freshness_data.get('summary', {})
            }

        # Add Leak Guard status (Phase N.10C)
        leak_data = self.load_state_file('leak_guard_status.json')
        if leak_data:
            brief['security'] = {
                'leak_guard': {
                    'status': leak_data.get('security_status', 'UNKNOWN'),
                    'total_findings': leak_data.get('total_findings', 0),
                    'by_severity': leak_data.get('by_severity', {}),
                    'recommendation': leak_data.get('recommendation', 'UNKNOWN')
                }
            }
            brief['sanitized'] = leak_data.get('security_status') == 'CLEAN'
        else:
            brief['sanitized'] = False

        # Add Executive Summary (Phase N.11)
        incidents_data = self.load_state_file('incidents.json')
        drift_data = self.load_state_file('control_drift.json')
        freshness_data = self.load_state_file('data_freshness.json')

        incidents = incidents_data.get('incidents', []) if incidents_data else []
        incident_count = len(incidents)
        critical_count = sum(1 for inc in incidents if inc.get('severity') == 'CRITICAL')
        high_count = sum(1 for inc in incidents if inc.get('severity') == 'HIGH')

        drift_count = drift_data.get('drifts_detected', 0) if drift_data else 0
        freshness_status = freshness_data.get('overall_status', 'UNKNOWN') if freshness_data else 'UNKNOWN'
        confidence_factor = freshness_data.get('confidence_factor', 0.5) if freshness_data else 0.5

        priority_1 = incidents[0]['title'] if incidents else 'Tất cả hệ thống BÌNH THƯỜNG'

        brief['executive_summary'] = {
            'overview': f'Hôm nay có {incident_count} sự cố ({critical_count} nghiêm trọng, {high_count} cao).',
            'control_drift': f'Có {drift_count} drift điều khiển được phát hiện.',
            'data_quality': f'Dữ liệu {freshness_status} với độ tin cậy {int(confidence_factor * 100)}%.',
            'security_status': f'Leak Guard: {"SẠCH ✅" if leak_data.get("security_status") == "CLEAN" else "CÓ LỖI ⚠️"}',
            'priority_1': priority_1,
            'incident_summary': {
                'total': incident_count,
                'critical': critical_count,
                'high': high_count,
                'medium': sum(1 for inc in incidents if inc.get('severity') == 'MEDIUM'),
                'low': sum(1 for inc in incidents if inc.get('severity') == 'LOW')
            },
            'drift_summary': {
                'total_drifts': drift_count,
                'control_status': drift_data.get('control_status_summary', {}) if drift_data else {}
            }
        }

        return brief

    def count_by_type(self, items, field):
        counts = defaultdict(int)
        for item in items:
            value = item.get(field, 'Unknown')
            counts[value] += 1
        return dict(counts)

    def get_top_items(self, items, sort_field, limit=5):
        sorted_items = sorted(items, key=lambda x: x.get(sort_field, 0), reverse=True)[:limit]
        return [{'name': item.get('ip') or item.get('service_type') or item.get('id', 'Unknown'), 'value': item.get(sort_field, 0)} for item in sorted_items]

    def save_brief(self, brief):
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            brief_file = self.brief_dir / f'{date_str}_brief.json'
            with open(brief_file, 'w') as f:
                json.dump(brief, f, indent=2)
            latest_file = self.brief_dir / 'latest.json'
            with open(latest_file, 'w') as f:
                json.dump(brief, f, indent=2)
            return True
        except Exception:
            return False

    def generate(self):
        brief = self.generate_brief()
        success = self.save_brief(brief)
        if success:
            return {'status': 'success', 'timestamp': datetime.now().isoformat(), 'brief_generated': True, 'summary': brief.get('summary', {})}
        else:
            return {'error': 'Failed to save brief'}


def main():
    generator = DailyBriefGenerator()
    result = generator.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
