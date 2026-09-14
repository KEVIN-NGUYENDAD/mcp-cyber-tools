#!/usr/bin/env python3
"""
LATERAL MOVEMENT THREAT HUNTING — LIVE

Nguồn: MCP tool `huntLateralMovement` (Security 4624/4768/4769) và
`huntRemoteDesktop` (4624/4625/4648/4778/4779) qua scripts/mcp_bridge.py.

Đây là script từng hardcode `'affected_assets': ['192.168.0.1', '192.168.0.10']`
— hai IP có thật — và vì thế dựng lên hai executive finding HIGH khuyên cô lập
hai thiết bị hoàn toàn bình thường. Sprint 6.1 đã gỡ phần quy kết giả; sprint
này thay nốt phần dữ liệu giả.

Khác với persistence và process, lateral movement là chuyện GIỮA các máy, nên
quy kết ở đây lấy từ chính nội dung sự kiện (IP trong Event 4624), không gán
bừa cho máy cục bộ.

Populates: state/hunting_lateral_movement.json
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

IPV4_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

TECHNIQUE_BY_EVENT = {
    4624: ('Remote Logon', 'MEDIUM'),
    4625: ('Failed Logon', 'MEDIUM'),
    4648: ('Explicit Credential Logon', 'HIGH'),
    4768: ('Kerberos TGT Request', 'MEDIUM'),
    4769: ('Kerberos Service Ticket', 'MEDIUM'),
    4778: ('RDP Session Reconnect', 'MEDIUM'),
    4779: ('RDP Session Disconnect', 'INFO'),
}

# Loopback và địa chỉ rỗng không phải là di chuyển ngang.
IGNORE_IPS = set(['127.0.0.1', '0.0.0.0', '::1', '255.255.255.255'])


class LateralMovementHunter(object):

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_lateral_movement.json'
        self.indicators = []
        self.errors = []
        self.observable = False
        self.coverage_reason = None
        self.tools_used = []

    # -- thu thập ---------------------------------------------------------

    def probe_security_log(self, bridge):
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
        return False, ('Security event log không đọc được. Không thể kết luận gì về '
                       'di chuyển ngang: 0 phát hiện ở đây là do KHÔNG NHÌN ĐƯỢC, '
                       'không phải do sạch.')

    def collect(self, bridge):
        readable, reason = self.probe_security_log(bridge)
        self.coverage_reason = reason

        events = []
        for tool in ('huntLateralMovement', 'huntRemoteDesktop'):
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
            for item in as_list(outcome['parsed']):
                if isinstance(item, dict):
                    item['_tool'] = tool
                    events.append(item)

        self.observable = readable
        return events

    # -- dựng chỉ báo -----------------------------------------------------

    @staticmethod
    def remote_ips(message):
        """IP trong nội dung sự kiện, bỏ loopback. Đây là quy kết CÓ CĂN CỨ."""
        found = []
        for ip in IPV4_RE.findall(message or ''):
            if ip not in IGNORE_IPS and ip not in found:
                found.append(ip)
        return found

    def build_indicators(self, events):
        for event in events:
            event_id = event.get('Id')
            try:
                event_id = int(event_id)
            except (TypeError, ValueError):
                event_id = 0
            technique, severity = TECHNIQUE_BY_EVENT.get(
                event_id, ('Logon Activity', 'INFO'))

            message = str(event.get('Message') or '')
            ips = self.remote_ips(message)

            # Không có IP từ xa thì đây là đăng nhập cục bộ, không phải lateral.
            if not ips and severity != 'HIGH':
                severity = 'INFO'

            self.indicators.append({
                'type': technique,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'event_time': event.get('TimeCreated'),
                'event_id': event_id,
                'description': '{} (Event {})'.format(technique, event_id),
                # Trích đoạn phải chứa IP đã dùng để quy kết. `message[:600]`
                # đúng chỉ khi IP tình cờ nằm ở đầu thông điệp — với sự kiện
                # đăng nhập thì địa chỉ mạng nằm ở cuối, nên nó sai gần như mọi
                # lần có quy kết thật.
                'evidence': [
                    detection_quality.evidence_excerpt(
                        message, ips[0] if ips else None),
                    'Nguồn MCP: {}'.format(event.get('_tool')),
                ],
                'matched_text': ips[0] if ips else None,
                # Với 4648, mức HIGH đến từ CHÍNH loại sự kiện, không từ một
                # đoạn văn bản khớp được — nên nó phải được khai riêng. Sáu chỉ
                # báo HIGH trước Sprint 12 không nói được vì sao chúng là HIGH.
                'severity_basis': 'Event ID {} — {}'.format(event_id, technique),
                'assessment': ('IP từ xa: {}'.format(', '.join(ips)) if ips
                               else 'Không có IP từ xa trong sự kiện'),
                'recommendation': ('Đối chiếu đăng nhập này với lịch làm việc thực tế'
                                   if ips else 'Không cần hành động'),
                'status': 'REQUIRES_VERIFICATION' if ips else 'DETECTED',
                'detection_method': 'MCP huntLateralMovement / huntRemoteDesktop',
                '_ips': ips,
            })

    # -- xuất báo cáo -----------------------------------------------------

    def generate_hunting_report(self):
        coverage = ioc_attribution.coverage_block(
            self.observable, 'Security event log (4624/4625/4648/4768/4769/4778/4779)',
            self.coverage_reason)

        scope = ioc_attribution.live_scope(
            coverage=coverage['status'],
            source_detail='huntLateralMovement + huntRemoteDesktop',
            reason=self.coverage_reason)

        for indicator in self.indicators:
            ips = indicator.pop('_ips', [])
            # Trước Sprint 11.1, chỉ báo không có IP từ xa thì affected_systems
            # rỗng — 283/428 chỉ báo. Nhưng "không có máy thứ hai dính líu" KHÔNG
            # có nghĩa là "không có máy nào bị ảnh hưởng": sự kiện đăng nhập cục
            # bộ vẫn xảy ra TRÊN máy này, và đó là một sự thật đã quan sát được.
            #
            # Rỗng ở đây làm correlation Rule 1 không có gì để ghép, và làm mọi
            # bảng hạ nguồn hiển thị một IOC không thuộc về ai.
            block = ioc_attribution.attribute_observed(
                remote_ips=ips,
                method='quan sát trên máy cục bộ + IP trích từ nội dung Security event',
                reason=(None if ips else
                        'Đăng nhập cục bộ: không có máy thứ hai trong sự kiện'))
            indicator['data_source'] = block['data_source']
            indicator['affected_assets'] = block['affected_systems']
            indicator['affected_systems'] = block['affected_systems']
            indicator['attribution'] = block['attribution']
            indicator['hunt_scope'] = scope['local_host']['ips']

        if self.observable:
            radius = ('Đã đọc Security log; {} sự kiện đăng nhập được soát'
                      .format(len(self.indicators)))
        else:
            radius = ('UNKNOWN: chưa đọc được Security log, không đánh giá được '
                      'phạm vi lây lan')

        output = {
            'timestamp': datetime.now().isoformat(),
            'hunting_type': 'Lateral Movement',
            'hunt_version': HUNT_VERSION,
            'data_source': ioc_attribution.SOURCE_LIVE,
            'coverage': coverage,
            'hunt_scope': scope,
            'tools_used': self.tools_used,
            'errors': self.errors,
            'question': 'Có chỉ báo di chuyển ngang trong hệ thống không?',
            'total_indicators': len(self.indicators),
            'blast_radius': radius,
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
            'hunting_type': 'Lateral Movement',
            'data_source': report['data_source'],
            'observable': report['coverage']['observable'],
            'coverage_reason': report['coverage']['reason'],
            'total_indicators': len(self.indicators),
            'critical': report['by_severity'].get('CRITICAL', 0),
            'high': report['by_severity'].get('HIGH', 0),
            'errors': self.errors,
        }


if __name__ == '__main__':
    hunter = LateralMovementHunter()
    result = hunter.hunt()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)
