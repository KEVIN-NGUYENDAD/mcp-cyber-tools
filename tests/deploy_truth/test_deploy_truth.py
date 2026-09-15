# -*- coding: utf-8 -*-
"""
Deploy truth + brief HTML trong pipeline (AQ-030 / AQ-007).

Sáu vòng audit liên tiếp ghi cùng một điều: `render.yaml` khởi động
`node web-server.js`, `package.json` khai `web/server.js` -- hai điểm vào,
không ai đối chiếu. Mọi công portal (86/86 XSS đã sửa, riskView(), lọc
suppressed) nằm trong tệp mà Render không chạy. Nửa thứ hai: `/latest` chỉ
được `send_daily_brief_telegram.py` ghi -- một script NGOÀI pipeline -- nên
mỗi lần Telegram không chạy (thiếu token, không mạng), `/latest` phục vụ bản
HTML cũ mà không có gì trên trang nói rằng nó cũ.

Cả hai đã được sửa (deploy_truth_audit.py đối chiếu điểm vào + route; AQ-042
gọi save_html_brief() thẳng từ generate_daily_brief.py, đồng bộ với JSON,
không chờ Telegram). Fixture này khoá lại: (a) cấu hình THẬT của repo không
còn lệch; (b) bộ dò audit vẫn nhận ra lệch khi có -- tái tạo đúng lỗi gốc
trên một cấu hình tổng hợp; (c) bản HTML được sinh CÙNG một lần gọi với JSON,
không phụ thuộc Telegram có chạy hay không.
"""
from __future__ import print_function

import io
import os
import sys
import shutil
import tempfile
import types

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import deploy_truth_audit as dta  # noqa: E402
import generate_daily_brief as gdb  # noqa: E402


