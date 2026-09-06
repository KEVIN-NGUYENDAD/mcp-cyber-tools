#!/usr/bin/env python3
"""Risk Score Calculator (Phase N.5)
Synthesizes all intelligence to calculate overall risk score
Inputs: All state intelligence files
Outputs: state/risk_score.json
"""
import json, sys, os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class RiskScoreCalculator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
    
    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def analyze_assets(self):
        """Analyze asset vulnerabilities"""
        assets = self.load_state('assets.json')
        if not assets or not isinstance(assets, dict):
            return 0, []
        
        findings = []
        critical_count = 0
        high_count = 0
        
        for asset in assets.get('assets', []):
            crit = asset.get('critical', 0)
            high = asset.get('high', 0)
            critical_count += crit
            high_count += high
            
            if crit > 0:
                findings.append({
                    'type': 'asset_critical',
                    'severity': 'CRITICAL',
                    'ip': asset.get('ip'),
                    'count': crit,
                    'impact': 'System compromise possible'
                })
            if high > 0:
                findings.append({
                    'type': 'asset_high',
                    'severity': 'HIGH',
                    'ip': asset.get('ip'),
                    'count': high,
                    'impact': 'Exploitation likely'
                })
        
        score = max(0, 100 - critical_count * 15 - high_count * 8)
        return score, findings
    
    def analyze_crypto(self):
        """Analyze cryptographic posture"""
        crypto = self.load_state('crypto_inventory.json')
        if not crypto or not isinstance(crypto, dict):
            return 50, []
        
        score = crypto.get('score', 50)
        findings = []
        
        sb = crypto.get('severity_breakdown', {})
        if sb.get('CRITICAL', 0) > 0:
            findings.append({
                'type': 'crypto_critical',
                'severity': 'CRITICAL',
                'count': sb.get('CRITICAL'),
                'impact': 'Encryption broken'
            })
        if sb.get('HIGH', 0) > 0:
            findings.append({
                'type': 'crypto_high',
                'severity': 'HIGH',
                'count': sb.get('HIGH'),
                'impact': 'Weak crypto detected'
            })
        
        return score, findings
    
    def analyze_waap(self):
        """Analyze WAAP posture"""
        waap = self.load_state('waap_score.json')
        if not waap or not isinstance(waap, dict):
            return 50, []
        
        score = waap.get('score', 50)
        findings = []
        
        if waap.get('status') in ['poor', 'fair']:
            findings.append({
                'type': 'waap_protection',
                'severity': 'HIGH',
                'status': waap.get('status'),
                'impact': 'Web apps vulnerable to attack'
            })
        
        threats = waap.get('threat_summary', {}).get('threats_detected', 0)
        if threats > 50:
            findings.append({
                'type': 'waap_threats',
                'severity': 'HIGH',
                'count': threats,
                'impact': 'Active threats detected'
            })
        
        return score, findings
    
    def calculate_overall_risk(self, component_scores):
        """Calculate overall risk from component scores"""
        scores = list(component_scores.values())
        if not scores:
            return 50
        
        # Weighted average: Asset (40%), Crypto (30%), WAAP (30%)
        weights = {
            'asset': 0.40,
            'crypto': 0.30,
            'waap': 0.30
        }
        
        weighted = (
            component_scores.get('asset', 50) * weights['asset'] +
            component_scores.get('crypto', 50) * weights['crypto'] +
            component_scores.get('waap', 50) * weights['waap']
        )
        return round(weighted)
    
    def determine_risk_level(self, score):
        """Convert score to risk level"""
        if score >= 80:
            return 'LOW'
        elif score >= 60:
            return 'MEDIUM'
        elif score >= 40:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def calculate(self):
        """Main calculation"""
        asset_score, asset_findings = self.analyze_assets()
        crypto_score, crypto_findings = self.analyze_crypto()
        waap_score, waap_findings = self.analyze_waap()
        
        component_scores = {
            'asset': asset_score,
            'crypto': crypto_score,
            'waap': waap_score
        }
        
        overall_score = self.calculate_overall_risk(component_scores)
        risk_level = self.determine_risk_level(overall_score)
        
        all_findings = asset_findings + crypto_findings + waap_findings
        all_findings.sort(key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}.get(x.get('severity'), 3))
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'risk_level': risk_level,
            'component_scores': component_scores,
            'findings': all_findings[:20],
            'finding_count': len(all_findings),
            'critical_count': sum(1 for f in all_findings if f.get('severity') == 'CRITICAL'),
            'high_count': sum(1 for f in all_findings if f.get('severity') == 'HIGH')
        }
        
        with open(self.state_dir / 'risk_score.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        return {
            'status': 'success',
            'overall_score': overall_score,
            'risk_level': risk_level,
            'findings_count': len(all_findings)
        }

if __name__ == '__main__':
    calc = RiskScoreCalculator()
    result = calc.calculate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
