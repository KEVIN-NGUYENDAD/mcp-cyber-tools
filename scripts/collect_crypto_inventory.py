#!/usr/bin/env python3
"""
CRYPTO INVENTORY COLLECTOR (Phase N)
Analyzes cryptographic material and practices in vulnerability data
Populates: state/crypto_inventory.json

Inputs:
- Nessus API vulnerability data
- Nessus API scan results

Outputs:
- state/crypto_inventory.json (crypto findings and risk assessment)
"""

import json
import sys
import os
from datetime import datetime
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


class CryptoInventory:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.crypto_file = self.state_dir / 'crypto_inventory.json'
        self.nessus_url = None
        self.access_key = None
        self.secret_key = None
        self.session = requests.Session()
        self.session.verify = False
        self.load_env()

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

    def find_scan_by_name(self, target_name='Home Network Discovery'):
        """Find scan by name"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            scans = data.get('scans', [])
            for scan in scans:
                if scan.get('name') == target_name:
                    return scan.get('id')
            return None
        except Exception:
            return None

    def get_latest_scan_id(self):
        """Get latest scan ID"""
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

    def get_scan_data(self, scan_id):
        """Get scan data"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {}

    def analyze_crypto(self, scan_data):
        """Analyze cryptographic findings in scan data"""
        findings = []
        severity_counts = defaultdict(int)

        vulnerabilities = scan_data.get('vulnerabilities', [])

        crypto_keywords = {
            'SSL': ['ssl', 'tls', 'certificate', 'cipher', 'https'],
            'Encryption': ['encryption', 'encrypted', 'encrypt', 'decrypt', 'crypto'],
            'Keys': ['private key', 'public key', 'key management', 'key exchange', 'pki'],
            'Hash': ['hash', 'md5', 'sha1', 'sha256', 'checksum', 'digest'],
            'Authentication': ['authentication', 'oauth', 'saml', 'jwt', 'mfa', 'two-factor'],
            'Password': ['password', 'passphrase', 'credential', 'secret', 'token'],
            'Weak Crypto': ['weak', 'deprecated', 'obsolete', 'insecure', 'vulnerable', 'rc4', 'des', 'md5']
        }

        for vuln in vulnerabilities:
            plugin_family = vuln.get('plugin_family', '')
            plugin_name = vuln.get('plugin_name', '')
            severity = vuln.get('severity', 'info')

            name_lower = plugin_name.lower() if plugin_name else ''
            family_lower = plugin_family.lower()

            # Check if this is a crypto-related vulnerability
            is_crypto = False
            crypto_category = None

            for category, keywords in crypto_keywords.items():
                if any(keyword in family_lower or keyword in name_lower for keyword in keywords):
                    is_crypto = True
                    crypto_category = category
                    break

            if is_crypto:
                severity_counts[severity] += 1
                findings.append({
                    'category': crypto_category,
                    'plugin_name': plugin_name,
                    'plugin_family': plugin_family,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                })

        # Calculate crypto score
        critical_count = severity_counts.get('CRITICAL', 0)
        high_count = severity_counts.get('HIGH', 0)
        medium_count = severity_counts.get('MEDIUM', 0)

        # Scoring: Start at 100, deduct based on findings
        crypto_score = 100
        crypto_score -= critical_count * 20  # Critical -20 each
        crypto_score -= high_count * 10      # High -10 each
        crypto_score -= medium_count * 5     # Medium -5 each
        crypto_score = max(0, crypto_score)

        return {
            'findings': findings,
            'score': crypto_score,
            'severity_breakdown': {
                'CRITICAL': critical_count,
                'HIGH': high_count,
                'MEDIUM': medium_count,
                'LOW': severity_counts.get('LOW', 0),
                'INFO': severity_counts.get('INFO', 0)
            }
        }

    def save_crypto_inventory(self, analysis):
        """Save crypto inventory"""
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'score': analysis['score'],
                'severity_breakdown': analysis['severity_breakdown'],
                'total_findings': len(analysis['findings']),
                'findings': analysis['findings'][:50]  # Top 50 findings
            }
            with open(self.crypto_file, 'w') as f:
                json.dump(output, f, indent=2)
            return True
        except Exception:
            return False

    def collect(self):
        """Main collection logic"""
        if not self.load_credentials():
            return {
                'error': 'Nessus API credentials not found',
                'solution': 'Create or update .env file in project root'
            }

        self.set_auth_headers()

        # Find scan
        scan_id = self.find_scan_by_name('Home Network Discovery')
        if not scan_id:
            scan_id = self.get_latest_scan_id()

        if not scan_id:
            return {
                'error': 'No scans found in Nessus',
                'solution': 'Run a vulnerability scan first'
            }

        # Get scan data
        scan_data = self.get_scan_data(scan_id)
        if not scan_data:
            return {
                'error': 'No scan data found'
            }

        # Analyze crypto
        analysis = self.analyze_crypto(scan_data)

        # Save results
        self.save_crypto_inventory(analysis)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'crypto_score': analysis['score'],
            'critical_findings': analysis['severity_breakdown']['CRITICAL'],
            'total_findings': len(analysis['findings'])
        }


def main():
    collector = CryptoInventory()
    result = collector.collect()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
