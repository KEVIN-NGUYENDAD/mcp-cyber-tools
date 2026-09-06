#!/usr/bin/env python3
"""
INCIDENT ENGINE - Automated Incident Creation (Phase N.9)
Tự động tạo Incidents dựa trên phát hiện kết hợp
Populates: state/incidents.json

Quy tắc tạo Incident:
1. New Device + Failed Logons + New Service → INCIDENT HIGH
2. Risk LOW → HIGH → INCIDENT HIGH
3. Defender Disabled → INCIDENT CRITICAL
4. Firewall Disabled → INCIDENT HIGH
5. Weak Cipher + WAAP thấp → INCIDENT MEDIUM
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class IncidentEngine:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.incidents = []
        self.incident_counter = 1
        self.incidents_file = self.state_dir / 'incidents.json'
        self.load_existing_incidents()

    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp, encoding='utf-8')) if fp.exists() else {}

    def load_existing_incidents(self):
        """Tải incidents hiện có để tiếp tục đánh số"""
        if self.incidents_file.exists():
            try:
                data = json.load(open(self.incidents_file))
                existing = data.get('incidents', [])
                if existing:
                    last_id = existing[-1].get('incident_id', 'INC-0000')
                    try:
                        self.incident_counter = int(last_id.split('-')[1]) + 1
                    except:
                        pass
            except:
                pass

    def create_incident(self, severity, title, assets, evidence, recommended_action, reason):
        """Tạo incident mới"""
        incident_id = f"INC-{self.incident_counter:04d}"
        self.incident_counter += 1

        incident = {
            'incident_id': incident_id,
            'severity': severity,
            'status': 'OPEN',
            'title': title,
            'description': reason,
            'assets': assets if isinstance(assets, list) else [assets] if assets else [],
            'evidence': evidence if isinstance(evidence, list) else [evidence] if evidence else [],
            'recommended_action': recommended_action,
            'created_at': datetime.now().isoformat()
        }

        self.incidents.append(incident)
        return incident_id

    def detect_device_service_logon_anomaly(self):
        """Quy tắc 1: New Device + Failed Logons + New Service"""
        timeline = self.load_state('timeline.json')
        events = timeline.get('events', [])

        new_devices = [e for e in events if e.get('type') == 'New Device']
        new_services = [e for e in events if e.get('type') == 'New Service']

        security_events = self.load_state('security_events.json')
        failed_logons = security_events.get('failed_logons', 0)

        if new_devices and new_services and failed_logons > 10:
            device_ips = [e.get('details', {}).get('ip') for e in new_devices if e.get('details', {}).get('ip')]
            evidence = [
                f"{len(new_devices)} thiết bị mới",
                f"{len(new_services)} service mới",
                f"{failed_logons} failed logons"
            ]

            self.create_incident(
                severity='HIGH',
                title='Hoạt động bất thường: Thiết bị mới + Failed Logons + Service mới',
                assets=device_ips,
                evidence=evidence,
                recommended_action='Kiểm tra thiết bị mới, xác thực người dùng, kiểm tra dịch vụ',
                reason='Kết hợp: New Device + High Failed Logons + New Service'
            )

    def detect_risk_escalation(self):
        """Quy tắc 2: Risk LOW → HIGH"""
        # Load current and previous risk scores
        risk = self.load_state('risk_score.json')
        current_level = risk.get('risk_level', 'UNKNOWN')
        current_score = risk.get('overall_score', 0)

        if current_level == 'HIGH':
            components = risk.get('component_scores', {})
            weak_components = [c for c, s in components.items() if s < 50]

            if weak_components:
                self.create_incident(
                    severity='HIGH',
                    title='Rủi ro tăng vọt: Risk Level = HIGH',
                    assets=[],
                    evidence=[
                        f'Risk Score: {current_score}',
                        f'Thành phần yếu: {", ".join(weak_components)}'
                    ],
                    recommended_action='Ưu tiên cải thiện các thành phần yếu',
                    reason='Risk Level escalation to HIGH'
                )

    def detect_defender_disabled(self):
        """Quy tắc 3: Defender Disabled → INCIDENT CRITICAL"""
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            self.create_incident(
                severity='CRITICAL',
                title='HỆ THỐNG BẤT ĐỮC BẢO VỆ: Defender bị tắt',
                assets=[],
                evidence=['Microsoft Defender disabled'],
                recommended_action='Bật ngay Microsoft Defender',
                reason='Critical: Defender disabled'
            )

    def detect_firewall_disabled(self):
        """Quy tắc 4: Firewall Disabled → INCIDENT HIGH"""
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            self.create_incident(
                severity='HIGH',
                title='Mạng không được bảo vệ: Firewall bị tắt',
                assets=[],
                evidence=['Windows Firewall disabled'],
                recommended_action='Bật Windows Firewall ngay',
                reason='Firewall disabled'
            )

    def detect_weak_crypto_plus_waap_low(self):
        """Quy tắc 5: Weak Cipher + WAAP thấp → INCIDENT MEDIUM"""
        crypto = self.load_state('crypto_inventory.json')
        waap = self.load_state('waap_score.json')

        weak_ciphers = crypto.get('severity_breakdown', {}).get('CRITICAL', 0)
        waap_score = waap.get('score', 100)

        if weak_ciphers > 0 and waap_score < 60:
            self.create_incident(
                severity='MEDIUM',
                title='Mã hóa yếu + WAAP thấp: Rủi ro bảo mật',
                assets=[],
                evidence=[
                    f'{weak_ciphers} weak crypto findings',
                    f'WAAP Score: {waap_score}/100'
                ],
                recommended_action='Cập nhật cipher suites, cải thiện WAAP score',
                reason='Combination: Weak Cipher + Low WAAP'
            )

    def detect_system_resource_critical(self):
        """Phát hiện: System resources critical"""
        health = self.load_state('system_health.json')
        disk_usage = health.get('disk_usage', 0)
        cpu_usage = health.get('cpu_usage', 0)

        if disk_usage > 95:
            self.create_incident(
                severity='HIGH',
                title='Tài nguyên hệ thống cần khẩn cấp: Đĩa đầy',
                assets=[],
                evidence=[f'Disk usage: {disk_usage}%'],
                recommended_action='Dọn dẹp đĩa ngay lập tức',
                reason='Critical disk usage'
            )

        if cpu_usage > 95:
            self.create_incident(
                severity='MEDIUM',
                title='CPU sử dụng cao: Cần kiểm tra',
                assets=[],
                evidence=[f'CPU usage: {cpu_usage}%'],
                recommended_action='Kiểm tra processes, tối ưu hóa',
                reason='High CPU usage'
            )

    def detect_multiple_vulnerabilities(self):
        """Phát hiện: Asset với nhiều critical/high vulnerabilities"""
        assets = self.load_state('assets.json')

        for asset in assets.get('assets', []):
            critical_count = asset.get('critical', 0)
            high_count = asset.get('high', 0)
            ip = asset.get('ip')

            if critical_count > 3:
                self.create_incident(
                    severity='CRITICAL',
                    title=f'Asset có nhiều Critical vulnerabilities: {ip}',
                    assets=[ip],
                    evidence=[
                        f'{critical_count} critical vulnerabilities',
                        f'{high_count} high vulnerabilities'
                    ],
                    recommended_action=f'Patch ngay các lỗ hổng trên {ip}',
                    reason='Multiple critical vulnerabilities'
                )
            elif critical_count > 0 or high_count > 5:
                self.create_incident(
                    severity='HIGH',
                    title=f'Asset có high-severity vulnerabilities: {ip}',
                    assets=[ip],
                    evidence=[
                        f'{critical_count} critical vulnerabilities',
                        f'{high_count} high vulnerabilities'
                    ],
                    recommended_action=f'Lập kế hoạch patch cho {ip}',
                    reason='High-severity vulnerabilities detected'
                )

    def detect_suspicious_events(self):
        """Phát hiện: Sự kiện lạ từ timeline"""
        timeline = self.load_state('timeline.json')
        critical_events = [e for e in timeline.get('events', []) if e.get('severity') == 'CRITICAL']

        for event in critical_events[:3]:  # Top 3 critical
            self.create_incident(
                severity='HIGH',
                title=f"Sự kiện nghi ngờ: {event.get('type')}",
                assets=event.get('details', {}).get('ip', []) if isinstance(event.get('details', {}), dict) else [],
                evidence=[event.get('description')],
                recommended_action='Điều tra sự kiện',
                reason=event.get('type')
            )

    def detect_persistence_threats(self):
        """Phát hiện: Persistence threat indicators (Phase N.9A)"""
        persistence = self.load_state('hunting_persistence.json')

        for indicator in persistence.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"PERSISTENCE THREAT: {indicator.get('type')}",
                    assets=[],
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Điều tra persistence'),
                    reason=f"Persistence type: {indicator.get('type')}"
                )

    def detect_suspicious_processes(self):
        """Phát hiện: Suspicious process execution (Phase N.9A)"""
        processes = self.load_state('hunting_suspicious_processes.json')

        for indicator in processes.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"SUSPICIOUS PROCESS: {indicator.get('process')}",
                    assets=[],
                    evidence=[
                        f"Process: {indicator.get('process')}",
                        f"Command: {indicator.get('command_line')}"
                    ],
                    recommended_action=indicator.get('recommendation', 'Điều tra process'),
                    reason=f"Suspicious pattern: {indicator.get('category')}"
                )

    def detect_lateral_movement_threats(self):
        """Phát hiện: Lateral movement indicators (Phase N.9B)"""
        lateral = self.load_state('hunting_lateral_movement.json')

        for indicator in lateral.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"LATERAL MOVEMENT THREAT: {indicator.get('type')}",
                    assets=indicator.get('affected_assets', []),
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Điều tra lateral movement'),
                    reason=f"Lateral movement pattern: {indicator.get('type')}"
                )

    def detect_credential_dumping_threats(self):
        """Phát hiện: Credential dumping indicators (Phase N.9B)"""
        credential = self.load_state('hunting_credential_dumping.json')

        for indicator in credential.get('indicators', []):
            severity = indicator.get('severity', 'MEDIUM')
            if severity in ['CRITICAL', 'HIGH']:
                self.create_incident(
                    severity=severity,
                    title=f"CREDENTIAL DUMPING: {indicator.get('type')}",
                    assets=indicator.get('affected_systems', []),
                    evidence=indicator.get('evidence', []),
                    recommended_action=indicator.get('recommendation', 'Reset passwords ngay'),
                    reason=f"Credential threat: {indicator.get('type')}"
                )

    def generate(self):
        """Phát hiện tất cả incidents"""
        self.detect_defender_disabled()
        self.detect_firewall_disabled()
        self.detect_risk_escalation()
        self.detect_device_service_logon_anomaly()
        self.detect_weak_crypto_plus_waap_low()
        self.detect_system_resource_critical()
        self.detect_multiple_vulnerabilities()
        self.detect_suspicious_events()
        # Phase N.9A: Threat Hunting Integration
        self.detect_persistence_threats()
        self.detect_suspicious_processes()
        # Phase N.9B: Advanced Threat Hunting
        self.detect_lateral_movement_threats()
        self.detect_credential_dumping_threats()

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
            'question': 'Có sự cố gì cần xử lý?',
            'total_incidents': len(self.incidents),
            'by_severity': {},
            'by_status': {'OPEN': len(self.incidents)},
            'incidents': self.incidents
        }

        # Thống kê by severity
        for incident in self.incidents:
            severity = incident.get('severity', 'UNKNOWN')
            output['by_severity'][severity] = output['by_severity'].get(severity, 0) + 1

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
    engine = IncidentEngine()
    result = engine.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
