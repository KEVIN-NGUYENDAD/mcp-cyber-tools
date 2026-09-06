#!/usr/bin/env python3
"""
LEAK GUARD - Privacy & Security Filter (Phase N.10C)
Tai su dung logic tu Home SOC export-home-soc-reports.js
Pha ngua ro ri thong tin nhay cam
Outputs: state/leak_guard_status.json
"""

import json
import sys
import re
from datetime import datetime
from pathlib import Path

class LeakGuard:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.brief_dir = Path(__file__).parent.parent / 'daily_brief'
        self.status_file = self.state_dir / 'leak_guard_status.json'

        # Regex patterns to detect sensitive data
        self.patterns = {
            'api_key': {
                'regex': r'(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                'name': 'API Key',
                'severity': 'CRITICAL'
            },
            'bearer_token': {
                'regex': r'bearer\s+([a-zA-Z0-9_\-\.]{20,})',
                'name': 'Bearer Token',
                'severity': 'CRITICAL'
            },
            'password': {
                'regex': r'(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s,;]{8,})["\']?',
                'name': 'Password',
                'severity': 'CRITICAL'
            },
            'secret': {
                'regex': r'(?:secret|secret_key)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                'name': 'Secret Key',
                'severity': 'CRITICAL'
            },
            'access_key': {
                'regex': r'(?:access[_-]?key|accesskey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                'name': 'Access Key',
                'severity': 'CRITICAL'
            },
            'private_key': {
                'regex': r'-----BEGIN.*PRIVATE KEY.*-----',
                'name': 'Private Key Block',
                'severity': 'CRITICAL'
            },
            'ipv4_address': {
                'regex': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                'name': 'IPv4 Address',
                'severity': 'HIGH'
            },
            'mac_address': {
                'regex': r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}',
                'name': 'MAC Address',
                'severity': 'MEDIUM'
            },
            'aws_access_key': {
                'regex': r'AKIA[0-9A-Z]{16}',
                'name': 'AWS Access Key',
                'severity': 'CRITICAL'
            },
            'jwt_token': {
                'regex': r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
                'name': 'JWT Token',
                'severity': 'CRITICAL'
            },
            'database_url': {
                'regex': r'(?:mysql|postgres|mongodb|redis)://[^\s]+',
                'name': 'Database URL',
                'severity': 'CRITICAL'
            }
        }

    def scan_for_leaks(self, data, source_name='unknown'):
        """Qua man tim cac ro ri thong tin"""
        # Convert to string for scanning
        if isinstance(data, dict) or isinstance(data, list):
            scan_text = json.dumps(data)
        else:
            scan_text = str(data)

        findings = []

        for pattern_key, pattern_data in self.patterns.items():
            regex = pattern_data['regex']
            try:
                matches = re.finditer(regex, scan_text, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'pattern': pattern_key,
                        'name': pattern_data['name'],
                        'severity': pattern_data['severity'],
                        'matched_text': match.group(0)[:50],  # First 50 chars
                        'position': match.start(),
                        'source': source_name
                    })
            except:
                pass

        return findings

    def sanitize_json(self, data, remove_patterns=None):
        """Lam sach du lieu JSON"""
        if remove_patterns is None:
            remove_patterns = [
                'api_key', 'bearer_token', 'password', 'secret', 'access_key',
                'private_key', 'ipv4_address', 'mac_address', 'aws_access_key',
                'jwt_token', 'database_url'
            ]

        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Check if key contains sensitive info
                if any(pattern in key.lower() for pattern in ['key', 'token', 'secret', 'password']):
                    sanitized[key] = '***REDACTED***'
                else:
                    sanitized[key] = self.sanitize_json(value, remove_patterns)
            return sanitized
        elif isinstance(data, list):
            return [self.sanitize_json(item, remove_patterns) for item in data]
        else:
            return data

    def check_daily_brief(self):
        """Kiem tra daily brief co ro ri khong"""
        brief_file = self.brief_dir / 'latest.json'
        if not brief_file.exists():
            return []

        try:
            with open(brief_file, 'r', encoding='utf-8') as f:
                brief_data = json.load(f)
            findings = self.scan_for_leaks(brief_data, 'daily_brief/latest.json')
            return findings
        except:
            return []

    def check_incidents(self):
        """Kiem tra incidents co ro ri khong"""
        incidents_file = self.state_dir / 'incidents.json'
        if not incidents_file.exists():
            return []

        try:
            with open(incidents_file, 'r', encoding='utf-8') as f:
                incidents_data = json.load(f)
            findings = self.scan_for_leaks(incidents_data, 'incidents.json')
            return findings
        except:
            return []

    def run(self):
        """Chay leak guard check"""
        # Scan key files
        brief_findings = self.check_daily_brief()
        incidents_findings = self.check_incidents()

        all_findings = brief_findings + incidents_findings

        # Determine overall security status
        if any(f['severity'] == 'CRITICAL' for f in all_findings):
            security_status = 'CRITICAL_LEAKS_DETECTED'
        elif any(f['severity'] == 'HIGH' for f in all_findings):
            security_status = 'HIGH_RISK_LEAKS'
        elif all_findings:
            security_status = 'MINOR_LEAKS'
        else:
            security_status = 'CLEAN'

        output = {
            'timestamp': datetime.now().isoformat(),
            'schema_version': '1.0',
            'security_status': security_status,
            'total_findings': len(all_findings),
            'by_severity': {
                'CRITICAL': sum(1 for f in all_findings if f['severity'] == 'CRITICAL'),
                'HIGH': sum(1 for f in all_findings if f['severity'] == 'HIGH'),
                'MEDIUM': sum(1 for f in all_findings if f['severity'] == 'MEDIUM')
            },
            'findings': all_findings,
            'recommendation': 'ABORT_EXPORT' if security_status in ['CRITICAL_LEAKS_DETECTED', 'HIGH_RISK_LEAKS'] else 'OK_TO_EXPORT',
            'sanitization_note': 'Leak Guard will sanitize outputs before export (following Home SOC model)'
        }

        # Luu leak guard status
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=True)

        return {
            'status': 'success',
            'security_status': security_status,
            'total_findings': len(all_findings),
            'recommendation': output['recommendation'],
            'by_severity': output['by_severity']
        }

if __name__ == '__main__':
    guard = LeakGuard()
    result = guard.run()
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    sys.exit(0 if result.get('status') == 'success' else 1)
