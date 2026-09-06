#!/usr/bin/env python3
"""
DEBUG: Investigate Nessus host detail data
Check what additional host info is available for asset enrichment
"""

import json
import sys
import os
from pathlib import Path

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from dotenv import load_dotenv
except ImportError:
    print('Missing dependencies')
    sys.exit(1)

env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv()

nessus_url = os.environ.get('NESSUS_URL')
access_key = os.environ.get('NESSUS_ACCESS_KEY')
secret_key = os.environ.get('NESSUS_SECRET_KEY')

if not all([nessus_url, access_key, secret_key]):
    print('ERROR: Credentials not found')
    sys.exit(1)

session = requests.Session()
session.verify = False
session.headers.update({
    'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
    'Content-Type': 'application/json'
})

print('=' * 70)
print('NESSUS HOST DETAIL INVESTIGATION')
print('=' * 70)

# Get Home Network Discovery scan
try:
    resp = session.get(f'{nessus_url}/scans', timeout=10)
    resp.raise_for_status()
    scans = resp.json()['scans']

    home_scan = None
    for scan in scans:
        if scan.get('name') == 'Home Network Discovery':
            home_scan = scan
            break

    if not home_scan:
        print('ERROR: Home Network Discovery scan not found')
        sys.exit(1)

    scan_id = home_scan.get('id')
    print(f'✓ Found scan: {home_scan["name"]} (ID: {scan_id})')

except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)

# Get scan data to access hosts
print(f'\n[1] Getting scan data for {scan_id}...')
try:
    resp = session.get(f'{nessus_url}/scans/{scan_id}', timeout=10)
    resp.raise_for_status()
    scan_data = resp.json()

    hosts = scan_data.get('hosts', [])
    print(f'✓ Hosts found: {len(hosts)}')

    if not hosts:
        print('No hosts in scan')
        sys.exit(1)

    # Examine each host from the scan data
    print(f'\n[2] Examining hosts from /scans/{scan_id} response...')
    for idx, host in enumerate(hosts[:3]):  # First 3 hosts
        print(f'\n  Host {idx + 1}: {host.get("hostname")}')
        print(f'  Fields: {list(host.keys())}')
        print(f'  Vulnerability breakdown: C={host.get("critical", 0)}, H={host.get("high", 0)}, M={host.get("medium", 0)}, L={host.get("low", 0)}, I={host.get("info", 0)}')

except Exception as e:
    print(f'ERROR: {e}')

# Try to get vulnerability details with more fields
print(f'\n[3] Examining vulnerability details for asset info...')
try:
    resp = session.get(f'{nessus_url}/scans/{scan_id}', timeout=10)
    resp.raise_for_status()
    scan_data = resp.json()

    vulns = scan_data.get('vulnerabilities', [])
    print(f'✓ Vulnerabilities: {len(vulns)}')

    if vulns:
        print(f'\n  First vulnerability fields: {list(vulns[0].keys())}')
        print(f'  Sample:\n{json.dumps(vulns[0], indent=4)[:1000]}')

        # Check if any vulnerabilities have asset/host info
        has_asset_info = False
        for vuln in vulns[:20]:
            if vuln.get('asset') or vuln.get('host') or vuln.get('hostname'):
                has_asset_info = True
                print(f'\n  Found host/asset info in vulnerability:')
                if vuln.get('asset'):
                    print(f'    asset: {json.dumps(vuln["asset"], indent=6)[:500]}')
                if vuln.get('host'):
                    print(f'    host: {vuln.get("host")}')
                if vuln.get('hostname'):
                    print(f'    hostname: {vuln.get("hostname")}')
                break

        if not has_asset_info:
            print(f'\n  No asset/host info found in vulnerabilities')

except Exception as e:
    print(f'ERROR: {e}')

# Try alternative endpoints for host info
print(f'\n[4] Checking alternative endpoints...')
endpoints_to_try = [
    f'/scans/{scan_id}/hosts',
    f'/assets',
    f'/assets/hosts',
    f'/scans/{scan_id}/host-details',
]

for endpoint in endpoints_to_try:
    try:
        resp = session.get(f'{nessus_url}{endpoint}', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f'✓ {endpoint}: Returns data')
            if isinstance(data, dict):
                print(f'  Top-level keys: {list(data.keys())[:10]}')
        elif resp.status_code == 405:
            print(f'✗ {endpoint}: 405 Method Not Allowed')
        elif resp.status_code == 404:
            print(f'✗ {endpoint}: 404 Not Found')
        else:
            print(f'? {endpoint}: {resp.status_code}')
    except Exception as e:
        print(f'✗ {endpoint}: {type(e).__name__}')

# Check for compliance/host-based data
print(f'\n[5] Checking compliance/host fields in scan...')
try:
    if 'compliance' in scan_data:
        print(f'✓ Compliance field exists: {type(scan_data["compliance"]).__name__}')

    if 'comphosts' in scan_data:
        comphosts = scan_data['comphosts']
        print(f'✓ Comphosts field exists: {len(comphosts)} entries')
        if comphosts:
            print(f'  First comphhost keys: {list(comphosts[0].keys())}')

    if 'filters' in scan_data:
        print(f'✓ Filters field exists')

except Exception as e:
    print(f'Note: {e}')

print('\n' + '=' * 70)
print('SUMMARY:')
print('- Hosts array contains: hostname (IP), vulnerability counts, severity breakdown')
print('- Vulnerabilities array limited: plugin info, severity, no asset details')
print('- Alternative endpoints mostly unavailable (405/404)')
print('- Need to use plugin family/names for service classification')
print('- Consider network patterns for device type classification')
print('=' * 70)
