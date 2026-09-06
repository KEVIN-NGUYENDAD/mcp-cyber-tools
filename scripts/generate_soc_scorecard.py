#!/usr/bin/env python3
"""SOC Scorecard Generator (v1.0 Release)
Generates SOC maturity scorecard
Output: state/soc_scorecard.json
"""
import json, sys
from datetime import datetime
from pathlib import Path

class SOCScorecard:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.scores = {}

    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def score_asset_hygiene(self):
        """Score asset management and patch management"""
        assets = self.load_state('assets.json')
        total_assets = len(assets.get('assets', []))

        if total_assets == 0:
            return 0

        vulnerable = sum(1 for a in assets.get('assets', []) if a.get('critical', 0) > 0)
        score = max(0, 100 - (vulnerable / total_assets) * 100)
        return score

    def score_vulnerability_management(self):
        """Score vulnerability detection and tracking"""
        crypto = self.load_state('crypto_inventory.json')
        crypto_score = crypto.get('score', 50)

        brief = self.load_state('daily_brief/latest.json')
        risk_level = brief.get('summary', {}).get('risk_level', 'HIGH')

        risk_to_score = {'LOW': 90, 'MEDIUM': 70, 'HIGH': 50, 'CRITICAL': 20}
        risk_score = risk_to_score.get(risk_level, 50)

        return (crypto_score + risk_score) / 2

    def score_threat_hunting(self):
        """Score threat hunting maturity"""
        findings = 0
        categories = [
            'threat_hunting_persistence.json',
            'threat_hunting_suspicious.json',
            'threat_hunting_lateral.json',
            'threat_hunting_credential.json'
        ]

        for cat in categories:
            data = self.load_state(cat)
            findings += data.get('findings_summary', {}).get('total', 0)

        # More findings = better threat hunting (up to 100)
        score = min(100, findings * 5)
        return score

    def score_incident_response(self):
        """Score incident response capability"""
        incidents = self.load_state('incidents.json')
        total_incidents = len(incidents.get('incidents', []))

        if total_incidents == 0:
            return 80  # Good if no incidents

        critical = sum(1 for i in incidents.get('incidents', []) if i.get('severity') == 'CRITICAL')
        high = sum(1 for i in incidents.get('incidents', []) if i.get('severity') == 'HIGH')

        # Fewer critical/high = better response
        score = max(20, 100 - (critical * 20 + high * 10))
        return score

    def score_control_baseline(self):
        """Score control baseline and monitoring"""
        drift = self.load_state('control_drift.json')
        status = drift.get('control_status_summary', {})

        drifts_detected = sum(1 for s in status.values() if 'DRIFT' in str(s))
        controls_monitored = len(status)

        if controls_monitored == 0:
            return 0

        score = max(0, 100 - (drifts_detected / controls_monitored) * 100)
        return score

    def score_data_freshness(self):
        """Score data quality and freshness"""
        freshness = self.load_state('data_freshness.json')
        confidence = freshness.get('confidence_factor', 0.5)

        # Confidence directly translates to score
        return confidence * 100

    def score_trust_layer(self):
        """Score security and trust layer"""
        leak = self.load_state('leak_guard_status.json')
        status = leak.get('security_status', 'UNKNOWN')

        status_scores = {
            'CLEAN': 95,
            'MINOR_LEAKS': 70,
            'HIGH_RISK_LEAKS': 40,
            'CRITICAL_LEAKS_DETECTED': 10
        }

        return status_scores.get(status, 50)

    def score_to_grade(self, score):
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def generate(self):
        """Generate SOC scorecard"""
        try:
            self.scores = {
                'Asset Hygiene': self.score_asset_hygiene(),
                'Vulnerability Management': self.score_vulnerability_management(),
                'Threat Hunting': self.score_threat_hunting(),
                'Incident Response': self.score_incident_response(),
                'Control Baseline': self.score_control_baseline(),
                'Data Freshness': self.score_data_freshness(),
                'Trust Layer': self.score_trust_layer(),
            }

            # Calculate overall score
            overall_score = sum(self.scores.values()) / len(self.scores) if self.scores else 0

            output = {
                'timestamp': datetime.now().isoformat(),
                'overall_score': round(overall_score, 1),
                'overall_grade': self.score_to_grade(overall_score),
                'scores': {
                    dimension: {
                        'score': round(score, 1),
                        'grade': self.score_to_grade(score)
                    }
                    for dimension, score in self.scores.items()
                },
                'interpretation': {
                    'A': 'Excellent - World-class SOC maturity',
                    'B': 'Good - Solid security posture',
                    'C': 'Fair - Needs improvement in key areas',
                    'D': 'Poor - Significant gaps in security',
                    'F': 'Critical - Immediate action required'
                }
            }

            with open(self.state_dir / 'soc_scorecard.json', 'w') as f:
                json.dump(output, f, indent=2)

            return {
                'status': 'success',
                'overall_score': round(overall_score, 1),
                'overall_grade': self.score_to_grade(overall_score)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    scorecard = SOCScorecard()
    result = scorecard.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
