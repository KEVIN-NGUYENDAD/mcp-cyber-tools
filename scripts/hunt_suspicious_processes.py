#!/usr/bin/env python3
"""
SUSPICIOUS PROCESS HUNTING — LIVE

Nguồn: MCP tool `huntLivingOffTheLand`, `huntNetworkBeacons`,
`huntIndicators(unusual_binaries)` — chạy trên máy này qua scripts/mcp_bridge.py.

Bản cũ xuất 6 tiến trình bịa (`certutil.exe -urlcache -f http://malicious.com/...`).
Bản này xuất tiến trình thật, và vì thế phải dè dặt: `powershell.exe` hay
`cmd.exe` đang chạy là chuyện bình thường trên mọi máy Windows. Điều đáng ngờ
không phải là *tên* binary mà là *nơi nó nằm* và *nó đang nói chuyện với ai*.

Populates: state/hunting_suspicious_processes.json
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from state_manager import write_state_atomic
import ioc_attribution
import detection_quality
from mcp_bridge import McpBridge, McpBridgeError, as_list

HUNT_VERSION = '2.0.0'

SUSPECT_PATH_RE = re.compile(
    r'(\\Temp\\|\\AppData\\Local\\Temp\\|\\ProgramData\\|\\Users\\Public\\|\\Downloads\\)',
    re.I)

# Binary hiếm khi có lý do chính đáng để chạy trên máy trạm cá nhân.
HIGH_RISK_LOLBINS = set(['mshta', 'bitsadmin', 'certutil', 'regsvr32',
                         'installutil', 'msbuild', 'regasm', 'regsvcs'])

# Cổng mà lưu lượng bình thường vẫn dùng.
COMMON_PORTS = set([80, 443, 8080, 53])


class SuspiciousProcessHunter(object):

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_suspicious_processes.json'
        self.indicators = []
        self.errors = []
        self.observable = False
        self.tools_used = []
        self._seen = {}
        self.self_log = detection_quality.SelfObservationLog()

    # -- thu thập ---------------------------------------------------------

    def call(self, bridge, tool, arguments=None):
        outcome = bridge.call_tool(tool, arguments)
        self.tools_used.append({
            'tool': tool,
            'ok': outcome['ok'],
            'records': len(as_list(outcome['parsed'])),
            'duration': outcome['duration'],
            'error': outcome['error'],
        })
        if not outcome['ok']:
            self.errors.append('{}: {}'.format(tool, outcome['error']))
            return []
        self.observable = True
        return as_list(outcome['parsed'])

    def collect(self, bridge):
        lolbins = self.call(bridge, 'huntLivingOffTheLand')
        beacons = self.call(bridge, 'huntNetworkBeacons')
        unusual = self.call(bridge, 'huntIndicators',
                            {'indicatorType': 'unusual_binaries'})
        return lolbins, beacons, unusual

    # -- dựng chỉ báo -----------------------------------------------------

    def add(self, kind, severity, name, description, evidence, assessment,
            recommendation, extra=None, dedup_key=None):
        # Một ứng dụng nhiều tiến trình con (Zalo, Chrome) sinh ra hàng loạt bản
        # ghi giống hệt nhau. Gộp lại: người đọc cần biết "Zalo mở 8 kết nối",
        # không phải 8 dòng cảnh báo rời rạc.
        if dedup_key is not None:
            existing = self._seen.get(dedup_key)
            if existing is not None:
                existing['occurrences'] = existing.get('occurrences', 1) + 1
                return
        indicator = {
            'type': kind,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'process': name,
            'category': kind,
            'description': description,
            'evidence': evidence,
            'assessment': assessment,
            'recommendation': recommendation,
            'status': 'DETECTED',
            'detection_method': 'MCP live process/network observation',
        }
        if extra:
            indicator.update(extra)
        indicator['occurrences'] = 1
        self.indicators.append(indicator)
        if dedup_key is not None:
            self._seen[dedup_key] = indicator

    def build_indicators(self, lolbins, beacons, unusual):
        for proc in lolbins:
            name = proc.get('Name') or 'unknown'
            path = proc.get('Path') or ''
            lowered = name.lower()

            # Chinh python/node dang chay cac script san nay cung la mot tien
            # trinh tren may. Khong loai thi bo may giam sat tu bao cao minh.
            if self.self_log.check('{} {}'.format(name, path), source='lolbin'):
                continue

            # Ghi lại CHÍNH đoạn đường dẫn đã kích hoạt kết luận. Không có nó,
            # người đọc thấy một kết luận HIGH và phải tự đoán chỗ nào đáng ngờ —
            # và `detection_quality` không kiểm chứng được gì cả.
            suspect = SUSPECT_PATH_RE.search(path)
            if suspect:
                severity, assessment = 'HIGH', 'LOLBin chạy từ thư mục tạm/công cộng'
            elif lowered in HIGH_RISK_LOLBINS:
                severity, assessment = 'MEDIUM', 'LOLBin ít khi chạy hợp lệ trên máy trạm'
            else:
                severity, assessment = 'INFO', 'LOLBin thông dụng, chạy từ vị trí hệ thống'

            self.add(
                'Living Off The Land Binary', severity, name,
                'Tiến trình {} (PID {}) đang chạy'.format(name, proc.get('Id')),
                ['Path={}'.format(path or 'n/a'),
                 'PID={}'.format(proc.get('Id')),
                 'StartTime={}'.format(proc.get('StartTime') or 'n/a')],
                assessment,
                'Đối chiếu tiến trình với phần mềm đã cài' if severity != 'INFO'
                else 'Không cần hành động',
                {'command_line': path, 'pid': proc.get('Id'),
                 'matched_text': suspect.group(0) if suspect else None},
                dedup_key=('lolbin', name, path))

        # Một kết nối ra cổng 443 là bình thường. Điều đáng chú ý là tiến trình
        # KHÔNG nằm trong thư mục hệ thống mà lại đang mở kết nối ra ngoài.
        for conn in beacons:
            name = conn.get('Process') or 'unknown'
            path = conn.get('Path') or ''
            remote = conn.get('RemoteAddress')
            port = conn.get('RemotePort')

            if self.self_log.check('{} {}'.format(name, path), source='beacon'):
                continue

            suspect = SUSPECT_PATH_RE.search(path)
            if suspect:
                severity = 'HIGH'
                assessment = 'Tiến trình ở thư mục tạm đang mở kết nối ra ngoài'
            elif port not in COMMON_PORTS:
                severity = 'MEDIUM'
                assessment = 'Kết nối ra cổng không thông dụng'
            else:
                severity = 'INFO'
                assessment = 'Kết nối ra cổng thông dụng từ tiến trình thông thường'

            self.add(
                'Network Connection', severity, name,
                '{} kết nối tới {}:{}'.format(name, remote, port),
                ['RemoteAddress={}'.format(remote),
                 'RemotePort={}'.format(port),
                 'LocalPort={}'.format(conn.get('LocalPort')),
                 'Path={}'.format(path or 'n/a')],
                assessment,
                'Xác minh đích đến của kết nối' if severity != 'INFO'
                else 'Không cần hành động',
                {'remote_address': remote, 'remote_port': port,
                 'pid': conn.get('ProcessId'),
                 'matched_text': suspect.group(0) if suspect else None},
                dedup_key=('conn', name, remote, port))

        for proc in unusual:
            name = proc.get('Name') or 'unknown'
            path = proc.get('Path') or ''

            if self.self_log.check('{} {}'.format(name, path), source='unusual'):
                continue

            # %LOCALAPPDATA%\Programs là nơi cài đặt hợp lệ của rất nhiều phần
            # mềm hiện đại. Chỉ Temp/Downloads/Public mới thực sự đáng ngờ.
            suspect = SUSPECT_PATH_RE.search(path)
            if suspect:
                severity = 'HIGH'
                assessment = 'Tiến trình chạy từ thư mục tạm/tải về/công cộng'
            else:
                severity = 'INFO'
                assessment = 'Cài đặt theo người dùng, vị trí hợp lệ'

            self.add(
                'Unusual Binary Location', severity, name,
                'Tiến trình {} chạy từ {}'.format(name, path or 'n/a'),
                ['Path={}'.format(path), 'PID={}'.format(proc.get('Id'))],
                assessment,
                'Kiểm tra chữ ký số và nguồn gốc của tệp' if severity == 'HIGH'
                else 'Không cần hành động',
                {'command_line': path, 'pid': proc.get('Id'),
                 'matched_text': suspect.group(0) if suspect else None},
                dedup_key=('unusual', name, path))

    # -- xuất báo cáo -----------------------------------------------------

    def generate_hunting_report(self):
        coverage = ioc_attribution.coverage_block(
            self.observable,
            'Process list + TCP connections',
            None if self.observable else
            'Không gọi được MCP tool: {}'.format('; '.join(self.errors) or 'không rõ'))

        scope = ioc_attribution.live_scope(
            coverage=coverage['status'],
            source_detail='huntLivingOffTheLand + huntNetworkBeacons + huntIndicators')

        local_ips = scope['local_host']['ips']
        for indicator in self.indicators:
            # Sprint 11.1: qua attribute_observed de moi chi bao mang cung mot
            # cach phan loai he thong (LOCAL_HOST / REMOTE_PEER, in_inventory).
            # Truoc day moi cuoc san tu rap khoi nay theo cach rieng, nen tuong
            # quan phai doan xem mot IP trong affected_systems nghia la gi.
            block = ioc_attribution.attribute_observed(
                method='host-local observation via MCP',
                reason='Quan sát trực tiếp trên máy {}'.format(
                    scope['local_host']['hostname']))
            indicator['data_source'] = block['data_source']
            indicator['affected_systems'] = block['affected_systems']
            indicator['attribution'] = block['attribution']
            indicator['hunt_scope'] = local_ips

        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Suspicious Processes',
            'hunt_version': HUNT_VERSION,
            'data_source': ioc_attribution.SOURCE_LIVE,
            'coverage': coverage,
            'hunt_scope': scope,
            'tools_used': self.tools_used,
            'errors': self.errors,
            'question': 'Có quy trình bất thường nào đang chạy không?',
            'total_detections': len(self.indicators),
            'total_indicators': len(self.indicators),
            'self_observation': self.self_log.report(
                'tien trinh cua chinh bo may giam sat'),
            'by_severity': {},
            'by_category': {},
            'indicators': self.indicators,
        }

        for indicator in self.indicators:
            sev = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][sev] = output['by_severity'].get(sev, 0) + 1
            cat = indicator.get('category', 'UNKNOWN')
            output['by_category'][cat] = output['by_category'].get(cat, 0) + 1

        write_state_atomic(self.hunting_file, output, indent=2)
        return output

    def hunt(self):
        try:
            with McpBridge() as bridge:
                lolbins, beacons, unusual = self.collect(bridge)
            self.build_indicators(lolbins, beacons, unusual)
        except McpBridgeError as error:
            self.errors.append('MCP bridge: {}'.format(error))

        report = self.generate_hunting_report()
        return {
            'status': 'success' if self.observable else 'degraded',
            'hunting_type': 'Suspicious Processes',
            'data_source': report['data_source'],
            'observable': report['coverage']['observable'],
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'errors': self.errors,
        }


if __name__ == '__main__':
    hunter = SuspiciousProcessHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)
