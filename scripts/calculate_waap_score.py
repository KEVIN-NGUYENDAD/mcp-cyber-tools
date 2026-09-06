#!/usr/bin/env python3
"""
WAAP RISK SCORE CALCULATOR (Phase N)
Calculates WAAP (Web Application and API Protection) risk score
Populates: state/waap_score.json

Inputs:
- state/waap_status.json (WAAP security posture)

Outputs:
- state/waap_score.json (calculated risk score and recommendations)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    pass


class WAAPScoreCalculator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.waap_status_file = self.state_dir / 'waap_status.json'
        self.waap_score_file = self.state_dir / 'waap_score.json'

    def load_waap_status(self):
        """Load WAAP status from state file"""
        if self.waap_status_file.exists():
            try:
                with open(self.waap_status_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def calculate_score(self, waap_status):
        """Calculate WAAP risk score"""
        if not waap_status:
            return {
                'score': 0,
                'status': 'unknown',
                'reason': 'No WAAP status data available'
            }

        score = 100
        findings = []

        # Check if WAAP is enabled
        if not waap_status.get('enabled', False):
            score -= 30
            findings.append({
                'issue': 'WAAP is not enabled',
                'severity': 'HIGH',
                'impact': -30
            })
        else:
            findings.append({
                'issue': 'WAAP is enabled',
                'severity': 'INFO',
                'impact': 0
            })

        # Check protection status
        if waap_status.get('protection_status') != 'active':
            score -= 20
            findings.append({
                'issue': 'WAAP protection is not active',
                'severity': 'HIGH',
                'impact': -20
            })
        else:
            findings.append({
                'issue': 'WAAP protection is active',
                'severity': 'INFO',
                'impact': 0
            })

        # Check threat count
        threats = waap_status.get('threats_detected', 0)
        if threats > 100:
            score -= 15
            findings.append({
                'issue': f'High threat count ({threats})',
                'severity': 'HIGH',
                'impact': -15
            })
        elif threats > 50:
            score -= 10
            findings.append({
                'issue': f'Elevated threat count ({threats})',
                'severity': 'MEDIUM',
                'impact': -10
            })
        else:
            findings.append({
                'issue': f'Threat count acceptable ({threats})',
                'severity': 'INFO',
                'impact': 0
            })

        # Check blocked requests
        blocked = waap_status.get('blocked_requests', 0)
        if blocked > 50:
            findings.append({
                'issue': f'High blocked request rate ({blocked})',
                'severity': 'MEDIUM',
                'impact': 0  # Blocked = good, not penalized
            })

        # Check last update
        if waap_status.get('last_update'):
            last_update = waap_status.get('last_update')
            try:
                last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                age_days = (datetime.now(datetime.timezone.utc) - last_update_dt).days
                if age_days > 1:
                    score -= 5
                    findings.append({
                        'issue': f'WAAP data is {age_days} days old',
                        'severity': 'LOW',
                        'impact': -5
                    })
            except Exception:
                pass

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Determine status
        if score >= 80:
            status = 'excellent'
        elif score >= 60:
            status = 'good'
        elif score >= 40:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'score': score,
            'status': status,
            'findings': findings,
            'threat_summary': {
                'threats_detected': threats,
                'blocked_requests': blocked
            }
        }

    def save_score(self, score_result):
        """Save score calculation results"""
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'score': score_result['score'],
                'status': score_result['status'],
                'findings': score_result['findings'],
                'threat_summary': score_result['threat_summary']
            }
            with open(self.waap_score_file, 'w') as f:
                json.dump(output, f, indent=2)
            return True
        except Exception:
            return False

    def calculate(self):
        """Main calculation logic"""
        waap_status = self.load_waap_status()

        if not waap_status:
            return {
                'error': 'WAAP status file not found',
                'solution': 'Run collect_waap_snapshot.py first'
            }

        score_result = self.calculate_score(waap_status)

        # Save results
        self.save_score(score_result)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'waap_score': score_result['score'],
            'waap_status': score_result['status'],
            'critical_findings': len([
                f for f in score_result['findings']
                if f.get('severity') == 'HIGH'
            ])
        }


def main():
    calculator = WAAPScoreCalculator()
    result = calculator.calculate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
    main()
