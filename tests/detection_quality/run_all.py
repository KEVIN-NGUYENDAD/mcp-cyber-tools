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

# Bo kiem ngoai thu muc nay, nap theo duong dan. Telegram Truth song rieng vi no
# kiem mot lop khac, nhung no phai chay cung mot lenh — mot cong chan chia lam
# hai lenh la mot cong chan se co lan chi chay mot nua.
EXTRA_SUITES = [
    ('telegram_truth', 'test_telegram_fields'),
    # PHASE 1. Cau noi sang `node --test`: che danh tinh + ket noi lai la ma
    # JavaScript, nhung chung phai do bang CUNG mot lenh nhu phan Python, neu
    # khong se co lan chi chay mot nua.
    ('telegram_truth', 'test_bot_runtime'),
    # PHASE 1. Co HAI duong gui Telegram (bot Node, script Python) nen co hai
    # ban sao cua bo che. Hai ban sao khong kiem chung nhau se troi khoi nhau,
    # va cai troi ra se la mot duong ro ma khong ai nhin.
    ('telegram_truth', 'test_redaction_parity'),
    ('sensor_coverage', 'test_coverage_refresh'),
    ('sensor_coverage', 'test_auto_validate'),
    ('ioc_quality', 'test_ioc_quality'),
    # PHASE 1. Bo loc tien trinh Windows. Phan lon ca kiem la ca AM TINH: mot bo
    # loc tieng on chi duoc kiem theo chieu "co loc duoc khong" se im lang dung
    # vao lop tan cong dung nhi phan hop le.
    ('ioc_quality', 'test_os_whitelist'),
    ('crypto_inventory', 'test_crypto_inventory'),
    ('nessus_snapshot', 'test_nessus_snapshot'),
    ('deploy_truth', 'test_deploy_truth'),
    ('green_defaults', 'test_green_defaults'),
    ('portal_hardening', 'test_portal_hardening'),
    ('gate_integrity', 'test_gate_integrity'),
    ('fixtures', 'test_scoring_fixtures'),
    ('sqlite_mirror', 'test_sqlite_mirror'),
    # AQ-045. `schema_reconcile_audit` giu bon bat bien ma cong chan merge tren
    # do, nhung chinh no chua tung duoc kiem. Mot bo do chua bao gio duoc chung
    # minh la BAO DUOC thi `0 vi pham` cua no khong phan biet duoc voi `khong
    # chay` — dung lop loi AQ-030 da day.
    ('schema_reconcile', 'test_schema_reconcile'),
    # AQ-050. Ban ghi mot lan chay phai noi ve dung lan chay do. So stage tung
    # phinh 36 -> 41 -> 43 vi mot script ngoai pipeline append vao ban ghi cua
    # lan chay da ket thuc; mau so cua "0 that bai" bi thoi len theo.
    ('pipeline_ledger', 'test_pipeline_ledger'),
    # AQ-048. Mot bo kiem khong chay duoc phai doc ra khac mot bo kiem dat —
    # `TONG: 443/443 dat` canh chu TRUOT la mot mau so tu co lai theo so bo con
    # song sot, tuc mot default xanh trong chinh dong cong in ra.
    ('suite_isolation', 'test_suite_isolation'),
    # AUDIT_SECURITY_AND_DATA.md, 4 CRITICAL. Bo nay TIEM payload that vao lop
    # truyen lenh (cmd.exe, PowerShell), vao HTTP, vao git — roi hoi payload co
    # duoc THUC THI khong. Mot ca chi doc ma nguon se van xanh vao ngay ai do
    # viet lai bang cu phap khac, nen phan quyet dinh phai la hanh vi.
    ('exec_safety', 'test_exec_safety'),
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

    for folder, name in EXTRA_SUITES:
        folder_path = os.path.join(os.path.dirname(TESTS_DIR), folder)
        if folder_path not in sys.path:
            sys.path.insert(0, folder_path)
        try:
            suites.append(__import__(name).run())
        except Exception as error:  # noqa: BLE001
            broken.append((name, '%s: %s' % (type(error).__name__, error)))

    code = harness.render(suites, missing=len(broken))

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
