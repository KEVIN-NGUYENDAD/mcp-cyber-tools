#!/usr/bin/env python3
"""Threat Hunting Results Generator (Phase N - Dashboard)
Aggregates threat hunting results from incidents
Output: state/threat_hunting_*.json
"""
import json, sys
from datetime import datetime
from pathlib import Path

class ThreatHuntingGenerator:
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

    def extract_hunting_results(self):
        """Extract threat hunting results from incidents"""
        incidents = self.load_state('incidents.json').get('incidents', [])

        hunting_categories = {
            'persistence': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'findings': []},
            'suspicious': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'findings': []},
            'lateral': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'findings': []},
            'credential': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'findings': []},
        }

        # Map incident types to hunting categories
        type_mapping = {
            'PERSISTENCE': 'persistence',
            'SUSPICIOUS_PROCESS': 'suspicious',
            'LATERAL_MOVEMENT': 'lateral',
            'CREDENTIAL_DUMPING': 'credential',
        }

        for incident in incidents:
            incident_type = incident.get('type', '').upper()
            severity = incident.get('severity', 'LOW')

            category = type_mapping.get(incident_type)
            if category:
                cat = hunting_categories[category]
                cat[severity] += 1
                cat['findings'].append({
                    'title': incident.get('title', 'Unknown'),
                    'severity': severity,
                    'evidence_count': incident.get('evidence_count', 0),
                    'last_seen': incident.get('timestamp', datetime.now().isoformat())
                })

        return hunting_categories

    def save_hunting_results(self, hunting_data):
        """Save threat hunting results to separate files"""
        results = {'persistence': 'Persistence', 'suspicious': 'Suspicious Process', 'lateral': 'Lateral Movement', 'credential': 'Credential Dumping'}

        for key, label in results.items():
            if key not in hunting_data:
                continue

            data = hunting_data[key]
            output = {
                'timestamp': datetime.now().isoformat(),
                'category': label,
                'findings_summary': {
                    'CRITICAL': data.get('CRITICAL', 0),
                    'HIGH': data.get('HIGH', 0),
                    'MEDIUM': data.get('MEDIUM', 0),
                    'LOW': data.get('LOW', 0),
                    'total': sum([data.get(s, 0) for s in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']])
                },
                'findings': data.get('findings', [])[:10]  # Top 10 findings per category
            }

            filename = f'threat_hunting_{key}.json'
            with open(self.state_dir / filename, 'w') as f:
                json.dump(output, f, indent=2)

    def generate(self):
        """Generate threat hunting results"""
        try:
            hunting_data = self.extract_hunting_results()
            self.save_hunting_results(hunting_data)

            # Calculate totals
            total_findings = sum([
                sum([hunting_data[cat].get(sev, 0) for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']])
                for cat in hunting_data
            ])

            critical_count = sum([
                hunting_data[cat].get('CRITICAL', 0) for cat in hunting_data
            ])

            return {
                'status': 'success',
                'total_findings': total_findings,
                'critical_findings': critical_count,
                'categories': len(hunting_data)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    generator = ThreatHuntingGenerator()
    result = generator.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
