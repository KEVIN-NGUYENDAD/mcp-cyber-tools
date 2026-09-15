# -*- coding: utf-8 -*-
"""
Schema Reconcile - khoa BO DO, khong khoa ket qua hom nay (AQ-045/AQ-002/AQ-020/AQ-021).

`scripts/schema_reconcile_audit.py` giu bon bat bien da dong bon muc trong hang
doi, va `sprint_gate.py` chan merge tren moi vi pham no bao. Nhung cho toi vong
nay no CHUA co mot phep kiem nao. Do la dung lop loi ma AQ-030 da day: mot bo do
in `0 vi pham` co the co nghia la "hai dau khop", hoac co nghia la "phep kiem
khong bao gio chay". Nhin tu cong thi hai cau tra loi do giong het nhau.

Nen fixture nay khong hoi "hom nay co vi pham khong". No tiem tung loai lech mot
va hoi bo do CO BAO KHONG, roi go ra va hoi no co im lai khong. Moi ca chay tren
mot `state/` gia trong thu muc tam - khong ca nao doc state that, vi state that
chi noi duoc ve lan chay vua roi.
"""

from __future__ import print_function

import io
import json
import os
import shutil
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import schema_reconcile_audit as sra  # noqa: E402


class FakeState(object):
    """Mot thu muc `state/` dung rieng cho mot ca kiem.

    Bo do doc qua `sra.STATE_DIR`, nen gan lai bien do la du. Gan lai - chu
    khong va `_read` - vi day cung la phep kiem rang duong doc that su di qua
    bien do, khong bi dong bang vao gia tri luc import.
    """

    def __init__(self, files):
        self.dir = tempfile.mkdtemp(prefix='schema_reconcile_')
        for name, payload in files.items():
            with io.open(os.path.join(self.dir, name), 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(payload, ensure_ascii=False))

    def __enter__(self):
        self.saved = sra.STATE_DIR
        sra.STATE_DIR = self.dir
        return self

    def __exit__(self, *exc):
        sra.STATE_DIR = self.saved
        shutil.rmtree(self.dir, ignore_errors=True)
        return False

    def levels(self):
        findings, _scope = sra.audit()
        return [f['level'] for f in findings]


def indicator(severity, suppressed=False, quality=None, hostname_source=None):
    row = {'severity': severity, 'suppressed': suppressed}
    if quality:
        row['attribution_quality'] = quality
    if hostname_source:
        row['attribution'] = {'systems': [{'ip': '10.0.0.1',
                                           'hostname_source': hostname_source}]}
    return row


def hunt(indicators, by_severity):
    return {'indicators': indicators, 'by_severity': by_severity}


def clean():
    """Nen sach: moi tep co mat, moi phep cong khop.

    Moi ca duoi day sao lai nen nay roi chi doi DUNG MOT dieu, de khi bo do bao
    thi biet chac no bao vi dieu do.
    """
    return {
        'crypto_inventory.json': {'total_findings': 3, 'score': 72,
                                  'severity_breakdown': {'CRITICAL': 1,
                                                         'MEDIUM': 2}},
        'assets.json': {'assets': [{'vulnerability_count': 40},
                                   {'vulnerability_count': 60}]},
        'nessus_status.json': {'total': 64, 'total_unit': 'distinct_plugins',
                               'distinct_plugins': 64, 'total_instances': 100},
        'hunting_lateral_movement.json': hunt(
            [indicator('INFO', quality='FULL', hostname_source='local host'),
             indicator('HIGH', suppressed=True, quality='PARTIAL',
                       hostname_source='unresolved')],
            {'INFO': 1}),
    }


