#!/usr/bin/env python3
"""
Risk Engine - Calculate comprehensive risk scores from Nessus data
Generates risk_score.json and patch_queue.json for dashboard
"""

import json
from datetime import datetime
from typing import Dict, List
from asset_builder import AssetBuilder

class RiskEngine:
    def __init__(self, assets_path: str = 'state/assets.json'):
        self.assets_path = assets_path
        self.risk_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0,
            'threat_level': 'LOW',
            'risk_summary': {
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
            },
            'top_risk_hosts': [],
            'risk_by_type': {},
            'trend': 'stable',
        }

    def load_assets(self) -> List[Dict]:
        """Load assets from JSON file"""
        try:
            with open(self.assets_path, 'r') as f:
                data = json.load(f)
                return data.get('all_assets', [])
        except FileNotFoundError:
            print(f'[RISK] ⚠️  Assets file not found: {self.assets_path}')
            return []

    def calculate_overall_score(self, assets: List[Dict]) -> int:
        """Calculate overall risk score: 0-100"""
        if not assets:
            return 0

        total_risk = 0
        for asset in assets:
            total_risk += asset.get('risk_score', 0)

        avg_risk = total_risk / len(assets)
        return int(avg_risk)

    def calculate_threat_level(self, score: int) -> str:
        """Map score to threat level"""
        if score >= 80:
            return 'CRITICAL'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'

    def build_risk_summary(self, assets: List[Dict]) -> Dict:
        """Build vulnerability summary across all assets"""
        summary = {
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'total_vulnerabilities': 0,
        }

        for asset in assets:
            vulns = asset.get('vulnerabilities', {})
            summary['critical_count'] += vulns.get('critical', 0)
            summary['high_count'] += vulns.get('high', 0)
            summary['medium_count'] += vulns.get('medium', 0)
            summary['low_count'] += vulns.get('low', 0)

        summary['total_vulnerabilities'] = (
            summary['critical_count'] +
            summary['high_count'] +
            summary['medium_count'] +
            summary['low_count']
        )

        return summary

    def get_top_risk_hosts(self, assets: List[Dict], count: int = 5) -> List[Dict]:
        """Get highest risk hosts"""
        sorted_assets = sorted(assets, key=lambda x: x.get('risk_score', 0), reverse=True)
        return sorted_assets[:count]

    def get_risk_by_type(self, assets: List[Dict]) -> Dict:
        """Calculate average risk by asset type"""
        risk_by_type = {}

        for asset in assets:
            asset_type = asset.get('type', 'Unknown')
            risk_score = asset.get('risk_score', 0)

            if asset_type not in risk_by_type:
                risk_by_type[asset_type] = {
                    'count': 0,
                    'total_risk': 0,
                    'avg_risk': 0,
                }

            risk_by_type[asset_type]['count'] += 1
            risk_by_type[asset_type]['total_risk'] += risk_score

        # Calculate averages
        for asset_type in risk_by_type:
            total = risk_by_type[asset_type]['total_risk']
            count = risk_by_type[asset_type]['count']
            risk_by_type[asset_type]['avg_risk'] = int(total / count) if count > 0 else 0

        return risk_by_type

    def calculate_risks(self) -> Dict:
        """Calculate all risk metrics"""
        assets = self.load_assets()

        if assets:
            overall_score = self.calculate_overall_score(assets)
            self.risk_data['overall_score'] = overall_score
            self.risk_data['threat_level'] = self.calculate_threat_level(overall_score)
            self.risk_data['risk_summary'] = self.build_risk_summary(assets)
            self.risk_data['top_risk_hosts'] = self.get_top_risk_hosts(assets)
            self.risk_data['risk_by_type'] = self.get_risk_by_type(assets)

        return self.risk_data

    def save(self, filepath: str):
        """Save risk data to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.risk_data, f, indent=2)
            print(f'[RISK] ✅ Saved to {filepath}')
            return True
        except Exception as e:
            print(f'[RISK] ❌ Save failed: {e}')
            return False

if __name__ == '__main__':
    engine = RiskEngine()
    risks = engine.calculate_risks()
    engine.save('state/risk_score.json')
    print(f'[RISK] Overall score: {engine.risk_data["overall_score"]} ({engine.risk_data["threat_level"]})')
