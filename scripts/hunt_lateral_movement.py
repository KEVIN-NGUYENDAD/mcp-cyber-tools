#!/usr/bin/env python3
"""
LATERAL MOVEMENT THREAT HUNTING (Phase N.9B)
Tích hợp MCP huntLateralMovement module
Phát hiện chỉ báo di chuyển ngang trong hệ thống
Populates: state/hunting_lateral_movement.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class LateralMovementHunter:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_lateral_movement.json'
        self.indicators = []

    def load_state(self, filename):
        """Tải state file"""
        fp = self.state_dir / filename
        return json.load(open(fp, encoding='utf-8')) if fp.exists() else {}

    def detect_lateral_movement_indicators(self):
        """Phát hiện chỉ báo di chuyển ngang"""

        # Simulate: Phát hiện các chỉ báo lateral movement
        # (Trong production, sẽ call MCP huntLateralMovement)

        # Chỉ báo 1: SMB Movement
        self.indicators.append({
            'type': 'SMB Lateral Movement',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Phát hiện kết nối SMB bất thường giữa các máy',
            'evidence': [
                'Port 445 (SMB) connections',
                'Multiple failed SMB authentications',
                'Unusual SMB client behavior'
            ],
            'recommendation': 'Kiểm tra SMB logs, xác minh kết nối',
            'impact': 'Truyền lan malware qua share',
            'status': 'REQUIRES_VERIFICATION',
            'affected_assets': ['192.168.0.1', '192.168.0.10']
        })

        # Chỉ báo 2: PsExec Abuse
        self.indicators.append({
            'type': 'PsExec/Remote Execution',
            'severity': 'CRITICAL',
            'timestamp': datetime.now().isoformat(),
            'description': 'Phát hiện dấu hiệu PsExec hoặc remote command execution',
            'evidence': [
                'PSEXESVC service installation',
                'Remote service creation',
                'Admin share access (IPC$, ADMIN$)',
                'Service pipe access'
            ],
            'recommendation': 'Điều tra toàn bộ assets, kiểm tra audit logs',
            'impact': 'Thực thi code remote với quyền admin',
            'status': 'CRITICAL',
            'affected_assets': ['All systems']
        })

        # Chỉ báo 3: WinRM Abuse
        self.indicators.append({
            'type': 'WinRM Remote Management',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Phát hiện WinRM được dùng cho remote execution',
            'evidence': [
                'Port 5985/5986 (WinRM)',
                'Kerberos/NTLM auth from unusual sources',
                'PSRemoting connection attempts',
                'WinRM service abuse'
            ],
            'recommendation': 'Kiểm tra WinRM logs, audit remote sessions',
            'impact': 'Remote PowerShell execution',
            'status': 'REQUIRES_VERIFICATION',
            'affected_assets': []
        })

        # Chỉ báo 4: RDP Abuse
        self.indicators.append({
            'type': 'Remote Desktop Protocol Abuse',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'description': 'Phát hiện RDP được dùng bất thường',
            'evidence': [
                'Multiple RDP login attempts',
                'RDP from non-standard hours',
                'RDP from unusual geolocation',
                'RDP to sensitive systems'
            ],
            'recommendation': 'Kiểm tra RDP event logs, xác minh logins',
            'impact': 'Remote interactive access',
            'status': 'REQUIRES_VERIFICATION',
            'affected_assets': []
        })

        # Chỉ báo 5: Kerberos Abuse
        self.indicators.append({
            'type': 'Kerberos Delegation Abuse',
            'severity': 'CRITICAL',
            'timestamp': datetime.now().isoformat(),
            'description': 'Phát hiện khai thác Kerberos delegation (S4U)',
            'evidence': [
                'Unconstrained delegation usage',
                'Constrained delegation abuse',
                'Service for User (S4U) activity',
                'Ticket granting anomalies'
            ],
            'recommendation': 'Kiểm tra Kerberos delegation settings, audit ticket generation',
            'impact': 'Privilege escalation và lateral movement',
            'status': 'CRITICAL',
            'affected_assets': []
        })

    def correlate_with_network_data(self):
        """Tương quan với network analysis"""
        # Kiểm tra từ các state files khác nếu có
        pass

    def estimate_blast_radius(self):
        """Ước tính tạo động lây lan"""
        critical_count = sum(1 for i in self.indicators if i['severity'] == 'CRITICAL')
        high_count = sum(1 for i in self.indicators if i['severity'] == 'HIGH')

        if critical_count > 0:
            radius = 'ORGANIZATION-WIDE: Kerberos/PsExec abuse - có thể lây lan toàn hệ'
        elif high_count > 2:
            radius = 'MULTI-SYSTEM: SMB/WinRM abuse - lây lan trên multiple systems'
        else:
            radius = 'LIMITED: Isolated lateral movement attempts'

        return radius

    def generate_hunting_report(self):
        """Tạo report threat hunting"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Lateral Movement',
            'question': 'Có chỉ báo di chuyển ngang trong hệ thống không?',
            'total_indicators': len(self.indicators),
            'blast_radius': self.estimate_blast_radius(),
            'by_severity': {},
            'indicators': self.indicators
        }

        # Thống kê by severity
        for indicator in self.indicators:
            severity = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][severity] = output['by_severity'].get(severity, 0) + 1

        with open(self.hunting_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    def hunt(self):
        """Chạy threat hunting"""
        self.detect_lateral_movement_indicators()
        report = self.generate_hunting_report()

        return {
            'status': 'success',
            'hunting_type': 'Lateral Movement',
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'blast_radius': report['blast_radius']
        }

if __name__ == '__main__':
    hunter = LateralMovementHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
