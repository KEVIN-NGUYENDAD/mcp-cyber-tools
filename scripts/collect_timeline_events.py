#!/usr/bin/env python3
"""
TIMELINE EVENTS COLLECTOR (Phase N.7)
Phát hiện thay đổi trong 24 giờ qua bằng cách so sánh snapshots
Populates: state/timeline.json

Theo dõi:
- Asset Changes (thiết bị mới, biến mất)
- Service Changes (service mới, port mới)
- WAAP Changes (điểm tăng/giảm)
- Risk Changes (thay đổi mức độ rủi ro)
- MCP Changes (Defender, Firewall, CPU, Disk)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

class TimelineEventCollector:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.history_dir = self.state_dir / 'history'
        self.timeline_file = self.state_dir / 'timeline.json'
        self.history_dir.mkdir(exist_ok=True)
        self.events = []

    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}

    def load_previous_state(self, filename):
        """Tải snapshot trước đó từ history"""
        fp = self.history_dir / f'{filename}.prev'
        return json.load(open(fp)) if fp.exists() else {}

    def save_current_state_as_previous(self, filename, data):
        """Lưu snapshot hiện tại để dùng cho lần check tiếp theo"""
        fp = self.history_dir / f'{filename}.prev'
        with open(fp, 'w') as f:
            json.dump(data, f)

    def detect_asset_changes(self):
        """Phát hiện thiết bị mới/biến mất"""
        current = self.load_state('assets.json')
        previous = self.load_previous_state('assets.json')

        current_ips = {a['ip'] for a in current.get('assets', [])}
        previous_ips = {a['ip'] for a in previous.get('assets', [])}

        new_ips = current_ips - previous_ips
        removed_ips = previous_ips - current_ips

        if new_ips:
            for ip in new_ips:
                asset = next((a for a in current.get('assets', []) if a['ip'] == ip), {})
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Asset',
                    'type': 'New Device',
                    'severity': 'MEDIUM',
                    'description': f"Thiết bị mới: {ip} ({asset.get('device_type', 'Unknown')})",
                    'details': {'ip': ip, 'device_type': asset.get('device_type')}
                })

        if removed_ips:
            for ip in removed_ips:
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Asset',
                    'type': 'Device Removed',
                    'severity': 'LOW',
                    'description': f"Thiết bị biến mất: {ip}",
                    'details': {'ip': ip}
                })

        self.save_current_state_as_previous('assets.json', current)

    def detect_service_changes(self):
        """Phát hiện service mới/port mới"""
        current = self.load_state('services.json')
        previous = self.load_previous_state('services.json')

        current_services = {s['id'] for s in current.get('services', [])}
        previous_services = {s['id'] for s in previous.get('services', [])}

        new_services = current_services - previous_services
        if new_services:
            for service_id in new_services:
                service = next((s for s in current.get('services', []) if s['id'] == service_id), {})
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Service',
                    'type': 'New Service',
                    'severity': 'MEDIUM',
                    'description': f"Service mới: {service.get('service_type')} ({service.get('plugin_family')})",
                    'details': {'service_id': service_id, 'service_type': service.get('service_type')}
                })

        self.save_current_state_as_previous('services.json', current)

    def detect_waap_changes(self):
        """Phát hiện thay đổi WAAP score"""
        current = self.load_state('waap_score.json')
        previous = self.load_previous_state('waap_score.json')

        current_score = current.get('score', 0)
        previous_score = previous.get('score', 0)

        if previous_score and current_score != previous_score:
            delta = current_score - previous_score
            if abs(delta) >= 10:
                severity = 'HIGH' if delta < -20 else 'MEDIUM' if delta < 0 else 'LOW'
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'WAAP',
                    'type': 'Score Change',
                    'severity': severity,
                    'description': f"WAAP score {'tăng' if delta > 0 else 'giảm'} {abs(delta)} điểm (từ {previous_score} → {current_score})",
                    'details': {'previous_score': previous_score, 'current_score': current_score, 'delta': delta}
                })

        self.save_current_state_as_previous('waap_score.json', current)

    def detect_risk_changes(self):
        """Phát hiện thay đổi mức độ rủi ro"""
        current = self.load_state('risk_score.json')
        previous = self.load_previous_state('risk_score.json')

        current_level = current.get('risk_level', 'UNKNOWN')
        previous_level = previous.get('risk_level', 'UNKNOWN')

        if previous_level and current_level != previous_level:
            severity_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
            is_escalation = severity_order.get(current_level, 0) > severity_order.get(previous_level, 0)

            self.events.append({
                'timestamp': datetime.now().isoformat(),
                'category': 'Risk',
                'type': 'Level Change',
                'severity': 'CRITICAL' if is_escalation else 'LOW',
                'description': f"Mức rủi ro thay đổi: {previous_level} → {current_level}",
                'details': {
                    'previous_level': previous_level,
                    'current_level': current_level,
                    'previous_score': previous.get('overall_score'),
                    'current_score': current.get('overall_score')
                }
            })

        self.save_current_state_as_previous('risk_score.json', current)

    def detect_mcp_changes(self):
        """Phát hiện thay đổi MCP (Defender, Firewall, Resources)"""

        # Defender changes
        defender_current = self.load_state('defender_status.json')
        defender_previous = self.load_previous_state('defender_status.json')

        if defender_previous:
            if defender_previous.get('enabled') and not defender_current.get('enabled'):
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Security',
                    'type': 'Defender Disabled',
                    'severity': 'CRITICAL',
                    'description': 'Microsoft Defender đã bị tắt',
                    'details': {}
                })
            elif not defender_previous.get('enabled') and defender_current.get('enabled'):
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Security',
                    'type': 'Defender Enabled',
                    'severity': 'LOW',
                    'description': 'Microsoft Defender đã bật lại',
                    'details': {}
                })

        self.save_current_state_as_previous('defender_status.json', defender_current)

        # Firewall changes
        firewall_current = self.load_state('firewall_status.json')
        firewall_previous = self.load_previous_state('firewall_status.json')

        if firewall_previous:
            if firewall_previous.get('enabled') and not firewall_current.get('enabled'):
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Security',
                    'type': 'Firewall Disabled',
                    'severity': 'CRITICAL',
                    'description': 'Windows Firewall đã bị tắt',
                    'details': {}
                })
            elif not firewall_previous.get('enabled') and firewall_current.get('enabled'):
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'Security',
                    'type': 'Firewall Enabled',
                    'severity': 'LOW',
                    'description': 'Windows Firewall đã bật lại',
                    'details': {}
                })

        self.save_current_state_as_previous('firewall_status.json', firewall_current)

        # System health changes
        health_current = self.load_state('system_health.json')
        health_previous = self.load_previous_state('system_health.json')

        if health_previous:
            if health_previous.get('disk_usage', 0) <= 90 and health_current.get('disk_usage', 0) > 90:
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'System',
                    'type': 'Disk Critical',
                    'severity': 'HIGH',
                    'description': f"Dung lượng đĩa tới mức nguy hiểm: {health_current.get('disk_usage')}%",
                    'details': {'disk_usage': health_current.get('disk_usage')}
                })

            if health_previous.get('cpu_usage', 0) <= 90 and health_current.get('cpu_usage', 0) > 90:
                self.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'category': 'System',
                    'type': 'CPU Critical',
                    'severity': 'HIGH',
                    'description': f"Sử dụng CPU cao: {health_current.get('cpu_usage')}%",
                    'details': {'cpu_usage': health_current.get('cpu_usage')}
                })

        self.save_current_state_as_previous('system_health.json', health_current)

    def collect(self):
        """Phát hiện tất cả thay đổi"""
        self.detect_asset_changes()
        self.detect_service_changes()
        self.detect_waap_changes()
        self.detect_risk_changes()
        self.detect_mcp_changes()

        # Sắp xếp theo thời gian (mới nhất trước)
        self.events.sort(key=lambda x: x['timestamp'], reverse=True)

        # Tạo timeline summary
        output = {
            'timestamp': datetime.now().isoformat(),
            'period': f"24 giờ gần nhất ({(datetime.now() - timedelta(hours=24)).isoformat()})",
            'total_events': len(self.events),
            'by_category': {},
            'by_severity': {},
            'events': self.events
        }

        # Thống kê theo category
        for event in self.events:
            cat = event.get('category')
            output['by_category'][cat] = output['by_category'].get(cat, 0) + 1

        # Thống kê theo severity
        for event in self.events:
            sev = event.get('severity')
            output['by_severity'][sev] = output['by_severity'].get(sev, 0) + 1

        with open(self.timeline_file, 'w') as f:
            json.dump(output, f, indent=2)

        return {
            'status': 'success',
            'total_events': len(self.events),
            'by_category': output['by_category'],
            'by_severity': output['by_severity']
        }

if __name__ == '__main__':
    collector = TimelineEventCollector()
    result = collector.collect()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
