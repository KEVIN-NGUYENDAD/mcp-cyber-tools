# -*- coding: utf-8 -*-
"""Hai bo che phai cho ra CUNG mot ket qua, va moi duong gui phai di qua mot bo.

Co hai duong gui Telegram doc lap:
  - bot Node    -> scripts/telegram/redact.js
  - script Python -> scripts/telemetry_redaction.py

Hai ban sao khong duoc kiem chung nhau se troi khoi nhau: mot ben sua quy tac,
ben kia khong, va tu do co mot duong ro ma khong ai nhin. Nen bo kiem nay chay
CA HAI tren cung mot tap dau vao va doi tung ky tu bang nhau.

Phan thu hai kiem theo HANH VI chu khong doc ma nguon: goi that ham gui, chan
`requests.post`, roi doc payload thuc su di ra day. Mot ca chi grep chu `redact(`
se van xanh vao ngay ai do them mot cho gui thu ba.
"""

from __future__ import print_function

import json
import os
import subprocess
import sys

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(TESTS_DIR, 'detection_quality'))
from harness import Suite, PROJECT_ROOT  # noqa: E402

TEST_USERNAME = 'tamng'

# Dau vao lay tu du lieu that: duong dan RunKey trong hunting_persistence.json,
# nhat ky su kien 4688, va cac hinh dang bi mat thuong gap.
SAMPLES = [
    r'C:\Users\tamng\Downloads\hoadon.exe',
    r'"C:\Users\tamng\AppData\Local\Programs\Zalo\Zalo.exe"',
    r'C:\Windows\System32\cmd.exe',
    '/home/tamng/.ssh/id_rsa',
    'Ket noi toi 192.168.1.50 tu 10.0.0.7',
    'password=SieuMatKhau123!',
    'api_key: abcdef1234567890',
    'token = "Bearer xyz"',
    'lien he admin@congty.vn ngay',
    'powershell.exe -enc ' + 'S' * 64,
    'powershell -EncodedCommand ' + 'QQ' * 40,
    'Account Name:\t\ttamng',
    'Account Name:\t\tKEVIN$',
    'Account Name:\t\tSYSTEM',
    'Welcome back tamng',
    'tamnghiep la mot tu khac',
    'CRITICAL: svchost.exe tai C:\\Users\\tamng\\AppData\\Local\\Temp\\a.exe',
    '',
]

# Dau vao di qua STDIN, khong qua tham so dong lenh. Tren Windows, tham so co
# dau nhay va dau `\` bi lop dong lenh vien lai truoc khi node nhin thay — dung
# tham so thi tep nay se im lang tra ve chuoi rong.
NODE_BRIDGE = r'''
process.env.USERNAME = process.env.PARITY_USERNAME;
const { redact } = await import('./scripts/telegram/redact.js');
let raw = '';
process.stdin.setEncoding('utf8');
for await (const chunk of process.stdin) raw += chunk;
process.stdout.write(JSON.stringify(JSON.parse(raw).map(redact)));
'''


def node_redact(samples):
    """Chay redact.js tren cung tap dau vao. Tra ve (ket_qua, loi)."""
    env = dict(os.environ)
    env['PARITY_USERNAME'] = TEST_USERNAME
    try:
        process = subprocess.Popen(
            ['node', '--input-type=module', '-e', NODE_BRIDGE],
            cwd=PROJECT_ROOT, env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate(json.dumps(samples).encode('utf-8'))
    except OSError as error:
        return None, '%s: %s' % (type(error).__name__, error)
    if process.returncode != 0:
        return None, err.decode('utf-8', 'replace')[:200]
    try:
        return json.loads(out.decode('utf-8')), None
    except ValueError as error:
        return None, 'khong doc duoc JSON, stderr=%s' % err.decode('utf-8', 'replace')[:150]


def check_parity(suite):
    os.environ['USERNAME'] = TEST_USERNAME
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
    import telemetry_redaction
    # Module doc ten dang nhap luc nap; nap lai de an theo USERNAME vua dat.
    try:
        import importlib
        importlib.reload(telemetry_redaction)
    except Exception:  # noqa: BLE001 — Python 2 style fallback khong can thiet
        pass

    js_results, error = node_redact(SAMPLES)
    if error is not None:
        suite.check('redact.js chay duoc de doi chieu', False, error)
        return

    for index, sample in enumerate(SAMPLES):
        py = telemetry_redaction.redact(sample)
        js = js_results[index]
        label = 'khop JS/Python: %s' % (sample[:46] or '(chuoi rong)')
        suite.check(label, py == js, 'py=%r js=%r' % (py, js))


def check_python_senders(suite):
    """Payload THUC SU di ra day phai da duoc che."""
    scripts_dir = os.path.join(PROJECT_ROOT, 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    leaky = r'Tien trinh la: C:\Users\tamng\AppData\Local\Temp\x.exe, mail admin@congty.vn'

    captured = []

    class FakeResponse(object):
        status_code = 200

        @staticmethod
        def json():
            return {'ok': True, 'result': {'message_id': 1}}

    def fake_post(url, json=None, timeout=None, **kwargs):  # noqa: A002
        captured.append(json)
        return FakeResponse()

    # --- send_daily_brief_telegram ---
    try:
        import send_daily_brief_telegram as brief
        original = brief.requests.post
        brief.requests.post = fake_post
        try:
            brief.send_via_telegram(leaky, 'token-gia', 'chat-gia')
        finally:
            brief.requests.post = original
        sent = captured[-1]['text'] if captured else ''
        suite.check('daily brief: ten nguoi dung khong ra khoi may',
                    'tamng' not in sent, 'da gui: %r' % sent[:120])
        suite.check('daily brief: email bi che', '<EMAIL>' in sent,
                    'da gui: %r' % sent[:120])
        suite.check('daily brief: thu muc Temp con lai (giu cau truc)',
                    'Temp' in sent, 'da gui: %r' % sent[:120])
    except Exception as error:  # noqa: BLE001
        suite.check('daily brief: goi duoc ham gui', False,
                    '%s: %s' % (type(error).__name__, error))

    # --- auto_investigation_playbook ---
    try:
        import auto_investigation_playbook as playbook
        source = open(os.path.join(scripts_dir, 'auto_investigation_playbook.py'),
                      'r', encoding='utf-8').read()
        # Ham gui o day nhan nhieu tham so ngu canh (dedup, project_root) nen
        # goi truc tiep se keo theo ca lop trang thai. Doi tuong can kiem chi la
        # mot dieu: payload duoc dung tu `redact(message)`, khong phai `message`.
        suite.check('playbook: payload dung redact(message)',
                    "'text': redact(message)" in source,
                    'khong thay trong nguon')
        suite.check('playbook: co nap bo che',
                    'from telemetry_redaction import redact' in source)
        suite.check('playbook: khong con cho nao gui chuoi tho',
                    "'text': message" not in source,
                    'van con mot payload chua che')
    except Exception as error:  # noqa: BLE001
        suite.check('playbook: doc duoc nguon', False,
                    '%s: %s' % (type(error).__name__, error))


def run():
    suite = Suite('che danh tinh: hai nhanh gui phai trung nhau')
    check_parity(suite)
    check_python_senders(suite)
    return suite


if __name__ == '__main__':
    import harness
    sys.exit(harness.render([run()]))
