#!/usr/bin/env python3
"""
WAAP / VNETWORK COLLECTOR (Phase I)
Integrates web application protection data into SentinelOps
Collects: WAF status, SSL status, CDN status, Protection mode
Outputs: state/waap_status.json

Credentials from .env:
- VNETWORK_API_TOKEN (optional)
"""

import json
import sys
import os
import socket
from datetime import datetime
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    import ssl
except ImportError:
    print('{"error": "Missing dependencies. Install: pip install requests python-dotenv cryptography"}', file=sys.stderr)
    sys.exit(1)


class WAAPCollector:
    def __init__(self, domain=None):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'waap_status.json'
        self.load_env()
        self.domain = domain or os.environ.get('DOMAIN', 'sentinelops.fyi')
        self.api_token = os.environ.get('VNETWORK_API_TOKEN')
        self.api_base_url = os.environ.get('VNETWORK_API_URL', 'https://api.vnetwork.io')
        self.session = requests.Session()
        self.session.verify = False

    def load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

    def set_auth_headers(self):
        """Configure session headers for VNETWORK API"""
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        })

    def get_ssl_status(self):
        """Check SSL certificate status"""
        try:
            hostname = self.domain
            port = 443
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)

            if not cert_der:
                return None

            cert = x509.load_der_x509_certificate(cert_der, default_backend())
            not_after = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after

            now = datetime.now(not_after.tzinfo) if not_after.tzinfo else datetime.utcnow()
            days_until_expiry = (not_after - now).days

            return {
                'ssl_status': 'valid' if days_until_expiry > 0 else 'expired',
                'expiration_date': not_after.isoformat(),
                'days_until_expiry': days_until_expiry,
                'issuer': cert.issuer.rfc4514_string()
            }

        except:
            return None

    def get_waf_status_vnetwork(self):
        """Get WAF status from VNETWORK API"""
        if not self.api_token:
            return None

        try:
            self.set_auth_headers()
            url = f'{self.api_base_url}/domains/{self.domain}/protection'
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            return {
                'waf_enabled': data.get('waf_enabled', False),
                'waf_mode': data.get('mode', 'unknown'),
                'protection_level': data.get('protection_level', 'standard'),
                'rules_version': data.get('rules_version')
            }

        except:
            return None

    def get_cdn_status(self):
        """Check if domain uses CDN"""
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, 'CNAME', lifetime=5)
            if answers:
                cname = str(answers[0])
                cdn_providers = {
                    'cloudflare': ['cloudflare.com', '.cf'],
                    'akamai': ['akamai.com', '.edgekey.net'],
                    'cloudfront': ['cloudfront.net'],
                    'fastly': ['fastly.net'],
                    'bunny': ['bunnycdn.com']
                }

                for provider, patterns in cdn_providers.items():
                    if any(pattern in cname for pattern in patterns):
                        return {
                            'cdn_enabled': True,
                            'cdn_provider': provider,
                            'cname': cname
                        }

                return {
                    'cdn_enabled': True,
                    'cdn_provider': 'unknown',
                    'cname': cname
                }

            return {
                'cdn_enabled': False,
                'cdn_provider': None,
                'cname': None
            }

        except:
            return None

    def get_domain_protection_status(self):
        """Get domain protection status from VNETWORK"""
        if not self.api_token:
            return None

        try:
            url = f'{self.api_base_url}/domains/{self.domain}/status'
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            return {
                'protection_status': data.get('status', 'unknown'),
                'last_check': data.get('last_check'),
                'health_score': data.get('health_score'),
                'issues': data.get('issues', [])
            }

        except:
            return None

    def collect(self):
        """Main collection logic"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain
        }

        ssl_status = self.get_ssl_status()
        if ssl_status:
            output.update(ssl_status)
        else:
            output['ssl_status'] = 'unknown'

        waf_status = self.get_waf_status_vnetwork()
        if waf_status:
            output.update(waf_status)
        else:
            output['waf_enabled'] = False
            output['waf_mode'] = 'unknown'

        cdn_status = self.get_cdn_status()
        if cdn_status:
            output.update(cdn_status)
        else:
            output['cdn_enabled'] = False

        protection_status = self.get_domain_protection_status()
        if protection_status:
            output.update(protection_status)
        else:
            output['protection_status'] = 'unknown'

        output['security_summary'] = {
            'ssl_valid': output.get('ssl_status') == 'valid',
            'waf_active': output.get('waf_enabled', False),
            'cdn_active': output.get('cdn_enabled', False),
            'protection_active': output.get('protection_status') == 'active'
        }

        return output

    def save(self, data):
        """Save snapshot to state/waap_status.json"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except:
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Collect WAAP/web protection data')
    parser.add_argument('--domain', help='Domain to monitor', default=None)
    args = parser.parse_args()

    collector = WAAPCollector(domain=args.domain)
    data = collector.collect()

    collector.save(data)
    print(json.dumps(data, indent=2))

    is_error = isinstance(data, dict) and 'error' in data
    sys.exit(0 if data else 1)


if __name__ == '__main__':
    main()
