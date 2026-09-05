#!/usr/bin/env python3
"""
DOMAIN MONITORING COLLECTOR (Phase H)
Integrates domain & DNS data into SentinelOps
Collects: Domain expiration, Nameservers, DNS records
Outputs: state/domain_status.json

Credentials from .env:
- PORKBUN_API_KEY (optional)
- PORKBUN_SECRET_KEY (optional)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import dns.resolver
    import dns.rdatatype
    import requests
    from dotenv import load_dotenv
except ImportError:
    print('{"error": "Missing dependencies. Install: pip install dnspython requests python-dotenv"}', file=sys.stderr)
    sys.exit(1)


class DomainCollector:
    def __init__(self, domain=None):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'domain_status.json'
        self.load_env()
        self.domain = domain or os.environ.get('DOMAIN', 'sentinelops.fyi')
        self.api_key = os.environ.get('PORKBUN_API_KEY')
        self.api_secret = os.environ.get('PORKBUN_SECRET_KEY')

    def load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

    def get_dns_records(self, record_type):
        """Query DNS records using dnspython"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, record_type, lifetime=5)
            return [str(rdata) for rdata in answers]
        except Exception:
            return None

    def get_nameservers(self):
        """Get nameservers for domain"""
        try:
            records = self.get_dns_records('NS')
            return records if records else None
        except:
            return None

    def get_a_records(self):
        """Get A records (IPv4)"""
        try:
            records = self.get_dns_records('A')
            return records if records else None
        except:
            return None

    def get_mx_records(self):
        """Get MX records (Mail)"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, 'MX', lifetime=5)
            return [f"{int(rdata.preference)} {str(rdata.exchange)}" for rdata in answers]
        except:
            return None

    def get_spf_record(self):
        """Get SPF record"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, 'TXT', lifetime=5)
            for rdata in answers:
                for txt_string in rdata.strings:
                    record = txt_string.decode('utf-8') if isinstance(txt_string, bytes) else str(txt_string)
                    if record.startswith('v=spf1'):
                        return record
            return None
        except:
            return None

    def get_dmarc_record(self):
        """Get DMARC record (TXT or CNAME)"""
        try:
            resolver = dns.resolver.Resolver()
            # Try TXT record first
            try:
                answers = resolver.resolve(f'_dmarc.{self.domain}', 'TXT', lifetime=5)
                for rdata in answers:
                    for txt_string in rdata.strings:
                        record = txt_string.decode('utf-8') if isinstance(txt_string, bytes) else str(txt_string)
                        if record.startswith('v=DMARC1'):
                            return record
            except (dns.resolver.NoAnswer, dns.exception.DNSException):
                pass

            # Try CNAME (common for hosted DMARC services)
            try:
                answers = resolver.resolve(f'_dmarc.{self.domain}', 'CNAME', lifetime=5)
                for rdata in answers:
                    return f"CNAME {str(rdata)}"
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
                pass

            return None
        except:
            return None

    def get_domain_expiration_porkbun(self):
        """Get domain expiration from Porkbun API"""
        if not (self.api_key and self.api_secret):
            return None

        try:
            url = 'https://api.porkbun.com/api/json/v3/domain/info'
            payload = {
                'domain': self.domain,
                'apikey': self.api_key,
                'secretapikey': self.api_secret
            }

            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') == 'success':
                return {
                    'expiration_date': data.get('expiredate'),
                    'registration_date': data.get('registrationdate'),
                    'auto_renew': data.get('autorenew', False)
                }
            return None

        except:
            return None

    def collect(self):
        """Main collection logic"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain
        }

        ns = self.get_nameservers()
        output['nameservers'] = ns if ns else []

        a_records = self.get_a_records()
        output['a_records'] = a_records if a_records else []

        mx_records = self.get_mx_records()
        output['mx_records'] = mx_records if mx_records else []

        spf = self.get_spf_record()
        output['spf'] = spf

        dmarc = self.get_dmarc_record()
        output['dmarc'] = dmarc

        expiration = self.get_domain_expiration_porkbun()
        if expiration:
            output.update(expiration)
        else:
            output['expiration_date'] = None
            output['registration_date'] = None

        output['dns_complete'] = {
            'has_nameservers': bool(ns),
            'has_a_records': bool(a_records),
            'has_mx_records': bool(mx_records),
            'has_spf': bool(spf),
            'has_dmarc': bool(dmarc)
        }

        return output

    def save(self, data):
        """Save snapshot to state/domain_status.json"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except:
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Collect domain monitoring data')
    parser.add_argument('--domain', help='Domain to monitor', default=None)
    args = parser.parse_args()

    collector = DomainCollector(domain=args.domain)
    data = collector.collect()

    collector.save(data)
    print(json.dumps(data, indent=2))

    is_error = isinstance(data, dict) and 'error' in data
    sys.exit(1 if is_error else 0)


if __name__ == '__main__':
    main()
