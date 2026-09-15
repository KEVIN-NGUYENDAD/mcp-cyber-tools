# -*- coding: utf-8 -*-
"""
AQ-050 — Pipeline Stage Inflation. Mot lan chay, mot so stage dung.

Trieu chung do duoc: so stage tren man hinh cong tang dan qua cac lan goi —
36, roi 41, roi 43 — trong khi `run_intelligence_pipeline` khong he them mot
viec nao. Khi do that thi `logs/pipeline_results.json` co 45 dong ghi cho 29
stage: `Generate Handoff` xuat hien 17 lan.

Goc khong phai stage leak, cung khong phai metadata drift. `generate_handoff`
KHONG phai mot stage cua pipeline: no chay tu `npm run handoff` va tu chinh
`sprint_gate`. Moi lan chay no append vo dieu kien mot dong vao ban ghi cua mot
lan chay DA KET THUC. Ban ghi cua lan chay A dan dan ke ca nhung viec lam sau
khi A ket thuc.

Con so bi thoi phong o day khong vo hai: no la MAU SO cua dong "0 that bai".
Mot cong doc "45 stage, 0 that bai" dang bao cao ve 45 viec ma pipeline chi lam
29 — cung ho lo default xanh, chi khac la lan nay no thoi mau so len.

Nen bo kiem nay khoa hai dau:
  1. `generate_handoff._record_stage` chi ghi khi no o TRONG lan chay do.
  2. `sprint_gate.evaluate` CHAN khi ban ghi co ten stage lap — de neu duong
     ghi lai ho lan nua thi cong noi ra, thay vi cong bo mot mau so to hon.
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
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality'),
             os.path.join(PROJECT_ROOT, 'tests', 'gate_integrity')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
from test_gate_integrity import base_data  # noqa: E402
import sprint_gate  # noqa: E402
import generate_handoff as gh  # noqa: E402
import run_context  # noqa: E402


class FakeLedger(object):
    """Mot `logs/pipeline_results.json` gia, cong voi bien moi truong lan chay.

    `generate_handoff` doc qua `PROJECT_ROOT`, nen doi bien do la du de no ghi
    vao thu muc tam. Doi luon `CYBER_RUN_ID` de dieu khien cau hoi duy nhat ma
    duong ghi phai tra loi: tien trinh nay co thuoc lan chay trong tep khong.
    """

    def __init__(self, ledger, my_run_id=None):
        self.dir = tempfile.mkdtemp(prefix='pipeline_ledger_')
        self.ledger = ledger
        self.my_run_id = my_run_id
        os.makedirs(os.path.join(self.dir, 'logs'))
        if ledger is not None:
            with io.open(os.path.join(self.dir, 'logs', 'pipeline_results.json'),
                         'w', encoding='utf-8') as fh:
                fh.write(json.dumps(ledger, ensure_ascii=False))

    def __enter__(self):
        self.saved_root = gh.PROJECT_ROOT
        self.saved_env = os.environ.get(run_context.ENV_RUN_ID)
        gh.PROJECT_ROOT = self.dir
        if self.my_run_id:
            os.environ[run_context.ENV_RUN_ID] = self.my_run_id
        else:
            os.environ.pop(run_context.ENV_RUN_ID, None)
        return self

    def __exit__(self, *exc):
        gh.PROJECT_ROOT = self.saved_root
        if self.saved_env is None:
            os.environ.pop(run_context.ENV_RUN_ID, None)
        else:
            os.environ[run_context.ENV_RUN_ID] = self.saved_env
        shutil.rmtree(self.dir, ignore_errors=True)
        return False

    def record(self):
        return gh._record_stage(0.5, 'docs/project/HANDOFF.md')

    def names(self):
        with io.open(os.path.join(self.dir, 'logs', 'pipeline_results.json'),
                     encoding='utf-8') as fh:
            return [s.get('name') for s in json.load(fh)['stages']]


def ledger(run_id, names):
    return {'run_id': run_id,
            'stages': [{'name': n, 'status': 'success'} for n in names]}


def with_stages(stages):
    data = base_data()
    data['pipeline']['stages'] = stages
    return data


def run():
    suite = Suite('pipeline ledger - mot lan chay, mot so stage (AQ-050)')

    # -- 1. Duong ghi: chi ghi vao lan chay CUA MINH ------------------------
    # Day la ca that: `npm run handoff` va `sprint_gate` deu chay ngoai pipeline.
    with FakeLedger(ledger('RUN-A', ['Nessus Collector'])) as fake:
        result = fake.record()
        suite.check('chay tay (khong co run_id) -> khong dong vao ban ghi',
                    result == 'STANDALONE')
        suite.check('... va ban ghi khong he doi',
                    fake.names() == ['Nessus Collector'])

    # Ban ghi cua mot lan chay khac cung khong duoc dong vao — day dung la hinh
    # dang da sinh ra 17 dong `Generate Handoff` chong len mot lan chay cu.
    with FakeLedger(ledger('RUN-A', ['Nessus Collector']),
                    my_run_id='RUN-B') as fake:
        result = fake.record()
        suite.check('lan chay khac -> khong ghi de len ban ghi cua nguoi ta',
                    result == 'LAN CHAY KHAC')
        suite.check('... va ban ghi van dung mot dong',
                    fake.names() == ['Nessus Collector'])

    # Cung lan chay thi ghi — neu khong thi ban va nay chi la tat han mot duong
    # ghi, chu khong phai sua no.
    with FakeLedger(ledger('RUN-A', ['Nessus Collector']),
                    my_run_id='RUN-A') as fake:
        suite.check('cung lan chay -> co ghi', fake.record() == 'DA GHI')
        suite.check('... dung mot dong Generate Handoff duoc them',
                    fake.names() == ['Nessus Collector', 'Generate Handoff'])

    # Goi hai lan trong cung lan chay van la MOT stage: ghi de theo ten, khong
    # phai them. Day chinh la bat bien ma phien ban cu khong co.
    with FakeLedger(ledger('RUN-A', ['Nessus Collector']),
                    my_run_id='RUN-A') as fake:
        fake.record()
        fake.record()
        fake.record()
        suite.check('ba lan goi trong cung lan chay -> van mot dong (ghi de)',
                    fake.names().count('Generate Handoff') == 1)

    # Khong co tep thi khai khong doc duoc, khong tao mot ban ghi tu bia ra.
    with FakeLedger(None, my_run_id='RUN-A') as fake:
        suite.check('khong co ban ghi -> KHONG DOC DUOC, khong tu tao',
                    fake.record() == 'KHONG DOC DUOC')

    # -- 2. Bo do: cong phai CHAN khi ten stage lap -------------------------
    verdict = sprint_gate.evaluate(with_stages(
        [{'name': 'A', 'status': 'success'},
         {'name': 'Generate Handoff', 'status': 'success'},
         {'name': 'Generate Handoff', 'status': 'success'}]))
    suite.check('ten stage lap -> chan merge',
                not verdict['merge_ready'])
    suite.check('... va blocker noi ra ca hai con so (dong ghi vs stage that)',
                any('ghi lap' in b and '3' in b and '2' in b
                    for b in verdict['blockers']))
    suite.check('... verdict khai so stage that ben canh so dong ghi',
                verdict['stages'] == 3 and verdict['distinct_stages'] == 2)

    # Khong lap thi phai im — mot bo do keu tren ban ghi binh thuong se bi tat.
    verdict = sprint_gate.evaluate(with_stages(
        [{'name': 'A', 'status': 'success'},
         {'name': 'B', 'status': 'success'},
         {'name': 'Generate Handoff', 'status': 'success'}]))
    suite.check('ten stage deu khac nhau -> im, va du dieu kien merge',
                verdict['merge_ready'])
    suite.check('... so dong ghi bang so stage that',
                verdict['stages'] == verdict['distinct_stages'] == 3)

    # Hinh dang that da do duoc o vong 16: 45 dong / 29 stage.
    stages = ([{'name': 'S%d' % i, 'status': 'success'} for i in range(28)]
              + [{'name': 'Generate Handoff', 'status': 'success'}] * 17)
    verdict = sprint_gate.evaluate(with_stages(stages))
    suite.check('hinh dang that 45 dong / 29 stage -> chan',
                not verdict['merge_ready']
                and verdict['stages'] == 45
                and verdict['distinct_stages'] == 29)

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
