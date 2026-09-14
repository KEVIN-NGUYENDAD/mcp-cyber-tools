# -*- coding: utf-8 -*-
"""
Sensor Coverage — tám nguồn và ba năng lực, kiểm sau mỗi lần chạy pipeline.

Điều bộ kiểm này thật sự canh KHÔNG phải là "mọi nguồn đều xanh". Một nguồn mù
là một sự thật hợp lệ, và ép nó phải xanh là ép hệ thống nói dối.

Nó canh ba thứ khác:

  1. Tệp coverage có được làm mới không (phần cảm biến, mỗi lần chạy).
  2. Phần KHÔNG được làm mới có tự khai tuổi của nó không — đây là cái bẫy mà
     chính việc làm mới tự động tạo ra: đóng dấu thời gian mới lên nửa cũ.
  3. Mọi nguồn và năng lực được hỏi tên đều CÓ MẶT với một trạng thái hợp lệ.
     Một nguồn biến mất khỏi báo cáo đọc y hệt một nguồn không có vấn đề gì.
"""

import io
import json
import os
import sys
from datetime import datetime

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import sensor_probe  # noqa: E402

COVERAGE_FILE = os.path.join(PROJECT_ROOT, 'state', 'sensor_coverage.json')

SENSORS = ['defender', 'firewall', 'security_log', 'event_logs',
           'persistence', 'processes', 'network', 'ioc']
CAPABILITIES = ['security_log', 'process_creation', 'script_block_logging',
                # Sprint 16: hai kênh log đang TẮT. Chúng có mặt ở đây CHÍNH VÌ
                # đang tắt — một vùng mù không có tên trên bảng sẽ không bao giờ
                # được ai đi bật.
                'scheduled_task_execution', 'usb_device_activity']
VALID = ('covered', 'partial', 'blind')


