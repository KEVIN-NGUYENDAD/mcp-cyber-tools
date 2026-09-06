#!/usr/bin/env python3
"""
DAILY BRIEF GENERATOR (Phase N)
Generates comprehensive daily security briefing combining all SentinelOps data sources
Inputs: All collector outputs + intelligence files
Outputs: daily_brief/YYYY-MM-DD.json
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict


class DailyBriefGenerator:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.brief_dir = Path(__file__).parent.parent / 'daily_brief'
        self.brief_dir.mkdir(exist_ok=True)
        self.today = date.today().isoformat()
        self.brief_file = self.brief_dir / f'{self.today}.json'

    def load_json(self, filename):
        """Load a JSON file from state directory"""
        filepath = self.state_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def generate_vulnerability_summary(self):
        """Generate vulnerability summary from Nessus data"""
        nessus_data = self.load_json('nessus_status.json')
        if not nessus_data:
            return None

        return {
            'scan_name': nessus_data.get('scan_name', 'Unknown'),
            'scan_age_hours': nessus_data.get('scan_age_hours', 0),
            'total_findings': nessus_data.get('total', 0),
            'critical': nessus_data.get('critical', 0),
            'high': nessus_data.get('high', 0),
            'medium': nessus_data.get('medium', 0),
            'low': nessus_data.get('low', 0),
            'info': nessus_data.get('info', 0),
            'scanner_status': nessus_data.get('scanner_status', 'unknown')
        }

    def generate_domain_summary(self):
        """Generate domain and DNS summary"""
        domain_data = self.load_json('domain_status.json')
        if not domain_data:
            return None

        dns_complete = domain_data.get('dns_complete', {})
        return {
            'domain': domain_data.get('domain', 'Unknown'),
            'dns_health': {
                'spf': dns_complete.get('has_spf', False),
                'dmarc': dns_complete.get('has_dmarc', False),
                'nameservers': dns_complete.get('has_nameservers', False),
                'a_records': dns_complete.get('has_a_records', False),
                'mx_records': dns_complete.get('has_mx_records', False)
            },
            'nameserver_count': len(domain_data.get('nameservers', [])),
            'a_record_count': len(domain_data.get('a_records', [])),
            'mx_record_count': len(domain_data.get('mx_records', []))
        }

    def generate_waap_summary(self):
        """Generate WAAP and SSL summary"""
        status_data = self.load_json('waap_status.json')
        score_data = self.load_json('waap_score.json')

        if not status_data or not score_data:
            return None

        return {
            'domain': status_data.get('domain', 'Unknown'),
            'ssl_status': status_data.get('ssl_status', 'unknown'),
            'days_until_expiry': status_data.get('days_until_expiry', None),
            'health_score': score_data.get('health_score', 0),
            'grade': score_data.get('grade', '—'),
            'status': score_data.get('status', 'unknown'),
            'recommendation_count': len(score_data.get('recommendations', []))
        }

    def generate_asset_summary(self):
        """Generate asset intelligence summary"""
        assets_data = self.load_json('assets.json')
        changes_data = self.load_json('asset_changes.json')

        if not assets_data:
            return None

        summary = {
            'total_assets': assets_data.get('total_assets', 0),
            'known_devices': 0,
            'unknown_devices': 0,
            'new_assets': 0,
            'removed_assets': 0,
            'top_vulnerable_devices': []
        }

        # Count known vs unknown
        assets = assets_data.get('assets', [])
        summary['known_devices'] = sum(1 for a in assets if a.get('hostname'))
        summary['unknown_devices'] = summary['total_assets'] - summary['known_devices']

        # Changes
        if changes_data:
            summary['new_assets'] = len(changes_data.get('new_assets', []))
            summary['removed_assets'] = len(changes_data.get('removed_assets', []))

        # Top vulnerable
        top_vuln = sorted(assets, key=lambda x: x.get('vulnerability_count', 0), reverse=True)[:5]
        summary['top_vulnerable_devices'] = [
            {
                'ip': a.get('ip'),
                'hostname': a.get('hostname', 'Unknown'),
                'vulnerability_count': a.get('vulnerability_count', 0),
                'severity_critical': a.get('critical', 0),
                'severity_high': a.get('high', 0)
            }
            for a in top_vuln
        ]

        return summary

    def generate_service_summary(self):
        """Generate service inventory summary"""
        services_data = self.load_json('services.json')
        changes_data = self.load_json('service_changes.json')

        if not services_data:
            return None

        summary = {
            'total_services': services_data.get('service_count', 0),
            'service_types': len(services_data.get('service_inventory', {})),
            'new_services': 0,
            'closed_services': 0,
            'top_services': []
        }

        # Changes
        if changes_data:
            summary['new_services'] = len(changes_data.get('new_services', []))
            summary['closed_services'] = len(changes_data.get('closed_services', []))

        # Top services
        inventory = services_data.get('service_inventory', {})
        top_services = sorted(
            inventory.items(),
            key=lambda x: x[1].get('host_count', 0),
            reverse=True
        )[:5]

        summary['top_services'] = [
            {
                'name': name,
                'host_count': data.get('host_count', 0),
                'finding_count': data.get('finding_count', 0)
            }
            for name, data in top_services
        ]

        return summary

    def generate_crypto_summary(self):
        """Generate cryptographic intelligence summary"""
        crypto_data = self.load_json('crypto_inventory.json')
        changes_data = self.load_json('crypto_changes.json')

        if not crypto_data:
            return None

        summary = {
            'health_score': crypto_data.get('health_score', 0),
            'certificate_count': crypto_data.get('certificate_count', 0),
            'cipher_suite_count': crypto_data.get('cipher_suite_count', 0),
            'weak_cipher_count': crypto_data.get('weak_cipher_count', 0),
            'newly_expired_certs': 0,
            'new_weak_ciphers': 0
        }

        if changes_data:
            summary['newly_expired_certs'] = len(changes_data.get('expired_certificates', []))
            summary['new_weak_ciphers'] = len(changes_data.get('new_weak_ciphers', []))

        return summary

    def generate_change_summary(self):
        """Tóm tắt thay đổi từ timeline"""
        timeline = self.load_json('timeline.json')
        if not timeline:
            return {
                'total_changes': 0,
                'changes_by_category': {},
                'critical_incidents': [],
                'summary_text': 'Không có thay đổi'
            }

        events = timeline.get('events', [])
        summary_text = 'Không có thay đổi'

        if len(events) == 0:
            summary_text = 'Không có thay đổi'
        elif len(events) > 0:
            critical = [e for e in events if e.get('severity') == 'CRITICAL']
            high = [e for e in events if e.get('severity') == 'HIGH']

            if critical:
                summary_text = f'{len(critical)} sự kiện CRITICAL, {len(high)} sự kiện HIGH'
            elif high:
                summary_text = f'{len(high)} sự kiện HIGH, {len(events)} thay đổi tổng cộng'
            else:
                summary_text = f'{len(events)} thay đổi bình thường'

        return {
            'total_changes': len(events),
            'changes_by_category': timeline.get('by_category', {}),
            'changes_by_severity': timeline.get('by_severity', {}),
            'critical_incidents': [e for e in events if e.get('severity') == 'CRITICAL'],
            'summary_text': summary_text
        }

    def generate_risk_assessment(self):
        """Generate overall risk assessment"""
        nessus = self.generate_vulnerability_summary() or {}
        waap = self.generate_waap_summary() or {}
        assets = self.generate_asset_summary() or {}
        services = self.generate_service_summary() or {}
        crypto = self.generate_crypto_summary() or {}

        # Calculate risk level
        risk_score = 0
        risk_factors = []

        # Vulnerability risk
        critical = nessus.get('critical', 0)
        high = nessus.get('high', 0)
        if critical > 0:
            risk_score += 40
            risk_factors.append(f'{critical} critical vulnerabilities detected')
        if high > 0:
            risk_score += 20
            risk_factors.append(f'{high} high-severity vulnerabilities')

        # Cryptographic risk
        if crypto.get('weak_cipher_count', 0) > 0:
            risk_score += 15
            risk_factors.append(f'{crypto["weak_cipher_count"]} weak ciphers in use')

        # WAAP/SSL risk
        if waap.get('ssl_status') != 'valid':
            risk_score += 10
            risk_factors.append('SSL certificate invalid or missing')
        if waap.get('days_until_expiry', 999) < 7:
            risk_score += 5
            risk_factors.append('SSL certificate expiring soon')

        # Unknown devices
        if assets.get('unknown_devices', 0) > 0:
            risk_score += 10
            risk_factors.append(f'{assets["unknown_devices"]} unknown devices on network')

        risk_level = 'LOW'
        if risk_score >= 70:
            risk_level = 'CRITICAL'
        elif risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'

        return {
            'risk_level': risk_level,
            'risk_score': min(100, risk_score),
            'risk_factors': risk_factors
        }

    def generate_brief(self):
        """Generate complete daily brief"""
        brief = {
            'timestamp': datetime.now().isoformat(),
            'date': self.today,
            'change_summary': self.generate_change_summary(),
            'vulnerability_summary': self.generate_vulnerability_summary(),
            'domain_summary': self.generate_domain_summary(),
            'waap_summary': self.generate_waap_summary(),
            'asset_summary': self.generate_asset_summary(),
            'service_summary': self.generate_service_summary(),
            'crypto_summary': self.generate_crypto_summary(),
            'risk_assessment': self.generate_risk_assessment()
        }

        return brief

    def save_brief(self, brief):
        """Save daily brief to file"""
        try:
            with open(self.brief_file, 'w') as f:
                json.dump(brief, f, indent=2)
            return True
        except Exception:
            return False


def main():
    generator = DailyBriefGenerator()

    brief = generator.generate_brief()

    # Print to stdout
    print(json.dumps(brief, indent=2))

    # Save to file
    if generator.save_brief(brief):
        print(f'\n✓ Daily brief saved to {generator.brief_file}', file=sys.stderr)
        sys.exit(0)
    else:
        print(f'\n✗ Failed to save daily brief', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
