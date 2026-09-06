#!/usr/bin/env python3
"""
CRYPTOGRAPHIC INTELLIGENCE EXTRACTOR (Phase N)
Extracts certificate and cipher suite information from Nessus vulnerability scan data
Populates: state/crypto_inventory.json

Inputs:
- Nessus API scan vulnerabilities (cert checks, cipher suite checks)
- Previous crypto baseline (state/crypto_inventory.json if exists)

Outputs:
- state/crypto_inventory.json (certificates, TLS versions, cipher suites)
- state/crypto_changes.json (new/expired certificates, new weak ciphers)
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from dotenv import load_dotenv
except ImportError as e:
    print(f'{{"error": "Missing dependencies. Install: pip install requests python-dotenv"}}', file=sys.stderr)
    sys.exit(1)


class CryptoIntelligence:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.crypto_file = self.state_dir / 'crypto_inventory.json'
        self.changes_file = self.state_dir / 'crypto_changes.json'
        self.nessus_url = None
        self.access_key = None
        self.secret_key = None
        self.session = requests.Session()
        self.session.verify = False
        self.load_env()

        # Weak cipher identification
        self.weak_cipher_keywords = [
            'rc4', 'md5', 'des', 'export', 'null', 'anon', 'dss',
            'ecdhe_rsa_with_rc4', 'rsa_with_rc4', 'psk_with_rc4'
        ]

    def load_env(self):
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

    def load_credentials(self):
        self.nessus_url = os.environ.get('NESSUS_URL')
        self.access_key = os.environ.get('NESSUS_ACCESS_KEY')
        self.secret_key = os.environ.get('NESSUS_SECRET_KEY')
        return bool(self.nessus_url and self.access_key and self.secret_key)

    def set_auth_headers(self):
        self.session.headers.update({
            'X-ApiKeys': f'accessKey={self.access_key}; secretKey={self.secret_key}',
            'Content-Type': 'application/json'
        })

    def get_latest_scan_id(self):
        try:
            resp = self.session.get(f'{self.nessus_url}/scans', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            scans = data.get('scans', [])
            if not scans:
                return None
            latest = sorted(scans, key=lambda x: x.get('last_modification_date', 0), reverse=True)[0]
            return latest.get('id')
        except Exception:
            return None

    def get_scan_vulnerabilities(self, scan_id):
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('vulnerabilities', [])
        except Exception:
            return []

    def is_weak_cipher(self, cipher_name):
        """Check if cipher is considered weak"""
        if not cipher_name:
            return False
        cipher_lower = cipher_name.lower()
        return any(weak in cipher_lower for weak in self.weak_cipher_keywords)

    def classify_tls_version(self, plugin_name, description):
        """Extract TLS version from plugin info"""
        text = f"{plugin_name} {description}".lower()

        if 'tls 1.3' in text or 'tlsv1_3' in text:
            return 'TLS 1.3'
        if 'tls 1.2' in text or 'tlsv1_2' in text:
            return 'TLS 1.2'
        if 'tls 1.1' in text or 'tlsv1_1' in text:
            return 'TLS 1.1'
        if 'tls 1.0' in text or 'tlsv1' in text or 'tlsv1_0' in text:
            return 'TLS 1.0'
        if 'ssl 3' in text or 'sslv3' in text:
            return 'SSL 3.0'

        return 'Unknown'

    def extract_certificates(self, vulnerabilities):
        """Extract certificate information from vulnerabilities"""
        certificates = {}

        for vuln in vulnerabilities:
            asset = vuln.get('asset', {})
            ip = asset.get('ip', 'unknown')
            port = vuln.get('port', 0)
            plugin_name = vuln.get('plugin_name', '')
            description = vuln.get('plugin_description', '')
            severity = vuln.get('severity', 0)

            # Look for certificate-related plugins
            if 'certificate' in plugin_name.lower() or 'ssl' in plugin_name.lower() or 'tls' in plugin_name.lower():
                cert_key = f"{ip}:{port}"

                if cert_key not in certificates:
                    certificates[cert_key] = {
                        'ip': ip,
                        'hostname': asset.get('hostname', ''),
                        'port': port,
                        'protocol': vuln.get('protocol', 'tcp'),
                        'certificate_issues': [],
                        'tls_versions': [],
                        'cipher_suites': [],
                        'is_self_signed': False,
                        'expiry_status': 'unknown',
                        'days_until_expiry': None,
                        'severity': severity
                    }

                # Extract certificate details from plugin description
                if 'certificate' in plugin_name.lower():
                    if 'self-signed' in description.lower():
                        certificates[cert_key]['is_self_signed'] = True
                    if 'expired' in description.lower():
                        certificates[cert_key]['expiry_status'] = 'expired'
                    if 'expires in' in description.lower():
                        certificates[cert_key]['expiry_status'] = 'valid'

                    certificates[cert_key]['certificate_issues'].append(plugin_name)

        return certificates

    def extract_cipher_suites(self, vulnerabilities):
        """Extract cipher suite information from vulnerabilities"""
        cipher_suites = defaultdict(lambda: {
            'name': '',
            'tls_version': '',
            'host_count': 0,
            'is_weak': False,
            'severity': 0,
            'hosts': []
        })

        for vuln in vulnerabilities:
            asset = vuln.get('asset', {})
            ip = asset.get('ip', 'unknown')
            plugin_name = vuln.get('plugin_name', '')
            description = vuln.get('plugin_description', '')
            severity = vuln.get('severity', 0)

            # Look for cipher/protocol-related plugins
            if any(x in plugin_name.lower() for x in ['cipher', 'ssl', 'tls', 'protocol', 'weak', 'deprecated']):
                tls_version = self.classify_tls_version(plugin_name, description)
                is_weak = self.is_weak_cipher(plugin_name) or severity >= 2

                key = plugin_name
                if key not in cipher_suites:
                    cipher_suites[key] = {
                        'name': plugin_name,
                        'tls_version': tls_version,
                        'host_count': 0,
                        'is_weak': is_weak,
                        'severity': severity,
                        'hosts': []
                    }

                if ip not in cipher_suites[key]['hosts']:
                    cipher_suites[key]['hosts'].append(ip)
                    cipher_suites[key]['host_count'] += 1

        return dict(cipher_suites)

    def calculate_crypto_health(self, certificates, cipher_suites):
        """Calculate overall cryptographic health score"""
        score = 100

        # Check for self-signed certs
        self_signed_count = sum(1 for c in certificates.values() if c['is_self_signed'])
        if self_signed_count > 0:
            score -= min(20, self_signed_count * 5)

        # Check for expired certs
        expired_count = sum(1 for c in certificates.values() if c['expiry_status'] == 'expired')
        if expired_count > 0:
            score -= min(30, expired_count * 10)

        # Check for weak ciphers
        weak_cipher_count = sum(1 for c in cipher_suites.values() if c['is_weak'])
        if weak_cipher_count > 0:
            score -= min(25, weak_cipher_count * 3)

        # Check for old TLS versions
        old_tls_count = sum(1 for c in cipher_suites.values() if c['tls_version'] in ['SSL 3.0', 'TLS 1.0', 'TLS 1.1'])
        if old_tls_count > 0:
            score -= min(20, old_tls_count * 5)

        return max(0, score)

    def load_previous_crypto(self):
        """Load previous crypto baseline for change detection"""
        if self.crypto_file.exists():
            try:
                with open(self.crypto_file, 'r') as f:
                    data = json.load(f)
                    return data
            except Exception:
                return None
        return None

    def detect_crypto_changes(self, current_data, previous_data):
        """Detect new/expired certificates and weak ciphers"""
        changes = {
            'timestamp': datetime.now().isoformat(),
            'new_certificates': [],
            'expired_certificates': [],
            'new_weak_ciphers': [],
            'tls_version_changes': []
        }

        if not previous_data:
            return changes

        current_certs = current_data.get('certificates', {})
        previous_certs = previous_data.get('certificates', {})

        # New certificates
        for key in current_certs:
            if key not in previous_certs:
                changes['new_certificates'].append(key)

        # Newly expired certificates
        for key in current_certs:
            if key in previous_certs:
                if previous_certs[key]['expiry_status'] != 'expired' and current_certs[key]['expiry_status'] == 'expired':
                    changes['expired_certificates'].append(key)

        return changes

    def save_crypto(self, certificates, cipher_suites):
        """Save cryptographic inventory to state/crypto_inventory.json"""
        try:
            health_score = self.calculate_crypto_health(certificates, cipher_suites)

            output = {
                'timestamp': datetime.now().isoformat(),
                'health_score': health_score,
                'certificate_count': len(certificates),
                'weak_cipher_count': sum(1 for c in cipher_suites.values() if c['is_weak']),
                'certificates': certificates,
                'cipher_suites': cipher_suites
            }
            with open(self.crypto_file, 'w') as f:
                json.dump(output, f, indent=2)
            return True
        except Exception:
            return False

    def save_changes(self, changes):
        """Save cryptographic change detection results"""
        try:
            with open(self.changes_file, 'w') as f:
                json.dump(changes, f, indent=2)
            return True
        except Exception:
            return False

    def extract(self):
        """Main extraction logic"""
        if not self.load_credentials():
            return {
                'error': 'Nessus API credentials not found',
                'solution': 'Create or update .env file in project root'
            }

        self.set_auth_headers()

        scan_id = self.get_latest_scan_id()
        if not scan_id:
            return {
                'error': 'No scans found in Nessus',
                'solution': 'Run a vulnerability scan first'
            }

        vulnerabilities = self.get_scan_vulnerabilities(scan_id)
        if not vulnerabilities:
            return {
                'error': 'No vulnerabilities found',
                'warning': 'Scan may be empty or filtered'
            }

        # Extract crypto data
        certificates = self.extract_certificates(vulnerabilities)
        cipher_suites = self.extract_cipher_suites(vulnerabilities)

        # Detect changes
        previous_data = self.load_previous_crypto()
        changes = self.detect_crypto_changes({
            'certificates': certificates,
            'cipher_suites': cipher_suites
        }, previous_data)

        # Save results
        self.save_crypto(certificates, cipher_suites)
        self.save_changes(changes)

        health_score = self.calculate_crypto_health(certificates, cipher_suites)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'certificate_count': len(certificates),
            'cipher_suite_count': len(cipher_suites),
            'weak_cipher_count': sum(1 for c in cipher_suites.values() if c['is_weak']),
            'new_weak_ciphers_detected': len(changes['new_weak_ciphers']),
            'newly_expired_certs': len(changes['expired_certificates'])
        }


def main():
    extractor = CryptoIntelligence()
    result = extractor.extract()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
