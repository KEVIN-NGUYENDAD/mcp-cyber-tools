#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HANDOFF GENERATOR (AQ-011)

`docs/project/HANDOFF.md` — tệp mà quy trình yêu cầu đọc mỗi phiên — không tồn
tại. Hai tệp gần nhất (`AI_HANDOFF.md`, `SESSION_STATE.md`) được viết tay ngày
2026-09-07 và chưa bao giờ được sinh lại. Chúng nói:

    Risk Score      74/100        state thật:  10
    Open Incidents  18            state thật:   1
    Critical        7             state thật:   0
    Threat Level    HIGH          state thật:  LOW

Bất kỳ ai onboard theo đúng hướng dẫn sẽ khởi động với một bức tranh rủi ro sai
lệch nhiều lần — và sẽ tin nó, vì nó nằm trong tệp mà quy trình bảo phải đọc.

Đây không phải lỗi của người viết. Đây là điều luôn xảy ra với một tài liệu viết
tay công bố số liệu mà state đã trả lời: nó đúng đúng một ngày, rồi sai mãi mãi,
và không có gì đánh dấu thời điểm nó ngừng đúng.

`TECHNICAL_DEBT.md` không gặp vấn đề đó vì nó được sinh ra từ `sprint_gate.py`.
Tệp này áp dụng đúng cách chữa đó cho handoff: mọi con số đọc thẳng từ `state/`
tại thời điểm chạy. Không có chỗ nào để gõ tay một con số vào.
"""

from __future__ import print_function

import io
import json
import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs', 'project')
HANDOFF_FILE = os.path.join(DOCS_DIR, 'HANDOFF.md')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def read_json(name, folder='state'):
    path = os.path.join(PROJECT_ROOT, folder, name)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def git(*args):
    try:
        out = subprocess.check_output(['git'] + list(args), cwd=PROJECT_ROOT,
                                      stderr=subprocess.STDOUT)
        return out.decode('utf-8', 'replace').strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def unknown(value, suffix=''):
    """Thiếu dữ liệu đọc ra UNKNOWN, không đọc ra 0.

    Cùng một luật với Sprint A. Một bản handoff báo "Risk Score: 0" cho một tệp
    không đọc được sẽ khiến người tiếp nhận yên tâm về đúng thứ họ chưa hề đo.
    """
    if value is None:
        return 'UNKNOWN'
    return '%s%s' % (value, suffix)


def build():
    validation = read_json('tool_validation.json') or {}
    summary = validation.get('summary') or {}
    risk = read_json('risk_score.json') or {}
    incidents = read_json('incidents.json') or {}
    findings = read_json('executive_findings.json') or {}
    coverage = read_json('sensor_coverage.json') or {}
    pipeline = read_json('pipeline_results.json', folder='logs') or {}

    lines = []
    add = lines.append

    add('# HANDOFF')
    add('')
    add('Sinh tự động bởi `scripts/generate_handoff.py`. **Đừng sửa tay** — mọi '
        'con số dưới đây đọc thẳng từ `state/` lúc chạy.')
    add('')
    add('Cập nhật: %s' % datetime.now().isoformat())
    add('')

    add('## Sprint vừa xong')
    add('')
    add('| | |')
    add('|---|---|')
    add('| Commit | `%s` |' % (git('rev-parse', '--short', 'HEAD') or 'UNKNOWN'))
    add('| Branch | `%s` |' % (git('rev-parse', '--abbrev-ref', 'HEAD') or 'UNKNOWN'))
    add('| Tiêu đề | %s |' % (git('log', '-1', '--pretty=%s') or 'UNKNOWN'))
    add('| Cây làm việc | %s |'
        % ('sạch' if not git('status', '--porcelain') else 'CÓ THAY ĐỔI CHƯA COMMIT'))
    add('')

    add('## Cổng merge')
    add('')
    add('| | |')
    add('|---|---|')
    for key in ('PASS', 'EMPTY', 'BLIND', 'FAIL'):
        add('| %s | %s |' % (key, unknown(summary.get(key))))
    stages = pipeline.get('stages') or pipeline.get('results') or []
    # AQ-026. Ban dau dong nay la ban sao cua chinh loi AQ-013: doc khoa
    # `success` ma bo ghi pipeline khong bao gio ghi, voi mac dinh True. Toi sua
    # o `sprint_gate.py` va de nguyen ban sao o day — dung kieu sai ma vong audit
    # truoc vua chung minh la khong scale.
    #
    # Thieu truong trang thai KHONG duoc tinh la dat; no duoc dem rieng.
    failed = [s for s in stages
              if str(s.get('status', '')).lower()
              not in ('success', 'ok', 'passed', 'skipped')
              and 'status' in s]
    unstated = [s for s in stages if 'status' not in s]
    add('| Pipeline | %d stage, %d thất bại%s |'
        % (len(stages), len(failed),
           '' if not unstated else ', %d không khai trạng thái' % len(unstated)))
    integrity = validation.get('detection_integrity') or {}
    add('| Toàn vẹn bằng chứng | %s vi phạm / %s chỉ báo |'
        % (unknown(integrity.get('total_violations')),
           unknown(integrity.get('total_indicators'))))
    add('')

    add('## Trạng thái thật (đọc từ state/)')
    add('')
    add('| | |')
    add('|---|---|')
    # Điểm rủi ro có thể là None khi engine không đo được thành phần nào — và
    # None phải đọc ra UNKNOWN, không phải 0.
    add('| Risk Score | %s |' % unknown(risk.get('overall_score'), '/100'))
    add('| Risk Level | %s |' % (risk.get('risk_level') or 'UNKNOWN'))
    by_severity = incidents.get('by_severity') or {}
    add('| Sự cố đang mở | %s |' % unknown(incidents.get('total_incidents')))
    add('| └ CRITICAL | %s |' % by_severity.get('CRITICAL', 0))
    add('| └ HIGH | %s |' % by_severity.get('HIGH', 0))
    add('| Phát hiện cấp điều hành | %s |'
        % unknown(findings.get('total_findings')))
    add('| └ cảnh báo chất lượng | %s |' % findings.get('quality_warnings', 0))
    add('| Rule không kết luận được | %s |'
        % len(findings.get('coverage_gaps') or []))
    add('')

    skipped = incidents.get('skipped_rules') or []
    if skipped:
        add('> ⚠ **%d luật phát hiện không đánh giá được lần này.** "0 sự cố" '
            'trên một luật không chạy được đọc y hệt "0 sự cố" trên một máy '
            'sạch — nên chúng được liệt kê ra:' % len(skipped))
        add('>')
        for item in skipped:
            add('> - %s' % item)
        add('')

    add('## Vùng quan sát')
    add('')
    add('| Nguồn / Năng lực | Trạng thái |')
    add('|---|---|')
    for key in ('defender', 'firewall', 'security_log', 'event_logs',
                'persistence', 'processes', 'network', 'ioc'):
        add('| `%s` | %s |' % (key, coverage.get(key) or 'UNKNOWN'))
    for capability in coverage.get('detection_capabilities') or []:
        add('| **%s** | %s |' % (capability.get('label'), capability.get('status')))
    add('')
    if coverage.get('freshness_note'):
        add('_%s_' % coverage['freshness_note'])
        add('')

    add('## Việc tiếp theo')
    add('')
    add('1. Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.')
    add('2. Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.')
    add('3. `npm run gate` trước khi mở PR.')
    add('')
    add('## Tài liệu handoff viết tay')
    add('')
    add('`AI_HANDOFF.md` và `SESSION_STATE.md` là bản viết tay ngày 2026-09-07. '
        'Chúng **không được cập nhật theo state** và số liệu trong đó đã sai '
        'nhiều lần. Đọc tệp này thay cho chúng.')
    add('')
    return '\n'.join(lines) + '\n'


def main():
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    with io.open(HANDOFF_FILE, 'w', encoding='utf-8') as handle:
        handle.write(build())
    print(json.dumps({'status': 'success',
                      'handoff': os.path.relpath(HANDOFF_FILE, PROJECT_ROOT)},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
