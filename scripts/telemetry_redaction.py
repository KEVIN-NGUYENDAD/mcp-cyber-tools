# -*- coding: utf-8 -*-
"""Che thong tin ca nhan truoc khi tin nhan roi khoi may — nhanh Python.

Day la ban sao cua `scripts/telegram/redact.js`. Ton tai hai ban vi co HAI duong
gui Telegram doc lap: bot Node (`telegramBot.js`) va cac script Python
(`send_daily_brief_telegram.py`, `auto_investigation_playbook.py`) goi thang
api.telegram.org. Che mot ben thi ben kia van ro.

Hai bo che khac nhau thi te hon mot bo, nen quy tac o day duoc giu TRUNG TEN va
TRUNG KET QUA voi ban JS, va `tests/telegram_truth/test_redaction_parity.py`
kiem chinh dieu do bang cach chay ca hai tren cung mot tap dau vao.

Nguyen tac (giong ban JS): che DANH TINH, giu CAU TRUC.

  C:\\Users\\tamng\\Downloads\\hoadon.exe -> C:\\Users\\<USER>\\Downloads\\hoadon.exe

chu khong phai `[WINDOWS_PATH]`. Thu muc Downloads la mot phan cua ket luan phap
chung: mot nhi phan chay tu Downloads khac han mot nhi phan chay tu System32.

Vi cung ly do, IP KHONG bi che. Ban dau tien cua tep nay che ca IP, ca duong dan
va ca ten may — tuc la bien mot canh bao lateral movement thanh mot tin nhan
rong. An toan, va vo dung.
"""

from __future__ import print_function

import getpass
import os
import re

SYSTEM_ACCOUNTS = ('SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE',
                   'ANONYMOUS LOGON', '-')


def _local_identities():
    """Ten dang nhap that cua may nay.

    Day la quy tac manh nhat trong tep: khi biet ten that la `tamng`, ta che duoc
    ca nhung cho no xuat hien TRAN TRUI (`Account Name: tamng`, `Welcome tamng`)
    chu khong chi trong duong dan.
    """
    names = set()
    candidates = [os.environ.get('USERNAME'), os.environ.get('USER')]
    try:
        candidates.append(getpass.getuser())
    except Exception:  # noqa: BLE001 — khong co ten dang nhap thi bo qua
        pass
    for raw in candidates:
        name = (raw or '').strip()
        # Ten qua ngan sinh ra thay the bua bai giua cac tu khac.
        if len(name) >= 3:
            names.add(name.lower())
    return sorted(names)


def _mask_account(match):
    label, value = match.group(1), match.group(2)
    name = value.strip()
    # Tai khoan may (`KEVIN$`) va tai khoan he thong khong phai danh tinh ca
    # nhan, va chung la manh moi phan biet dang nhap nen voi dang nhap nguoi
    # dung — giu nguyen.
    if name.endswith('$') or name.upper() in SYSTEM_ACCOUNTS:
        return match.group(0)
    return '%s<USER>' % label


RULES = [
    # Duong dan ho so nguoi dung — giu lai phan duoi, chi thay ten.
    ('windows_user_path',
     re.compile(r'([A-Za-z]:\\Users\\)([^\\/\s"\'<>|]+)', re.IGNORECASE),
     lambda m: '%s<USER>' % m.group(1)),
    ('unix_home_path',
     re.compile(r'(/(?:home|Users)/)([^/\s"\'<>|]+)'),
     lambda m: '%s<USER>' % m.group(1)),
    # Mat khau / token / khoa API: che GIA TRI, giu TEN TRUONG, de nguoi doc biet
    # o day co mot bi mat bi lo chu khong phai mot dong bien mat.
    ('secret_assignment',
     re.compile(r'\b(pass(?:word|wd)?|pwd|secret|token|api[_-]?key|apikey'
                r'|client[_-]?secret|bearer)\b(\s*[=:]\s*|\s+)'
                r'("[^"]*"|\'[^\']*\'|[^\s,;"\')]+)', re.IGNORECASE),
     lambda m: '%s%s<REDACTED>' % (m.group(1), m.group(2))),
    ('email',
     re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
     lambda m: '<EMAIL>'),
    # Chuoi base64 cua PowerShell -enc giu lai DO DAI: do dai la tin hieu san
    # tim, noi dung la thu co the chua thong tin dang nhap.
    #
    # `\b` truoc dau `-` KHONG BAO GIO khop (dau cach va `-` deu khong phai ky
    # tu tu), va thu tu nhanh phai dai truoc ngan, neu khong `-e` se nuot mat
    # `-enc`. Ca hai loi nay tung lam quy tac chet lang trong ban JS.
    ('powershell_encoded',
     re.compile(r'(^|\s)(-encodedcommand|-enc|-en|-e)\s+([A-Za-z0-9+/=]{40,})',
                re.IGNORECASE),
     lambda m: '%s%s <ENCODED:%dchars>' % (m.group(1), m.group(2), len(m.group(3)))),
    # Tai khoan Windows trong nhat ky su kien.
    ('event_account_name',
     re.compile(r'(Account Name:\s*)([^\r\n\t]+)'),
     _mask_account),
]

IDENTITY_RULES = [
    ('local_identity:%s' % name,
     re.compile(r'(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])' % re.escape(name),
                re.IGNORECASE),
     lambda m: '<USER>')
    for name in _local_identities()
]


def redact(text):
    """Che thong tin ca nhan trong mot chuoi."""
    if not isinstance(text, str) or not text:
        return text
    output = text
    for _name, pattern, replace in RULES:
        output = pattern.sub(replace, output)
    # Chay sau cung: luc nay duong dan da thanh `<USER>`, nen quy tac nay chi con
    # gap ten tran trui thuc su.
    for _name, pattern, replace in IDENTITY_RULES:
        output = pattern.sub(replace, output)
    return output


def redact_deep(value):
    """Che de quy trong dict/list. Khong sua ban goc."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_deep(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_deep(item) for item in value)
    if isinstance(value, dict):
        return dict((key, redact_deep(val)) for key, val in value.items())
    return value


if __name__ == '__main__':
    samples = [
        r'C:\Users\tamng\Downloads\hoadon.exe',
        r'C:\Windows\System32\cmd.exe',
        'Ket noi toi 192.168.1.50 tu 10.0.0.7',
        'password=SieuMatKhau123!',
        'lien he admin@congty.vn',
        'powershell.exe -enc ' + 'S' * 64,
        'Account Name:\t\tKEVIN$',
    ]
    for sample in samples:
        print('%-60s -> %s' % (sample, redact(sample)))
