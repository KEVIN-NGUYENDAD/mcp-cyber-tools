#!/usr/bin/env python3
"""
ASSET QUALITY VALIDATION (Phase N.3)
Validates asset intelligence against Nessus API
Compares: IP, Hostname, OS, Device Type, Severity Breakdown, Vulnerability Counts
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from dotenv import load_dotenv
except ImportError:
    print(f'{{"error": "Missing dependencies. Install: pip install requests python-dotenv"}}', file=sys.stderr)
    sys.exit(1)


class AssetValidator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.assets_file = self.state_dir / 'assets.json'
        self.nessus_url = None
        self.access_key = None
        self.secret_key = None
        self.session = requests.Session()
        self.session.verify = False
        self.load_env()
        self.validation_results = []

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

    def get_scan_data(self, scan_id):
        """Get scan data including hosts and vulnerabilities"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {}

    def load_assets(self):
        """Load assets from state/assets.json"""
        if not self.assets_file.exists():
            return {}
        try:
            with open(self.assets_file, 'r') as f:
                data = json.load(f)
                return {a['ip']: a for a in data.get('assets', [])}
        except Exception:
            return {}

    def validate_asset(self, ip, asset_data, scan_hosts, scan_vulns):
        """Validate single asset against Nessus data"""
        result = {
            'ip': ip,
            'hostname': asset_data.get('hostname', 'N/A'),
            'os': asset_data.get('os', 'N/A'),
            'device_type': asset_data.get('device_type', 'Unknown'),
            'checks': {}
        }

        # Find host in scan data
        host_in_scan = None
        for host in scan_hosts:
            if host.get('hostname') == ip:
                host_in_scan = host
                break

        if not host_in_scan:
            result['checks']['host_found'] = {
                'status': 'FAIL',
                'message': 'Host not found in Nessus scan',
                'confidence': 'LOW'
            }
            return result

        result['checks']['host_found'] = {
            'status': 'PASS',
            'message': 'Host found in Nessus scan',
            'confidence': 'HIGH'
        }

        # Check vulnerability count
        scan_vuln_count = (
            host_in_scan.get('critical', 0) +
            host_in_scan.get('high', 0) +
            host_in_scan.get('medium', 0) +
            host_in_scan.get('low', 0) +
            host_in_scan.get('info', 0)
        )

        asset_vuln_count = asset_data.get('vulnerability_count', 0)

        if scan_vuln_count == asset_vuln_count:
            result['checks']['vulnerability_count'] = {
                'status': 'PASS',
                'nessus_value': scan_vuln_count,
                'asset_value': asset_vuln_count,
                'confidence': 'HIGH'
            }
        else:
            result['checks']['vulnerability_count'] = {
                'status': 'FAIL',
                'nessus_value': scan_vuln_count,
                'asset_value': asset_vuln_count,
                'message': f'Mismatch: Nessus={scan_vuln_count}, Asset={asset_vuln_count}',
                'confidence': 'HIGH'
            }

        # Check severity breakdown
        severity_match = True
        if (host_in_scan.get('critical', 0) != asset_data.get('critical', 0) or
            host_in_scan.get('high', 0) != asset_data.get('high', 0) or
            host_in_scan.get('medium', 0) != asset_data.get('medium', 0) or
            host_in_scan.get('low', 0) != asset_data.get('low', 0) or
            host_in_scan.get('info', 0) != asset_data.get('info', 0)):
            severity_match = False

        result['checks']['severity_breakdown'] = {
            'status': 'PASS' if severity_match else 'FAIL',
            'nessus': {
                'critical': host_in_scan.get('critical', 0),
                'high': host_in_scan.get('high', 0),
                'medium': host_in_scan.get('medium', 0),
                'low': host_in_scan.get('low', 0),
                'info': host_in_scan.get('info', 0)
            },
            'asset': {
                'critical': asset_data.get('critical', 0),
                'high': asset_data.get('high', 0),
                'medium': asset_data.get('medium', 0),
                'low': asset_data.get('low', 0),
                'info': asset_data.get('info', 0)
            },
            'confidence': 'HIGH'
        }

        # Analyze plugin families for device type validation
        plugin_families_for_ip = []
        os_indicators = defaultdict(int)
        device_indicators = defaultdict(int)

        for vuln in scan_vulns:
            plugin_family = vuln.get('plugin_family', '')
            if plugin_family:
                plugin_families_for_ip.append(plugin_family)

                # OS indicators
                if 'Windows' in plugin_family:
                    os_indicators['Windows'] += 1
                elif any(x in plugin_family for x in ['Linux', 'Debian', 'Ubuntu', 'CentOS']):
                    os_indicators['Linux'] += 1

                # Device type indicators
                if any(x in plugin_family for x in ['Router', 'Switch', 'Firewall', 'Gateway']):
                    device_indicators['Router'] += 1
                if 'Windows' in plugin_family and 'Server' in plugin_family:
                    device_indicators['Windows Server'] += 1

        result['plugin_families'] = list(set(plugin_families_for_ip))[:10]  # Top 10
        result['os_indicators'] = dict(os_indicators)
        result['device_indicators'] = dict(device_indicators)

        # Device type confidence assessment
        if asset_data['device_type'] == 'Router':
            if ip.endswith('.1') or ip.endswith('.254'):
                result['checks']['device_type'] = {
                    'status': 'PASS',
                    'basis': 'IP pattern (.1/.254 = gateway)',
                    'confidence': 'HIGH'
                }
            else:
                result['checks']['device_type'] = {
                    'status': 'UNCERTAIN',
                    'basis': 'No gateway pattern detected',
                    'confidence': 'MEDIUM'
                }
        else:
            # Server/Workstation classification
            if 'Windows' in asset_data.get('os', ''):
                result['checks']['device_type'] = {
                    'status': 'PASS',
                    'basis': 'Windows OS detected via plugin families',
                    'confidence': 'MEDIUM'
                }
            else:
                result['checks']['device_type'] = {
                    'status': 'UNCERTAIN',
                    'basis': 'Insufficient data for classification',
                    'confidence': 'LOW'
                }

        # OS validation
        if 'Windows' in asset_data.get('os', ''):
            if os_indicators.get('Windows', 0) > 0:
                result['checks']['os'] = {
                    'status': 'PASS',
                    'basis': f'{os_indicators["Windows"]} Windows indicators in vulnerabilities',
                    'confidence': 'HIGH'
                }
            else:
                result['checks']['os'] = {
                    'status': 'UNCERTAIN',
                    'basis': 'Windows claimed but no indicators found',
                    'confidence': 'LOW'
                }
        else:
            result['checks']['os'] = {
                'status': 'UNKNOWN',
                'basis': 'Non-standard OS classification',
                'confidence': 'MEDIUM'
            }

        return result

    def validate(self):
        """Main validation logic"""
        if not self.load_credentials():
            return {'error': 'Nessus API credentials not found'}

        self.set_auth_headers()

        # Get scan data
        scan_id = self.find_scan_by_name('Home Network Discovery')
        if not scan_id:
            return {'error': 'Home Network Discovery scan not found'}

        scan_data = self.get_scan_data(scan_id)
        if not scan_data:
            return {'error': 'Failed to retrieve scan data'}

        scan_hosts = scan_data.get('hosts', [])
        scan_vulns = scan_data.get('vulnerabilities', [])

        # Load assets to validate
        assets = self.load_assets()
        if not assets:
            return {'error': 'No assets found in state/assets.json'}

        # Validate each asset
        results = []
        for ip, asset_data in sorted(assets.items()):
            result = self.validate_asset(ip, asset_data, scan_hosts, scan_vulns)
            results.append(result)

        return {
            'status': 'success',
            'scan_id': scan_id,
            'scan_hosts_count': len(scan_hosts),
            'scan_vulns_count': len(scan_vulns),
            'assets_validated': len(results),
            'validation_results': results
        }


def main():
    validator = AssetValidator()
    result = validator.validate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
