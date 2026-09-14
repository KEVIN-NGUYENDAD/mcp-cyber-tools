# -*- coding: utf-8 -*-
"""
Sprint C — Portal Hardening (AQ-009, AQ-010).

Hai lỗi khác nhau, cùng một gốc: portal đối xử với dữ liệu DFIR như dữ liệu nội
bộ đáng tin.

AQ-009 — nó là đầu vào KHÔNG đáng tin theo đúng định nghĩa. Bảng điều khiển này
hiển thị tên tiến trình, dòng lệnh, tên tác vụ theo lịch và đường dẫn tệp thu từ
chính máy đang bị theo dõi. Nếu máy đó đã bị xâm nhập thì kẻ tấn công *kiểm soát*
nội dung các trường ấy — và một tiến trình đặt tên
`<img src=x onerror=...>` sẽ thực thi trong trình duyệt của người trực ca, ngay
lúc họ mở dashboard để điều tra chính cuộc xâm nhập đó.

AQ-010 — KPI đếm 602 trong khi con số thật là 375, và bốn danh sách top-10 lấy
`.slice(0, 10)` trên mảng CHƯA sắp xếp. Hai chỉ báo HIGH thật nằm ở vị trí bất kỳ
trong 455 phần tử, nên bảng gần như chắc chắn hiển thị mười mục INFO và giấu đi
cả hai mục đáng xem — đúng ngược với việc nó sinh ra để làm.
"""

import io
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
for path in (SCRIPTS_DIR, os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import portal_escape_audit as pea  # noqa: E402

APP_JS = os.path.join(PROJECT_ROOT, 'web', 'app.js')


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def state(filename):
    try:
        with io.open(os.path.join(PROJECT_ROOT, 'state', filename),
                     encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run():
    suite = Suite('portal hardening (Sprint C)')
    app = read(APP_JS)

    # -- AQ-009: escape ----------------------------------------------------
    findings = pea.audit()
    unescaped = [f for f in findings if f['level'] == 'UNESCAPED']
    suite.check('Khong con bieu thuc chua escape di vao innerHTML',
                not unescaped,
                '; '.join('%s:%s' % (f['line'], f['expression'][:30])
                          for f in unescaped[:4]))
    suite.check('Bo audit co quet duoc gi do (khong phai 0 bieu thuc)',
                len(findings) >= 40, '%d bieu thuc' % len(findings))

    # Bộ audit phải BẮT ĐƯỢC lỗi thật, nếu không thì con số 0 ở trên vô nghĩa.
    # Đây là phép thử đột biến chạy ngay trong bộ kiểm: một biểu thức thô phải
    # bị xếp là chưa escape.
    suite.check('is_safe() xep `incident.title` la CHUA escape',
                not pea.is_safe('incident.title'))
    suite.check('is_safe() xep `ind?.process` la CHUA escape',
                not pea.is_safe('ind?.process'))
    suite.check('is_safe() chap nhan escapeHtmlSafe(...)',
                pea.is_safe('escapeHtmlSafe(incident.title)'))

    # Những trường thật sự do máy bị giám sát điều khiển.
    for field in ('incident.title', 'ind?.process'):
        suite.check('Truong "%s" khong con di thang vao innerHTML' % field,
                    ('${%s}' % field) not in app)

    suite.check('Portal co ham escape', 'function escapeHtmlSafe(' in app)
    # `h` là template có thẻ: escape theo mặc định, `raw()` là ngoại lệ phải viết
    # ra. "Nhớ gọi đúng chỗ" là thứ thất bại đều đặn — 25/26 sink đã không gọi.
    suite.check('Portal co template co the `h` (escape mac dinh)',
                'function h(strings, ...values)' in app)
    suite.check('  -> va raw() de khai bao ngoai le mot cach doc duoc',
                'function raw(' in app)

    # -- AQ-010: dem dung, sap xep truoc khi cat --------------------------
    suite.check('Portal co loc `suppressed` truoc khi dem',
                'suppressed' in app)
    suite.check('Danh sach top-10 duoc SAP XEP truoc khi .slice(0, 10)',
                'SEVERITY_RANK[b?.severity]' in app
                and 'ranked.slice(0, 10)' in app)
    suite.check('Khong con .slice(0, 10) tren mang chua sap xep',
                'indicators.slice(0, 10)' not in app)
    suite.check('So tieng on hien canh so that, khong bi giau',
                'noise > 0' in app and '+${escapeHtmlSafe(noise)} noise' in app)

    # Con số thật trong state: nếu 602 quay lại, bản vá đã mất.
    total = 0
    kept = 0
    for filename in ('hunting_credential_dumping.json', 'hunting_persistence.json',
                     'hunting_lateral_movement.json',
                     'hunting_suspicious_processes.json'):
        data = state(filename) or {}
        indicators = data.get('indicators') or []
        total += len(indicators)
        kept += len([i for i in indicators if not i.get('suppressed')])
    suite.check('State that co ca chi bao giu lai lan tieng on',
                total > 0 and kept > 0, 'tong=%d giu=%d' % (total, kept))
    suite.check('  -> va hai con so do KHAC nhau (co tieng on de loc)',
                kept < total, 'tong=%d giu=%d' % (total, kept))

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))
