#!/usr/bin/env python3
"""
NESSUS SNAPSHOT COLLECTOR (Phase G)
Integrates Nessus vulnerability scanner data into SentinelOps
Collects: Scanner status, Latest scan, Vulnerability counts
Outputs: state/nessus_status.json

Credentials loaded from .env file:
- NESSUS_URL
- NESSUS_ACCESS_KEY
- NESSUS_SECRET_KEY
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Import atomic write functions for file safety (TD-L3-001, TD-L3-002, TD-L3-003)
from state_manager import write_state_atomic, read_state_safe

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from dotenv import load_dotenv
except ImportError as e:
    print(f'{{"error": "Missing dependencies. Install: pip install requests python-dotenv"}}', file=sys.stderr)
    sys.exit(1)


class NessusCollector:
    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.state_dir.mkdir(exist_ok=True)
        self.output_file = self.state_dir / 'nessus_status.json'
        self.nessus_url = None
        self.access_key = None
        self.secret_key = None
        self.session = requests.Session()
        self.session.verify = False
        self.load_env()

    def load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            example_path = Path(__file__).parent.parent / '.env.example'
            if example_path.exists():
                pass

    def load_credentials(self):
        """Load credentials from .env file (via environment variables)"""
        self.nessus_url = os.environ.get('NESSUS_URL')
        self.access_key = os.environ.get('NESSUS_ACCESS_KEY')
        self.secret_key = os.environ.get('NESSUS_SECRET_KEY')

        return bool(self.nessus_url and self.access_key and self.secret_key)

    def set_auth_headers(self):
        """Configure session headers for Nessus API v2"""
        self.session.headers.update({
            'X-ApiKeys': f'accessKey={self.access_key}; secretKey={self.secret_key}',
            'Content-Type': 'application/json'
        })

    # AQ-021. `status: 'on'` từ `/scanners` là trạng thái LIÊN KẾT của scanner
    # daemon (nó có đang kết nối với Nessus manager hay không) — KHÔNG phải
    # trạng thái của một job quét cụ thể. Bản đồ cũ `'on' -> 'running'` mượn
    # đúng cái tên một job đang chạy dùng, nên `scanner_status: running` đứng
    # cạnh `scan_age_hours: 158` đọc như "đã quét suốt 158 giờ" — một mâu
    # thuẫn không hề tồn tại. Scanner online liên tục là bình thường; bản quét
    # gần nhất xong từ lâu là một sự thật KHÁC, và `scan_stale` bên dưới mới
    # là trường trả lời đúng câu đó.
    SCANNER_LINK_STATUS = {'on': 'online', 'off': 'offline'}

    def get_scanner_status(self):
        """Trạng thái LIÊN KẾT của scanner daemon — không nói gì về một job quét."""
        try:
            resp = self.session.get(f'{self.nessus_url}/scanners', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get('scanners'):
                scanner = data['scanners'][0]
                raw = scanner.get('status', 'unknown')
                return self.SCANNER_LINK_STATUS.get(raw, 'unknown'), raw
            return 'unknown', None
        except Exception as e:
            return 'error', None

    def find_scan_by_name(self, target_name):
        """Find scan by name (primary: Home Network Discovery)"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans', timeout=10)
            resp.raise_for_status()
            data = resp.json()

            scans = data.get('scans', [])
            if not scans:
                return None

            # Look for exact name match first
            for scan in scans:
                if scan.get('name') == target_name:
                    scan_id = scan.get('id')
                    scan_name = scan.get('name', 'Unknown')
                    last_scan_time = scan.get('last_modification_date')
                    if scan_id:
                        return self.get_scan_details(scan_id, last_scan_time, scan_name)

            return None

        except Exception as e:
            return None

    def get_latest_scan(self):
        """Get latest scan results (deprecated - use find_scan_by_name)"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans', timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if not data.get('scans'):
                return None

            scans = data.get('scans', [])
            if not scans:
                return None

            latest = sorted(scans, key=lambda x: x.get('last_modification_date', 0), reverse=True)[0]
            scan_id = latest.get('id')
            scan_name = latest.get('name', 'Unknown')
            last_scan_time = latest.get('last_modification_date')

            if scan_id:
                return self.get_scan_details(scan_id, last_scan_time, scan_name)
            return None

        except Exception as e:
            return None

    def get_scan_details(self, scan_id, timestamp, scan_name):
        """Get detailed vulnerability counts from scan"""
        try:
            resp = self.session.get(f'{self.nessus_url}/scans/{scan_id}', timeout=10)
            resp.raise_for_status()
            data = resp.json()

            vulnerabilities = data.get('vulnerabilities', [])

            severity_counts = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            }

            # AQ-021 / AQ-041, ba vòng chưa trả: `assets.json` cộng lại ra 399
            # lỗ hổng, `nessus_status.json` khai `total: 64`, trên cùng một bản
            # quét. Chênh 6.2 lần, và ba vòng audit đọc nó như một con số sai.
            #
            # Không con số nào sai. Chúng đếm hai ĐƠN VỊ khác nhau:
            #
            #   `vulnerabilities[]` của Nessus đã gộp theo plugin — mỗi phần tử
            #   là một plugin kèm `count` = số host dính. 64 = số plugin riêng
            #   biệt.
            #
            #   `assets[].vulnerability_count` cộng severity theo từng host, nên
            #   nó đếm lượt (host × plugin). 399 = số lượt.
            #
            # Lỗi thật nằm ở chỗ cả hai cùng mang tên `total`, và không tệp nào
            # nói mình đếm gì. Nên đây không phải bài toán sửa một phép đếm —
            # mà là bài toán đặt tên cho đơn vị, rồi ghi cả hai để còn đối chiếu
            # được. Sửa một trong hai con số cho "khớp" sẽ phá đúng cái thông
            # tin mà nó đang mang.
            instances = 0
            for vuln in vulnerabilities:
                try:
                    instances += max(1, int(vuln.get('count') or 1))
                except (TypeError, ValueError):
                    instances += 1

            for vuln in vulnerabilities:
                severity = vuln.get('severity', -1)
                if severity == 4:
                    severity_counts['critical'] += 1
                elif severity == 3:
                    severity_counts['high'] += 1
                elif severity == 2:
                    severity_counts['medium'] += 1
                elif severity == 1:
                    severity_counts['low'] += 1
                elif severity == 0:
                    severity_counts['info'] += 1
                else:
                    severity_counts['info'] += 1

            scan_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            age_hours = (datetime.now() - scan_time).total_seconds() / 3600

            return {
                'last_scan': scan_time.isoformat(),
                'scan_name': scan_name,
                'scan_age_hours': round(age_hours, 1),
                'critical': severity_counts['critical'],
                'high': severity_counts['high'],
                'medium': severity_counts['medium'],
                'low': severity_counts['low'],
                'info': severity_counts['info'],
                # `total` giữ nguyên nghĩa cũ để không consumer nào đổi nghĩa
                # dưới chân, nhưng từ đây nó đi kèm nhãn đơn vị của chính mình.
                'total': len(vulnerabilities),
                'total_unit': 'distinct_plugins',
                'distinct_plugins': len(vulnerabilities),
                # Đơn vị mà `assets[].vulnerability_count` đang cộng. Có trường
                # này thì hai tệp mới đối chiếu được bằng một phép so tổng.
                'total_instances': instances,
            }

        except Exception as e:
            return None

    def collect(self):
        """Main collection logic"""

        if not self.load_credentials():
            return {
                'error': 'Nessus API credentials not found',
                'solution': 'Create or update .env file in project root',
                'required_credentials_in_env': {
                    'NESSUS_URL': 'https://localhost:8834',
                    'NESSUS_ACCESS_KEY': 'from Nessus Settings > My Account > API Keys',
                    'NESSUS_SECRET_KEY': 'from Nessus Settings > My Account > API Keys'
                },
                'template': 'Copy .env.example to .env and fill in your credentials'
            }

        self.set_auth_headers()

        output = {
            'timestamp': datetime.now().isoformat(),
            'nessus_url': self.nessus_url,
            'nessus_endpoint': 'https://localhost:8834'
        }

        status, raw_status = self.get_scanner_status()
        output['scanner_status'] = status
        output['scanner_status_raw'] = raw_status

        # Try to find "Home Network Discovery" scan first
        scan_data = self.find_scan_by_name('Home Network Discovery')

        # Fallback to latest if specific scan not found
        if not scan_data:
            scan_data = self.get_latest_scan()

        if scan_data:
            output.update(scan_data)
        else:
            output.update({
                'last_scan': None,
                'scan_name': 'No scans found',
                'scan_age_hours': None,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
                'total': 0,
                'total_unit': 'distinct_plugins',
                'distinct_plugins': 0,
                'total_instances': 0,
            })

        return output

    def save(self, data):
        """Save snapshot to state/nessus_status.json"""
        try:
            write_state_atomic(self.output_file, data, indent=2)
            return True
        except Exception as e:
            return False


def main():
    collector = NessusCollector()
    data = collector.collect()

    collector.save(data)
    print(json.dumps(data, indent=2))

    is_error = isinstance(data, dict) and 'error' in data
    sys.exit(1 if is_error else 0)


if __name__ == '__main__':
    main()
