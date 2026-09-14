#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPRINT GATE (Sprint 12 — TASK 4, 5, 6)

Một lệnh trả lời hai câu hỏi kết thúc mỗi sprint:

    Sprint này có được merge không?
    Còn nợ gì?

    python scripts/sprint_gate.py            đọc kết quả kiểm gần nhất
    python scripts/sprint_gate.py --validate  chạy lại tool_validator trước (chậm)

Thoát 0 nghĩa là ĐỦ ĐIỀU KIỆN MERGE. Khác 0 thì không, và lý do được in ra.

Vì sao cổng chặn phải là một tệp chứ không phải một thói quen
-------------------------------------------------------------
Điều kiện merge của dự án này là FAIL=0 và BLIND=0. Nhớ kiểm hai con số đó mỗi
lần là một thói quen, và thói quen hỏng đúng vào hôm mệt. Một lệnh có mã thoát
thì không.

Cổng này cố ý KHÔNG tự merge. Nó trả lời "có đạt không"; quyết định đẩy mã lên
nhánh chung vẫn là của con người, và đó là ranh giới nên giữ.
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
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs', 'project')
DEBT_FILE = os.path.join(DOCS_DIR, 'TECHNICAL_DEBT.md')
TEST_RUNNER = os.path.join(PROJECT_ROOT, 'tests', 'detection_quality', 'run_all.py')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import detection_quality  # noqa: E402
import portal_field_audit  # noqa: E402
import telegram_field_audit  # noqa: E402
import tool_validator  # noqa: E402


