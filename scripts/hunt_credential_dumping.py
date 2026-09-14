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
import detection_quality

HUNT_VERSION = '2.0.0'

TECHNIQUE_RE = [
    (re.compile(r'\blsass\b', re.I), 'LSASS Memory Access', 'CRITICAL'),
    (re.compile(r'\bmimikatz\b', re.I), 'Mimikatz Activity', 'CRITICAL'),
    (re.compile(r'\bntdsutil\b', re.I), 'NTDS Extraction', 'CRITICAL'),
    (re.compile(r'\bcomsvcs\b', re.I), 'comsvcs.dll MiniDump', 'CRITICAL'),
    (re.compile(r'\bprocdump\b', re.I), 'Process Dumping', 'HIGH'),
]

# Trường của Event 4688. Khớp ở trường nào quyết định kết luận mạnh đến đâu:
# một TIẾN TRÌNH tên procdump.exe khác hẳn một dòng lệnh có nhắc chữ "procdump".
FIELD_RE = {
    'new_process': re.compile(r'New Process Name:\s*(.+)'),
    'creator_process': re.compile(r'Creator Process Name:\s*(.+)'),
    # Lấy tới HẾT thông điệp, không chỉ hết dòng. Dòng lệnh nhiều dòng (heredoc,
    # script inline) là chuyện bình thường, và `(.+)` chỉ bắt được dòng đầu —
    # phần còn lại rơi ra ngoài mọi trường, nên vừa không lọc được nhiễu tự sinh
    # vừa để lọt một dòng lệnh tấn công trải qua nhiều dòng.
    # 4688 đặt trường này cuối cùng, nên "tới hết" chính là "hết dòng lệnh".
    'command_line': re.compile(r'Process Command Line:\s*([\s\S]+)'),
    'account': re.compile(r'Account Name:\s*(.+)'),
}

# Bộ lọc tự-quan-sát và luật "evidence phải chứa trigger" nay sống ở
# `detection_quality.py`. Chúng không phải chuyện riêng của cuộc săn này: bộ máy
# giám sát là một tiến trình chạy trên chính máy nó giám sát, nên MỌI cuộc săn
# đọc tiến trình hay dòng lệnh đều nhìn thấy chính mình trong dữ liệu.
#
# Giữ bản sao ở đây thì cuộc săn thứ hai sẽ dính lại đúng lỗi này, và lần đó sẽ
# không có ai đang nhìn.


