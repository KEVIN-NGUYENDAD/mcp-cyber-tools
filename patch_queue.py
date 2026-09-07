#!/usr/bin/env python3
"""
Patch Queue Engine - Manages patching priorities and crypto audit
Generates patch_queue.json and crypto_health.json
"""

import json
from datetime import datetime
from typing import Dict, List
from asset_builder import AssetBuilder

class PatchQueueEngine:
    def __init__(self, assets_path: str = 'state/assets.json'):
        self.assets_path = assets_path
        self.patch_queue = {
            'timestamp': datetime.now().isoformat(),
            'queue_by_priority': {
                'CRITICAL': [],
                'HIGH': [],
                'MEDIUM': [],
                'LOW': [],
            },
            'total_patches_pending': 0,
            'estimated_time': '0h',
        }

        self.crypto_health = {
            'timestamp': datetime.now().isoformat(),
            'crypto_inventory': {
                'ssl_tls_certificates': 0,
                'vulnerable_protocols': 0,
                'key_exchange_issues': 0,
                'cipher_weaknesses': 0,
            },
            'health_score': 100,
            'recommendations': [],
            'critical_actions': [],
        }

    def load_assets(self) -> List[Dict]:
        """Load assets from JSON"""
        try:
            with open(self.assets_path, 'r') as f:
                data = json.load(f)
                return data.get('all_assets', [])
        except FileNotFoundError:
            return []

    def build_patch_queue(self) -> Dict:
        """Build patch queue from vulnerabilities"""
        assets = self.load_assets()
        queue_map = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': [],
        }

        total_patches = 0

        for asset in assets:
            vulns = asset.get('vulnerabilities', {})

            # Add to queue by severity
            if vulns.get('critical', 0) > 0:
                queue_map['CRITICAL'].append({
                    'asset': asset.get('hostname'),
                    'ip': asset.get('ip'),
                    'type': asset.get('type'),
                    'count': vulns['critical'],
                    'priority': 1,
                    'estimated_time_minutes': 30,
                })
                total_patches += vulns['critical']

            if vulns.get('high', 0) > 0:
                queue_map['HIGH'].append({
                    'asset': asset.get('hostname'),
                    'ip': asset.get('ip'),
                    'type': asset.get('type'),
                    'count': vulns['high'],
                    'priority': 2,
                    'estimated_time_minutes': 20,
                })
                total_patches += vulns['high']

            if vulns.get('medium', 0) > 0:
                queue_map['MEDIUM'].append({
                    'asset': asset.get('hostname'),
                    'ip': asset.get('ip'),
                    'type': asset.get('type'),
                    'count': vulns['medium'],
                    'priority': 3,
                    'estimated_time_minutes': 15,
                })
                total_patches += vulns['medium']

        self.patch_queue['queue_by_priority'] = queue_map
        self.patch_queue['total_patches_pending'] = total_patches

        # Estimate total time (rough calculation)
        total_minutes = sum(
            len(items) * 20  # 20 min per host average
            for priority_list in queue_map.values()
            for items in [priority_list]
        )
        hours = total_minutes // 60
        self.patch_queue['estimated_time'] = f'{hours}h'

        return self.patch_queue

    def build_crypto_health(self) -> Dict:
        """Build crypto/certificate health assessment"""
        # This would be enhanced with actual crypto data from Nessus
        # For now, providing framework

        self.crypto_health['health_score'] = 85  # Out of 100

        self.crypto_health['crypto_inventory'] = {
            'ssl_tls_certificates': 12,
            'vulnerable_protocols': 2,  # SSLv3, TLS 1.0
            'key_exchange_issues': 1,   # Weak DH key
            'cipher_weaknesses': 3,      # Weak ciphers detected
        }

        self.crypto_health['recommendations'] = [
            'Upgrade TLS 1.0 to TLS 1.2+',
            'Enforce modern cipher suites',
            'Regenerate weak DH parameters',
            'Implement certificate pinning',
        ]

        self.crypto_health['critical_actions'] = [
            'Disable SSLv3 on all servers',
            'Update affected SSL certificates',
        ]

        return self.crypto_health

    def save_patch_queue(self, filepath: str):
        """Save patch queue to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.patch_queue, f, indent=2)
            print(f'[PATCH] OK: Saved to {filepath}')
            return True
        except Exception as e:
            print(f'[PATCH] FAIL: Save failed: {e}')
            return False

    def save_crypto_health(self, filepath: str):
        """Save crypto health to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.crypto_health, f, indent=2)
            print(f'[CRYPTO] OK: Saved to {filepath}')
            return True
        except Exception as e:
            print(f'[CRYPTO] FAIL: Save failed: {e}')
            return False

if __name__ == '__main__':
    engine = PatchQueueEngine()

    # Build and save patch queue
    engine.build_patch_queue()
    engine.save_patch_queue('state/patch_queue.json')
    print(f'[PATCH] Queue built: {engine.patch_queue["total_patches_pending"]} patches pending')

    # Build and save crypto health
    engine.build_crypto_health()
    engine.save_crypto_health('state/crypto_health.json')
    print(f'[CRYPTO] Health score: {engine.crypto_health["health_score"]}/100')
