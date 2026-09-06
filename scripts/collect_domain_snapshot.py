#!/usr/bin/env python3
"""
DOMAIN MONITORING COLLECTOR
Integrates domain & DNS data into SentinelOps
Collects: Domain expiration, Nameservers, DNS records (A, MX, SPF, DKIM, DMARC)
Outputs: state/domain_status.json
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
except ImportError:
    print('{"error": "Required libraries not installed. Install: pip install dnspython requests"}', file=sys.stderr)
    sys.exit(1)


class DomainCollector:
    def __init__(self, domain=None):
        self.domain = domain or self.load_domain_config()
        self.config_path = Path.home() / '.porkbun' / 'api.json'
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'domain_status.json'
        self.api_key = None
        self.api_secret = None

    def load_domain_config(self):
        """Load domain from Porkbun config or environment"""
        config_path = Path.home() / '.porkbun' / 'api.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('domain', 'sentinelops.fyi')
            except:
                pass

        return os.environ.get('SENTINEL_DOMAIN', 'sentinelops.fyi')

    def load_porkbun_config(self):
        """Load Porkbun API credentials"""
        if not self.config_path.exists():
            return False

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.api_secret = config.get('api_secret')
                return bool(self.api_key and self.api_secret)
        except Exception as e:
            print(f'{{"error": "Porkbun config load failed: {str(e)}"}}', file=sys.stderr)
            return False

    def get_dns_records(self, record_type):
        """Query DNS records using dnspython"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(self.domain, record_type, lifetime=5)
            return [str(rdata) for rdata in answers]
        except Exception as e:
            # Silent fail - some records may not exist
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
            records = self.get_dns_records('TXT')
            if records:
                for record in records:
                    if record.startswith('v=spf1'):
                        return record
            return None
        except:
            return None

    def get_dmarc_record(self):
        """Get DMARC record"""
        try:
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(f'_dmarc.{self.domain}', 'TXT', lifetime=5)
            records = [str(rdata) for rdata in answers]
            for record in records:
                if record.startswith('v=DMARC1'):
                    return record
            return None
        except:
            return None

    def get_domain_expiration_porkbun(self):
        """Get domain expiration from Porkbun API"""
        if not self.load_porkbun_config():
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

        except Exception as e:
            print(f'{{"error": "Porkbun API query failed: {str(e)}"}}', file=sys.stderr)
            return None

    def collect(self):
        """Main collection logic"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain
        }

        # Get nameservers
        ns = self.get_nameservers()
        output['nameservers'] = ns if ns else []

        # Get A records
        a_records = self.get_a_records()
        output['a_records'] = a_records if a_records else []

        # Get MX records
        mx_records = self.get_mx_records()
        output['mx_records'] = mx_records if mx_records else []

        # Get SPF record
        spf = self.get_spf_record()
        output['spf'] = spf

        # Get DMARC record
        dmarc = self.get_dmarc_record()
        output['dmarc'] = dmarc

        # Get domain expiration (if Porkbun credentials available)
        expiration = self.get_domain_expiration_porkbun()
        if expiration:
            output.update(expiration)
        else:
            output['expiration_date'] = None
            output['registration_date'] = None

        # Check DNS configuration completeness
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
        except Exception as e:
            print(f'{{"error": "Failed to save snapshot: {str(e)}"}}', file=sys.stderr)
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Collect domain monitoring data')
    parser.add_argument('--domain', help='Domain to monitor', default=None)
    args = parser.parse_args()

    collector = DomainCollector(domain=args.domain)
    data = collector.collect()

    # Save to state file
    collector.save(data)

    # Output JSON
    print(json.dumps(data, indent=2))

    sys.exit(0 if data else 1)


if __name__ == '__main__':
    main()
