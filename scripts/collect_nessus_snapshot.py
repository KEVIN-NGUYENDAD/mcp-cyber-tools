#!/usr/bin/env python3
"""
NESSUS SNAPSHOT COLLECTOR
Integrates Nessus vulnerability scanner data into SentinelOps
Collects: Scanner status, Latest scan, Vulnerability counts
Outputs: state/nessus_status.json
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print('{"error": "requests library not installed. Install: pip install requests"}', file=sys.stderr)
    sys.exit(1)


class NessusCollector:
    def __init__(self):
        self.config_path = Path.home() / '.nessus' / 'api.json'
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'nessus_status.json'
        self.nessus_url = None
        self.api_key = None
        self.api_secret = None
        self.session = requests.Session()

    def load_config(self):
        """Load Nessus API credentials from ~/.nessus/api.json"""
        if not self.config_path.exists():
            return False

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.nessus_url = config.get('url', 'https://localhost:8834')
                self.api_key = config.get('api_key')
                self.api_secret = config.get('api_secret')
                return bool(self.api_key and self.api_secret)
        except Exception as e:
            print(f'{{"error": "Config load failed: {str(e)}"}}', file=sys.stderr)
            return False

    def set_auth_headers(self):
        """Configure session headers for Nessus API v2"""
        self.session.headers.update({
            'X-ApiKeys': f'accessKey={self.api_key}; secretKey={self.api_secret}',
            'Content-Type': 'application/json'
        })
        # Disable SSL verification for self-signed certs
        self.session.verify = False

    def get_scanner_status(self):
        """Get scanner status"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scanners', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get('scanners'):
                # Return status of first scanner
                status = data['scanners'][0].get('status', 'unknown')
                return 'running' if status == 'on' else 'ready'
            return 'unknown'
        except Exception as e:
            print(f'{{"error": "Scanner status query failed: {str(e)}"}}', file=sys.stderr)
            return 'error'

    def get_latest_scan(self):
        """Get latest scan results"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans', timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if not data.get('scans'):
                return None

            # Get most recent scan
            latest = sorted(data['scans'], key=lambda x: x.get('last_modification_date', 0), reverse=True)[0]

            scan_id = latest.get('id')
            scan_name = latest.get('name', 'Unknown')
            last_scan_time = latest.get('last_modification_date')

            # Get detailed scan results
            if scan_id:
                return self.get_scan_details(scan_id, last_scan_time, scan_name)
            return None

        except Exception as e:
            print(f'{{"error": "Latest scan query failed: {str(e)}"}}', file=sys.stderr)
            return None

    def get_scan_details(self, scan_id, timestamp, scan_name):
        """Get detailed vulnerability counts from scan"""
        try:
            # Try to get detailed scan info
            resp = self.session.get(
                f'{self.nessus_url}/scans/{scan_id}',
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract vulnerability info from vulnerabilities section
            vulns = data.get('vulnerabilities', [])

            critical = len([v for v in vulns if v.get('severity') == 3])
            high = len([v for v in vulns if v.get('severity') == 2])
            medium = len([v for v in vulns if v.get('severity') == 1])
            low = len([v for v in vulns if v.get('severity') == 0])
            info = len([v for v in vulns if v.get('severity') == -1])

            # Calculate scan age
            scan_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            age = (datetime.now() - scan_time).total_seconds() / 3600

            return {
                'last_scan': scan_time.isoformat(),
                'scan_name': scan_name,
                'scan_age_hours': round(age, 1),
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low,
                'info': info,
                'total': len(vulns)
            }

        except Exception as e:
            print(f'{{"error": "Scan details query failed: {str(e)}"}}', file=sys.stderr)
            return None

    def collect(self):
        """Main collection logic"""

        # Check if config exists
        if not self.load_config():
            output = {
                'error': 'Nessus API credentials not found',
                'required_file': str(self.config_path),
                'required_format': {
                    'url': 'https://nessus-host:8834',
                    'api_key': 'your-api-key',
                    'api_secret': 'your-api-secret'
                }
            }
            print(json.dumps(output, indent=2))
            return False

        # Set authentication
        self.set_auth_headers()

        # Collect data
        output = {
            'timestamp': datetime.now().isoformat(),
            'nessus_url': self.nessus_url
        }

        # Get scanner status
        status = self.get_scanner_status()
        output['scanner_status'] = status

        # Get latest scan
        scan_data = self.get_latest_scan()
        if scan_data:
            output.update(scan_data)
        else:
            output.update({
                'last_scan': None,
                'scan_age_hours': None,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
                'total': 0
            })

        return output

    def save(self, data):
        """Save snapshot to state/nessus_status.json"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f'{{"error": "Failed to save snapshot: {str(e)}"}}', file=sys.stderr)
            return False


def main():
    collector = NessusCollector()
    data = collector.collect()

    # Save to state file
    collector.save(data)

    # Output JSON
    print(json.dumps(data, indent=2))

    # Exit code (handle both dict and error cases)
    is_error = isinstance(data, dict) and 'error' in data
    sys.exit(1 if is_error else 0)


if __name__ == '__main__':
    main()
