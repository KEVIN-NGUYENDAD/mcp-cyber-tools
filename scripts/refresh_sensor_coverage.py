#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REFRESH SENSOR COVERAGE (Sprint 15)

Làm mới `state/sensor_coverage.json` sau mỗi lần chạy pipeline.

Vì sao trước đây không làm mới
-------------------------------
`tool_validator.py` gọi THẬT cả 99 tool, mất khoảng 5 phút và có tác dụng phụ
(ghi báo cáo, chạy quét). Đưa nguyên nó vào pipeline là không được, nên
`sensor_coverage.json` đứng yên giữa các lần kiểm tay — Portal phải hiển thị
tuổi của dữ liệu kèm cảnh báo quá 24 giờ để bù.

Nhưng tệp đó trộn HAI câu trả lời có giá rất khác nhau:

    "nguồn này có mở được không?"    <- sensor_probe.py, ~10 giây, không tác dụng phụ
    "tool nào trả về bằng chứng?"    <- 99 lời gọi thật, ~5 phút, có tác dụng phụ

Nửa đắt tiền là lý do cả tệp đứng yên. Nửa rẻ tiền mới là nửa thay đổi thường
xuyên: một log bị tắt, một quyền bị thu hồi, một dịch vụ dừng — tất cả xảy ra
giữa hai lần kiểm tay, và tất cả đều thuộc nửa rẻ.

Cái bẫy phải tránh
------------------
Cách làm sai hiển nhiên là làm mới nửa rẻ rồi đóng dấu thời gian MỚI lên cả tệp.
Khi đó phần kết quả tool cũ ba ngày sẽ đọc như vừa đo xong — và đó đúng là kiểu
nói dối mà mọi sprint trước đã đi xoá.

Nên tệp mang HAI mốc thời gian, và phần nào cũ thì tự khai là cũ.
"""

from __future__ import print_function

import io
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
VALIDATION_FILE = os.path.join(STATE_DIR, 'tool_validation.json')
COVERAGE_FILE = os.path.join(STATE_DIR, 'sensor_coverage.json')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import sensor_probe  # noqa: E402
import tool_validator  # noqa: E402


def _read_json(path):
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def _age_hours(timestamp):
    if not timestamp:
        return None
    try:
        then = datetime.fromisoformat(str(timestamp).replace('Z', ''))
    except ValueError:
        return None
    return round((datetime.now() - then).total_seconds() / 3600.0, 1)


def refresh():
    """Dò lại cảm biến, dựng lại coverage, giữ nguyên phần kết quả tool."""
    probes = sensor_probe.probe_all()

    previous = _read_json(VALIDATION_FILE)
    if previous is None:
        # Chưa từng chạy tool_validator. Vẫn làm mới được phần cảm biến — và
        # nói thẳng là phần tool chưa có, thay vì báo 0 tool PASS (đọc y hệt
        # "mọi tool đều hỏng").
        rows = []
        tools_at = None
    else:
        rows = previous.get('results') or []
        tools_at = previous.get('generated_at')

    now = datetime.now().isoformat()
    report = {
        'version': tool_validator.VERSION,
        'generated_at': now,
        'tools_registered': (previous or {}).get('tools_registered', len(rows)),
        'probes': probes,
        'event_4688': sensor_probe.security_log_summary(probes),
        'access_diagnosis': sensor_probe.access_diagnosis(probes),
        'fallback_sources': sensor_probe.fallback_summary(probes),
        'detection_capabilities': sensor_probe.capability_summary(probes),
        'results': rows,
        'summary': tool_validator._summarize(rows),
    }

    coverage = tool_validator.sensor_coverage(report)

    # Hai mốc thời gian, tách bạch. `generated_at` giữ nghĩa cũ (lần dựng tệp
    # này) để Portal không vỡ; hai trường mới nói rõ từng nửa già bao nhiêu.
    coverage['probe_generated_at'] = now
    coverage['tools_generated_at'] = tools_at
    coverage['tools_age_hours'] = _age_hours(tools_at)
    coverage['refreshed_by'] = 'refresh_sensor_coverage'
    coverage['freshness_note'] = (
        'Phần cảm biến (đọc được hay không) vừa dò lại. Phần kết quả tool là của '
        'lần chạy tool_validator gần nhất%s — chạy `npm run validate` để làm mới.'
        % ('' if tools_at is None else ' (%s giờ trước)'
           % coverage['tools_age_hours']))
    if tools_at is None:
        coverage['freshness_note'] = (
            'Chưa từng chạy tool_validator. Coverage dưới đây chỉ phản ánh việc '
            'nguồn có mở được hay không, chưa có tool nào được kiểm.')

    with io.open(COVERAGE_FILE, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(coverage, indent=2, ensure_ascii=False))

    return coverage


REPORTED = ['defender', 'firewall', 'security_log', 'event_logs',
            'persistence', 'processes', 'network', 'ioc']


def main():
    coverage = refresh()

    flat = {key: coverage.get(key) for key in REPORTED}
    print(json.dumps({
        'status': 'success',
        'coverage': flat,
        'capabilities': {c['key']: c['status']
                         for c in coverage.get('detection_capabilities') or []},
        'event_4688': coverage['event_4688']['observable'],
        'tools_age_hours': coverage.get('tools_age_hours'),
    }, indent=2, ensure_ascii=False))

    # Nguồn mù là một sự thật cần biết, KHÔNG phải lỗi của pipeline. Thoát 0 để
    # một cảm biến mù không làm cả pipeline đỏ — chỗ báo động đúng là bảng
    # coverage, không phải mã thoát của một stage.
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
