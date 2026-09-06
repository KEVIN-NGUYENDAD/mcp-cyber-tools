#!/usr/bin/env python3
"""Weekly Executive Report Generator (v1.0 Release)
Generates executive summary with trends
Output: state/weekly_executive_report.json
"""
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

class WeeklyReport:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'

    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def calculate_risk_trend(self):
        """Calculate risk trend"""
        brief = self.load_state('daily_brief/latest.json')
        current_risk = brief.get('summary', {}).get('risk_level', 'HIGH')

        risk_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        current_level = risk_order.get(current_risk, 3)

        return {
            'current': current_risk,
            'previous_trend': 'Stable' if current_level == 3 else ('Improving' if current_level < 3 else 'Degrading'),
            'direction': 'Up' if current_level > 3 else ('Down' if current_level < 3 else 'Stable'),
            'recommendation': 'Address high-risk findings immediately' if current_level >= 3 else 'Continue current security posture'
        }

    def calculate_incident_trend(self):
        """Calculate incident trend"""
        incidents = self.load_state('incidents.json').get('incidents', [])
        alerts = self.load_state('alerts.json').get('alerts', [])

        total_incidents = len(incidents)
        critical_count = sum(1 for i in incidents if i.get('severity') == 'CRITICAL')
        high_count = sum(1 for i in incidents if i.get('severity') == 'HIGH')

        return {
            'total_incidents': total_incidents,
            'critical_incidents': critical_count,
            'high_incidents': high_count,
            'active_alerts': len(alerts),
            'trend': 'Increasing' if total_incidents > 5 else ('Stable' if total_incidents > 0 else 'Clear'),
            'resolution_rate': 0 if total_incidents == 0 else 'Pending Analysis',
            'recommendation': 'Escalate critical incidents for immediate response' if critical_count > 0 else 'Monitor incident trend'
        }

    def calculate_threat_hunting_trend(self):
        """Calculate threat hunting effectiveness"""
        categories = {
            'Persistence': 'threat_hunting_persistence.json',
            'Suspicious Process': 'threat_hunting_suspicious.json',
            'Lateral Movement': 'threat_hunting_lateral.json',
            'Credential Dumping': 'threat_hunting_credential.json',
        }

        total_findings = 0
        critical_findings = 0
        findings_by_category = {}

        for name, file in categories.items():
            data = self.load_state(file)
            summary = data.get('findings_summary', {})
            count = summary.get('total', 0)
            critical = summary.get('CRITICAL', 0)

            total_findings += count
            critical_findings += critical
            findings_by_category[name] = {
                'total': count,
                'critical': critical
            }

        return {
            'total_findings': total_findings,
            'critical_findings': critical_findings,
            'by_category': findings_by_category,
            'maturity': 'Advanced' if total_findings > 50 else ('Intermediate' if total_findings > 10 else 'Basic'),
            'coverage': 'Comprehensive' if len(findings_by_category) >= 4 else 'Partial',
            'recommendation': 'Investigate all critical threat hunt findings' if critical_findings > 0 else 'Continue threat hunting operations'
        }

    def calculate_control_drift_trend(self):
        """Calculate control baseline trend"""
        drift = self.load_state('control_drift.json')
        status = drift.get('control_status_summary', {})
        drifts_detected = drift.get('drifts_detected', 0)

        drift_summary = {}
        for control, state in status.items():
            drift_summary[control] = 'DRIFT' in str(state)

        return {
            'total_controls_monitored': len(status),
            'drifts_detected': drifts_detected,
            'by_control': drift_summary,
            'stability': 'Stable' if drifts_detected == 0 else ('Degrading' if drifts_detected > 3 else 'Minor Variance'),
            'trend': 'No Change',
            'recommendation': 'Investigate and remediate control drifts' if drifts_detected > 0 else 'Maintain current control settings'
        }

    def calculate_priority_trend(self):
        """Calculate priority queue trend"""
        priorities = self.load_state('priority_queue.json').get('priority_queue', [])

        critical_priorities = sum(1 for p in priorities if p.get('severity') == 'CRITICAL')
        high_priorities = sum(1 for p in priorities if p.get('severity') == 'HIGH')

        return {
            'total_priorities': len(priorities),
            'critical': critical_priorities,
            'high': high_priorities,
            'top_priority': priorities[0].get('title', 'None') if priorities else 'None',
            'estimated_resolution_time': '4-8 hours' if critical_priorities > 0 else '1-2 hours',
            'backlog': 'High' if len(priorities) > 5 else ('Moderate' if len(priorities) > 2 else 'Low'),
            'recommendation': 'Address top priority immediately'
        }

    def generate(self):
        """Generate weekly report"""
        try:
            scorecard = self.load_state('soc_scorecard.json')
            freshness = self.load_state('data_freshness.json')

            output = {
                'timestamp': datetime.now().isoformat(),
                'report_period': {
                    'start': (datetime.now() - timedelta(days=7)).isoformat(),
                    'end': datetime.now().isoformat()
                },
                'executive_summary': {
                    'soc_score': scorecard.get('overall_score', 0),
                    'soc_grade': scorecard.get('overall_grade', 'F'),
                    'data_confidence': round((freshness.get('confidence_factor', 0) * 100), 1),
                    'data_freshness': freshness.get('overall_status', 'UNKNOWN')
                },
                'trends': {
                    'risk': self.calculate_risk_trend(),
                    'incidents': self.calculate_incident_trend(),
                    'threat_hunting': self.calculate_threat_hunting_trend(),
                    'control_baseline': self.calculate_control_drift_trend(),
                    'priorities': self.calculate_priority_trend()
                },
                'key_findings': [
                    {
                        'finding': 'SOC Maturity Assessment',
                        'detail': f"Current SOC grade: {scorecard.get('overall_grade', 'F')}",
                        'priority': 'HIGH' if scorecard.get('overall_score', 0) < 70 else 'MEDIUM'
                    },
                    {
                        'finding': 'Data Quality',
                        'detail': f"Data confidence: {round((freshness.get('confidence_factor', 0) * 100), 1)}%",
                        'priority': 'MEDIUM'
                    }
                ],
                'recommendations': [
                    'Review and address high-priority incidents',
                    'Remediate control drift findings',
                    'Continue threat hunting operations',
                    'Improve asset hygiene through patching',
                    'Maintain data freshness monitoring'
                ]
            }

            with open(self.state_dir / 'weekly_executive_report.json', 'w') as f:
                json.dump(output, f, indent=2)

            return {
                'status': 'success',
                'soc_score': scorecard.get('overall_score', 0),
                'soc_grade': scorecard.get('overall_grade', 'F')
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    report = WeeklyReport()
    result = report.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