def run():
    suite = Suite('schema reconcile - bo do co bao khong (AQ-045/002/020/021)')

    # -- 0. Nen sach phai im -------------------------------------------------
    with FakeState(clean()) as state:
        suite.check('nen sach -> 0 vi pham', state.levels() == [])

    # -- 0b. Duong doc that su di qua STATE_DIR ------------------------------
    with FakeState({}):
        _findings, scope = sra.audit()
        suite.check('gan lai STATE_DIR doi huong doc (khong dong bang luc import)',
                    scope.get('crypto') == 'KHONG DOC DUOC')

    # -- 1. AQ-045: by_severity phai dem tap DA LOC --------------------------
    # Day chinh la hinh dang loi that: 6 chi bao ROUTINE_OS_ACTIVITY mang nhan
    # HIGH trong bang tong ket, chiem 78% diem rui ro (18.0 / 23).
    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO'), indicator('HIGH', suppressed=True)],
        {'INFO': 1, 'HIGH': 1})           # <- dem ca chi bao da bi loc
    with FakeState(files) as state:
        levels = state.levels()
        suite.check('by_severity dem ca chi bao suppressed -> SUPPRESSED_COUNTED',
                    'SUPPRESSED_COUNTED' in levels)
        suite.check('... va bat rieng hau qua: khai HIGH khi 0 HIGH con lai',
                    'NOISE_SCORED' in levels)

    # Chi bao bi loc van ton tai la BINH THUONG - no o lai mang co, dung y
    # thiet ke. Cai phai bao la no van duoc DEM, khong phai no ton tai.
    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO'), indicator('HIGH', suppressed=True)], {'INFO': 1})
    with FakeState(files) as state:
        suite.check('chi bao suppressed ton tai nhung KHONG duoc dem -> im',
                    state.levels() == [])

    # NOISE_SCORED chi duoc bao khi 0 chi bao con lai o muc do. Con mot HIGH
    # that thi bang khai HIGH la dung, khong duoc bao.
    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('HIGH'), indicator('HIGH', suppressed=True)], {'HIGH': 1})
    with FakeState(files) as state:
        suite.check('con HIGH that -> khong bao NOISE_SCORED (khong duong tinh gia)',
                    state.levels() == [])

    # -- 2. AQ-002: FULL phai di kem mot hostname co nguon -------------------
    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO', quality='FULL', hostname_source='unresolved')],
        {'INFO': 1})
    with FakeState(files) as state:
        suite.check('FULL tren hostname unresolved -> ATTRIBUTION_UNBACKED',
                    'ATTRIBUTION_UNBACKED' in state.levels())

    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO', quality='FULL',
                   hostname_source='khong khai')], {'INFO': 1})
    with FakeState(files) as state:
        suite.check('FULL ma he thong khai nguon rong -> cung bao',
                    'ATTRIBUTION_UNBACKED' in state.levels())

    # May cuc bo tu biet ten no - day la ngoai le HOP LE, va no phai im, neu
    # khong bo do se bi tat vi keu qua nhieu.
    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO', quality='FULL', hostname_source='local host')],
        {'INFO': 1})
    with FakeState(files) as state:
        suite.check('FULL tu `local host` -> im (ngoai le hop le)',
                    state.levels() == [])

    files = clean()
    files['hunting_lateral_movement.json'] = hunt(
        [indicator('INFO', quality='PARTIAL', hostname_source='unresolved')],
        {'INFO': 1})
    with FakeState(files) as state:
        suite.check('peer o xa khong phan giai duoc + PARTIAL -> im (dung luat)',
                    state.levels() == [])

    # -- 3. AQ-020: sum(severity_breakdown) == total_findings ----------------
    files = clean()
    files['crypto_inventory.json'] = {'total_findings': 19, 'score': 90,
                                      'severity_breakdown': {'CRITICAL': 1}}
    with FakeState(files) as state:
        suite.check('breakdown tong 1 nhung total 19 -> SUM_MISMATCH',
                    'SUM_MISMATCH' in state.levels())

    # Trieu chung rieng cua cung loi khoa int/str: breakdown rong + score 100.
    files = clean()
    files['crypto_inventory.json'] = {'total_findings': 19, 'score': 100,
                                      'severity_breakdown': {}}
    with FakeState(files) as state:
        suite.check('breakdown rong + score 100 tren 19 finding -> CONSTANT_SCORE',
                    'CONSTANT_SCORE' in state.levels())

    files = clean()
    files['crypto_inventory.json'] = {'score': 90,
                                      'severity_breakdown': {'CRITICAL': 1}}
    with FakeState(files) as state:
        suite.check('thieu total_findings -> NO_TOTAL, khong doan',
                    'NO_TOTAL' in state.levels())

    # -- 4. AQ-021: hai don vi phai khai ten, va cung don vi thi phai khop ----
    files = clean()
    files['nessus_status.json'] = {'total': 64}
    with FakeState(files) as state:
        suite.check('nessus.total khong khai don vi -> UNIT_UNDECLARED',
                    'UNIT_UNDECLARED' in state.levels())

    files = clean()
    files['nessus_status.json'] = {'total': 64, 'total_unit': 'distinct_plugins',
                                   'distinct_plugins': 64}
    with FakeState(files) as state:
        suite.check('thieu total_instances (don vi cung he) -> UNIT_MISSING',
                    'UNIT_MISSING' in state.levels())

    # Day la con so that da lam tam vong audit goi nham la "loi dem": 399 luot
    # canh 64 plugin. Khai du don vi thi KHONG duoc bao - hai cau hoi khac nhau.
    files = clean()
    files['assets.json'] = {'assets': [{'vulnerability_count': 399}]}
    files['nessus_status.json'] = {'total': 64, 'total_unit': 'distinct_plugins',
                                   'distinct_plugins': 64, 'total_instances': 399}
    with FakeState(files) as state:
        suite.check('399 luot vs 64 plugin, du don vi -> im (khong phai drift)',
                    state.levels() == [])

    # Con lech cung don vi qua bac do lon thi phai bao.
    files = clean()
    files['assets.json'] = {'assets': [{'vulnerability_count': 399}]}
    files['nessus_status.json'] = {'total': 64, 'total_unit': 'distinct_plugins',
                                   'distinct_plugins': 64, 'total_instances': 64}
    with FakeState(files) as state:
        suite.check('cung don vi ma chenh 6.2 lan -> UNIT_MISMATCH',
                    'UNIT_MISMATCH' in state.levels())

    # -- 5. Vang mat khong duoc doc thanh sach -------------------------------
    with FakeState({}):
        _findings, scope = sra.audit()
        suite.check('khong co state -> pham vi noi KHONG DOC DUOC',
                    scope.get('vulns') == 'KHONG DOC DUOC')
        suite.check('... va khong bia mot pham vi suppressed',
                    scope.get('suppressed') == '-')

    # -- 6. Bo do phai chay DU bon bat bien ----------------------------------
    # Neu ai do them mot check ma quen noi vao INVARIANTS thi no khong bao gio
    # chay, va cong van xanh. Dem o day de viec do khong im lang.
    suite.check('du bon bat bien duoc noi vao INVARIANTS',
                len(sra.INVARIANTS) == 4)
    with FakeState(clean()):
        _findings, scope = sra.audit()
        suite.check('... va ca bon deu khai pham vi (khong cai nao chay rong)',
                    all(scope.get(k) for k in
                        ('crypto', 'vulns', 'attribution', 'suppressed')))

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
