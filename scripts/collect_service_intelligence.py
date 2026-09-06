#!/usr/bin/env python3
"""
SERVICE INTELLIGENCE COLLECTOR (Phase N)
Extracts network services from Nessus vulnerability scan data
Populates: state/services.json

Inputs:
- Nessus API scan vulnerabilities with plugin families
- Nessus API host data with port information

Outputs:
- state/services.json (network services inventory)
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


class ServiceIntelligence:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.services_file = self.state_dir / 'services.json'
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

    def extract_services(self, scan_data):
        """Extract services from Nessus scan data"""
        services = {}
        services_by_host = defaultdict(list)
        service_counter = defaultdict(int)

        vulnerabilities = scan_data.get('vulnerabilities', [])

        for vuln in vulnerabilities:
            plugin_family = vuln.get('plugin_family', '')
            plugin_name = vuln.get('plugin_name', '')
            severity = vuln.get('severity', 'info')

            if not plugin_family:
                continue

            # Extract service type from plugin family
            service_type = self.classify_service(plugin_family, plugin_name)

            # Create service identifier
            service_id = f'{service_type}_{plugin_family}'.replace(' ', '_').lower()

            if service_id not in services:
                services[service_id] = {
                    'id': service_id,
                    'service_type': service_type,
                    'plugin_family': plugin_family,
                    'plugin_name': plugin_name,
                    'severity': severity,
                    'vulnerability_count': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat(),
                    'common_vulnerabilities': []
                }

            services[service_id]['vulnerability_count'] += 1
            services[service_id]['last_seen'] = datetime.now().isoformat()

            # Track top vulnerabilities
            if plugin_name and len(services[service_id]['common_vulnerabilities']) < 5:
                if plugin_name not in services[service_id]['common_vulnerabilities']:
                    services[service_id]['common_vulnerabilities'].append(plugin_name)

        return services

    def classify_service(self, plugin_family, plugin_name):
        """Classify service type based on plugin family"""
        family_lower = plugin_family.lower()

        # Web services
        if any(x in family_lower for x in ['http', 'web', 'nginx', 'apache', 'iis', 'tomcat', 'jetty']):
            return 'Web Server'

        # Mail services
        if any(x in family_lower for x in ['mail', 'smtp', 'pop', 'imap', 'exchange']):
            return 'Mail Service'

        # Database services
        if any(x in family_lower for x in ['database', 'sql', 'mysql', 'postgresql', 'oracle', 'mssql', 'mongodb']):
            return 'Database'

        # DNS services
        if any(x in family_lower for x in ['dns', 'bind', 'dnsmasq']):
            return 'DNS'

        # SSH/Remote access
        if any(x in family_lower for x in ['ssh', 'telnet', 'remote', 'rdp', 'vnc']):
            return 'Remote Access'

        # VPN services
        if any(x in family_lower for x in ['vpn', 'openvpn', 'wireguard', 'ipsec']):
            return 'VPN'

        # FTP services
        if any(x in family_lower for x in ['ftp', 'sftp', 'ftps']):
            return 'File Transfer'

        # NFS/SMB services
        if any(x in family_lower for x in ['smb', 'cifs', 'nfs', 'samba']):
            return 'File Share'

        # SNMP
        if 'snmp' in family_lower:
            return 'SNMP'

        # Directory services
        if any(x in family_lower for x in ['ldap', 'active directory', 'kerberos', 'nds']):
            return 'Directory Service'

        # Media services
        if any(x in family_lower for x in ['rtsp', 'upnp', 'dlna', 'media']):
            return 'Media Service'

        # Monitoring/Management
        if any(x in family_lower for x in ['snmp', 'nagios', 'zabbix', 'prometheus', 'splunk']):
            return 'Monitoring'

        # IoT services
        if any(x in family_lower for x in ['iot', 'mqtt', 'zigbee', 'z-wave']):
            return 'IoT Service'

        # Default to generic
        return 'Network Service'

    def save_services(self, services):
        """Save services inventory"""
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'total_services': len(services),
                'services': sorted(
                    services.values(),
                    key=lambda x: x['vulnerability_count'],
                    reverse=True
                )
            }
            with open(self.services_file, 'w') as f:
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

        # Extract services
        services = self.extract_services(scan_data)

        # Save results
        self.save_services(services)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_services': len(services),
            'top_services': [
                {
                    'service_type': s['service_type'],
                    'vulnerabilities': s['vulnerability_count']
                }
                for s in sorted(
                    services.values(),
                    key=lambda x: x['vulnerability_count'],
                    reverse=True
                )[:10]
            ]
        }


def main():
    collector = ServiceIntelligence()
    result = collector.collect()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
