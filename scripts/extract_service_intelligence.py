#!/usr/bin/env python3
"""
SERVICE INTELLIGENCE EXTRACTOR (Phase N)
Extracts port/service information from Nessus vulnerability scan data
Populates: state/services.json

Inputs:
- Nessus API scan vulnerabilities
- Previous service baseline (state/services.json if exists)

Outputs:
- state/services.json (port/service inventory)
- state/service_changes.json (new/closed ports and services)
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
        self.changes_file = self.state_dir / 'service_changes.json'
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
        except Exception:
            return None

    def get_scan_data(self, scan_id):
        """Get full scan data including hosts and vulnerabilities"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {}

    def get_scan_vulnerabilities(self, scan_id):
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('vulnerabilities', [])
        except Exception:
            return []

    def identify_service_name(self, port, protocol, plugin_name):
        """Identify service name from port and plugin info"""
        common_services = {
            22: 'SSH',
            80: 'HTTP',
            443: 'HTTPS',
            25: 'SMTP',
            53: 'DNS',
            110: 'POP3',
            143: 'IMAP',
            445: 'SMB',
            3306: 'MySQL',
            3389: 'RDP',
            5432: 'PostgreSQL',
            5984: 'CouchDB',
            6379: 'Redis',
            27017: 'MongoDB',
            9200: 'Elasticsearch',
            8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt',
            8834: 'Nessus',
            8888: 'HTTP-Custom'
        }

        if isinstance(port, int) and port in common_services:
            return common_services[port]

        if plugin_name:
            plugin_lower = plugin_name.lower()
            if 'ssh' in plugin_lower:
                return 'SSH'
            if 'http' in plugin_lower or 'web' in plugin_lower:
                return 'HTTP/HTTPS'
            if 'smtp' in plugin_lower:
                return 'SMTP'
            if 'dns' in plugin_lower:
                return 'DNS'
            if 'smb' in plugin_lower or 'samba' in plugin_lower:
                return 'SMB'
            if 'mysql' in plugin_lower or 'database' in plugin_lower:
                return 'Database'
            if 'rdp' in plugin_lower or 'remote desktop' in plugin_lower:
                return 'RDP'

        return f'Service({port})'

    def extract_services(self, scan_data):
        """Extract services from plugin vulnerabilities"""
        services_by_key = {}
        service_global_stats = defaultdict(lambda: {
            'name': '',
            'port_count': 0,
            'host_count': 0,
            'finding_count': 0,
            'severity_critical': 0,
            'severity_high': 0,
            'severity_medium': 0,
            'severity_low': 0,
            'severity_info': 0,
            'hosts': []
        })

        vulnerabilities = scan_data.get('vulnerabilities', [])
        hosts = scan_data.get('hosts', [])

        # Build IP to hostname mapping
        ip_to_host = {}
        for host in hosts:
            ip = host.get('hostname', '')
            if ip:
                ip_to_host[ip] = host

        # Extract services from vulnerability plugin families and names
        for vuln in vulnerabilities:
            plugin_name = vuln.get('plugin_name', '')
            plugin_family = vuln.get('plugin_family', '')
            severity = vuln.get('severity', 0)

            # Identify service from plugin family/name
            service_name = self.identify_service_name(0, 'tcp', plugin_name)
            if service_name == 'Service(0)' and plugin_family:
                # Use plugin family as fallback
                service_name = plugin_family

            # Use all hosts for this service (plugin affects all scanned hosts)
            for ip, host in ip_to_host.items():
                service_key = f"{ip}:*:{service_name.lower()}"

                if service_key not in services_by_key:
                    services_by_key[service_key] = {
                        'ip': ip,
                        'hostname': ip,
                        'port': 0,
                        'protocol': 'tcp',
                        'service_name': service_name,
                        'finding_count': 0,
                        'critical': 0,
                        'high': 0,
                        'medium': 0,
                        'low': 0,
                        'info': 0,
                        'last_seen': datetime.now().isoformat()
                    }

                services_by_key[service_key]['finding_count'] += 1
                services_by_key[service_key]['last_seen'] = datetime.now().isoformat()

                # Count severity
                if severity == 4:
                    services_by_key[service_key]['critical'] += 1
                elif severity == 3:
                    services_by_key[service_key]['high'] += 1
                elif severity == 2:
                    services_by_key[service_key]['medium'] += 1
                elif severity == 1:
                    services_by_key[service_key]['low'] += 1
                else:
                    services_by_key[service_key]['info'] += 1

            # Global service stats
            global_key = service_name
            if service_global_stats[global_key]['name'] == '':
                service_global_stats[global_key]['name'] = service_name

            service_global_stats[global_key]['finding_count'] += 1
            if severity == 4:
                service_global_stats[global_key]['severity_critical'] += 1
            elif severity == 3:
                service_global_stats[global_key]['severity_high'] += 1
            elif severity == 2:
                service_global_stats[global_key]['severity_medium'] += 1
            elif severity == 1:
                service_global_stats[global_key]['severity_low'] += 1
            else:
                service_global_stats[global_key]['severity_info'] += 1

            # Add all hosts to this service
            for ip in ip_to_host.keys():
                if ip not in service_global_stats[global_key]['hosts']:
                    service_global_stats[global_key]['hosts'].append(ip)

            service_global_stats[global_key]['host_count'] = len(service_global_stats[global_key]['hosts'])

        return {
            'services_by_host': dict(services_by_key),
            'service_inventory': dict(service_global_stats)
        }

    def load_previous_services(self):
        """Load previous service baseline for change detection"""
        if self.services_file.exists():
            try:
                with open(self.services_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('services_by_host', {}).keys())
            except Exception:
                return set()
        return set()

    def detect_service_changes(self, current_services, previous_services):
        """Detect new/closed ports and services"""
        current_keys = set(current_services.keys())

        changes = {
            'timestamp': datetime.now().isoformat(),
            'new_services': [],
            'closed_services': [],
            'unchanged_count': 0
        }

        # New services
        for key in current_keys - previous_services:
            svc = current_services[key]
            changes['new_services'].append({
                'ip': svc['ip'],
                'port': svc['port'],
                'protocol': svc['protocol'],
                'service': svc['service_name']
            })

        # Closed services
        for key in previous_services - current_keys:
            changes['closed_services'].append(key)

        changes['unchanged_count'] = len(current_keys & previous_services)

        return changes

    def save_services(self, services_data):
        """Save service inventory to state/services.json"""
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'service_count': len(services_data['services_by_host']),
                'services_by_host': services_data['services_by_host'],
                'service_inventory': services_data['service_inventory']
            }
            with open(self.services_file, 'w') as f:
                json.dump(output, f, indent=2)
            return True
        except Exception:
            return False

    def save_changes(self, changes):
        """Save service change detection results"""
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

        # Get scan data
        scan_data = self.get_scan_data(scan_id)

        if not scan_data:
            return {
                'error': 'No scan data found',
                'warning': 'Failed to retrieve scan data'
            }

        # Extract services
        services_data = self.extract_services(scan_data)
        previous_services = self.load_previous_services()

        # Detect changes
        changes = self.detect_service_changes(services_data['services_by_host'], previous_services)

        # Save results
        self.save_services(services_data)
        self.save_changes(changes)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_services': len(services_data['services_by_host']),
            'new_services': len(changes['new_services']),
            'closed_services': len(changes['closed_services']),
            'service_types': len(services_data['service_inventory'])
        }


def main():
    extractor = ServiceIntelligence()
    result = extractor.extract()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
