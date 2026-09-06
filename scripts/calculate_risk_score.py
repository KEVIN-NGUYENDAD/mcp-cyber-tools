#!/usr/bin/env python3
"""Risk Score Calculator - Phase N.5"""
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
        findings, crit, high = [], 0, 0
        for a in assets.get('assets', []):
            crit += a.get('critical', 0)
            high += a.get('high', 0)
        score = max(0, 100 - crit * 15 - high * 8)
        return score, findings
    
    def analyze_crypto(self):
        crypto = self.load_state('crypto_inventory.json')
        return crypto.get('score', 50), []
    
    def analyze_waap(self):
        waap = self.load_state('waap_score.json')
        return waap.get('score', 50), []
    
    def calculate(self):
        asset_score, _ = self.analyze_assets()
        crypto_score, _ = self.analyze_crypto()
        waap_score, _ = self.analyze_waap()
        
        overall = round(0.4 * asset_score + 0.3 * crypto_score + 0.3 * waap_score)
        risk_level = 'LOW' if overall >= 80 else ('MEDIUM' if overall >= 60 else ('HIGH' if overall >= 40 else 'CRITICAL'))
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall,
            'risk_level': risk_level,
            'component_scores': {'asset': asset_score, 'crypto': crypto_score, 'waap': waap_score}
        }
        
        with open(self.state_dir / 'risk_score.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return {'status': 'success', 'overall_score': overall, 'risk_level': risk_level}

if __name__ == '__main__':
    calc = RiskScoreCalculator()
    result = calc.calculate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
