#!/usr/bin/env python3
"""
Nessus API Client - Direct API integration without CSV exports
Connects to Nessus Professional/Essentials scanner
"""

import os
import json
import requests
import ssl
import warnings
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class NessusClient:
    def __init__(self):
        self.url = os.getenv('NESSUS_URL', 'https://localhost:8834')
        self.access_key = os.getenv('NESSUS_ACCESS_KEY')
        self.secret_key = os.getenv('NESSUS_SECRET_KEY')
        self.base_endpoint = ''  # Will be set during auth
        self.session = self._create_session()
        self.session_token = None
        self.authenticate()

    def _create_session(self):
        session = requests.Session()
        session.verify = False
        session.headers.update({
            'Content-Type': 'application/json',
            'X-ApiKeys': f'accessKey={self.access_key}; secretKey={self.secret_key}'
        })
        return session

    def authenticate(self) -> bool:
        try:
            # Debug: Print connection details
            print(f'[NESSUS] URL: {self.url}')
            print(f'[NESSUS] Headers: {self.session.headers}')

            # Test endpoint
            endpoint = f'{self.url}/scans'
            print(f'[NESSUS] Testing endpoint: {endpoint}')

            resp = self.session.get(endpoint, timeout=5)
            print(f'[NESSUS] Status: {resp.status_code}')
            print(f'[NESSUS] Response: {resp.text[:200]}')

            if resp.status_code == 200:
                print('[NESSUS] OK: Authentication successful')
                return True
            else:
                print(f'[NESSUS] FAIL: Status {resp.status_code}, trying alternate endpoints...')

                # Try alternate endpoints
                for alt_endpoint in [
                    f'{self.url}/scans',
                    f'{self.url}/rest/scans',
                    f'{self.url}/api/scans',
                    f'{self.url}/nessus6/scans',
                ]:
                    print(f'[NESSUS] Trying: {alt_endpoint}')
                    alt_resp = self.session.get(alt_endpoint, timeout=5)
                    print(f'[NESSUS]   -> {alt_resp.status_code}')
                    if alt_resp.status_code == 200:
                        self.base_endpoint = alt_endpoint.replace('/scans', '')
                        print(f'[NESSUS] Found working base: {self.base_endpoint}')
                        return True

                return False
        except Exception as e:
            print(f'[NESSUS] FAIL: Connection failed: {e}')
            return False

    def get_scans(self) -> List[Dict]:
        try:
            # Use discovered endpoint or default
            endpoint = f'{self.base_endpoint}/scans' if self.base_endpoint else f'{self.url}/scans'
            print(f'[NESSUS] Getting scans from: {endpoint}')

            resp = self.session.get(endpoint)
            print(f'[NESSUS] Scans response: {resp.status_code}')

            if resp.status_code == 200:
                data = resp.json()
                print(f'[NESSUS] Scans data: {data}')
                return data.get('scans', [])
            return []
        except Exception as e:
            print(f'[NESSUS] Error fetching scans: {e}')
            return []

    def get_scan_details(self, scan_id: int) -> Optional[Dict]:
        try:
            resp = self.session.get(f'{self.url}/nessus6/scans/{scan_id}')
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f'[NESSUS] Error fetching scan {scan_id}: {e}')
            return None

    def get_scan_hosts(self, scan_id: int) -> List[Dict]:
        try:
            # Try direct scan details first
            endpoint = f'{self.url}/scans/{scan_id}'
            print(f'[NESSUS] Getting scan details from: {endpoint}')
            resp = self.session.get(endpoint)
            print(f'[NESSUS] Scan details response: {resp.status_code}')
            if resp.status_code == 200:
                data = resp.json()
                # Hosts might be in 'hosts' or within the response itself
                hosts = data.get('hosts', [])
                print(f'[NESSUS] Hosts in details: {len(hosts)}')
                if hosts:
                    return hosts

            # Try alternate endpoint
            endpoint = f'{self.url}/scans/{scan_id}/hosts'
            print(f'[NESSUS] Trying: {endpoint}')
            resp = self.session.get(endpoint)
            print(f'[NESSUS] Response: {resp.status_code}')
            if resp.status_code == 200:
                data = resp.json()
                return data.get('hosts', [])
            else:
                print(f'[NESSUS] Error: {resp.text[:100]}')

            return []
        except Exception as e:
            print(f'[NESSUS] Error fetching hosts for scan {scan_id}: {e}')
            return []

    def get_host_details(self, scan_id: int, host_id: int) -> Optional[Dict]:
        try:
            # Try v6 endpoint first
            resp = self.session.get(f'{self.url}/nessus6/scans/{scan_id}/hosts/{host_id}')
            if resp.status_code == 200:
                return resp.json()

            # Try alternate endpoint
            resp = self.session.get(f'{self.url}/scans/{scan_id}/hosts/{host_id}')
            if resp.status_code == 200:
                return resp.json()

            return None
        except Exception as e:
            print(f'[NESSUS] Error fetching host {host_id}: {e}')
            return None

    def get_vulnerabilities(self, scan_id: int, host_id: int) -> List[Dict]:
        try:
            resp = self.session.get(
                f'{self.url}/nessus6/scans/{scan_id}/hosts/{host_id}/plugins',
                params={'filter.0.quality_metrics.cvss_v3_base_score': 'gte:0'}
            )
            if resp.status_code == 200:
                return resp.json().get('plugins', [])
            return []
        except Exception as e:
            print(f'[NESSUS] Error fetching vulnerabilities: {e}')
            return []

    def get_plugin_details(self, plugin_id: int, scan_id: int, host_id: int) -> Optional[Dict]:
        try:
            resp = self.session.get(
                f'{self.url}/nessus6/scans/{scan_id}/hosts/{host_id}/plugins/{plugin_id}'
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f'[NESSUS] Error fetching plugin {plugin_id}: {e}')
            return None

    def export_scan(self, scan_id: int, format_type: str = 'nessus') -> Optional[int]:
        try:
            payload = {'format': format_type}
            resp = self.session.post(f'{self.url}/nessus6/scans/{scan_id}/export', json=payload)
            if resp.status_code == 200:
                return resp.json().get('file')
            return None
        except Exception as e:
            print(f'[NESSUS] Error exporting scan: {e}')
            return None
