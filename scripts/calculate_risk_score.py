#!/usr/bin/env python3
"""Risk Score Calculator - Phase N.5-N.6 (With MCP Telemetry)"""
import json, sys
from datetime import datetime
from pathlib import Path

class RiskScoreCalculator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'

    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}

    def analyze_assets(self):
        assets = self.load_state('assets.json')
        crit, high = 0, 0
        for a in assets.get('assets', []):
            crit += a.get('critical', 0)
            high += a.get('high', 0)
        score = max(0, 100 - crit * 15 - high * 8)
        return score

    def analyze_crypto(self):
        crypto = self.load_state('crypto_inventory.json')
        return crypto.get('score', 50)

    def analyze_waap(self):
        waap = self.load_state('waap_score.json')
        return waap.get('score', 50)

    def analyze_defender(self):
        defender = self.load_state('defender_status.json')
        if not defender.get('enabled'):
            return 20
        if defender.get('threat_count', 0) > 0:
            return max(0, 100 - defender.get('threat_count', 0) * 10)
        return 100

    def analyze_firewall(self):
        firewall = self.load_state('firewall_status.json')
        if not firewall.get('enabled'):
            return 20
        return 90

    def analyze_security_events(self):
        events = self.load_state('security_events.json')
        score = 100
        score -= events.get('failed_logons', 0)
        score -= events.get('critical_events', 0) * 20
        score -= events.get('warning_events', 0) * 2
        return max(0, score)

    def calculate(self):
        asset_score = self.analyze_assets()
        crypto_score = self.analyze_crypto()
        waap_score = self.analyze_waap()
        defender_score = self.analyze_defender()
        firewall_score = self.analyze_firewall()
        events_score = self.analyze_security_events()

        overall = round(
            0.30 * asset_score +
            0.20 * waap_score +
            0.15 * crypto_score +
            0.15 * defender_score +
            0.10 * firewall_score +
            0.10 * events_score
        )

        risk_level = 'LOW' if overall >= 80 else ('MEDIUM' if overall >= 60 else ('HIGH' if overall >= 40 else 'CRITICAL'))

        output = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall,
            'risk_level': risk_level,
            'component_scores': {
                'asset': asset_score,
                'waap': waap_score,
                'crypto': crypto_score,
                'defender': defender_score,
                'firewall': firewall_score,
                'security_events': events_score
            },
            'weights': {
                'asset': 0.30,
                'waap': 0.20,
                'crypto': 0.15,
                'defender': 0.15,
                'firewall': 0.10,
                'security_events': 0.10
            }
        }

        with open(self.state_dir / 'risk_score.json', 'w') as f:
            json.dump(output, f, indent=2)

        return {'status': 'success', 'overall_score': overall, 'risk_level': risk_level}

if __name__ == '__main__':
    calc = RiskScoreCalculator()
    result = calc.calculate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
