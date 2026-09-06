#!/usr/bin/env python3
"""
ASSET INTELLIGENCE EXTRACTOR (Phase N)
Extracts device/host information from Nessus vulnerability scan data
Populates: state/assets.json

Inputs:
- Nessus API scan vulnerabilities
- Previous asset baseline (state/assets.json if exists)

Outputs:
- state/assets.json (device inventory with vulnerability summaries)
- state/asset_changes.json (new/removed/changed assets)
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


class AssetIntelligence:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.assets_file = self.state_dir / 'assets.json'
        self.changes_file = self.state_dir / 'asset_changes.json'
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
        except Exception as e:
            return None

    def get_scan_data(self, scan_id):
        """Get scan data including hosts and vulnerabilities"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {}

    def get_scan_vulnerabilities(self, scan_id):
        """Get detailed vulnerability data including asset/service info"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('vulnerabilities', [])
        except Exception as e:
            return []

    def classify_device_type(self, os_info):
        """Auto-classify device based on OS"""
        if not os_info:
            return "Unknown"

        os_lower = os_info.lower()

        if 'router' in os_lower or 'network' in os_lower:
            return "Router"
        elif 'windows' in os_lower:
            if 'server' in os_lower:
                return "Server"
            return "Workstation"
        elif 'linux' in os_lower or 'ubuntu' in os_lower or 'debian' in os_lower:
            if 'server' in os_lower:
                return "Server"
            return "Workstation"
        elif 'mac' in os_lower or 'darwin' in os_lower:
            return "Workstation"
        elif 'ios' in os_lower or 'android' in os_lower:
            return "Mobile Device"
        elif 'printer' in os_lower or 'xerox' in os_lower or 'canon' in os_lower:
            return "Printer"
        elif 'iot' in os_lower or 'embedded' in os_lower or 'camera' in os_lower:
            return "IoT Device"

        return "Unknown"

    def extract_assets(self, scan_data):
        """Extract unique assets from scan host data"""
        assets_by_ip = {}

        # Extract from host-level data in scan response
        hosts = scan_data.get('hosts', [])

        for host in hosts:
            ip = host.get('hostname', '')  # In Nessus API, hostname field contains IP

            if not ip:
                continue

            # Get vulnerability counts from host data
            assets_by_ip[ip] = {
                'ip': ip,
                'hostname': ip,  # Default to IP; could be enriched with reverse DNS
                'os': '',  # Not available in simple host data
                'device_type': 'Unknown',
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'vulnerability_count': 0,
                'critical': host.get('critical', 0),
                'high': host.get('high', 0),
                'medium': host.get('medium', 0),
                'low': host.get('low', 0),
                'info': host.get('info', 0)
            }

            # Calculate total vulnerability count
            assets_by_ip[ip]['vulnerability_count'] = (
                host.get('critical', 0) +
                host.get('high', 0) +
                host.get('medium', 0) +
                host.get('low', 0) +
                host.get('info', 0)
            )

        # If we don't have hosts from host-level data, try to extract from vulnerabilities
        if not assets_by_ip:
            vulnerabilities = scan_data.get('vulnerabilities', [])
            for vuln in vulnerabilities:
                # Basic extraction without asset field
                # This is fallback data
                pass

        # Assign device types (without OS data, default to Unknown)
        for ip, asset in assets_by_ip.items():
            asset['device_type'] = self.classify_device_type(asset['os'])

        return assets_by_ip

    def load_previous_assets(self):
        """Load previous asset baseline for change detection"""
        if self.assets_file.exists():
            try:
                with open(self.assets_file, 'r') as f:
                    data = json.load(f)
                    return {a['ip']: a for a in data.get('assets', [])}
            except Exception:
                return {}
        return {}

    def detect_changes(self, current_assets, previous_assets):
        """Detect new/removed/changed assets"""
        changes = {
            'timestamp': datetime.now().isoformat(),
            'new_assets': [],
            'removed_assets': [],
            'changed_assets': [],
            'unchanged_assets': []
        }

        current_ips = set(current_assets.keys())
        previous_ips = set(previous_assets.keys())

        # New assets
        for ip in current_ips - previous_ips:
            changes['new_assets'].append({
                'ip': ip,
                'hostname': current_assets[ip]['hostname'],
                'device_type': current_assets[ip]['device_type']
            })

        # Removed assets
        for ip in previous_ips - current_ips:
            changes['removed_assets'].append({
                'ip': ip,
                'hostname': previous_assets[ip]['hostname'],
                'device_type': previous_assets[ip]['device_type']
            })

        # Changed assets (vulnerability count changes)
        for ip in current_ips & previous_ips:
            if current_assets[ip]['vulnerability_count'] != previous_assets[ip]['vulnerability_count']:
                changes['changed_assets'].append({
                    'ip': ip,
                    'hostname': current_assets[ip]['hostname'],
                    'previous_count': previous_assets[ip]['vulnerability_count'],
                    'current_count': current_assets[ip]['vulnerability_count']
                })
            else:
                changes['unchanged_assets'].append(ip)

        return changes

    def save_assets(self, assets):
        """Save asset inventory to state/assets.json"""
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'total_assets': len(assets),
                'assets': sorted(assets.values(), key=lambda x: x['ip'])
            }
            with open(self.assets_file, 'w') as f:
                json.dump(output, f, indent=2)
            return True
        except Exception as e:
            return False

    def save_changes(self, changes):
        """Save change detection results"""
        try:
            with open(self.changes_file, 'w') as f:
                json.dump(changes, f, indent=2)
            return True
        except Exception as e:
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

        # Get scan data which includes hosts and vulnerabilities
        scan_data = self.get_scan_data(scan_id)

        if not scan_data:
            return {
                'error': 'No scan data found',
                'warning': 'Failed to retrieve scan data'
            }

        # Extract assets from scan data
        current_assets = self.extract_assets(scan_data)
        previous_assets = self.load_previous_assets()

        # Detect changes
        changes = self.detect_changes(current_assets, previous_assets)

        # Save results
        self.save_assets(current_assets)
        self.save_changes(changes)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_assets': len(current_assets),
            'new_assets': len(changes['new_assets']),
            'removed_assets': len(changes['removed_assets']),
            'changed_assets': len(changes['changed_assets'])
        }


def main():
    extractor = AssetIntelligence()
    result = extractor.extract()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
