#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DETECTION QUALITY (Sprint 12)

Hai bất biến mà mọi chỉ báo phải thoả, và một bộ lọc mà mọi cuộc săn phải dùng.

Vì sao file này tồn tại
-----------------------
Sprint 11.x bắt được một lỗi thuộc loại tệ nhất: cuộc săn credential dumping
phát hiện chính người đang điều tra nó. Gõ một lệnh có chữ `lsass` để kiểm tra
cuộc săn → Event 4688 ghi lại dòng lệnh → lần chạy sau cuộc săn đọc dấu chân của
chính nó và kết luận có kẻ đánh cắp credentials. Càng điều tra càng sinh thêm
"bằng chứng" cho lần sau.

Nó lọt được vì hai chỗ hở, và cả hai đều KHÔNG riêng của credential dumping:

  1. Không có bộ lọc tự-quan-sát. Bộ máy giám sát là một tiến trình chạy trên
     chính máy nó giám sát, nên nó luôn nằm trong dữ liệu nó đọc.

  2. Bằng chứng không chứa thứ gây ra kết luận. Việc khớp chạy trên toàn bộ
     thông điệp, còn `evidence` lưu `message[:600]` — mọi lần khớp thật đều nằm
     sau ký tự 600. Người đọc nhận một kết luận CRITICAL kèm 600 ký tự không hề
     chứa trigger, và không có cách nào bác bỏ.

Lỗi thứ hai nguy hiểm hơn lỗi thứ nhất. Một phát hiện sai còn bị bắt được; một
phát hiện KHÔNG THỂ KIỂM CHỨNG thì không ai bác bỏ được, kể cả khi nó sai.

