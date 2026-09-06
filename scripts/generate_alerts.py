#!/usr/bin/env python3
"""Alert Engine (v1.0 Release)
Generates alerts from security findings
Output: state/alerts.json
"""
import json, sys
from datetime import datetime
from pathlib import Path

class AlertEngine:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.alerts = []
        self.alert_id = 1000

    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def check_threat_hunting(self):
        """Generate alerts from threat hunting findings"""
        categories = {
            'persistence': 'threat_hunting_persistence.json',
            'credential': 'threat_hunting_credential.json',
            'lateral': 'threat_hunting_lateral.json',
        }

        for category, file in categories.items():
            data = self.load_state(file)
            findings = data.get('findings_summary', {})

            if findings.get('CRITICAL', 0) > 0:
                severity = 'CRITICAL' if category == 'credential' else 'HIGH'
                self.alerts.append({
                    'id': f'ALT-{self.alert_id}',
                    'severity': severity,
                    'category': category.upper(),
                    'title': f'Threat Hunt: {category.title()} Activity Detected',
                    'description': f"{findings.get('CRITICAL', 0)} critical findings in {category}",
                    'source': file,
                    'timestamp': datetime.now().isoformat(),
                    'action': f'Review threat hunting results for {category}',
                    'count': findings.get('CRITICAL', 0)
                })
                self.alert_id += 1

    def check_control_drift(self):
        """Generate alerts from critical control drifts"""
        drift_data = self.load_state('control_drift.json')
        status = drift_data.get('control_status_summary', {})

        critical_controls = ['defender', 'firewall']
        for control in critical_controls:
            control_status = status.get(control, '')
            if 'DRIFT' in control_status:
                self.alerts.append({
                    'id': f'ALT-{self.alert_id}',
                    'severity': 'CRITICAL',
                    'category': 'CONTROL_DRIFT',
                    'title': f'Critical: {control.title()} Control Drift Detected',
                    'description': f'{control.title()} control has changed unexpectedly',
                    'source': 'control_drift.json',
                    'timestamp': datetime.now().isoformat(),
                    'action': f'Investigate and remediate {control} drift immediately',
                    'control': control
                })
                self.alert_id += 1

    def check_defender_firewall_status(self):
        """Generate alerts if Defender or Firewall disabled"""
        defender = self.load_state('defender_status.json')
        firewall = self.load_state('firewall_status.json')

        if not defender.get('enabled', True):
            self.alerts.append({
                'id': f'ALT-{self.alert_id}',
                'severity': 'CRITICAL',
                'category': 'SECURITY_CONTROL',
                'title': 'CRITICAL: Windows Defender Disabled',
                'description': 'Windows Defender antivirus protection is disabled',
                'source': 'defender_status.json',
                'timestamp': datetime.now().isoformat(),
                'action': 'Enable Windows Defender immediately'
            })
            self.alert_id += 1

        if not firewall.get('enabled', True):
            self.alerts.append({
                'id': f'ALT-{self.alert_id}',
                'severity': 'CRITICAL',
                'category': 'SECURITY_CONTROL',
                'title': 'CRITICAL: Windows Firewall Disabled',
                'description': 'Windows Firewall protection is disabled',
                'source': 'firewall_status.json',
                'timestamp': datetime.now().isoformat(),
                'action': 'Enable Windows Firewall immediately'
            })
            self.alert_id += 1

    def check_risk_level(self):
        """Generate alerts for high risk levels"""
        brief = self.load_state('daily_brief/latest.json')
        risk = brief.get('summary', {}).get('risk_level', 'LOW')

        if risk in ['HIGH', 'CRITICAL']:
            self.alerts.append({
                'id': f'ALT-{self.alert_id}',
                'severity': 'HIGH' if risk == 'HIGH' else 'CRITICAL',
                'category': 'RISK_ASSESSMENT',
                'title': f'Risk Level: {risk}',
                'description': f'Overall SOC risk level is {risk}',
                'source': 'daily_brief.json',
                'timestamp': datetime.now().isoformat(),
                'action': 'Review risk factors and incidents'
            })
            self.alert_id += 1

    def check_incidents(self):
        """Generate alerts for critical incidents"""
        incidents = self.load_state('incidents.json').get('incidents', [])

        critical_incidents = [inc for inc in incidents if inc.get('severity') == 'CRITICAL']

        if critical_incidents:
            for inc in critical_incidents[:3]:  # Top 3 critical
                self.alerts.append({
                    'id': f'ALT-{self.alert_id}',
                    'severity': 'CRITICAL',
                    'category': 'INCIDENT',
                    'title': inc.get('title', 'Critical Incident'),
                    'description': inc.get('description', 'Critical security incident detected'),
                    'source': 'incidents.json',
                    'timestamp': inc.get('timestamp', datetime.now().isoformat()),
                    'action': 'Review and respond to incident immediately',
                    'incident_id': inc.get('id')
                })
                self.alert_id += 1

    def generate(self):
        """Generate all alerts"""
        try:
            self.check_threat_hunting()
            self.check_control_drift()
            self.check_defender_firewall_status()
            self.check_risk_level()
            self.check_incidents()

            # Sort by severity (CRITICAL first)
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'WARNING': 2, 'INFO': 3}
            self.alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 4))

            output = {
                'timestamp': datetime.now().isoformat(),
                'total_alerts': len(self.alerts),
                'by_severity': {
                    'CRITICAL': sum(1 for a in self.alerts if a.get('severity') == 'CRITICAL'),
                    'HIGH': sum(1 for a in self.alerts if a.get('severity') == 'HIGH'),
                    'WARNING': sum(1 for a in self.alerts if a.get('severity') == 'WARNING'),
                    'INFO': sum(1 for a in self.alerts if a.get('severity') == 'INFO'),
                },
                'alerts': self.alerts
            }

            with open(self.state_dir / 'alerts.json', 'w') as f:
                json.dump(output, f, indent=2)

            return {
                'status': 'success',
                'total_alerts': len(self.alerts),
                'critical_count': output['by_severity']['CRITICAL']
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    engine = AlertEngine()
    result = engine.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
