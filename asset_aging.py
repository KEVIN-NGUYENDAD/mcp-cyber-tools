#!/usr/bin/env python3
"""
Asset Aging Engine - Track asset freshness and staleness
Calculates: Last Scan Age, Last Seen Age, Stale/Zombie assets
Outputs: state/asset_aging.json
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class AssetAgingEngine:
    def __init__(self, assets_file: str = 'state/assets.json'):
        self.assets_file = assets_file
        self.state_dir = 'state'
        self.output_file = os.path.join(self.state_dir, 'asset_aging.json')

        self.stale_days = 30
        self.zombie_days = 60

    def load_assets(self) -> Optional[Dict]:
        """Load assets from state file"""
        try:
            if not os.path.exists(self.assets_file):
                return None
            with open(self.assets_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f'[AGING] Error loading assets: {e}')
            return None

    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse ISO format timestamp"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None

    def calculate_days_since(self, timestamp_str: str) -> Optional[int]:
        """Calculate days since timestamp"""
        ts = self.parse_timestamp(timestamp_str)
        if not ts:
            return None
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.utcnow()
        delta = now - ts
        return delta.days

    def find_oldest_scan(self, assets: Dict) -> Optional[Dict]:
        """Find asset with oldest/longest scan age"""
        all_assets = assets.get('all_assets', [])
        if not all_assets:
            return None

        oldest = None
        max_days = -1

        for asset in all_assets:
            last_updated = asset.get('last_updated', '')
            if not last_updated:
                continue

            days_since = self.calculate_days_since(last_updated)
            if days_since is not None and days_since > max_days:
                max_days = days_since
                oldest = {
                    'asset': asset.get('hostname', 'Unknown'),
                    'ip': asset.get('ip', 'Unknown'),
                    'days_since_scan': days_since,
                    'last_scanned': last_updated,
                    'type': asset.get('type', 'Unknown')
                }

        return oldest

    def find_oldest_last_seen(self, assets: Dict) -> Optional[Dict]:
        """Find asset with oldest last seen time"""
        all_assets = assets.get('all_assets', [])
        if not all_assets:
            return None

        oldest = None
        max_days = -1

        for asset in all_assets:
            last_updated = asset.get('last_updated', '')
            if not last_updated:
                continue

            days_since = self.calculate_days_since(last_updated)
            if days_since is not None and days_since > max_days:
                max_days = days_since
                oldest = {
                    'asset': asset.get('hostname', 'Unknown'),
                    'ip': asset.get('ip', 'Unknown'),
                    'days_since_last_seen': days_since,
                    'last_seen': last_updated,
                    'status': asset.get('status', 'Unknown')
                }

        return oldest

    def find_stale_assets(self, assets: Dict) -> List[Dict]:
        """Find assets not scanned in > N days but still in inventory"""
        all_assets = assets.get('all_assets', [])
        stale = []

        for asset in all_assets:
            last_updated = asset.get('last_updated', '')
            if not last_updated:
                continue

            days_since = self.calculate_days_since(last_updated)
            if days_since is not None and days_since > self.stale_days:
                stale.append({
                    'asset': asset.get('hostname', 'Unknown'),
                    'ip': asset.get('ip', 'Unknown'),
                    'type': asset.get('type', 'Unknown'),
                    'days_since_scan': days_since,
                    'last_scanned': last_updated,
                    'status': asset.get('status', 'Unknown')
                })

        return sorted(stale, key=lambda x: x.get('days_since_scan', 0), reverse=True)

    def find_zombie_assets(self, assets: Dict) -> List[Dict]:
        """Find zombie assets: not seen in > N days or missing from recent scans"""
        all_assets = assets.get('all_assets', [])
        zombies = []

        for asset in all_assets:
            last_updated = asset.get('last_updated', '')
            if not last_updated:
                continue

            days_since = self.calculate_days_since(last_updated)
            if days_since is not None and days_since > self.zombie_days:
                zombies.append({
                    'asset': asset.get('hostname', 'Unknown'),
                    'ip': asset.get('ip', 'Unknown'),
                    'type': asset.get('type', 'Unknown'),
                    'days_since_last_seen': days_since,
                    'last_seen': last_updated,
                    'status': asset.get('status', 'Unknown')
                })

        return sorted(zombies, key=lambda x: x.get('days_since_last_seen', 0), reverse=True)

    def calculate_aging_score(self, days_since: int) -> Dict:
        """Calculate aging score (0-100) and color"""
        if days_since <= 30:
            return {'score': 100, 'status': 'GREEN', 'label': 'Fresh'}
        elif days_since <= 60:
            return {'score': 75, 'status': 'YELLOW', 'label': 'Aging'}
        elif days_since <= 90:
            return {'score': 50, 'status': 'ORANGE', 'label': 'Stale'}
        else:
            return {'score': 25, 'status': 'RED', 'label': 'Critical'}

    def calculate_overall_aging_score(self, assets: Dict) -> Dict:
        """Calculate overall asset freshness score"""
        all_assets = assets.get('all_assets', [])
        if not all_assets:
            return {'overall_score': 0, 'status': 'UNKNOWN', 'assets_scanned': 0}

        scores = []
        for asset in all_assets:
            last_updated = asset.get('last_updated', '')
            if last_updated:
                days_since = self.calculate_days_since(last_updated)
                if days_since is not None:
                    score_data = self.calculate_aging_score(days_since)
                    scores.append(score_data['score'])

        if not scores:
            return {'overall_score': 0, 'status': 'UNKNOWN', 'assets_scanned': len(all_assets)}

        avg_score = sum(scores) / len(scores)

        if avg_score >= 80:
            status = 'HEALTHY'
        elif avg_score >= 60:
            status = 'WARNING'
        else:
            status = 'CRITICAL'

        return {
            'overall_score': round(avg_score),
            'status': status,
            'assets_scanned': len(scores),
            'assets_total': len(all_assets)
        }

    def calculate(self) -> Dict:
        """Calculate all aging metrics"""
        assets = self.load_assets()
        if not assets:
            return None

        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'oldest_scan': None,
            'oldest_last_seen': None,
            'stale_assets': [],
            'zombie_assets': [],
            'aging_score': {}
        }

        # Calculate metrics
        oldest_scan = self.find_oldest_scan(assets)
        oldest_seen = self.find_oldest_last_seen(assets)
        stale = self.find_stale_assets(assets)
        zombies = self.find_zombie_assets(assets)
        aging_score = self.calculate_overall_aging_score(assets)

        output['oldest_scan'] = oldest_scan
        output['oldest_last_seen'] = oldest_seen
        output['stale_assets'] = stale
        output['zombie_assets'] = zombies
        output['aging_score'] = aging_score

        # Summary statistics
        output['summary'] = {
            'total_assets': assets.get('total_assets', 0),
            'stale_count': len(stale),
            'zombie_count': len(zombies),
            'definitions': {
                'stale': f'Last scanned > {self.stale_days} days ago',
                'zombie': f'Last seen > {self.zombie_days} days ago or missing from recent scans'
            }
        }

        return output

    def save(self, data: Dict) -> bool:
        """Save aging data to state file"""
        try:
            os.makedirs(self.state_dir, exist_ok=True)
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f'[AGING] Saved to {self.output_file}')
            return True
        except Exception as e:
            print(f'[AGING] Error saving: {e}')
            return False

    def run(self) -> bool:
        """Run complete aging calculation"""
        data = self.calculate()
        if not data:
            print('[AGING] No asset data available')
            return False

        success = self.save(data)

        if success:
            print(f'[AGING] Summary: {data["summary"]["total_assets"]} assets, '
                  f'{data["summary"]["stale_count"]} stale, '
                  f'{data["summary"]["zombie_count"]} zombies, '
                  f'Score: {data["aging_score"]["overall_score"]}/100 ({data["aging_score"]["status"]})')

        return success


if __name__ == '__main__':
    engine = AssetAgingEngine()
    engine.run()
