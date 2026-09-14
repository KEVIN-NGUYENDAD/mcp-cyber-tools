#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DETECTION QUALITY (Sprint 12)

Bộ kiểm hồi quy cho hai thứ đã hỏng một lần và sẽ hỏng lại nếu không ai canh:

  1. Cuộc săn phát hiện chính bộ máy giám sát (dương tính giả tự sinh).
  2. Bằng chứng không chứa thứ gây ra kết luận (kết luận không kiểm chứng được).

Vì sao là một tệp test chứ không phải một lần sửa
--------------------------------------------------
Sprint 11.x sửa cả hai cho cuộc săn credential dumping. Nhưng cách chúng lọt vào
không có gì riêng của cuộc săn đó: bộ máy giám sát chạy trên chính máy nó giám
sát, nên nó luôn nằm trong dữ liệu nó đọc; và `message[:600]` trông vô hại ở mọi
chỗ nó được viết ra.

Lần sau một cuộc săn mới ra đời, nó sẽ viết lại đúng hai dòng đó. Bộ kiểm này
tồn tại để lần đó có người nói trước khi dữ liệu sai đi tới báo cáo.

Chạy:  python scripts/test_detection_quality.py    (hoặc npm run test:detection)
Thoát khác 0 nếu có ca nào trượt.
"""

from __future__ import print_function

import io
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import detection_quality as dq  # noqa: E402
import hunt_credential_dumping as hcd  # noqa: E402

RESULTS = []


def check(name, condition, detail=''):
    RESULTS.append((bool(condition), name, detail))
    return bool(condition)


# --------------------------------------------------------------------------
# 1. Nhận diện credential dumping: tấn công thật phải qua, nhiễu phải bị hạ cấp
# --------------------------------------------------------------------------

def event_4688(new_process, command_line):
    message = ('A new process has been created.\r\n\r\nProcess Information:\r\n'
               '\tNew Process Name:\t%s\r\n'
               '\tCreator Process Name:\tC:\\Windows\\explorer.exe\r\n'
               '\tProcess Command Line:\t%s' % (new_process, command_line))
    return {'TimeCreated': 'test', 'Id': 4688, 'Message': message}


def classify(event):
    """Trả về ('INDICATOR', severity, matched_field) / ('SELF', lý do) / ('NONE',)."""
    hunter = hcd.CredentialDumpingHunter()
    hunter.build_indicators([event])
    if hunter.indicators:
        indicator = hunter.indicators[0]
        return ('INDICATOR', indicator['severity'], indicator['matched_field'],
                indicator)
    if hunter.self_observed:
        return ('SELF', hunter.self_observed[0]['reason'], None, None)
    return ('NONE', None, None, None)


ATTACKS = [
    ('mimikatz chạy như một tiến trình',
     r'C:\tools\mimikatz.exe', r'"C:\tools\mimikatz.exe" sekurlsa::logonpasswords'),
    ('procdump đổ bộ nhớ lsass',
     r'C:\tools\procdump64.exe', r'procdump64.exe -ma lsass.exe out.dmp'),
    ('comsvcs.dll MiniDump',
     r'C:\Windows\System32\rundll32.exe',
     r'rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump 660 lsass.dmp full'),
    ('ntdsutil trích NTDS',
     r'C:\Windows\System32\ntdsutil.exe', r'ntdsutil.exe "ac i ntds" "ifm" q q'),
]

NOISE = [
    ('grep tìm chữ lsass trong mã nguồn',
     r'C:\Program Files\Git\usr\bin\grep.exe', r'"grep.exe" -n lsass scripts/x.py'),
    ('mở tài liệu có tên nhắc tới lsass',
     r'C:\Windows\notepad.exe', r'notepad.exe lsass-notes.txt'),
]

SELF = [
    ('gọi thẳng script săn',
     r'C:\Python\python.exe', r'python scripts/hunt_credential_dumping.py'),
    ('truyền chuỗi nhận dạng',
     r'C:\Python\python.exe', r"python -c \"re.compile('lsass|mimikatz|ntdsutil')\""),
    ('chạy pipeline',
     r'C:\Python\python.exe', r'python scripts/run_intelligence_pipeline.py'),
]


def test_detection():
    for label, process, command in ATTACKS:
        kind, severity, field, _ = classify(event_4688(process, command))
        check('TAN CONG van bat duoc: %s' % label,
              kind == 'INDICATOR' and severity in ('CRITICAL', 'HIGH'),
              'nhan duoc: %s %s' % (kind, severity))

    for label, process, command in NOISE:
        kind, severity, field, _ = classify(event_4688(process, command))
        # Nhiễu KHÔNG bị xoá — nó bị hạ cấp. Xoá hẳn thì một lệnh tấn công núp
        # trong tham số của lệnh khác cũng biến mất cùng.
        check('NHIEU bi ha cap, khong bi xoa: %s' % label,
              kind != 'INDICATOR' or severity not in ('CRITICAL', 'HIGH'),
              'nhan duoc: %s %s' % (kind, severity))

    for label, process, command in SELF:
        kind, reason, _, _ = classify(event_4688(process, command))
        check('TU QUAN SAT bi loai: %s' % label, kind == 'SELF',
              'nhan duoc: %s' % kind)

    kind, _, _, _ = classify(event_4688(r'C:\Windows\notepad.exe', 'notepad.exe a.txt'))
    check('Su kien khong lien quan khong sinh chi bao', kind == 'NONE',
          'nhan duoc: %s' % kind)


# --------------------------------------------------------------------------
# 2. Bằng chứng phải chứa trigger
# --------------------------------------------------------------------------

def test_evidence_excerpt():
    # Đúng hình dạng của Event 4688: trigger nằm ở CUỐI, ngoài 600 ký tự đầu.
    message = ('A new process has been created.\r\n' + ('x' * 900)
               + '\r\n\tProcess Command Line:\tmimikatz.exe sekurlsa')
    naive = message[:600]
    check('Bug cu tai hien duoc: message[:600] khong chua trigger',
          'mimikatz' not in naive)

    excerpt = dq.evidence_excerpt(message, 'mimikatz')
    check('evidence_excerpt luon chua trigger', 'mimikatz' in excerpt)
    check('evidence_excerpt khong vuot qua gioi han',
          len(excerpt) <= dq.EVIDENCE_WIDTH, 'len=%d' % len(excerpt))

    # Không có trigger thì vẫn phải trả về một đoạn dùng được, không được nổ.
    check('evidence_excerpt chiu duoc trigger rong',
          len(dq.evidence_excerpt(message, None)) > 0)
    check('evidence_excerpt chiu duoc trigger khong ton tai',
          len(dq.evidence_excerpt(message, 'khong-he-co')) > 0)


def test_verify_indicator():
    good = {
        'severity': 'CRITICAL',
        'matched_text': 'mimikatz',
        'evidence': ['... mimikatz.exe sekurlsa::logonpasswords ...'],
        'attribution': {'systems': [{'ip': '10.0.0.1', 'scope': 'LOCAL_HOST'}]},
    }
    check('Chi bao dat khong bi bao loi', dq.verify_indicator(good) == [],
          str(dq.verify_indicator(good)))

    missing = dict(good, evidence=['khong co gi o day'])
    check('Bat duoc trigger vang mat trong evidence',
          any('matched_text' in v for v in dq.verify_indicator(missing)))

    peer = {
        'severity': 'HIGH',
        'evidence': ['Logon from somewhere'],
        'attribution': {'systems': [
            {'ip': '192.168.1.50', 'scope': 'REMOTE_PEER'}]},
    }
    check('Bat duoc REMOTE_PEER vang mat trong evidence',
          any('remote_peer' in v for v in dq.verify_indicator(peer)))

    local_only = {
        'severity': 'INFO',
        'evidence': ['Local logon'],
        'attribution': {'systems': [
            {'ip': '192.168.1.50', 'scope': 'LOCAL_HOST'}]},
    }
    # Máy cục bộ được quy kết vì cuộc săn CHẠY ở đó, không phải vì tên nó nằm
    # trong thông điệp. Đòi nó có mặt trong evidence là đòi sai chỗ.
    check('LOCAL_HOST khong bi doi phai co trong evidence',
          dq.verify_indicator(local_only) == [],
          str(dq.verify_indicator(local_only)))

    no_attr = {'severity': 'CRITICAL', 'evidence': ['co gi do']}
    check('Bat duoc chi bao CRITICAL khong co attribution',
          any('attribution' in v for v in dq.verify_indicator(no_attr)))

    no_basis = {
        'severity': 'HIGH',
        'evidence': ['mot su kien nao do'],
        'attribution': {'systems': [{'ip': '10.0.0.1', 'scope': 'LOCAL_HOST'}]},
    }
    check('Bat duoc chi bao HIGH khong khai co so',
          any('severity_basis' in v for v in dq.verify_indicator(no_basis)))

    # Cơ sở là siêu dữ liệu (Event ID), không phải văn bản khớp được — nên nó
    # KHÔNG bị đòi phải có mặt trong evidence.
    metadata_basis = dict(no_basis, severity_basis='Event ID 4648 — Explicit Credential Logon')
    check('severity_basis dang sieu du lieu duoc chap nhan',
          dq.verify_indicator(metadata_basis) == [],
          str(dq.verify_indicator(metadata_basis)))

    empty = {'severity': 'INFO', 'evidence': [], 'attribution': {}}
    check('Bat duoc chi bao khong co evidence',
          any('evidence' in v for v in dq.verify_indicator(empty)))


def test_self_observation_helper():
    check('Nhan ra loi goi script giam sat',
          dq.is_self_observation('python scripts/hunt_lateral_movement.py') is not None)
    check('Nhan ra chuoi nhan dang noi bang |',
          dq.is_self_observation("grep -E 'lsass|mimikatz'") is not None)
    check('Khong bao nham lenh tan cong that',
          dq.is_self_observation('mimikatz.exe sekurlsa::logonpasswords') is None)
    check('Khong bao nham chuoi rong', dq.is_self_observation('') is None)


# --------------------------------------------------------------------------
# 3. Trạng thái thật trên máy này
# --------------------------------------------------------------------------

def test_live_state():
    report = dq.audit_state()
    check('state/hunting_*.json khong co vi pham nao',
          report['total_violations'] == 0,
          '%d vi pham tren %d chi bao'
          % (report['total_violations'], report['total_indicators']))


def main():
    test_detection()
    test_evidence_excerpt()
    test_verify_indicator()
    test_self_observation_helper()
    test_live_state()

    failed = [row for row in RESULTS if not row[0]]
    for ok, name, detail in RESULTS:
        print('%-5s %s%s' % ('OK' if ok else 'TRUOT', name,
                             ('  [%s]' % detail) if (detail and not ok) else ''))
    print('')
    print('%d/%d dat' % (len(RESULTS) - len(failed), len(RESULTS)))
    return 1 if failed else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