class CredentialDumpingHunter(object):

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.hunting_file = self.state_dir / 'hunting_credential_dumping.json'
        self.indicators = []
        self.errors = []
        self.observable = False
        self.coverage_reason = None
        self.tools_used = []
        # Sự kiện do chính bộ máy giám sát sinh ra, và sự kiện không khớp trường
        # nào. Cả hai đều bị loại khỏi chỉ báo — nên cả hai đều phải đếm được và
        # hiện ra trong báo cáo. Bộ lọc im lặng là chỗ giấu tấn công tốt nhất.
        self.self_observed = []
        self.unmatched = 0

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

    @staticmethod
    def _fields(message):
        out = {}
        for name, pattern in FIELD_RE.items():
            match = pattern.search(message)
            out[name] = match.group(1).strip() if match else ''
        return out

    @staticmethod
    def _keyword_count(text):
        return sum(1 for pattern, _, _ in TECHNIQUE_RE if pattern.search(text or ''))

    def _self_observation(self, fields):
        """Sự kiện này có phải do chính bộ máy giám sát sinh ra không?

        Trả về lý do (chuỗi) nếu đúng, None nếu không. Không bao giờ lọc âm
        thầm: mọi sự kiện bị loại đều được đếm và báo cáo, vì một bộ lọc không
        ai nhìn thấy là chỗ hoàn hảo để giấu một cuộc tấn công thật.
        """
        command = fields.get('command_line') or ''
        if not command:
            return None
        reason = detection_quality.is_self_observation(command)
        return ('dòng lệnh ' + reason) if reason else None

    @staticmethod
    def _executable(command_line):
        """Phần thực thi của dòng lệnh: token đầu, kể cả khi nằm trong dấu nháy."""
        command = (command_line or '').strip()
        if command.startswith('"'):
            end = command.find('"', 1)
            return command[1:end] if end > 0 else command
        return command.split()[0] if command.split() else ''

    def build_indicators(self, events):
        for event in events:
            message = str(event.get('Message') or '')
            fields = self._fields(message)

            reason = self._self_observation(fields)
            if reason:
                self.self_observed.append({
                    'event_time': event.get('TimeCreated'),
                    'reason': reason,
                    'command_line': (fields.get('command_line') or '')[:200],
                })
                continue

            # Khớp ở TRƯỜNG NÀO, không chỉ "có khớp hay không".
            technique = severity = matched_field = matched_text = None
            for field in ('new_process', 'creator_process', 'command_line'):
                value = fields.get(field) or ''
                for pattern, label, level in TECHNIQUE_RE:
                    found = pattern.search(value)
                    if found:
                        technique, severity = label, level
                        matched_field, matched_text = field, found.group(0)
                        break
                if technique:
                    break

            if not technique:
                # Không khớp trường nào. Bản cũ mặc định HIGH ở đây, nên MỌI sự
                # kiện 4688 lọt tới đây đều thành chỉ báo credential access mức
                # HIGH — kể cả khi không có gì khớp cả.
                self.unmatched += 1
                continue

            # Tên tiến trình là bằng chứng mạnh. Dòng lệnh chỉ NHẮC TỚI một từ
            # khoá thì yếu hơn hẳn một bậc, và phải nói rõ là cần xác minh.
            if matched_field == 'command_line':
                command = fields.get('command_line') or ''
                # Từ khoá nằm ở CHÍNH TÊN chương trình được gọi, hoặc hai từ khoá
                # khác nhau cùng xuất hiện (`procdump ... lsass.exe` — công cụ
                # dump cộng với mục tiêu của nó): đó là lệnh tấn công thật.
                in_executable = bool(
                    re.search(r'lsass|mimikatz|ntdsutil|procdump|comsvcs',
                              self._executable(command), re.I))
                combo = self._keyword_count(command) >= 2
                if in_executable or combo:
                    status = severity
                else:
                    # Một từ khoá lọt vào tham số của một lệnh khác — `grep lsass`,
                    # một đường dẫn, một dòng nhật ký. Đây là MANH MỐI, không phải
                    # phát hiện: giữ lại để xem, nhưng không cho nó đẩy điểm rủi ro
                    # như một phát hiện đã xác nhận.
                    severity = {'CRITICAL': 'MEDIUM', 'HIGH': 'LOW'}.get(severity, severity)
                    status = 'REQUIRES_VERIFICATION'
            else:
                status = severity

            # Evidence PHẢI chứa phần đã khớp. Bản cũ lưu `message[:600]` trong
            # khi mọi lần khớp thật đều nằm sau ký tự 600 — người đọc nhận một
            # kết luận CRITICAL kèm 600 ký tự không hề chứa thứ gây ra nó, và
            # không có cách nào bác bỏ.
            excerpt = detection_quality.evidence_excerpt(message, matched_text)

            self.indicators.append({
                'type': technique,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'event_time': event.get('TimeCreated'),
                'event_id': event.get('Id'),
                'description': 'Sự kiện Security {} khớp mẫu credential dumping'.format(
                    event.get('Id')),
                'matched_field': matched_field,
                'matched_text': matched_text,
                'process': fields.get('new_process'),
                'creator_process': fields.get('creator_process'),
                'command_line': (fields.get('command_line') or '')[:300],
                'evidence': [excerpt],
                'assessment': 'Khớp "{}" tại trường {} của Event ID {}'.format(
                    matched_text, matched_field, event.get('Id')),
                'recommendation': (
                    'Xác minh dòng lệnh này trước khi hành động — khớp ở dòng lệnh '
                    'yếu hơn khớp ở tên tiến trình'
                    if matched_field == 'command_line'
                    else 'Điều tra ngay, đổi toàn bộ mật khẩu đã dùng trên máy'),
                'status': status,
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
            'self_observed_excluded': len(self.self_observed),
            'self_observation_note': (
                'Sự kiện 4688 do chính tiến trình giám sát sinh ra đã bị loại. '
                'Không loại thì mỗi lần điều tra lại tự tạo thêm bằng chứng cho '
                'lần chạy sau.' if self.self_observed else None),
            'self_observed_samples': self.self_observed[:5],
            'unmatched_events': self.unmatched,
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
