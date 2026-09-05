#!/usr/bin/env python3
"""
PHASE W: WAAP HEALTH SCORE CALCULATOR
Calculates domain security health score from multiple indicators
Integrates with Event Hub and Recommendation Engine

Inputs:
- SSL Status (valid/expired)
- SSL Expiry (days remaining)
- HTTP Status (accessible)
- HTTPS Status (accessible)
- DNS Status (resolves)
- Security Headers (present)

Output:
- state/waap_score.json
- Integration with daily_brief
"""

import json
import sys
import os
import socket
import ssl
from datetime import datetime
from pathlib import Path

try:
    import requests
    import dns.resolver
    from dotenv import load_dotenv
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print('{"error": "Missing dependencies. Install: pip install requests dnspython cryptography python-dotenv"}', file=sys.stderr)
    sys.exit(1)


class WAAPScoreCalculator:
    def __init__(self, domain=None):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'waap_score.json'

        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        self.domain = domain or os.environ.get('DOMAIN', 'sentinelops.fyi')
        self.session = requests.Session()
        self.session.verify = False

        # Score components (0-100 each)
        self.scores = {
            'ssl_status': 0,
            'ssl_expiry': 0,
            'http_status': 0,
            'https_status': 0,
            'dns_status': 0,
            'security_headers': 0
        }

        self.issues = []

    def check_ssl_status(self):
        """Check SSL certificate validity"""
        try:
            hostname = self.domain
            port = 443
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)

            if not cert_der:
                self.scores['ssl_status'] = 0
                self.issues.append('SSL certificate not found')
                return False

            cert = x509.load_der_x509_certificate(cert_der, default_backend())
            not_after = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after

            now = datetime.now(not_after.tzinfo) if not_after.tzinfo else datetime.utcnow()
            days_until_expiry = (not_after - now).days

            # SSL Status: Valid = 100, Invalid = 0
            if days_until_expiry > 0:
                self.scores['ssl_status'] = 100
            else:
                self.scores['ssl_status'] = 0
                self.issues.append(f'SSL certificate expired {abs(days_until_expiry)} days ago')

            # SSL Expiry: Score based on days remaining
            if days_until_expiry > 90:
                self.scores['ssl_expiry'] = 100
            elif days_until_expiry > 30:
                self.scores['ssl_expiry'] = 80
                self.issues.append(f'SSL certificate expiring in {days_until_expiry} days')
            elif days_until_expiry > 0:
                self.scores['ssl_expiry'] = 50
                self.issues.append(f'SSL certificate expiring soon: {days_until_expiry} days')
            else:
                self.scores['ssl_expiry'] = 0

            return True
        except Exception as e:
            self.scores['ssl_status'] = 0
            self.scores['ssl_expiry'] = 0
            self.issues.append(f'SSL check failed: {str(e)}')
            return False

    def check_https_status(self):
        """Check HTTPS accessibility"""
        try:
            resp = self.session.get(f'https://{self.domain}', timeout=5)
            if resp.status_code < 400:
                self.scores['https_status'] = 100
                return True
            else:
                self.scores['https_status'] = 50
                self.issues.append(f'HTTPS returned status {resp.status_code}')
                return False
        except Exception as e:
            self.scores['https_status'] = 0
            self.issues.append(f'HTTPS check failed: {str(e)}')
            return False

    def check_http_status(self):
        """Check HTTP accessibility"""
        try:
            resp = self.session.get(f'http://{self.domain}', timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                self.scores['http_status'] = 80
                return True
            else:
                self.scores['http_status'] = 50
                return False
        except Exception:
            self.scores['http_status'] = 30
            return False

    def check_dns_status(self):
        """Check DNS resolution"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, 'A', lifetime=5)
            if answers:
                self.scores['dns_status'] = 100
                return True
            else:
                self.scores['dns_status'] = 0
                self.issues.append('DNS resolution returned no records')
                return False
        except Exception as e:
            self.scores['dns_status'] = 0
            self.issues.append(f'DNS check failed: {str(e)}')
            return False

    def check_security_headers(self):
        """Check for security headers"""
        try:
            resp = self.session.get(f'https://{self.domain}', timeout=5)
            headers = resp.headers

            required_headers = {
                'Strict-Transport-Security': 'HSTS',
                'X-Content-Type-Options': 'X-Content-Type-Options',
                'X-Frame-Options': 'X-Frame-Options',
                'Content-Security-Policy': 'CSP'
            }

            found_headers = sum(1 for h in required_headers if h in headers)
            total_headers = len(required_headers)

            self.scores['security_headers'] = int((found_headers / total_headers) * 100)

            if found_headers < total_headers:
                missing = [required_headers[h] for h in required_headers if h not in headers]
                self.issues.append(f'Missing security headers: {", ".join(missing)}')

            return found_headers == total_headers
        except Exception as e:
            self.scores['security_headers'] = 0
            self.issues.append(f'Security headers check failed: {str(e)}')
            return False

    def calculate_overall_score(self):
        """Calculate weighted overall score"""
        weights = {
            'ssl_status': 0.25,      # 25% - SSL validity is critical
            'ssl_expiry': 0.20,      # 20% - Expiry matters
            'https_status': 0.20,    # 20% - HTTPS accessibility
            'dns_status': 0.15,      # 15% - DNS resolution
            'security_headers': 0.15 # 15% - Security hardening
        }

        # Ignore HTTP status in overall score (it's just a nice-to-have)

        overall = sum(
            self.scores.get(component, 0) * weight
            for component, weight in weights.items()
        )

        return round(overall)

    def calculate_health_grade(self, score):
        """Convert score to letter grade"""
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

    def collect(self):
        """Run all health checks"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain,
            'checks': {}
        }

        # Run all checks
        self.check_dns_status()
        self.check_https_status()
        self.check_http_status()
        self.check_ssl_status()
        self.check_security_headers()

        # Build output
        output['checks'] = {
            'ssl_valid': self.scores['ssl_status'] == 100,
            'ssl_expiry_score': self.scores['ssl_expiry'],
            'https_accessible': self.scores['https_status'] == 100,
            'http_accessible': self.scores['http_status'] >= 50,
            'dns_resolves': self.scores['dns_status'] == 100,
            'security_headers_present': self.scores['security_headers'] > 50
        }

        # Calculate overall health score
        overall_score = self.calculate_overall_score()
        grade = self.calculate_health_grade(overall_score)

        output['health_score'] = overall_score
        output['grade'] = grade
        output['status'] = 'healthy' if overall_score >= 80 else 'warning' if overall_score >= 60 else 'critical'

        # Add detailed scores
        output['component_scores'] = self.scores

        # Add issues
        output['issues'] = self.issues
        output['issue_count'] = len(self.issues)

        # Add recommendations
        output['recommendations'] = self._generate_recommendations()

        return output

    def _generate_recommendations(self):
        """Generate recommendations based on issues"""
        recommendations = []

        if self.scores['ssl_status'] < 100:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'SSL',
                'action': 'Fix or renew SSL certificate',
                'impact': 'SSL certificate is invalid or expired'
            })

        if self.scores['ssl_expiry'] < 100:
            days_left = 90  # Approximate
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'SSL',
                'action': f'Renew SSL certificate (expires in {days_left} days)',
                'impact': 'Certificate expiration will break HTTPS access'
            })

        if self.scores['security_headers'] < 100:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Security',
                'action': 'Add missing security headers (HSTS, CSP, X-Frame-Options)',
                'impact': 'Improves protection against XSS, clickjacking, and other attacks'
            })

        if self.scores['https_status'] < 100:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Availability',
                'action': 'Fix HTTPS accessibility',
                'impact': 'HTTPS endpoint not responding properly'
            })

        return recommendations

    def save(self, data):
        """Save score to state/waap_score.json"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f'Error saving: {e}', file=sys.stderr)
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Calculate WAAP health score')
    parser.add_argument('--domain', help='Domain to check', default=None)
    args = parser.parse_args()

    calculator = WAAPScoreCalculator(domain=args.domain)
    data = calculator.collect()

    calculator.save(data)
    print(json.dumps(data, indent=2))

    sys.exit(0)


if __name__ == '__main__':
    main()