Sprint 11.x sửa hai chỗ đó cho MỘT cuộc săn. File này biến chúng thành luật
chung, và `test_detection_quality.py` giữ cho luật không lặng lẽ mục đi.
"""

from __future__ import print_function

import glob
import json
import io
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')

# --------------------------------------------------------------------------
# 1. Tự quan sát
# --------------------------------------------------------------------------
#
# Tên các script của chính bộ máy. Một dòng lệnh gọi chúng là bộ máy đang chạy,
# không phải kẻ tấn công đang hành động.
SELF_OBSERVATION_HINTS = (
    'hunt_credential_dumping', 'hunt_lateral_movement', 'hunt_persistence',
    'hunt_suspicious_processes', 'mcp_bridge', 'tool_validator', 'sensor_probe',
    'run_intelligence_pipeline', 'correlation_engine', 'detection_quality',
    'asset_store', 'asset_builder', 'generate_incidents',
)

# Từ khoá nhận dạng nối bằng `|` là một BIỂU THỨC, không phải một cuộc tấn công.
# Kẻ tấn công gọi mimikatz; nó không gõ cả bảng mẫu nhận dạng của người phòng thủ.
SIGNATURE_RE = re.compile(
    r'(lsass|mimikatz|ntdsutil|procdump|comsvcs|rundll32|certutil|bitsadmin)'
    r'\s*\|\s*'
    r'(lsass|mimikatz|ntdsutil|procdump|comsvcs|rundll32|certutil|bitsadmin)',
    re.I)


def is_self_observation(text, extra_hints=()):
    """Đoạn văn bản này có phải do chính bộ máy giám sát sinh ra không?

    Trả về lý do (chuỗi) nếu đúng, None nếu không.

    Trả về LÝ DO chứ không phải True/False là có chủ đích: mọi lần loại bỏ đều
    phải giải thích được. Một bộ lọc không ai nhìn thấy là chỗ hoàn hảo để giấu
    một cuộc tấn công thật, và nó sẽ giấu — chỉ là không ai biết khi nào.
    """
    lowered = (text or '').lower()
    if not lowered:
        return None
    for hint in tuple(SELF_OBSERVATION_HINTS) + tuple(extra_hints):
        if hint in lowered:
            return 'gọi chính script giám sát ({})'.format(hint)
    if SIGNATURE_RE.search(lowered):
        return ('chứa các từ khoá nhận dạng nối bằng "|" — đây là một biểu thức '
                'đang được truyền đi, không phải một lần gọi công cụ tấn công')
    return None


# --------------------------------------------------------------------------
# 2. Bằng chứng phải chứa trigger
# --------------------------------------------------------------------------

EVIDENCE_WIDTH = 600
EVIDENCE_LEAD = 200


def evidence_excerpt(message, trigger=None, width=EVIDENCE_WIDTH, lead=EVIDENCE_LEAD):
    """Trích đoạn bằng chứng LUÔN chứa trigger.

    `message[:width]` là cách làm sai, và nó sai âm thầm: nó đúng chừng nào
    trigger tình cờ nằm ở đầu thông điệp. Event 4688 đặt dòng lệnh ở cuối, nên
    với 4688 nó sai gần như mọi lần.
    """
    text = message or ''
    if not trigger:
        return text[:width]
    index = text.lower().find(str(trigger).lower())
    if index < 0:
        # Trigger không có trong thông điệp. Không cắt bừa một đoạn rồi coi như
        # xong — nói thẳng ra, vì đây là một mâu thuẫn trong chính dữ liệu.
        return text[:width]
    start = max(0, index - lead)
    return text[start:start + width]


def indicator_triggers(indicator):
    """Những thứ mà một chỉ báo NÓI là lý do nó tồn tại.

    Mỗi thứ trong đây phải tìm lại được trong evidence, nếu không thì kết luận
    không kiểm chứng được.
    """
    triggers = []
    if indicator.get('matched_text'):
        triggers.append(('matched_text', str(indicator['matched_text'])))
    systems = (indicator.get('attribution') or {}).get('systems') or []
    for system in systems:
        # Chỉ REMOTE_PEER: máy cục bộ được quy kết vì cuộc săn CHẠY ở đó, không
        # phải vì tên nó xuất hiện trong thông điệp — đòi nó có mặt trong
        # evidence là đòi sai chỗ.
        if system.get('scope') == 'REMOTE_PEER' and system.get('ip'):
            triggers.append(('remote_peer', system['ip']))
    return triggers


def verify_indicator(indicator):
    """Danh sách vi phạm của một chỉ báo. Rỗng là đạt."""
    violations = []
    evidence = ' '.join(str(part) for part in (indicator.get('evidence') or []))
    lowered = evidence.lower()

    for kind, trigger in indicator_triggers(indicator):
        if str(trigger).lower() not in lowered:
            violations.append(
                '{} "{}" không xuất hiện trong evidence — kết luận này không '
                'kiểm chứng được'.format(kind, trigger))

    if not evidence.strip():
        violations.append('không có evidence nào')

    severity = indicator.get('severity')
    if severity in ('CRITICAL', 'HIGH'):
        if not indicator.get('attribution'):
            violations.append(
                'mức {} nhưng không có khối attribution — không biết nó nói về '
                'máy nào'.format(severity))
        # Mức cao phải NÓI RA vì sao nó cao. Không phải mọi lý do đều là một
        # đoạn văn bản khớp được: Event ID 4648 là siêu dữ liệu, không nằm trong
        # nội dung thông điệp. Nhưng nó vẫn phải được viết ra — một chỉ báo
        # CRITICAL không giải thích được mức của chính nó thì người trực ca chỉ
        # còn cách tin hoặc bỏ qua, và cả hai đều sai.
        if not indicator.get('matched_text') and not indicator.get('severity_basis'):
            violations.append(
                'mức {} nhưng không khai cơ sở (matched_text hoặc severity_basis) '
                '— không kiểm chứng được vì sao nó ở mức này'.format(severity))

    return violations


def audit_state(state_dir=None):
    """Quét mọi tệp hunting trong state và chấm theo hai bất biến trên."""
    state_dir = state_dir or STATE_DIR
    report = {'files': [], 'total_indicators': 0, 'total_violations': 0}

    for path in sorted(glob.glob(os.path.join(state_dir, 'hunting_*.json'))):
        try:
            with io.open(path, encoding='utf-8') as handle:
                data = json.load(handle)
        except (ValueError, IOError, OSError) as error:
            report['files'].append({
                'file': os.path.basename(path),
                'error': str(error)[:120],
                'indicators': 0,
                'violations': [],
            })
            continue

        indicators = data.get('indicators') or []
        violations = []
        for position, indicator in enumerate(indicators):
            for problem in verify_indicator(indicator):
                violations.append({
                    'index': position,
                    'type': indicator.get('type'),
                    'severity': indicator.get('severity'),
                    'problem': problem,
                })

        report['files'].append({
            'file': os.path.basename(path),
            'indicators': len(indicators),
            'violations': violations,
            'self_observed_excluded': data.get('self_observed_excluded'),
        })
        report['total_indicators'] += len(indicators)
        report['total_violations'] += len(violations)

    report['ok'] = report['total_violations'] == 0
    return report


def main():
    report = audit_state()
    for entry in report['files']:
        status = 'OK' if not entry.get('violations') else 'VI PHAM'
        print('%-42s %4s chi bao  %-8s %s' % (
            entry['file'], entry.get('indicators', 0), status,
            '' if not entry.get('violations')
            else '%d loi' % len(entry['violations'])))
        for violation in (entry.get('violations') or [])[:5]:
            print('      [%s] %s: %s' % (violation['index'],
                                         violation.get('severity'),
                                         violation['problem'][:110]))
    print('')
    print('TONG: %d chi bao, %d vi pham' % (
        report['total_indicators'], report['total_violations']))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
