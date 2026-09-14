#!/usr/bin/env python3
"""
PERSISTENCE THREAT HUNTING — LIVE

Nguồn: MCP tool `huntPersistence` + `huntSuspiciousTasks`, chạy trên máy này,
qua scripts/mcp_bridge.py.

Trước sprint này script chỉ xuất 5 chỉ báo hardcode. Nay nó xuất những cơ chế
tự khởi động CÓ THẬT trên máy — và vì thế phải chấm điểm dè dặt: một máy bình
thường có hàng chục scheduled task và Run key hợp lệ. Gắn CRITICAL cho tất cả
chỉ là đổi một kiểu nhiễu này lấy một kiểu nhiễu khác.

Mức độ được *kiếm* bằng dấu hiệu cụ thể, không phải bằng sự tồn tại.

Populates: state/hunting_persistence.json
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from state_manager import write_state_atomic
import ioc_attribution
from mcp_bridge import McpBridge, McpBridgeError, as_list

HUNT_VERSION = '2.0.0'

# Thư mục mà phần mềm hợp lệ hiếm khi dùng để tự khởi động.
SUSPECT_PATH_RE = re.compile(
    r'(\\Temp\\|\\AppData\\Local\\Temp\\|\\ProgramData\\|\\Users\\Public\\|\\Downloads\\)',
    re.I)

# Binary sống nhờ hệ thống — xuất hiện trong một mục autostart là đáng hỏi.
LOLBIN_RE = re.compile(
    r'\b(powershell|pwsh|cmd|wscript|cscript|mshta|rundll32|regsvr32|certutil|'
    r'bitsadmin|msbuild|installutil|regasm|regsvcs)\b', re.I)

ENCODED_RE = re.compile(r'-enc\b|-encodedcommand\b|frombase64string', re.I)


class PersistenceHunter(object):

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_persistence.json'
        self.indicators = []
        self.errors = []
        self.observable = False
        self.tools_used = []

    # -- thu thập ---------------------------------------------------------

    def collect(self, bridge):
        records = []
        for tool in ('huntPersistence', 'huntSuspiciousTasks'):
            outcome = bridge.call_tool(tool)
            self.tools_used.append({
                'tool': tool,
                'ok': outcome['ok'],
                'records': len(as_list(outcome['parsed'])),
                'duration': outcome['duration'],
                'error': outcome['error'],
            })
            if not outcome['ok']:
                self.errors.append('{}: {}'.format(tool, outcome['error']))
                continue
            self.observable = True
            for item in as_list(outcome['parsed']):
                if isinstance(item, dict):
                    item['_tool'] = tool
                    records.append(item)
        return records

    # -- chấm điểm --------------------------------------------------------

    @staticmethod
    def describe(record):
        kind = record.get('Kind') or ('ScheduledTask' if record.get('TaskName') else 'Autostart')
        name = record.get('Name') or record.get('TaskName') or 'Unknown'
        location = record.get('Location') or record.get('TaskPath') or ''
        command = record.get('Command') or ''
        return kind, name, location, command

    def classify(self, record):
        """Trả về (severity, lý do). Mặc định là INFO — mức phải kiếm được."""
        _, name, location, command = self.describe(record)
        haystack = '{} {} {}'.format(name, location, command)
        reasons = []
        severity = 'INFO'

        if ENCODED_RE.search(haystack):
            severity = 'CRITICAL'
            reasons.append('lệnh mã hoá base64 trong mục tự khởi động')
        elif SUSPECT_PATH_RE.search(haystack):
            severity = 'HIGH'
            reasons.append('tự khởi động từ thư mục tạm/công cộng')
        elif LOLBIN_RE.search(command):
            severity = 'MEDIUM'
            reasons.append('gọi binary sống nhờ hệ thống (LOLBin)')

        if not reasons:
            reasons.append('mục tự khởi động ở vị trí thông thường')
        return severity, '; '.join(reasons)

    def build_indicators(self, records):
        for record in records:
            kind, name, location, command = self.describe(record)
            severity, reason = self.classify(record)

            self.indicators.append({
                'type': 'Persistence: {}'.format(kind),
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'name': name,
                'location': location,
                'command': command,
                'description': '{} "{}" tại {}'.format(kind, name, location or 'n/a'),
                'evidence': [
                    'Kind={}'.format(kind),
                    'Name={}'.format(name),
                    'Location={}'.format(location or 'n/a'),
                    'Command={}'.format(command or 'n/a'),
                    'Nguồn MCP: {}'.format(record.get('_tool')),
                ],
                'assessment': reason,
                'recommendation': ('Xác minh mục này có phải do bạn cài đặt'
                                   if severity in ('CRITICAL', 'HIGH')
                                   else 'Không cần hành động, ghi nhận để đối chiếu'),
                'status': 'DETECTED',
                'detection_method': 'MCP huntPersistence / huntSuspiciousTasks',
            })

    # -- xuất báo cáo -----------------------------------------------------

    def generate_hunting_report(self):
        coverage = ioc_attribution.coverage_block(
            self.observable,
            'Scheduled Tasks + Registry Run keys',
            None if self.observable else
            'Không gọi được MCP tool: {}'.format('; '.join(self.errors) or 'không rõ'))

        scope = ioc_attribution.live_scope(
            coverage=coverage['status'],
            source_detail='huntPersistence + huntSuspiciousTasks')

        # Cuộc săn này quan sát CHÍNH máy đang chạy, nên quy kết về nó là sự
        # thật kiểm chứng được - không phải suy đoán như khi gán IOC cho IP lạ.
        local_ips = scope['local_host']['ips']
        for indicator in self.indicators:
            block = ioc_attribution.attribute(
                ioc_attribution.SOURCE_LIVE,
                affected_systems=local_ips,
                method='host-local observation via MCP',
                confidence='HIGH' if local_ips else 'LOW',
                reason='Quan sát trực tiếp trên máy {}'.format(
                    scope['local_host']['hostname']))
            indicator['data_source'] = block['data_source']
            indicator['affected_systems'] = block['affected_systems']
            indicator['attribution'] = block['attribution']
            indicator['hunt_scope'] = local_ips

        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Persistence Indicators',
            'hunt_version': HUNT_VERSION,
            'data_source': ioc_attribution.SOURCE_LIVE,
            'coverage': coverage,
            'hunt_scope': scope,
            'tools_used': self.tools_used,
            'errors': self.errors,
            'question': 'Có chỉ báo persistence nào trong hệ thống không?',
            'total_indicators': len(self.indicators),
            'by_severity': {},
            'by_status': {},
            'indicators': self.indicators,
        }

        for indicator in self.indicators:
            sev = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][sev] = output['by_severity'].get(sev, 0) + 1
            status = indicator.get('status', 'UNKNOWN')
            output['by_status'][status] = output['by_status'].get(status, 0) + 1

        write_state_atomic(self.hunting_file, output, indent=2)
        return output

    # -- điều phối --------------------------------------------------------

    def hunt(self):
        try:
            with McpBridge() as bridge:
                records = self.collect(bridge)
            self.build_indicators(records)
        except McpBridgeError as error:
            # Cầu nối chết: vẫn xuất báo cáo, nhưng nói rõ là KHÔNG quan sát được.
            # Im lặng ghi 0 phát hiện sẽ bị đọc nhầm thành "máy sạch".
            self.errors.append('MCP bridge: {}'.format(error))

        report = self.generate_hunting_report()
        return {
            'status': 'success' if self.observable else 'degraded',
            'hunting_type': 'Persistence Indicators',
            'data_source': report['data_source'],
            'observable': report['coverage']['observable'],
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'errors': self.errors,
        }


if __name__ == '__main__':
    hunter = PersistenceHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # degraded vẫn là exit 0: pipeline cần chạy tiếp, và báo cáo đã nói rõ
    # vì sao nó không kết luận được.
    sys.exit(0)