def _read_json(path):
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run_tests():
    """Bộ kiểm dương tính giả. Không chạy được cũng là TRƯỢT."""
    if not os.path.exists(TEST_RUNNER):
        return False, 'khong tim thay tests/detection_quality/run_all.py'
    try:
        process = subprocess.Popen(
            [sys.executable, TEST_RUNNER],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
        raw, _ = process.communicate()
    except OSError as error:
        return False, 'khong chay duoc bo kiem: %s' % error

    text = raw.decode('utf-8', 'replace')
    tail = [line for line in text.splitlines() if line.startswith('TONG:')]
    return process.returncode == 0, (tail[-1] if tail else text.strip()[-120:])


def collect(validate=False):
    """Mọi con số cổng chặn cần, ở một chỗ."""
    if validate:
        report = tool_validator.validate()
        coverage = tool_validator.sensor_coverage(report)
        tool_validator._write_json(
            os.path.join(STATE_DIR, 'tool_validation.json'), report)
        tool_validator._write_json(
            os.path.join(STATE_DIR, 'sensor_coverage.json'), coverage)
    else:
        report = _read_json(os.path.join(STATE_DIR, 'tool_validation.json'))
        coverage = _read_json(os.path.join(STATE_DIR, 'sensor_coverage.json'))

    tests_ok, tests_detail = run_tests()
    integrity = detection_quality.audit_state()
    # Portal doc truong khong ton tai la mot lop loi DA xay ra bon lan trong
    # repo nay, va lan nao cung im lang. No thuoc ve cong chan, khong phai mot
    # lan don dep.
    portal = portal_field_audit.audit()
    # Lop Telegram nguy hiem hon portal o mot diem: mot tin nhan sai di toi
    # dien thoai mot minh, khong co o nao ben canh de doi chieu.
    telegram = telegram_field_audit.audit()
    pipeline = _read_json(os.path.join(PROJECT_ROOT, 'logs', 'pipeline_results.json'))

    return {
        'report': report,
        'coverage': coverage,
        'integrity': integrity,
        'tests_ok': tests_ok,
        'tests_detail': tests_detail,
        'pipeline': pipeline,
        'portal': portal,
        'telegram': telegram,
    }


def evaluate(data):
    """Điều kiện merge, và lý do cụ thể khi không đạt."""
    blockers = []
    report = data['report']

    if not report:
        blockers.append('chua co state/tool_validation.json — chay `npm run validate`')
        summary = {}
    else:
        summary = report.get('summary') or {}
        if summary.get('FAIL', 0):
            blockers.append('%d tool FAIL' % summary['FAIL'])
        if summary.get('BLIND', 0):
            blockers.append('%d tool BLIND' % summary['BLIND'])
        if not summary.get('PASS', 0):
            blockers.append('khong tool nao PASS')

    if not data['tests_ok']:
        blockers.append('bo kiem phat hien truot (%s)' % data['tests_detail'])

    integrity = data['integrity']
    if not integrity.get('ok'):
        blockers.append('%d vi pham toan ven bang chung'
                        % integrity.get('total_violations', 0))

    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    if portal_missing:
        blockers.append('%d truong portal doc tu state khong ton tai'
                        % len(portal_missing))

    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    if telegram_missing:
        blockers.append('%d truong telegram doc tu state khong ton tai'
                        % len(telegram_missing))

    pipeline = data['pipeline'] or {}
    stages = pipeline.get('stages') or pipeline.get('results') or []
    failed_stages = [s for s in stages if not s.get('success', True)]
    if failed_stages:
        blockers.append('%d stage pipeline that bai' % len(failed_stages))

    return {
        'merge_ready': not blockers,
        'blockers': blockers,
        'summary': summary,
        'stages': len(stages),
        'failed_stages': len(failed_stages),
    }


# --------------------------------------------------------------------------
# TASK 5 — TECHNICAL_DEBT.md sinh tự động
# --------------------------------------------------------------------------

def debt_rows(data):
    """Nợ ĐO ĐƯỢC từ lần chạy này, cộng nợ đã ghi tay trong tool_validator.

    Tách hai loại vì chúng già đi theo hai cách khác nhau: nợ đo được tự biến
    mất khi vấn đề hết, còn nợ ghi tay chỉ mất khi có người xoá nó — và một bảng
    nợ toàn mục ghi tay là bảng sẽ nói sai trước tiên.
    """
    measured = []
    report = data['report'] or {}
    summary = report.get('summary') or {}

    if summary.get('FAIL', 0):
        measured.append(('Tool FAIL', '%d tool báo lỗi khi gọi thật'
                         % summary['FAIL'], 'CHẶN MERGE'))
    if summary.get('BLIND', 0):
        measured.append(('Tool BLIND', '%d tool không quan sát được nguồn'
                         % summary['BLIND'], 'CHẶN MERGE'))
    if summary.get('EMPTY', 0):
        measured.append((
            'Tool EMPTY', '%d tool đọc được nguồn nhưng không có bản ghi nào khớp'
            % summary['EMPTY'],
            'Không phải nợ — đây là "đã nhìn, không có gì". Ghi ra để không ai '
            'nhầm nó với BLIND.'))

    integrity = data['integrity']
    if not integrity.get('ok'):
        measured.append((
            'Toàn vẹn bằng chứng',
            '%d chỉ báo kết luận điều mà bằng chứng của nó không chứng minh được'
            % integrity.get('total_violations', 0), 'CHẶN MERGE'))

    coverage = data['coverage'] or {}
    for key, detail in (coverage.get('details') or {}).items():
        if detail.get('status') != 'covered':
            measured.append(('Cảm biến: %s' % detail.get('label', key),
                             detail.get('reason') or detail.get('status'),
                             detail.get('status', '').upper()))

    for capability in (coverage.get('detection_capabilities') or []):
        if capability.get('status') != 'covered':
            measured.append(('Năng lực: %s' % capability.get('label'),
                             ' '.join((capability.get('reason') or '').split())[:220],
                             capability.get('status', '').upper()))

    for row in (data['report'] or {}).get('results', []):
        if row.get('variants_failed'):
            measured.append(('Tham số: %s' % row['tool'],
                             '%d biến thể tham số lỗi' % len(row['variants_failed']),
                             'CẦN SỬA'))

    return measured


def write_debt(data, verdict):
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    lines = []
    add = lines.append
    add('# Technical Debt')
    add('')
    add('Sinh tự động bởi `scripts/sprint_gate.py`. Đừng sửa tay — sửa nguồn.')
    add('')
    add('Cập nhật: %s' % datetime.now().isoformat(timespec='seconds'))
    add('')
    add('## Cổng merge')
    add('')
    add('| | |')
    add('|---|---|')
    add('| Đủ điều kiện merge | **%s** |'
        % ('CÓ' if verdict['merge_ready'] else 'KHÔNG'))
    summary = verdict['summary']
    add('| PASS | %s |' % summary.get('PASS', '?'))
    add('| EMPTY | %s |' % summary.get('EMPTY', '?'))
    add('| BLIND | %s |' % summary.get('BLIND', '?'))
    add('| FAIL | %s |' % summary.get('FAIL', '?'))
    add('| Bộ kiểm phát hiện | %s |'
        % ('ĐẠT' if data['tests_ok'] else 'TRƯỢT'))
    add('| Toàn vẹn bằng chứng | %d vi phạm / %d chỉ báo |'
        % (data['integrity'].get('total_violations', 0),
           data['integrity'].get('total_indicators', 0)))
    add('| Pipeline | %d stage, %d thất bại |'
        % (verdict['stages'], verdict['failed_stages']))
    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    add('| Trường portal đọc sai | %d |' % len(portal_missing))
    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    add('| Trường Telegram đọc sai | %d |' % len(telegram_missing))
    add('')

    if verdict['blockers']:
        add('### Đang chặn')
        add('')
        for blocker in verdict['blockers']:
            add('- %s' % blocker)
        add('')

    measured = debt_rows(data)
    add('## Nợ đo được trong lần chạy này')
    add('')
    if measured:
        add('| Hạng mục | Chi tiết | Mức |')
        add('|---|---|---|')
        for title, detail, level in measured:
            add('| %s | %s | %s |' % (title, detail, level))
    else:
        add('Không có. Mọi thứ đo được đều đạt.')
    add('')

    add('## Nợ đã ghi nhận nhưng chưa trả')
    add('')
    add('Những món này không suy ra được từ số liệu — chúng là quyết định đã')
    add('hoãn lại, kèm lý do. Danh sách nằm trong `scripts/tool_validator.py`.')
    add('')
    add('| # | Món nợ | Vì sao chưa trả |')
    add('|---:|---|---|')
    index = 0
    settled = []
    for entry in tool_validator.REMAINING_DEBT:
        item, reason = entry[0], entry[1]
        resolved_when = entry[2] if len(entry) > 2 else None
        if resolved_when is not None and data['report'] \
                and not resolved_when(data['report']):
            settled.append(item)
            continue
        index += 1
        add('| %d | %s | %s |' % (index, item, reason))
    add('')
    if settled:
        add('Đã trả (đo được trong lần chạy này):')
        add('')
        for item in settled:
            add('- ✅ %s' % item)
        add('')

    with io.open(DEBT_FILE, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return DEBT_FILE


def main():
    validate = '--validate' in sys.argv[1:]

    print('=' * 64)
    print('SPRINT GATE')
    print('=' * 64)

    data = collect(validate=validate)
    verdict = evaluate(data)
    path = write_debt(data, verdict)

    summary = verdict['summary']
    print('')
    print('PASS %s | EMPTY %s | BLIND %s | FAIL %s' % (
        summary.get('PASS', '?'), summary.get('EMPTY', '?'),
        summary.get('BLIND', '?'), summary.get('FAIL', '?')))
    print('Bộ kiểm phát hiện : %s  (%s)'
          % ('ĐẠT' if data['tests_ok'] else 'TRƯỢT', data['tests_detail']))
    print('Toàn vẹn bằng chứng: %d vi phạm / %d chỉ báo'
          % (data['integrity'].get('total_violations', 0),
             data['integrity'].get('total_indicators', 0)))
    print('Pipeline           : %d stage, %d thất bại'
          % (verdict['stages'], verdict['failed_stages']))
    portal_missing = [f for f in (data.get('portal') or [])
                      if f['level'] == 'MISSING']
    print('Trường portal      : %d đọc sai / %d truy cập'
          % (len(portal_missing), len(data.get('portal') or [])))
    telegram_missing = [f for f in (data.get('telegram') or [])
                        if f['level'] == 'MISSING']
    print('Trường Telegram    : %d đọc sai / %d truy cập'
          % (len(telegram_missing), len(data.get('telegram') or [])))
    print('Nợ kỹ thuật        : %s' % os.path.relpath(path, PROJECT_ROOT))
    print('')

    if verdict['merge_ready']:
        print('KET QUA: DU DIEU KIEN MERGE')
        return 0

    print('KET QUA: CHUA DU DIEU KIEN MERGE')
    for blocker in verdict['blockers']:
        print('  - %s' % blocker)
    return 1


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
