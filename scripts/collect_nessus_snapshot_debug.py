#!/usr/bin/env python3
"""
NESSUS COLLECTOR - DEBUG VERSION
Investigate API calls, authentication, and response parsing
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from dotenv import load_dotenv
except ImportError:
    print('{"error": "Missing dependencies"}', file=sys.stderr)
    sys.exit(1)


class NessusDebug:
    def __init__(self):
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        self.nessus_url = os.environ.get('NESSUS_URL')
        self.access_key = os.environ.get('NESSUS_ACCESS_KEY')
        self.secret_key = os.environ.get('NESSUS_SECRET_KEY')
        self.session = requests.Session()
        self.session.verify = False

    def debug_server_status(self):
        """Test /server/status endpoint"""
        print("\n" + "="*60)
        print("1. SERVER STATUS CHECK")
        print("="*60)

        endpoint = f'{self.nessus_url}/server/status'
        print(f"\nEndpoint: {endpoint}")
        print(f"Auth Headers: X-ApiKeys: accessKey={self.access_key[:10]}...; secretKey={self.secret_key[:10]}...")

        self.session.headers.update({
            'X-ApiKeys': f'accessKey={self.access_key}; secretKey={self.secret_key}',
            'Content-Type': 'application/json'
        })

        try:
            resp = self.session.get(endpoint, timeout=10)
            print(f"Status Code: {resp.status_code}")
            print(f"Raw Response: {resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Parsed JSON: {json.dumps(data, indent=2)}")
                return data
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def debug_scanners_list(self):
        """Test /scanners endpoint"""
        print("\n" + "="*60)
        print("2. SCANNERS LIST")
        print("="*60)

        endpoint = f'{self.nessus_url}/scanners'
        print(f"\nEndpoint: {endpoint}")

        try:
            resp = self.session.get(endpoint, timeout=10)
            print(f"Status Code: {resp.status_code}")
            print(f"Raw Response: {resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Parsed JSON: {json.dumps(data, indent=2)[:1000]}")
                return data
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def debug_scans_list(self):
        """Test /scans endpoint"""
        print("\n" + "="*60)
        print("3. SCANS LIST")
        print("="*60)

        endpoint = f'{self.nessus_url}/scans'
        print(f"\nEndpoint: {endpoint}")

        try:
            resp = self.session.get(endpoint, timeout=10)
            print(f"Status Code: {resp.status_code}")
            print(f"Response Headers: {dict(resp.headers)}")
            print(f"Raw Response Length: {len(resp.text)} chars")
            print(f"Raw Response (first 1000 chars): {resp.text[:1000]}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Parsed JSON Keys: {list(data.keys())}")
                    print(f"Full JSON: {json.dumps(data, indent=2)[:2000]}")

                    if 'scans' in data:
                        print(f"\nScans Count: {len(data['scans'])}")
                        if data['scans']:
                            print("First Scan:")
                            print(json.dumps(data['scans'][0], indent=2))

                    return data
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {str(e)}")
                    return None
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def debug_scan_details(self, scan_id):
        """Get details for a specific scan"""
        print("\n" + "="*60)
        print(f"4. SCAN DETAILS: {scan_id}")
        print("="*60)

        endpoint = f'{self.nessus_url}/scans/{scan_id}'
        print(f"\nEndpoint: {endpoint}")

        try:
            resp = self.session.get(endpoint, timeout=10)
            print(f"Status Code: {resp.status_code}")
            print(f"Raw Response (first 1000 chars): {resp.text[:1000]}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Keys: {list(data.keys())}")
                print(f"Full Response: {json.dumps(data, indent=2)[:2000]}")
                return data
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def run_debug(self):
        """Run all debug checks"""
        print("\nNESS US COLLECTOR - DEBUG MODE")
        print(f"Nessus URL: {self.nessus_url}")
        print(f"Access Key: {self.access_key[:10] if self.access_key else 'NOT SET'}...")
        print(f"Secret Key: {self.secret_key[:10] if self.secret_key else 'NOT SET'}...")

        # Check server status
        server_status = self.debug_server_status()

        # Check scanners
        scanners = self.debug_scanners_list()

        # Check scans list
        scans_data = self.debug_scans_list()

        # Get first scan details if available
        if scans_data and 'scans' in scans_data and scans_data['scans']:
            first_scan = scans_data['scans'][0]
            scan_id = first_scan.get('id')
            if scan_id:
                self.debug_scan_details(scan_id)

        print("\n" + "="*60)
        print("DEBUG COMPLETE")
        print("="*60)


if __name__ == '__main__':
    debug = NessusDebug()
    debug.run_debug()
