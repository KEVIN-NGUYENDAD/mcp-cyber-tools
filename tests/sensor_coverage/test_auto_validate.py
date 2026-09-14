# -*- coding: utf-8 -*-
"""
Tự làm mới nửa KẾT QUẢ TOOL (Sprint 16) — và ba cách việc đó có thể nói dối.

Sprint 15 tách `sensor_coverage.json` thành hai mốc thời gian: nửa cảm biến làm
mới mỗi lần chạy pipeline, nửa tool tự khai tuổi của nó. Trung thực, nhưng không
ai đi sửa nửa già. Một con số đúng về một thứ không bao giờ được sửa vẫn là nợ.

Sprint 16 cho pipeline tự khởi chạy validator ở nền. Việc đó mở ba cửa mới, và
mỗi cửa ứng với một nhóm ca dưới đây:

  1. Chạy chồng nhau. Hai validator cùng ghi một tệp state.
  2. Đóng dấu mới lên nửa cũ — lỗi cũ quay lại qua một đường khác: validator ghi
     đè cả tệp mà KHÔNG đóng dấu gì, xoá sạch hai mốc Sprint 15 vừa dựng.
  3. Thất bại trong im lặng. Không khởi chạy được mà vẫn báo "tự động".
"""

import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import refresh_sensor_coverage as rsc  # noqa: E402
import tool_validator  # noqa: E402
import sensor_probe  # noqa: E402


