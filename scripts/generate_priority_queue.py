#!/usr/bin/env python3
"""Priority Queue Generator (Phase N - Dashboard)
Prioritizes actions from incidents and recommendations
Output: state/priority_queue.json
"""
import json, sys
from datetime import datetime
from pathlib import Path

class PriorityQueueGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.priority_queue = []

    def load_state(self, filename):
        fp = self.state_dir / filename
        if fp.exists():
            try:
                with open(fp, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def add_incident_priorities(self):
        """Extract top incidents as priorities"""
        incidents_data = self.load_state('incidents.json')
        incidents = incidents_data.get('incidents', [])

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_incidents = sorted(
            incidents,
            key=lambda x: (severity_order.get(x.get('severity', 'LOW'), 4), -x.get('count', 0))
        )

        for idx, incident in enumerate(sorted_incidents[:5], 1):
            priority = {
                'rank': idx,
                'source': 'incident',
                'severity': incident.get('severity', 'LOW'),
                'title': incident.get('title', 'Unknown Incident'),
                'description': incident.get('description', ''),
                'evidence_count': incident.get('evidence_count', 0),
                'action': f"Review incident: {incident.get('title', 'Unknown')}",
                'time_estimate': '15-30 min',
                'impact': 'HIGH' if incident.get('severity') in ['CRITICAL', 'HIGH'] else 'MEDIUM'
            }
            self.priority_queue.append(priority)

    def add_drift_priorities(self):
        """Extract control drifts as priorities"""
        drift_data = self.load_state('control_drift.json')
        drifts = drift_data.get('drifts', [])

        for drift in drifts[:3]:  # Top 3 drifts
            priority = {
                'rank': len(self.priority_queue) + 1,
                'source': 'control_drift',
                'severity': drift.get('severity', 'HIGH'),
                'title': f"Control Drift: {drift.get('control', 'Unknown')}",
                'description': f"{drift.get('control', 'Unknown')} changed from {drift.get('old_state', '')} to {drift.get('new_state', '')}",
                'evidence_count': 1,
                'action': f"Investigate and remediate {drift.get('control', 'control')} drift",
                'time_estimate': '10-20 min',
                'impact': 'HIGH'
            }
            self.priority_queue.append(priority)

    def add_security_priorities(self):
        """Extract security recommendations as priorities"""
        leak_data = self.load_state('leak_guard_status.json')

        if leak_data.get('total_findings', 0) > 0:
            priority = {
                'rank': len(self.priority_queue) + 1,
                'source': 'security',
                'severity': 'CRITICAL' if leak_data.get('security_status') == 'CRITICAL_LEAKS_DETECTED' else 'HIGH',
                'title': 'Data Leak Guard Alert',
                'description': f"{leak_data.get('total_findings', 0)} potential data leaks detected",
                'evidence_count': leak_data.get('total_findings', 0),
                'action': 'Review and remediate data leaks',
                'time_estimate': '30-60 min',
                'impact': 'CRITICAL'
            }
            self.priority_queue.append(priority)

    def generate(self):
        """Generate priority queue"""
        try:
            self.add_incident_priorities()
            self.add_drift_priorities()
            self.add_security_priorities()

            # Ensure ranks are sequential and sorted
            self.priority_queue.sort(key=lambda x: (
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x.get('severity', 'LOW'), 4),
                x.get('rank', 999)
            ))

            for idx, item in enumerate(self.priority_queue, 1):
                item['rank'] = idx

            output = {
                'timestamp': datetime.now().isoformat(),
                'total_priorities': len(self.priority_queue),
                'priority_queue': self.priority_queue[:5]  # Top 5 only
            }

            with open(self.state_dir / 'priority_queue.json', 'w') as f:
                json.dump(output, f, indent=2)

            return {
                'status': 'success',
                'total_priorities': len(self.priority_queue),
                'top_priority': self.priority_queue[0].get('title', '') if self.priority_queue else ''
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    generator = PriorityQueueGenerator()
    result = generator.generate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('status') == 'success' else 1)
