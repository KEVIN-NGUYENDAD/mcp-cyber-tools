#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chạy toàn bộ bộ kiểm chất lượng phát hiện.

    python tests/detection_quality/run_all.py      (hoặc npm run test:detection)

Thoát 1 nếu có bất kỳ ca nào trượt — dùng được làm cổng chặn trước khi merge.

Bộ kiểm này chia theo MODULE chứ không gộp một tệp, vì mỗi cuộc săn có một kiểu
dương tính giả riêng: credential dumping đọc dòng lệnh của người điều tra,
persistence đọc tác vụ chạy chính pipeline, process hunt đọc tiến trình của
chính nó. Gộp lại thì khi một cuộc săn mới ra đời sẽ không ai biết phải thêm ca
kiểm nào cho nó.
"""

from __future__ import print_function

import io
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

import harness  # noqa: E402

MODULES = [
    'test_invariants',
    'test_credential_dumping',
    'test_lateral_movement',
    'test_persistence',
    'test_suspicious_processes',
    'test_live_state',
]


def main():
    suites = []
    broken = []
    for name in MODULES:
        try:
            module = __import__(name)
            suites.append(module.run())
        except Exception as error:  # noqa: BLE001
            # Một tệp kiểm vỡ KHÔNG được phép đọc như "không có ca nào trượt".
            # Đó là cách một cổng chặn lặng lẽ ngừng chặn.
            broken.append((name, '%s: %s' % (type(error).__name__, error)))

    code = harness.render(suites)

    if broken:
        print('')
        print('!! %d tep kiem khong chay duoc:' % len(broken))
        for name, detail in broken:
            print('   %-30s %s' % (name, detail[:120]))
        code = 1

    return code


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
