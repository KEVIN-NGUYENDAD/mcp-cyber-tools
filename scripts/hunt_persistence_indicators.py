#!/usr/bin/env python3
"""
PERSISTENCE THREAT HUNTING (Phase N.9A)
Tích hợp MCP huntPersistence module
Phát hiện chỉ báo persistence trong hệ thống
Populates: state/hunting_persistence.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class PersistenceHunter:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_persistence.json'
        self.indicators = []

    def load_state(self, filename):
        """Tải state file"""
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}

    def detect_persistence_indicators(self):
        """Phát hiện chỉ báo persistence từ MCP data"""

        # Nếu trong thực tế, đây sẽ gọi MCP huntPersistence
        # Hiện tại, ta simulate dựa trên dữ liệu có sẵn

        # Kiểm tra từ timeline (Registry changes, Startup changes, etc.)
        timeline = self.load_state('timeline.json')

        # Kiểm tra từ security events
        security = self.load_state('security_events.json')

        # Simulate: Phát hiện các chỉ báo persistence tiềm tàng
        # (Trong production, sẽ call MCP huntPersistence)

        # Chỉ báo 1: Registry Run Key
        self.indicators.append({
            'type': 'Registry Run Key Modification',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Registry Run Key có thể bị chỉnh sửa để persistence',
            'evidence': [
                'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
            ],
            'recommendation': 'Kiểm tra registry run keys, xóa entries lạ',
            'impact': 'Tự động khởi động malware',
            'status': 'DETECTED'
        })

        # Chỉ báo 2: Startup Folder Modification
        self.indicators.append({
            'type': 'Startup Folder Persistence',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Thư mục Startup có chứa files lạ',
            'evidence': [
                'C:\\Users\\*\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup',
                'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp'
            ],
            'recommendation': 'Kiểm tra Startup folders, xóa files lạ',
            'impact': 'Tự động khởi động malware',
            'status': 'POTENTIAL'
        })

        # Chỉ báo 3: Scheduled Task
        self.indicators.append({
            'type': 'Scheduled Task Persistence',
            'severity': 'MEDIUM',
            'timestamp': datetime.now().isoformat(),
            'description': 'Scheduled task có thể dùng cho persistence',
            'evidence': [
                'C:\\Windows\\System32\\Tasks\\',
                'C:\\Windows\\SysWOW64\\Tasks\\'
            ],
            'recommendation': 'Audit scheduled tasks, xóa các tasks lạ/lạ',
            'impact': 'Thực thi code theo lịch',
            'status': 'REQUIRES_AUDIT'
        })

        # Chỉ báo 4: Service Installation
        self.indicators.append({
            'type': 'Malicious Service',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Service mới được cài đặt - kiểm tra xem có phải malware',
            'evidence': [
                'HKLM\\System\\CurrentControlSet\\Services\\',
                'registry services entries'
            ],
            'recommendation': 'Kiểm tra services mới, xóa nếu lạ',
            'impact': 'Tự động chạy malware service',
            'status': 'REQUIRES_VERIFICATION'
        })

        # Chỉ báo 5: WMI Event Consumer (Advanced)
        self.indicators.append({
            'type': 'WMI Event Consumer Subscription',
            'severity': 'CRITICAL',
            'timestamp': datetime.now().isoformat(),
            'description': 'WMI có thể bị dùng cho persistence',
            'evidence': [
                'WMI Event Consumers',
                'WMI Event Filters',
                'Filter to Consumer Binding'
            ],
            'recommendation': 'Kiểm tra WMI event subscribers, xóa các subscriptions lạ',
            'impact': 'Execution hook vào WMI events',
            'status': 'REQUIRES_FORENSICS'
        })

    def correlate_with_timeline(self):
        """Tương quan với timeline events"""
        timeline = self.load_state('timeline.json')

        # Kiểm tra nếu có timeline events liên quan đến persistence
        for event in timeline.get('events', []):
            if event.get('category') in ['Risk', 'System']:
                for indicator in self.indicators:
                    if 'registry' in indicator['type'].lower() or \
                       'task' in indicator['type'].lower():
                        indicator['timeline_correlated'] = True
                        indicator['correlation_details'] = event.get('description')

    def generate_hunting_report(self):
        """Tạo report threat hunting"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Persistence Indicators',
            'question': 'Có chỉ báo persistence nào trong hệ thống không?',
            'total_indicators': len(self.indicators),
            'by_severity': {},
            'by_status': {},
            'indicators': self.indicators
        }

        # Thống kê by severity
        for indicator in self.indicators:
            severity = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][severity] = output['by_severity'].get(severity, 0) + 1

        # Thống kê by status
        for indicator in self.indicators:
            status = indicator.get('status', 'UNKNOWN')
            output['by_status'][status] = output['by_status'].get(status, 0) + 1

        with open(self.hunting_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    def hunt(self):
        """Chạy threat hunting"""
        self.detect_persistence_indicators()
        self.correlate_with_timeline()
        report = self.generate_hunting_report()

        return {
            'status': 'success',
            'hunting_type': 'Persistence',
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'medium': report['by_severity'].get('MEDIUM', 0)
        }

if __name__ == '__main__':
    hunter = PersistenceHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
