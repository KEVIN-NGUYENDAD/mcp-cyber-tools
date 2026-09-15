# -*- coding: utf-8 -*-
"""
AQ-048 — mot bo kiem khong chay duoc phai doc ra khac mot bo kiem dat.

Trieu chung nhan vao: bo kiem truot mot lan trong bon tren Windows, khong do ma.
`test_sqlite_mirror` nem `PermissionError [WinError 32]` ngay dau `run()` khi mot
lan chay truoc de lai handle SQLite chua dong tren thu muc `_fixture` CO DINH.

Nhung phan dang no khong phai cai nem. La cai in ra sau do:

    Bo kiem phat hien : TRUOT  (TONG: 443/443 dat)

`443/443 dat` doc y het mot lan chay sach. 29 ca cua bo bi vo khong xuat hien o
dau ca — chung khong trach vao TU SO, chung bien mat khoi MAU SO. Mot mau so tu
co lai theo so bo con chay duoc thi luon khop tu so: day la mot default xanh nam
trong dong duy nhat ma cong trich ra de in len man hinh.

Nen bo kiem nay khoa ba thu:
  1. `harness.render(..., missing=n)` phai noi ra n ngay tren dong `TONG:`.
  2. `missing` phai lam ma thoat khac 0 ke ca khi moi ca chay duoc deu dat.
  3. Khong bo kiem nao con dung thu muc fixture CO DINH — nguon lay nhiem giua
     cac lan chay, va la thu da nem WinError 32 ngay tu dau.
"""

from __future__ import print_function

import io
import os
import re
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
TESTS_ROOT = os.path.join(PROJECT_ROOT, 'tests')
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

import harness  # noqa: E402
from harness import Suite  # noqa: E402


class Capture(object):
    """Bat stdout - o day chinh NOI DUNG in ra la thu dang kiem."""

    def __enter__(self):
        self.saved = sys.stdout
        sys.stdout = self.buffer = io.StringIO()
        return self

    def __exit__(self, *exc):
        sys.stdout = self.saved
        return False

    def text(self):
        return self.buffer.getvalue()


def passing_suite(n=3):
    suite = Suite('gia lap')
    for i in range(n):
        suite.check('ca %d' % i, True)
    return suite


def run():
    suite = Suite('cach ly bo kiem - vang mat khong doc thanh sach (AQ-048)')

    # -- 1. Khong co bo nao vo: dong TONG giu nguyen hinh dang cu -----------
    with Capture() as cap:
        code = harness.render([passing_suite()])
    suite.check('moi bo chay duoc -> ma thoat 0', code == 0)
    suite.check('... va dong TONG khong bia them canh bao',
                'TONG: 3/3 dat' in cap.text()
                and 'KHONG CHAY DUOC' not in cap.text())

    # -- 2. Co bo vo: phai hien NGAY TREN dong TONG -------------------------
    # Day la dong duy nhat `sprint_gate.run_tests()` trich ra (`startswith`
    # 'TONG:') va in len man hinh cong. Bao o cho khac thi cong khong thay.
    with Capture() as cap:
        code = harness.render([passing_suite()], missing=2)
    text = cap.text()
    tong = [line for line in text.splitlines() if line.startswith('TONG:')]
    suite.check('co bo vo -> ma thoat 1 du moi ca chay duoc deu dat', code == 1)
    suite.check('... va chinh dong TONG noi ra so bo khong chay duoc',
                tong and 'KHONG CHAY DUOC' in tong[-1] and '2' in tong[-1],
                str(tong))
    suite.check('... va no khong con doc duoc thanh mot lan chay sach',
                tong and tong[-1] != 'TONG: 3/3 dat', str(tong))

    # -- 3. run_all phai THUC SU truyen so bo vo vao render -----------------
    # Bat bien tren la vo nghia neu cho goi that van goi `render(suites)`.
    with io.open(os.path.join(TESTS_ROOT, 'detection_quality', 'run_all.py'),
                 encoding='utf-8') as fh:
        runner = fh.read()
    suite.check('run_all goi render() co truyen missing=len(broken)',
                'harness.render(suites, missing=len(broken))' in runner)

    # -- 4. Khong bo kiem nao con dung thu muc fixture CO DINH --------------
    # `os.path.join(TESTS_DIR, '_fixture')` la duong lay nhiem giua cac lan
    # chay, va la thu da nem WinError 32 lam ca bo sqlite_mirror khong chay.
    pattern = re.compile(r"os\.path\.join\(\s*TESTS_DIR\s*,\s*['\"]_fixture['\"]")
    offenders = []
    for folder, _dirs, files in os.walk(TESTS_ROOT):
        for name in files:
            if not name.startswith('test_') or not name.endswith('.py'):
                continue
            path = os.path.join(folder, name)
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue          # chinh bo kiem nay mang mau do de doi chieu
            with io.open(path, encoding='utf-8') as fh:
                if pattern.search(fh.read()):
                    offenders.append(os.path.relpath(path, PROJECT_ROOT))
    suite.check('khong bo kiem nao dung thu muc fixture co dinh',
                offenders == [], str(offenders))

    # Va thu muc do khong con nam lai tren dia tu cac lan chay truoc.
    stale = [os.path.relpath(os.path.join(f, '_fixture'), PROJECT_ROOT)
             for f, dirs, _files in os.walk(TESTS_ROOT) if '_fixture' in dirs]
    suite.check('khong con thu muc _fixture sot lai trong cay kiem',
                stale == [], str(stale))

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
