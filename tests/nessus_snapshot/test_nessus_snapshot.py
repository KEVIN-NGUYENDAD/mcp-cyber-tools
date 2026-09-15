# -*- coding: utf-8 -*-
"""
Nessus snapshot / daily brief — don vi va nhan trang thai (AQ-021).

Loi goc gom hai phan, ca hai deu la NHAN chu khong phai phep dem sai:

1. `nessus_status.json` khai `total: 64` (dem theo PLUGIN rieng biet), con
   `assets.json` cong `vulnerability_count` theo TUNG HOST ra 399 (dem theo
   LUOT host x plugin). Chenh 6.2 lan tren cung mot ban quet, va daily brief
   cu chi in "64" tran khong nhan don vi -- doc nhu tu mau thuan voi con so
   399 o phan khac cua brief.

2. `/scanners` API tra `status: 'on'` nghia la scanner daemon dang LIEN KET
   voi Nessus manager -- khong phai "dang co mot job quet chay". Ban do cu
   `'on' -> 'running'` muon dung ten mot job dang chay, nen `scanner_status:
   running` dung canh `scan_age_hours: 158` doc nhu "da quet suot 158 gio".

Fixture nay khoa: (a) `get_scanner_status()` khong bao gio tra ve chuoi
'running' cho status LIEN KET 'on'; (b) brief's vulnerability summary luon
mang ca `total_findings` (co nhan don vi) VA `total_instances`, khong bao
gio in mot con so tran khong ngu canh; (c) `scan_stale` phan anh dung
nguong 48h dung boi calculate_risk_score.py.
"""
from __future__ import print_function

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
from collect_nessus_snapshot import NessusCollector  # noqa: E402
from generate_daily_brief import DailyBriefGenerator  # noqa: E402


def run():
    suite = Suite('nessus snapshot / daily brief (AQ-021)')
    collector = NessusCollector()

    # -- 1. get_scanner_status(): 'on' KHONG DUOC anh xa thanh 'running' -----
    status_on, raw_on = collector.SCANNER_LINK_STATUS.get('on'), 'on'
    suite.check("scanner status 'on' anh xa thanh 'online', khong phai 'running'",
                status_on == 'online', str(status_on))
    suite.check("khong con nhan 'running' nao trong bang anh xa (ten job, khong "
                "phai trang thai lien ket)",
                'running' not in collector.SCANNER_LINK_STATUS.values(),
                str(collector.SCANNER_LINK_STATUS))

    status_off = collector.SCANNER_LINK_STATUS.get('off')
    suite.check("scanner status 'off' anh xa thanh 'offline'",
                status_off == 'offline', str(status_off))

    # -- 2. generate_vulnerability_summary(): khong in so tran khong nhan -----
    class _FakeBrief(DailyBriefGenerator):
        def __init__(self, fixture):
            self._fixture = fixture

        def load_json(self, filename):
            if filename == 'nessus_status.json':
                return self._fixture
            return None

    stale_fixture = {
        'scan_name': 'Home Network Discovery',
        'scan_age_hours': 158,
        'total': 64,
        'total_unit': 'distinct_plugins',
        'total_instances': 399,
        'critical': 0,
        'high': 0,
        'medium': 5,
        'low': 10,
        'info': 49,
        'scanner_status': 'online',
    }
    fake = _FakeBrief(stale_fixture)
    summary = fake.generate_vulnerability_summary()

    suite.check('brief mang total_findings (64, dem plugin) VA total_instances '
                '(399, dem luot host) cung luc -- khong con so nao dung mot minh',
                summary['total_findings'] == 64 and summary['total_instances'] == 399,
                str(summary))
    suite.check('  -> total_findings co nhan don vi ro rang',
                summary['total_findings_unit'] == 'distinct_plugins',
                summary['total_findings_unit'])
    suite.check("scanner_status truyen qua nguyen ('online'), khong con la 'running'",
                summary['scanner_status'] == 'online', summary['scanner_status'])
    suite.check('ban quet 158h > nguong 48h -> scan_stale = True (khong con doc '
                "'running' + 158h nhu mot mau thuan)",
                summary['scan_stale'] is True, str(summary))

    # -- 3. ban quet moi -> khong bi gan nhan stale -----------------------
    fresh_fixture = dict(stale_fixture, scan_age_hours=2)
    fresh_summary = _FakeBrief(fresh_fixture).generate_vulnerability_summary()
    suite.check('ban quet 2h tuoi -> scan_stale = False',
                fresh_summary['scan_stale'] is False, str(fresh_summary))

    # -- 4. thieu nessus_status.json -> None, khong bia du lieu -------------
    empty_summary = _FakeBrief(None).generate_vulnerability_summary()
    suite.check('khong co nessus_status.json -> summary la None, khong bia so 0',
                empty_summary is None, str(empty_summary))

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
