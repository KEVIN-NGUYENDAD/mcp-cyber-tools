#!/usr/bin/env python3
"""
INCIDENT GENERATOR - Tạo Incidents từ Drift Events (Phase N.10A)
Tích hợp Control Drift detection vào incident workflow
Outputs: state/incidents.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class IncidentGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.incidents_file = self.state_dir / 'incidents.json'
        self.incidents = []
        self.incident_counter = 1
        self.load_existing_incidents()

    def load_state(self, filename):
        """Tải state file"""
        fp = self.state_dir / filename
        if fp.exists():
            try:
                return json.load(open(fp, encoding='utf-8'))
            except:
                return {}
        return {}

    def load_existing_incidents(self):
        """Tải incidents hiện có để tiếp tục đánh số"""
        if self.incidents_file.exists():
            try:
                data = json.load(open(self.incidents_file, encoding='utf-8'))
                existing = data.get('incidents', [])
                if existing:
                    last_id = existing[-1].get('incident_id', 'INC-0000')
                    try:
                        self.incident_counter = int(last_id.split('-')[1]) + 1
                    except:
                        pass
            except:
                pass

    def create_incident(self, severity, title, description, evidence, recommended_action):
        """Tạo incident mới"""
        incident_id = f"INC-{self.incident_counter:04d}"
        self.incident_counter += 1

        incident = {
            'incident_id': incident_id,
            'severity': severity,
            'status': 'OPEN',
            'title': title,
            'description': description,
            'evidence': evidence if isinstance(evidence, list) else [evidence],
            'recommended_action': recommended_action,
            'created_at': datetime.now().isoformat()
        }

        self.incidents.append(incident)
        return incident_id

    def detect_control_drift_incidents(self):
        """Phát hiện Control Drift incidents (Phase N.10A)"""
        drift_events = self.load_state('drift_events.json')

        for event in drift_events.get('events', []):
            severity = event.get('severity', 'MEDIUM')
            control = event.get('control', 'unknown')
            change_type = event.get('change_type', 'CHANGE')

            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"🔴 CONTROL DRIFT: {control.upper()}",
                    description=event.get('description', f'{control} changed'),
                    evidence=[
                        f"Control: {control}",
                        f"Loại thay đổi: {change_type}",
                        f"Giá trị cũ: {event.get('old_value')}",
                        f"Giá trị mới: {event.get('new_value')}",
                        f"Phát hiện lúc: {event.get('timestamp')}"
                    ],
                    recommended_action=f"Kiểm tra ngay lập tức - Tại sao {control} thay đổi so với baseline?"
                )

    def detect_critical_conditions(self):
        """Phát hiện các điều kiện nguy hiểm khác"""

        # Defender disabled
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled', False):
            self.create_incident(
                severity='CRITICAL',
                title='🔴 CRITICAL: Windows Defender Disabled',
                description='Microsoft Defender không được bảo vệ',
                evidence=['Windows Defender bị tắt'],
                recommended_action='Bật ngay Windows Defender'
            )

        # Firewall disabled
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled', False):
            self.create_incident(
                severity='HIGH',
                title='⚠ HIGH: Windows Firewall Disabled',
                description='Windows Firewall không được bảo vệ',
                evidence=['Windows Firewall bị tắt'],
                recommended_action='Bật ngay Windows Firewall'
            )

        # Risk escalation
        risk = self.load_state('risk_score.json')
        if risk.get('risk_level') == 'CRITICAL':
            self.create_incident(
                severity='CRITICAL',
                title='🔴 CRITICAL: Risk Level = CRITICAL',
                description=f"Tổng thể rủi ro lên mức CRITICAL (Score: {risk.get('overall_score', 0)})",
                evidence=[
                    f"Risk Score: {risk.get('overall_score', 0)}",
                    f"Risk Level: {risk.get('risk_level', 'UNKNOWN')}"
                ],
                recommended_action='Ưu tiên xử lý các vấn đề bảo mật ngay lập tức'
            )

    def generate(self):
        """Tạo tất cả incidents"""
        self.detect_control_drift_incidents()
        self.detect_critical_conditions()

        # Loại bỏ duplicates (kiểm tra title + severity)
        seen = set()
        unique_incidents = []
        for incident in self.incidents:
            key = (incident['title'], incident['severity'])
            if key not in seen:
                seen.add(key)
                unique_incidents.append(incident)

        self.incidents = unique_incidents

        # Sắp xếp: CRITICAL → HIGH → MEDIUM → LOW
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.incidents.sort(key=lambda x: severity_order.get(x.get('severity'), 99))

        # Tạo output
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_incidents': len(self.incidents),
            'by_severity': {},
            'by_status': {'OPEN': len(self.incidents)},
            'incidents': self.incidents
        }

        # Thống kê by severity
        for incident in self.incidents:
            severity = incident.get('severity', 'UNKNOWN')
            output['by_severity'][severity] = output['by_severity'].get(severity, 0) + 1

        # Lưu incidents
        with open(self.incidents_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return {
            'status': 'success',
            'total_incidents': len(self.incidents),
            'critical': output['by_severity'].get('CRITICAL', 0),
            'high': output['by_severity'].get('HIGH', 0),
            'medium': output['by_severity'].get('MEDIUM', 0)
        }

if __name__ == '__main__':
    generator = IncidentGenerator()
    result = generator.generate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get('status') == 'success' else 1)
