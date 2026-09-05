#!/usr/bin/env python3
"""
PHASE W: WAAP SCORE INTEGRATION
Integrates WAAP Health Score into Daily Brief pipeline
Reads waap_score.json and generates Event Hub changes + recommendations
Reuses existing Event Hub and Recommendation Engine (no new architecture)

Outputs to:
- daily_brief_store (via add_change and add_recommendation)
- Event Hub (via event_schema)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    from daily_brief_store import add_change, add_recommendation
except ImportError:
    print('Error: daily_brief_store module not found', file=sys.stderr)
    sys.exit(1)


class WAAPIntegration:
    """Integrates WAAP health score into Daily Brief"""

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.waap_score_file = self.state_dir / 'waap_score.json'
        self.baseline_file = self.state_dir / 'waap_score_baseline.json'

    def load_waap_score(self):
        """Load current WAAP health score"""
        if not self.waap_score_file.exists():
            return None
        try:
            with open(self.waap_score_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def load_baseline(self):
        """Load baseline WAAP score for comparison"""
        if not self.baseline_file.exists():
            return None
        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def save_baseline(self, score_data):
        """Save current score as new baseline"""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(score_data, f, indent=2)
            return True
        except:
            return False

    def detect_score_change(self, current, baseline):
        """Detect changes in WAAP health score"""
        if not baseline:
            return None

        current_score = current.get('health_score')
        baseline_score = baseline.get('health_score')

        if current_score != baseline_score:
            delta = current_score - baseline_score
            direction = 'improved' if delta > 0 else 'degraded'
            return {
                'delta': delta,
                'direction': direction,
                'previous': baseline_score,
                'current': current_score
            }

        return None

    def generate_score_event(self, score_data, delta=None):
        """Generate Event Hub event for score change"""
        event = {
            'timestamp': score_data.get('timestamp', datetime.now().isoformat()),
            'source': 'waap_monitor',
            'severity': self._get_severity(score_data),
            'title': self._get_title(score_data, delta),
            'summary': self._get_summary(score_data),
            'evidence': [
                {'key': 'health_score', 'value': score_data.get('health_score')},
                {'key': 'grade', 'value': score_data.get('grade')},
                {'key': 'status', 'value': score_data.get('status')},
                {'key': 'domain', 'value': score_data.get('domain')},
                {'key': 'issue_count', 'value': score_data.get('issue_count')},
            ]
        }

        if delta:
            event['evidence'].append({'key': 'score_delta', 'value': delta['delta']})

        return event

    def _get_severity(self, score_data):
        """Map health score to severity"""
        score = score_data.get('health_score', 0)
        status = score_data.get('status', 'critical')

        if status == 'critical' or score < 60:
            return 'high'
        elif status == 'warning' or score < 80:
            return 'medium'
        else:
            return 'low'

    def _get_title(self, score_data, delta=None):
        """Generate event title"""
        domain = score_data.get('domain', 'unknown')
        score = score_data.get('health_score', 0)
        grade = score_data.get('grade', '?')

        if delta:
            direction = delta['direction']
            delta_val = abs(delta['delta'])
            return f"WAAP Health {direction.upper()}: {domain} ({grade}, {score}/100) {delta_val:+d} points"
        else:
            return f"WAAP Health Score: {domain} ({grade}, {score}/100)"

    def _get_summary(self, score_data):
        """Generate event summary"""
        issues = score_data.get('issues', [])
        if not issues:
            return f"Domain health is {score_data.get('status', 'unknown')}. No security issues detected."

        issue_text = '; '.join(issues[:2])
        if len(issues) > 2:
            issue_text += f'; and {len(issues) - 2} more'

        return f"Issues: {issue_text}"

    def generate_recommendations(self, score_data):
        """Convert WAAP recommendations into action items"""
        recommendations = []

        for rec in score_data.get('recommendations', []):
            if not isinstance(rec, dict):
                continue

            priority = rec.get('priority', 'MEDIUM').lower()
            category = rec.get('category', 'Security')
            action = rec.get('action', '')
            impact = rec.get('impact', '')

            recommendation = {
                'source': 'waap_monitor',
                'category': category,
                'action_priority': priority,
                'recommendation': action,
                'rationale': impact
            }

            recommendations.append(recommendation)

        return recommendations

    def integrate(self):
        """Main integration logic"""
        score_data = self.load_waap_score()
        if not score_data:
            print('No WAAP score data found', file=sys.stderr)
            return False

        baseline = self.load_baseline()
        delta = self.detect_score_change(score_data, baseline) if baseline else None

        # Generate and store event
        event = self.generate_score_event(score_data, delta)
        add_change(event)
        print(f"Added WAAP score event: {event['title']}")

        # Generate and store recommendations
        recommendations = self.generate_recommendations(score_data)
        for rec in recommendations:
            add_recommendation(rec)
            print(f"Added recommendation: [{rec['action_priority'].upper()}] {rec['recommendation']}")

        # Update baseline for next comparison
        self.save_baseline(score_data)

        return True


def main():
    integration = WAAPIntegration()
    success = integration.integrate()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