class Spy(object):
    """Đếm số lần validator được khởi chạy, mà không khởi chạy cái nào."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return 4242


def with_spawn(spy, holder, coverage):
    real_spawn, real_holder = rsc._spawn_validator, rsc._lock_holder
    rsc._spawn_validator = spy
    rsc._lock_holder = lambda: holder
    try:
        return rsc.auto_validate(coverage)
    finally:
        rsc._spawn_validator = real_spawn
        rsc._lock_holder = real_holder


def run():
    suite = Suite('auto-validate (Sprint 16)')

    # -- 1. khi nao KHOI CHAY, khi nao KHONG --------------------------------
    spy = Spy()
    verdict = with_spawn(spy, None, {'tools_age_hours': 3.0})
    suite.check('Nua tool con moi -> khong khoi chay',
                verdict['state'] == 'fresh' and spy.calls == 0,
                '%s, %d lan goi' % (verdict['state'], spy.calls))

    spy = Spy()
    verdict = with_spawn(spy, None, {'tools_age_hours': rsc.STALE_HOURS + 1})
    suite.check('Nua tool qua han -> khoi chay dung mot lan',
                verdict['state'] == 'started' and spy.calls == 1,
                '%s, %d lan goi' % (verdict['state'], spy.calls))

    spy = Spy()
    verdict = with_spawn(spy, None, {'tools_age_hours': None})
    suite.check('Chua tung validate bao gio -> khoi chay',
                verdict['state'] == 'started' and spy.calls == 1,
                '%s, %d lan goi' % (verdict['state'], spy.calls))

    # Ca quan trong nhat: mot ban DANG chay. Neu cho khoi chay them, hai
    # validator se gianh cung mot tep state va cung mot hang doi PowerShell.
    spy = Spy()
    verdict = with_spawn(spy, {'pid': 999, 'started_at': 'x'},
                         {'tools_age_hours': 99.0})
    suite.check('Dang co mot ban chay -> KHONG khoi chay them',
                verdict['state'] == 'running' and spy.calls == 0,
                '%s, %d lan goi' % (verdict['state'], spy.calls))

    # -- 2. that bai phai noi ra ---------------------------------------------
    def broken():
        raise OSError('khong tao duoc tien trinh')

    verdict = with_spawn(broken, None, {'tools_age_hours': 99.0})
    suite.check('Khoi chay that bai -> bao state=failed, khong nuot loi',
                verdict['state'] == 'failed' and bool(verdict.get('error')),
                str(verdict)[:90])

    # Bốn trạng thái phải phân biệt được với nhau: chúng nói bốn điều khác nhau
    # về mức độ tin được của nửa tool, và gộp chúng lại là bước đầu tiên của
    # mọi lần một bảng điều khiển bắt đầu nói dối.
    states = set()
    for holder, age, spawn in ((None, 1.0, Spy()), (None, 99.0, Spy()),
                               ({'pid': 1, 'started_at': 'x'}, 99.0, Spy()),
                               (None, 99.0, broken)):
        states.add(with_spawn(spawn, holder, {'tools_age_hours': age})['state'])
    suite.check('Bon trang thai tach bach: fresh/started/running/failed',
                states == set(['fresh', 'started', 'running', 'failed']),
                str(sorted(states)))

    # -- 3. phep kiem tien trinh khong duoc GIET tien trinh -------------------
    # `os.kill(pid, 0)` tren Windows duoc hien thuc bang TerminateProcess, nen
    # tin hieu 0 — thu chi co nghia "hoi tham" tren POSIX — se giet that. Neu
    # ai do thay _pid_alive bang os.kill, ca kiem nay se tu sat.
    me = os.getpid()
    alive = rsc._pid_alive(me)
    suite.check('_pid_alive thay chinh minh con song', alive is True, str(alive))
    suite.check('Va KHONG giet chinh minh khi hoi', rsc._pid_alive(me) is True)
    suite.check('_pid_alive tra False cho pid khong ton tai',
                rsc._pid_alive(0x7FFFFFF0) is False)

    # -- 4. dong dau tuoi: mot cho duy nhat biet hop dong hai moc -------------
    both = tool_validator.stamp_freshness({}, '2026-01-01T00:00:00',
                                          '2026-01-01T00:00:00', 'test')
    suite.check('Hai nua do cung luc -> noi thang la cung luc',
                'cùng một lần chạy' in both['freshness_note'],
                both['freshness_note'][:70])

    split = tool_validator.stamp_freshness({}, '2026-01-02T00:00:00',
                                           '2026-01-01T00:00:00', 'test')
    suite.check('Hai nua khac tuoi -> noi ro nua tool cu bao nhieu',
                'giờ trước' in split['freshness_note'],
                split['freshness_note'][:70])

    never = tool_validator.stamp_freshness({}, '2026-01-02T00:00:00', None, 'test')
    suite.check('Chua tung validate -> KHONG doc nhu "0 tool dat"',
                'Chưa từng chạy' in never['freshness_note'],
                never['freshness_note'][:70])
    suite.check('Chua tung validate -> tuoi nua tool la None, khong phai 0',
                never['tools_age_hours'] is None,
                repr(never['tools_age_hours']))

    # Chinh tool_validator phai dong dau, khong chi rieng refresh. Day la lo hong
    # Sprint 15 de lai: validator ghi de ca tep va lam hai moc bien mat.
    #
    # Phep kiem nay TUNG doc ma nguon cua `main()` va tim chuoi `stamp_freshness(`.
    # Nhung dieu can bao dam khong phai "main() co goi ham do" — ma la "coverage
    # di ra tu day luon mang dau tuoi". Hai cau do khac nhau, va su khac nhau vua
    # tra gia that: `sprint_gate.collect(validate=True)` goi thang
    # `sensor_coverage()` roi tu ghi tep, khong di qua `main()` — nen
    # `npm run gate:full` sinh ra mot tep thieu ca ba truong, trong khi phep kiem
    # tim-chuoi nay van xanh. No canh dung mot duong di trong nhieu duong.
    #
    # Dau tuoi nay da chuyen vao `sensor_coverage()`, noi coverage duoc TAO RA,
    # nen moi nguoi goi deu duoc dong dau. Phep kiem vi the hoi thang ket qua,
    # khong hoi ma nguon: no manh hon ban cu, vi no dung cho MOI duong goi chu
    # khong rieng `main()`.
    report_file = os.path.join(PROJECT_ROOT, 'state', 'tool_validation.json')
    if not os.path.exists(report_file):
        suite.check('co state/tool_validation.json de kiem dau tuoi', False,
                    'chay `npm run validate` truoc')
    else:
        with open(report_file, encoding='utf-8') as handle:
            report = json.load(handle)
        coverage = tool_validator.sensor_coverage(report)
        for field in ('probe_generated_at', 'tools_generated_at',
                      'freshness_note', 'refreshed_by'):
            suite.check('sensor_coverage() tra ve co `%s`' % field,
                        coverage.get(field) is not None,
                        'duong goi nao cung phai duoc dong dau, khong rieng main()')

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))
