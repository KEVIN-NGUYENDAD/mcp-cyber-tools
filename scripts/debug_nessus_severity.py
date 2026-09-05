#!/usr/bin/env python3
"""Debug Nessus severity values"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

nessus_url = os.environ.get('NESSUS_URL')
access_key = os.environ.get('NESSUS_ACCESS_KEY')
secret_key = os.environ.get('NESSUS_SECRET_KEY')

session = requests.Session()
session.verify = False
session.headers.update({
    'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
    'Content-Type': 'application/json'
})

# Get latest scan
resp = session.get(f'{nessus_url}/scans', timeout=10)
data = resp.json()

if data.get('scans'):
    latest = sorted(data['scans'], key=lambda x: x.get('last_modification_date', 0), reverse=True)[0]
    scan_id = latest.get('id')

    print(f"Latest Scan: {latest.get('name')}")
    print(f"Scan ID: {scan_id}")
    print()

    # Get scan details
    resp = session.get(f'{nessus_url}/scans/{scan_id}', timeout=10)
    scan_data = resp.json()

    vulns = scan_data.get('vulnerabilities', [])
    print(f"Total Vulnerabilities: {len(vulns)}")
    print()

    severity_map = {}
    for vuln in vulns:
        severity = vuln.get('severity')
        if severity not in severity_map:
            severity_map[severity] = []
        severity_map[severity].append(vuln)

    print("Severity Distribution:")
    for sev in sorted(severity_map.keys()):
        count = len(severity_map[sev])
        print(f"  Severity {sev}: {count} vulnerabilities")
        if count > 0:
            print(f"    Example: {severity_map[sev][0]}")

    print()
    print("Raw Severity Values:")
    for i, vuln in enumerate(vulns[:5]):
        print(f"  Vuln {i}: severity={vuln.get('severity')}, plugin_name={vuln.get('plugin_name')}")
