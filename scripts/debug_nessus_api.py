#!/usr/bin/env python3
"""
DEBUG SCRIPT: Inspect Nessus API responses
Investigate what data is actually available
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
    print('Missing dependencies. Install: pip install requests python-dotenv')
    sys.exit(1)

# Load credentials
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

nessus_url = os.environ.get('NESSUS_URL')
access_key = os.environ.get('NESSUS_ACCESS_KEY')
secret_key = os.environ.get('NESSUS_SECRET_KEY')

if not all([nessus_url, access_key, secret_key]):
    print('ERROR: Nessus credentials not found')
    sys.exit(1)

session = requests.Session()
session.verify = False
session.headers.update({
    'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
    'Content-Type': 'application/json'
})

print('=' * 60)
print('NESSUS API DEBUGGING')
print('=' * 60)

# Get latest scan
print('\n[1] Getting latest scan...')
try:
    resp = session.get(f'{nessus_url}/scans', timeout=10)
    resp.raise_for_status()
    scans_data = resp.json()
    scans = scans_data.get('scans', [])

    if not scans:
        print('ERROR: No scans found')
        sys.exit(1)

    latest = sorted(scans, key=lambda x: x.get('last_modification_date', 0), reverse=True)[0]
    scan_id = latest.get('id')
    print(f'✓ Found scan: {latest.get("name")} (ID: {scan_id})')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)

# Inspect /scans/{scan_id}
print(f'\n[2] Inspecting /scans/{scan_id}...')
try:
    resp = session.get(f'{nessus_url}/scans/{scan_id}', timeout=10)
    resp.raise_for_status()
    scan_data = resp.json()

    print(f'Top-level keys: {list(scan_data.keys())}')

    if 'vulnerabilities' in scan_data:
        vulns = scan_data['vulnerabilities']
        print(f'Vulnerabilities count: {len(vulns)}')
        if vulns:
            print(f'First vulnerability keys: {list(vulns[0].keys())}')
            print(f'First vulnerability (sample):\n{json.dumps(vulns[0], indent=2)[:500]}...')
except Exception as e:
    print(f'ERROR: {e}')

# Inspect /scans/{scan_id}/hosts
print(f'\n[3] Inspecting /scans/{scan_id}/hosts...')
try:
    resp = session.get(f'{nessus_url}/scans/{scan_id}/hosts', timeout=10)
    resp.raise_for_status()
    hosts_data = resp.json()

    print(f'Response keys: {list(hosts_data.keys())}')

    if 'hosts' in hosts_data:
        hosts = hosts_data['hosts']
        print(f'Hosts count: {len(hosts)}')
        if hosts:
            print(f'First host keys: {list(hosts[0].keys())}')
            print(f'First host (sample):\n{json.dumps(hosts[0], indent=2)}')
    else:
        print(f'No "hosts" key in response')
        print(f'Full response: {json.dumps(hosts_data, indent=2)[:1000]}')
except requests.exceptions.HTTPError as e:
    print(f'HTTP Error: {e.response.status_code}')
    print(f'Response: {e.response.text[:500]}')
except Exception as e:
    print(f'ERROR: {e}')

# Try /scans/{scan_id}/hosts/{host_id}
print(f'\n[4] Inspecting /scans/{scan_id}/hosts/{{host_id}}...')
try:
    resp = session.get(f'{nessus_url}/scans/{scan_id}/hosts', timeout=10)
    resp.raise_for_status()
    hosts_data = resp.json()

    if hosts_data.get('hosts'):
        first_host_id = hosts_data['hosts'][0].get('host_id')
        if first_host_id:
            resp = session.get(f'{nessus_url}/scans/{scan_id}/hosts/{first_host_id}', timeout=10)
            resp.raise_for_status()
            host_detail = resp.json()
            print(f'Response keys: {list(host_detail.keys())}')
            print(f'Sample: {json.dumps(host_detail, indent=2)[:1000]}...')
        else:
            print('No host_id found in hosts list')
    else:
        print('No hosts in /scans/{scan_id}/hosts response')
except requests.exceptions.HTTPError as e:
    print(f'HTTP Error: {e.response.status_code}')
    print(f'Response: {e.response.text[:500]}')
except Exception as e:
    print(f'ERROR: {e}')

# Get scan compliance data
print(f'\n[5] Checking for alternative data sources...')
try:
    endpoints = [
        f'/scans/{scan_id}/export',
        f'/assets',
        f'/assets/hosts'
    ]

    for endpoint in endpoints:
        try:
            resp = session.get(f'{nessus_url}{endpoint}', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print(f'✓ {endpoint}: {type(data).__name__} with keys {list(data.keys())[:5]}')
        except:
            pass
except Exception as e:
    print(f'Note: {e}')

print('\n' + '=' * 60)
print('END DEBUG')
print('=' * 60)