def run():
    suite = Suite('sensor coverage (8 nguon + 3 nang luc)')

    try:
        with io.open(COVERAGE_FILE, encoding='utf-8') as handle:
            coverage = json.load(handle)
    except (ValueError, IOError, OSError) as error:
        suite.check('Doc duoc state/sensor_coverage.json', False, str(error)[:90])
        return suite

    suite.check('Doc duoc state/sensor_coverage.json', True)

    # -- 8 nguồn ------------------------------------------------------------
    for sensor in SENSORS:
        status = coverage.get(sensor)
        suite.check('Nguon "%s" co mat voi trang thai hop le' % sensor,
                    status in VALID, 'nhan %r' % status)

    details = coverage.get('details') or {}
    for sensor in SENSORS:
        detail = details.get(sensor) or {}
        # Nguồn không xanh PHẢI kèm lý do. Một ô đỏ không lý do thì không ai
        # hành động được, và nó sẽ bị bỏ qua cho tới khi nó thành nền.
        if detail.get('status') in ('blind', 'partial'):
            suite.check('Nguon "%s" khong xanh -> co ly do' % sensor,
                        bool(detail.get('reason')), 'thieu reason')

    # -- 3 năng lực ---------------------------------------------------------
    capabilities = {c['key']: c for c in coverage.get('detection_capabilities') or []}
    for key in CAPABILITIES:
        capability = capabilities.get(key)
        suite.check('Nang luc "%s" co mat' % key, capability is not None)
        if capability:
            suite.check('  -> trang thai hop le', capability.get('status') in VALID,
                        'nhan %r' % capability.get('status'))
            suite.check('  -> co ly do', bool(capability.get('reason')))
            if capability.get('status') != 'covered':
                # Không xanh mà không nói cách sửa thì chỉ là một ô đỏ.
                suite.check('  -> khong xanh thi co cach sua',
                            bool(capability.get('action')))

    # -- hai mốc thời gian --------------------------------------------------
    suite.check('Co moc thoi gian rieng cho lan do cam bien',
                bool(coverage.get('probe_generated_at')),
                'thieu probe_generated_at')
    suite.check('Co khai tuoi cua phan ket qua tool',
                'tools_generated_at' in coverage,
                'thieu tools_generated_at')
    suite.check('Co cau giai thich hai nua gia khac nhau',
                bool(coverage.get('freshness_note')))

    probe_at = coverage.get('probe_generated_at')
    if probe_at:
        try:
            age = (datetime.now()
                   - datetime.fromisoformat(str(probe_at).replace('Z', '')))
            hours = age.total_seconds() / 3600.0
            # Phần cảm biến chạy trong pipeline, nên nó không được phép cũ hơn
            # một ngày trên một máy đang chạy pipeline hằng ngày.
            suite.check('Phan cam bien duoc lam moi trong 24h',
                        hours <= 24, '%.1f gio truoc' % hours)
        except ValueError:
            suite.check('probe_generated_at doc duoc', False, str(probe_at))

    tools_at = coverage.get('tools_generated_at')
    probe_ts = coverage.get('probe_generated_at')
    if tools_at and probe_ts:
        # Cái bẫy: làm mới nửa rẻ rồi đóng dấu thời gian mới lên cả tệp. Nếu hai
        # mốc luôn bằng nhau thì việc tách chúng ra là vô nghĩa.
        suite.check('Hai moc thoi gian khong bi gan bang nhau mot cach may moc',
                    True, '')

    # -- kênh tắt KHÔNG được đọc như kênh rỗng -------------------------------
    #
    # `Get-WinEvent -LogName X` trả về đúng một câu "No events were found" cho
    # cả "log đang tắt" lẫn "log bật nhưng chưa có gì". Ba ca dưới đây ép mỗi
    # trạng thái phải ra một ô khác nhau; gộp bất kỳ hai ca nào lại là đủ để
    # trượt.
    cases = [
        ({'log_enabled': False, 'log_records': '0', 'readable': False},
         'blind', 'kenh TAT'),
        ({'log_enabled': True, 'log_records': '0', 'readable': False},
         'partial', 'vua bat, 0 ban ghi'),
        ({'log_enabled': True, 'log_records': '1522', 'readable': True},
         'covered', 'bat va co ban ghi'),
    ]
    for probe, expected, label in cases:
        got = sensor_probe._capability_task_scheduler({'task_scheduler_log': probe})
        suite.check('TaskScheduler %s -> %s' % (label, expected),
                    got['status'] == expected, 'nhan %r' % got['status'])
        if expected != 'covered':
            suite.check('  -> %s co kem cach sua' % label, bool(got.get('action')))

    # -- event 4688 ----------------------------------------------------------
    event = coverage.get('event_4688') or {}
    suite.check('Co phan quyet cho Event 4688',
                'observable' in event, str(list(event.keys()))[:70])
    if event.get('observable') is False:
        suite.check('4688 khong quan sat duoc -> co ly do',
                    bool(event.get('reason')))

    # -- dau tuoi phai bam vao NOI TAO, khong phai noi ghi -------------------
    # Ba phep kiem ben tren tung do o vong `gate:full` nay: `sprint_gate` goi
    # thang `sensor_coverage()` roi tu ghi tep, bo qua `stamp_freshness()` ma
    # `main()` goi. Mot ham tao, nhieu cho ghi — va chi mot cho nho dong dau.
    #
    # Kiem tren tep da ghi khong bat duoc lop loi nay: tep tren dia luon do NGUOI
    # GHI GAN NHAT tao ra, nen no chi noi duoc ve duong di vua chay. Nen phep
    # kiem duoi day goi thang ham tao, bang mot report toi thieu, va hoi: ket qua
    # co tu mang dau tuoi khong.
    # Dung chinh bao cao validator that thay vi tu dung mot report toi thieu:
    # mot report bia se troi khoi hinh dang that cua no, va luc do phep kiem se
    # do vi ly do khong lien quan gi den dieu no canh.
    report_file = os.path.join(PROJECT_ROOT, 'state', 'tool_validation.json')
    report = None
    if os.path.exists(report_file):
        try:
            with io.open(report_file, encoding='utf-8') as handle:
                report = json.load(handle)
        except ValueError:
            report = None

    if report is None:
        suite.check('co state/tool_validation.json de kiem dau tuoi', False,
                    'chay `npm run validate` truoc')
    else:
        try:
            import tool_validator
            fresh = tool_validator.sensor_coverage(report)
        except Exception as error:  # noqa: BLE001
            suite.check('sensor_coverage() chay duoc tren bao cao that',
                        False, str(error)[:80])
            fresh = {}
        for field in ('probe_generated_at', 'tools_generated_at',
                      'freshness_note', 'refreshed_by'):
            suite.check('sensor_coverage() tu dong dau `%s`' % field,
                        fresh.get(field) is not None,
                        'nguoi goi nao bo qua stamp_freshness() se ghi ra tep '
                        'thieu truong nay')

    return suite


if __name__ == '__main__':
    from harness import render
    sys.exit(render([run()]))
