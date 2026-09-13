#!/usr/bin/env python3
"""
CREDENTIAL DUMPING THREAT HUNTING — LIVE

Nguồn: MCP tool `huntCredentialDumping` (Security log, Event ID 4688) qua
scripts/mcp_bridge.py.

Điều quan trọng nhất ở script này KHÔNG phải là những gì nó tìm thấy, mà là
việc nó thừa nhận khi không nhìn được.

Bản cũ luôn xuất 5 chỉ báo CRITICAL hardcode ("LSASS Memory Access",
"Mimikatz Activity"...) — 4 trong số 14 phát hiện CRITICAL từng đẩy risk_level
lên HIGH đến từ đây, và không cái nào có thật.

Sự thật trên máy này: Security log không đọc được (Windows Home, audit process
creation tắt mặc định, tiến trình không chạy quyền admin). Nên kết quả đúng là
0 phát hiện KÈM cờ `coverage.observable = false` — "chưa quan sát được", tuyệt
đối không phải "đã kiểm tra và sạch".

Populates: state/hunting_credential_dumping.json
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

TECHNIQUE_RE = [
    (re.compile(r'\blsass\b', re.I), 'LSASS Memory Access', 'CRITICAL'),
    (re.compile(r'\bmimikatz\b', re.I), 'Mimikatz Activity', 'CRITICAL'),
    (re.compile(r'\bntdsutil\b', re.I), 'NTDS Extraction', 'CRITICAL'),
    (re.compile(r'\bcomsvcs\b', re.I), 'comsvcs.dll MiniDump', 'CRITICAL'),
    (re.compile(r'\bprocdump\b', re.I), 'Process Dumping', 'HIGH'),
]


class CredentialDumpingHunter(object):

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_credential_dumping.json'
        self.indicators = []
        self.errors = []
        self.observable = False
        self.coverage_reason = None
        self.tools_used = []

    # -- thu thập ---------------------------------------------------------

    def probe_security_log(self, bridge):
        """Security log có đọc được không?

        Cần biết điều này VÌ `huntCredentialDumping` trả `[]` trong cả hai
        trường hợp: không có sự kiện đáng ngờ, và không đọc được log. Hai câu
        trả lời trái ngược nhau mà nhìn giống hệt nhau là thứ nguy hiểm nhất
        trong một hệ thống giám sát.
        """
        outcome = bridge.call_tool('securityLogs', {'count': 5})
        self.tools_used.append({
            'tool': 'securityLogs (probe)',
            'ok': outcome['ok'],
            'records': len(as_list(outcome['parsed'])),
            'duration': outcome['duration'],
            'error': outcome['error'],
        })
        if outcome['ok']:
            return True, None
        return False, ('Security event log không đọc được. Nguyên nhân thường gặp: '
                       'audit "Process Creation" (4688) tắt mặc định trên Windows '
                       'Home, và/hoặc tiến trình không chạy quyền Administrator.')

    def collect(self, bridge):
        readable, reason = self.probe_security_log(bridge)
        self.coverage_reason = reason

        outcome = bridge.call_tool('huntCredentialDumping')
        self.tools_used.append({
            'tool': 'huntCredentialDumping',
            'ok': outcome['ok'],
            'records': len(as_list(outcome['parsed'])),
            'duration': outcome['duration'],
            'error': outcome['error'],
        })
        if not outcome['ok']:
            self.errors.append('huntCredentialDumping: {}'.format(outcome['error']))
            return []

        # Tool chạy được, nhưng chỉ coi là "quan sát được" khi log thực sự đọc được.
        self.observable = readable
        return as_list(outcome['parsed'])

    # -- dựng chỉ báo -----------------------------------------------------

    def build_indicators(self, events):
        for event in events:
            message = str(event.get('Message') or '')
            technique, severity = 'Credential Access Attempt', 'HIGH'
            for pattern, label, level in TECHNIQUE_RE:
                if pattern.search(message):
                    technique, severity = label, level
                    break

            self.indicators.append({
                'type': technique,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'event_time': event.get('TimeCreated'),
                'event_id': event.get('Id'),
                'description': 'Sự kiện Security {} khớp mẫu credential dumping'.format(
                    event.get('Id')),
                'evidence': [message[:600]],
                'assessment': 'Khớp mẫu {} trong Event ID {}'.format(
                    technique, event.get('Id')),
                'recommendation': 'Điều tra ngay, đổi toàn bộ mật khẩu đã dùng trên máy',
                'status': severity,
                'detection_method': 'MCP huntCredentialDumping (Security 4688)',
            })

    # -- xuất báo cáo -----------------------------------------------------

    def generate_hunting_report(self):
        coverage = ioc_attribution.coverage_block(
            self.observable, 'Security event log (ID 4688)', self.coverage_reason)

        scope = ioc_attribution.live_scope(
            coverage=coverage['status'],
            source_detail='huntCredentialDumping',
            reason=self.coverage_reason)

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

        if self.observable:
            risk = ('SEVERE: phát hiện dấu hiệu credential dumping - đổi mật khẩu ngay'
                    if self.indicators else
                    'LOW: đã đọc Security log, không thấy dấu hiệu credential dumping')
        else:
            risk = ('UNKNOWN: chưa quan sát được Security log. Không có kết luận nào '
                    'về credential dumping trên máy này.')

        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Credential Dumping',
            'hunt_version': HUNT_VERSION,
            'data_source': ioc_attribution.SOURCE_LIVE,
            'coverage': coverage,
            'hunt_scope': scope,
            'tools_used': self.tools_used,
            'errors': self.errors,
            'question': 'Có chỉ báo đánh cắp credentials nào không?',
            'total_indicators': len(self.indicators),
            'credential_risk_level': risk,
            'by_severity': {},
            'indicators': self.indicators,
        }

        for indicator in self.indicators:
            sev = indicator.get('severity', 'UNKNOWN')
            output['by_severity'][sev] = output['by_severity'].get(sev, 0) + 1

        write_state_atomic(self.hunting_file, output, indent=2)
        return output

    def hunt(self):
        try:
            with McpBridge() as bridge:
                events = self.collect(bridge)
            self.build_indicators(events)
        except McpBridgeError as error:
            self.errors.append('MCP bridge: {}'.format(error))
            self.coverage_reason = 'MCP bridge không dùng được: {}'.format(error)

        report = self.generate_hunting_report()
        return {
            'status': 'success' if self.observable else 'degraded',
            'hunting_type': 'Credential Dumping',
            'data_source': report['data_source'],
            'observable': report['coverage']['observable'],
            'coverage_reason': report['coverage']['reason'],
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'errors': self.errors,
        }


if __name__ == '__main__':
    hunter = CredentialDumpingHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)
