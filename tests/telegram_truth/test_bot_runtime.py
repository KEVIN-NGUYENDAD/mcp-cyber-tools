# -*- coding: utf-8 -*-
"""Cau noi: keo bo kiem JavaScript cua bot vao cung mot cong chan.

`redact.js` va `resilientPolling.js` la ma nguon Node, duoc kiem bang `node
--test`. Neu de chung chay bang mot lenh npm rieng thi se co lan chi chay mot
nua — dung loi da chep san trong `run_all.py`: "mot cong chan chia lam hai lenh
la mot cong chan se co lan chi chay mot nua".

Nen tep nay goi `node --test` roi doc TAP tra ve, bien tung ca JS thanh mot
check trong bang ket qua Python. Mot ca JS truot lam do dong `TONG:` va lam
`npm run gate` thoat 1, y het mot ca Python truot.

Truong hop khong chay duoc (khong co node, sai duong dan, tien trinh vo) KHONG
duoc doc ra la "khong ca nao truot" — no duoc ghi thanh mot check TRUOT rieng.
"""

from __future__ import print_function

import os
import re
import subprocess
import sys

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

sys.path.insert(0, os.path.join(TESTS_DIR, 'detection_quality'))
from harness import Suite, PROJECT_ROOT  # noqa: E402

# Node coi thu muc la mot module, khong phai mot cay kiem — phai dua glob.
TEST_GLOB = 'tests/telegram_truth/*.test.mjs'

# TAP: `ok 3 - ten ca` / `not ok 3 - ten ca`. Chi lay dong muc dau, bo qua ca
# con long nhau (co thut dau dong).
TAP_LINE = re.compile(r'^(not )?ok (\d+) - (.+?)(?:\s+# (SKIP|TODO).*)?$')


def run_node_tests():
    """Tra ve (stdout, ma_thoat, loi_khoi_chay)."""
    command = [
        'node', '--test', '--test-reporter=tap', TEST_GLOB
    ]
    try:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=(sys.platform == 'win32'),
        )
        output, _ = process.communicate()
        return output.decode('utf-8', 'replace'), process.returncode, None
    except OSError as error:
        return '', -1, '%s: %s' % (type(error).__name__, error)


def parse_tap(output):
    """Bien TAP thanh [(ten, dat)]."""
    cases = []
    for line in output.splitlines():
        if line.startswith((' ', '\t', '#')):
            continue
        match = TAP_LINE.match(line.strip())
        if not match:
            continue
        failed, _number, name, directive = match.groups()
        if directive:  # SKIP/TODO khong tinh la dat cung khong tinh la truot
            continue
        cases.append((name.strip(), failed is None))
    return cases


def run():
    suite = Suite('bot runtime JS (che danh tinh + ket noi lai)')

    output, code, launch_error = run_node_tests()

    if launch_error is not None:
        suite.check('node --test khoi chay duoc', False, launch_error)
        return suite

    cases = parse_tap(output)

    # Mot bo kiem tra ve 0 ca la mot bo kiem khong chay, khong phai mot bo kiem
    # sach. Thieu mau so o day chinh la lop loi AQ-048.
    if not cases:
        suite.check('bo kiem JS co ca de chay', False,
                    'TAP khong co dong ca nao; ma thoat %s' % code)
        return suite

    for name, ok in cases:
        detail = '' if ok else 'xem `node --test %s` de doc chi tiet' % TEST_GLOB
        suite.check(name, ok, detail)

    # Ma thoat khac 0 ma moi ca deu dat nghia la co thu vo NGOAI cac ca — mot
    # tep khong nap duoc, mot loi bat dong bo sau khi chay xong.
    if code != 0 and not suite.failed:
        suite.check('tien trinh node thoat 0', False,
                    'moi ca dat nhung ma thoat = %s' % code)

    return suite


if __name__ == '__main__':
    import harness
    sys.exit(harness.render([run()]))
