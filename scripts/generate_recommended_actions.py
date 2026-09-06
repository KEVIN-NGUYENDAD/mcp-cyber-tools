#!/usr/bin/env python3
"""Recommended Actions Generator - Phase N.5"""
import json, sys
from datetime import datetime
from pathlib import Path

class ActionGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.actions = []
    
    def load_state(self, filename):
        fp = self.state_dir / filename
        return json.load(open(fp)) if fp.exists() else {}
    
    def generate_asset_actions(self):
        assets = self.load_state('assets.json')
        critical_assets = [a for a in assets.get('assets', []) if a.get('critical', 0) > 0]
        if critical_assets:
            top = sorted(critical_assets, key=lambda x: x.get('critical'), reverse=True)[0]
            self.actions.append({
                'priority': 'CRITICAL',
                'category': 'Patch Management',
                'title': f"Patch {top.get('ip')} ({top.get('device_type')})",
                'description': f"{top.get('critical')} critical, {top.get('high')} high vulns",
                'steps': ['Identify patches', 'Test in staging', 'Schedule window', 'Apply patches', 'Verify'],
                'time_estimate': '4-8 hours',
                'impact': 'Prevents compromise'
            })
    
    def generate_crypto_actions(self):
        crypto = self.load_state('crypto_inventory.json')
        sb = crypto.get('severity_breakdown', {})
        if sb.get('CRITICAL', 0) > 0:
            self.actions.append({
                'priority': 'CRITICAL',
                'category': 'Cryptography',
                'title': 'Fix broken crypto',
                'description': f"{sb.get('CRITICAL')} critical issues",
                'steps': ['Audit TLS/SSL', 'Disable weak ciphers', 'Enforce TLS 1.2+'],
                'time_estimate': '8-16 hours',
                'impact': 'Restores encryption'
            })
    
    def generate(self):
        self.generate_asset_actions()
        self.generate_crypto_actions()
        
        order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
        self.actions.sort(key=lambda x: order.get(x.get('priority'), 99))
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'question': 'What do I need to do right now?',
            'total_actions': len(self.actions),
            'by_priority': {
                'CRITICAL': len([a for a in self.actions if a.get('priority') == 'CRITICAL']),
                'HIGH': len([a for a in self.actions if a.get('priority') == 'HIGH'])
            },
            'recommended_actions': self.actions
        }
        
        with open(self.state_dir / 'recommended_actions.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return {'status': 'success', 'total_actions': len(self.actions)}

if __name__ == '__main__':
    gen = ActionGenerator()
    result = gen.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