def run():
    suite = Suite('deploy truth + brief HTML trong pipeline (AQ-030/AQ-007)')

    # -- 1. Cau hinh THAT cua repo khong con lech --------------------------
    findings, scope = dta.audit()
    suite.check('render.yaml va package.json khai CUNG mot diem vao',
                not any(f['level'] == 'ENTRYPOINT_MISMATCH' for f in findings),
                str(findings))
    suite.check("Diem vao la web/server.js, khong con la 'web-server.js'",
                scope['entrypoint'] == 'web/server.js', str(scope))
    suite.check('Moi route render.yaml cong bo deu co handler trong tep se chay',
                not any(f['level'] == 'ROUTE_UNSERVED' for f in findings),
                str(findings))
    suite.check('audit() tren cau hinh that: 0 vi pham',
                findings == [], str(findings))

    # -- 2. Bo do van nhan ra lech khi CO lech (tai tao dung loi goc) ------
    # AQ-048. Thu muc tam, khong phai `TESTS_DIR/_fixture` co dinh: mot thu muc
    # dung chung qua cac lan chay la mot duong lay nhiem giua cac lan chay.
    tmp_dir = tempfile.mkdtemp(prefix='deploy_truth_')
    tmp_render = os.path.join(tmp_dir, 'render.yaml')
    tmp_package = os.path.join(tmp_dir, 'package.json')

    old_render_path, old_package_path = dta.RENDER_YAML, dta.PACKAGE_JSON
    try:
        # Dung dung tinh huong AQ-030/AQ-007: render.yaml goi thang mot tep
        # khac voi tep package.json khai la "start".
        with io.open(tmp_render, 'w', encoding='utf-8') as handle:
            handle.write('services:\n  - type: web\n'
                         '    startCommand: node web-server.js\n')
        with io.open(tmp_package, 'w', encoding='utf-8') as handle:
            handle.write('{"scripts": {"start": "node web/server.js"}}')

        dta.RENDER_YAML, dta.PACKAGE_JSON = tmp_render, tmp_package
        mismatch_findings, mismatch_scope = dta.audit()
        suite.check('Cau hinh tong hop LECH -> ENTRYPOINT_MISMATCH bi bat',
                    any(f['level'] == 'ENTRYPOINT_MISMATCH'
                        for f in mismatch_findings),
                    str(mismatch_findings))

        # Sua lai khop -> het vi pham, chung minh bo do phan biet duoc hai
        # tinh huong chu khong phai luon bao loi.
        with io.open(tmp_render, 'w', encoding='utf-8') as handle:
            handle.write('services:\n  - type: web\n'
                         '    startCommand: npm start\n')
        matched_findings, _ = dta.audit()
        suite.check('  -> sua khop lai -> het ENTRYPOINT_MISMATCH',
                    not any(f['level'] == 'ENTRYPOINT_MISMATCH'
                            for f in matched_findings),
                    str(matched_findings))
    finally:
        dta.RENDER_YAML, dta.PACKAGE_JSON = old_render_path, old_package_path
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # -- 3. Ban HTML sinh CUNG luc voi JSON, khong cho Telegram ------------
    calls = []

    def _fake_save_html_brief(brief, date):
        calls.append((brief, date))
        return True

    fake_module = types.ModuleType('send_daily_brief_telegram')
    fake_module.save_html_brief = _fake_save_html_brief
    old_module = sys.modules.get('send_daily_brief_telegram')
    sys.modules['send_daily_brief_telegram'] = fake_module
    try:
        result = gdb.write_html_brief({'date': '2026-09-14'}, '2026-09-14')
        suite.check('write_html_brief() goi thang save_html_brief() cua bo render '
                    'co san, khong tu viet lai',
                    len(calls) == 1, str(calls))
        suite.check('  -> voi dung brief va ngay vua sinh',
                    calls and calls[0] == ({'date': '2026-09-14'}, '2026-09-14'),
                    str(calls))
        suite.check('  -> va bao thanh cong khi bo render thanh cong',
                    result is True, str(result))
    finally:
        if old_module is not None:
            sys.modules['send_daily_brief_telegram'] = old_module
        else:
            sys.modules.pop('send_daily_brief_telegram', None)

    # write_html_brief() phai bi loi ro rang khi bo render loi, khong nuot
    # loi thanh "thanh cong" gia.
    def _failing_save_html_brief(brief, date):
        return False

    fake_module.save_html_brief = _failing_save_html_brief
    sys.modules['send_daily_brief_telegram'] = fake_module
    try:
        failed_result = gdb.write_html_brief({'date': '2026-09-14'}, '2026-09-14')
        suite.check('Bo render loi -> write_html_brief() bao False, khong bia thanh cong',
                    failed_result is False, str(failed_result))
    finally:
        if old_module is not None:
            sys.modules['send_daily_brief_telegram'] = old_module
        else:
            sys.modules.pop('send_daily_brief_telegram', None)

    # -- 4. main(): goi write_html_brief() NGAY sau khi luu JSON, khong co
    #    dieu kien nao ve Telegram/credentials dung giua hai buoc do -------
    with io.open(os.path.join(PROJECT_ROOT, 'scripts', 'generate_daily_brief.py'),
                 encoding='utf-8') as handle:
        source = handle.read()
    main_body = source[source.index('\ndef main('):]
    save_at = main_body.index('generator.save_brief(brief)')
    html_at = main_body.index('write_html_brief(')
    between = main_body[save_at:html_at]
    # Chi tim NHANH RE KIEN (if/else) giua hai loi goi -- binh luan noi ve
    # Telegram la binh luan GIAI THICH vi sao KHONG cho no, khong phai mot
    # nhanh dieu kien thuc su. Mot nhanh `if` giua hai loi goi moi la dau
    # hieu cho thay write_html_brief() bi gan dieu kien tro lai.
    code_lines = [line for line in between.splitlines()
                 if line.strip() and not line.strip().startswith('#')]
    suite.check('main(): write_html_brief() dung NGAY sau save_brief(), khong '
                'co nhanh if/else xen giua',
                html_at > save_at
                and not any(line.strip().startswith(('if ', 'elif ', 'else'))
                            for line in code_lines),
                between[:200])

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
