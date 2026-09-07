#!/usr/bin/env python3
"""
Asset Builder - Transform Nessus scan data into assets.json format
Auto-classifies assets by hostname/OS patterns
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from nessus_client import NessusClient

class AssetBuilder:
    # Classification patterns
    PATTERNS = {
        'Windows': [
            r'WIN|WINDOWS|WK|WS|DC|SERVER|DOMAIN|MEMBER',
            r'^[A-Z]{2,4}\d+',  # ABCD01, WIN01 pattern
        ],
        'Camera': [
            r'REOLINK|HIKVISION|CAMERA|CAM|RTSP',
            r'192\.168\.1\.2[0-9]{2}',  # Typical camera IP range
        ],
        'Router': [
            r'GATEWAY|ROUTER|GW|RTR|EDGE|FIREWALL',
            r'OPNSENSE|PFSENSE',
        ],
        'NAS': [
            r'NAS|SYNOLOGY|QNAP|STORAGE|BACKUP',
            r'DS\d+',  # Synology model pattern
        ],
        'Linux': [
            r'LINUX|UBUNTU|DEBIAN|CENTOS|RHEL|FEDORA',
            r'^[a-z]+-[a-z0-9]+',
        ],
    }

    def __init__(self):
        self.nessus = NessusClient()
        self.assets = {
            'total_assets': 0,
            'last_updated': datetime.now().isoformat(),
            'assets_by_type': {},
            'all_assets': []
        }

    def classify_asset(self, hostname: str, os_info: str, ipv4: str = '') -> str:
        """Auto-classify asset based on hostname, OS, and IP"""
        text = f"{hostname} {os_info} {ipv4}".upper()

        for asset_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return asset_type

        return 'Unknown'

    def build_assets(self) -> Dict:
        """Fetch scans and build asset inventory"""
        scans = self.nessus.get_scans()
        print(f'[ASSETS] Found {len(scans)} scans')

        asset_dict = {}

        for scan in scans:
            scan_id = scan.get('id')
            scan_name = scan.get('name', 'Unknown')

            try:
                hosts = self.nessus.get_scan_hosts(scan_id)

                for host in hosts:
                    host_id = host.get('host_id')
                    host_detail = self.nessus.get_host_details(scan_id, host_id)

                    if not host_detail:
                        continue

                    host_info = host_detail.get('info', {})
                    hostname = host_info.get('host-fqdn', host_info.get('host-ip', 'Unknown'))
                    os_type = host_info.get('os', '')
                    ipv4 = host_info.get('host-ip', '')

                    asset_type = self.classify_asset(hostname, os_type, ipv4)

                    # Build vulnerability counts
                    vuln_counts = host.get('severities', {})

                    asset_key = ipv4 or hostname
                    if asset_key not in asset_dict:
                        asset_dict[asset_key] = {
                            'id': len(asset_dict) + 1,
                            'hostname': hostname,
                            'ip': ipv4,
                            'type': asset_type,
                            'os': os_type,
                            'last_scan': scan_name,
                            'vulnerabilities': {
                                'critical': vuln_counts.get('critical', {}).get('count', 0),
                                'high': vuln_counts.get('high', {}).get('count', 0),
                                'medium': vuln_counts.get('medium', {}).get('count', 0),
                                'low': vuln_counts.get('low', {}).get('count', 0),
                                'info': vuln_counts.get('info', {}).get('count', 0),
                            },
                            'risk_score': self._calculate_risk(vuln_counts),
                            'status': 'ONLINE' if host.get('scanProfilingStatus') == 'DONE' else 'SCANNING',
                            'last_updated': datetime.now().isoformat()
                        }
            except Exception as e:
                print(f'[ASSETS] Error processing scan {scan_id}: {e}')

        # Group by type
        self.assets['all_assets'] = list(asset_dict.values())
        self.assets['total_assets'] = len(asset_dict)

        for asset in self.assets['all_assets']:
            asset_type = asset['type']
            if asset_type not in self.assets['assets_by_type']:
                self.assets['assets_by_type'][asset_type] = []
            self.assets['assets_by_type'][asset_type].append(asset)

        return self.assets

    def _calculate_risk(self, severities: Dict) -> int:
        """Calculate risk score: 0-100"""
        critical = severities.get('critical', {}).get('count', 0) * 25
        high = severities.get('high', {}).get('count', 0) * 10
        medium = severities.get('medium', {}).get('count', 0) * 3
        low = severities.get('low', {}).get('count', 0)

        score = min(100, critical + high + medium + low)
        return score

    def save(self, filepath: str):
        """Save assets to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.assets, f, indent=2)
            print(f'[ASSETS] OK: Saved to {filepath}')
            return True
        except Exception as e:
            print(f'[ASSETS] FAIL: Save failed: {e}')
            return False

if __name__ == '__main__':
    builder = AssetBuilder()
    assets = builder.build_assets()
    builder.save('state/assets.json')
    print(f'[ASSETS] Built {builder.assets["total_assets"]} assets')
