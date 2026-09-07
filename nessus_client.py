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

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class NessusClient:
    def __init__(self):
        self.url = os.getenv('NESSUS_URL', 'https://localhost:8834')
        self.access_key = os.getenv('NESSUS_ACCESS_KEY')
        self.secret_key = os.getenv('NESSUS_SECRET_KEY')
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
            resp = self.session.get(f'{self.url}/nessus6/scans', timeout=5)
            if resp.status_code == 200:
                print('[NESSUS] OK: Authentication successful')
                return True
            else:
                print(f'[NESSUS] FAIL: Auth failed: {resp.status_code}')
                return False
        except Exception as e:
            print(f'[NESSUS] FAIL: Connection failed: {e}')
            return False

    def get_scans(self) -> List[Dict]:
        try:
            resp = self.session.get(f'{self.url}/nessus6/scans')
            if resp.status_code == 200:
                return resp.json().get('scans', [])
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
            resp = self.session.get(f'{self.url}/nessus6/scans/{scan_id}/hosts')
            if resp.status_code == 200:
                return resp.json().get('hosts', [])
            return []
        except Exception as e:
            print(f'[NESSUS] Error fetching hosts for scan {scan_id}: {e}')
            return []

    def get_host_details(self, scan_id: int, host_id: int) -> Optional[Dict]:
        try:
            resp = self.session.get(f'{self.url}/nessus6/scans/{scan_id}/hosts/{host_id}')
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
