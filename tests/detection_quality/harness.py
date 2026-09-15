# -*- coding: utf-8 -*-
"""
Khung kiểm tối thiểu cho bộ test chất lượng phát hiện.

Vì sao không dùng pytest: repo này chạy trên Python 3.7 của Windows Store, không
có môi trường ảo, và bộ kiểm phải chạy được ngay sau `git clone` mà không cài
thêm gì. Một cổng chặn đòi cài đặt trước là một cổng chặn sẽ bị bỏ qua.
"""

from __future__ import print_function

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

for path in (SCRIPTS_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


class Suite(object):
    """Một nhóm ca kiểm. Giữ kết quả, không tự in, không tự thoát."""

    def __init__(self, name):
        self.name = name
        self.results = []

    def check(self, label, condition, detail=''):
        ok = bool(condition)
        self.results.append({'ok': ok, 'label': label, 'detail': detail})
        return ok

    def check_equal(self, label, actual, expected):
        return self.check(label, actual == expected,
                          'nhan %r, cho doi %r' % (actual, expected))

    @property
    def failed(self):
        return [row for row in self.results if not row['ok']]

    @property
    def passed(self):
        return [row for row in self.results if row['ok']]


def event_4688(new_process, command_line, creator=r'C:\Windows\explorer.exe'):
    """Một Event 4688 đúng hình dạng thật: dòng lệnh nằm CUỐI thông điệp.

    Thứ tự này không phải chi tiết vụn vặt — nó chính là lý do `message[:600]`
    từng cắt mất mọi trigger thật.
    """
    message = ('A new process has been created.\r\n\r\n'
               'Creator Subject:\r\n\tAccount Name:\t\ttamng\r\n\r\n'
               'Process Information:\r\n'
               '\tNew Process Name:\t%s\r\n'
               '\tCreator Process Name:\t%s\r\n'
               '\tProcess Command Line:\t%s' % (new_process, creator, command_line))
    return {'TimeCreated': 'test', 'Id': 4688, 'Message': message}


def logon_event(event_id, source_ip=None, process=None):
    """Sự kiện đăng nhập, địa chỉ mạng nằm cuối như log thật."""
    message = ('An account was successfully logged on.\r\n\r\n'
               'Subject:\r\n\tAccount Name:\t\tKEVIN$\r\n\r\n'
               'Logon Information:\r\n\tLogon Type:\t\t3\r\n\r\n'
               'Process Information:\r\n\tProcess Name:\t\t%s\r\n\r\n'
               'Network Information:\r\n\tSource Network Address:\t%s'
               % (process or r'C:\Windows\System32\lsass.exe', source_ip or '-'))
    return {'TimeCreated': 'test', 'Id': event_id, 'Message': message,
            '_tool': 'huntLateralMovement'}


def render(suites, missing=0):
    """In kết quả và trả về mã thoát. 0 nếu mọi ca đều đạt.

    AQ-048. `missing` là số bộ kiểm KHÔNG CHẠY ĐƯỢC. Nó phải đi vào chính dòng
    `TONG:` chứ không chỉ vào mã thoát, vì đó là dòng duy nhất cổng trích ra và
    in lên màn hình. Khi một bộ vỡ, dòng cũ in `TONG: 443/443 dat` — đọc y hệt
    một lần chạy sạch — đứng cạnh chữ `TRƯỢT`, và 29 ca chưa từng chạy không
    xuất hiện ở đâu. Mẫu số tự co lại theo số bộ còn chạy được là một default
    xanh: nó luôn khớp tử số.
    """
    total = failed = 0
    for suite in suites:
        total += len(suite.results)
        failed += len(suite.failed)
        print('')
        print('== %s  (%d/%d)' % (suite.name, len(suite.passed), len(suite.results)))
        for row in suite.results:
            mark = 'OK   ' if row['ok'] else 'TRUOT'
            suffix = ('  [%s]' % row['detail']) if (row['detail'] and not row['ok']) else ''
            print('  %s %s%s' % (mark, row['label'], suffix))
    print('')
    if missing:
        print('TONG: %d/%d dat, %d BO KIEM KHONG CHAY DUOC (mau so thieu)'
              % (total - failed, total, missing))
    else:
        print('TONG: %d/%d dat' % (total - failed, total))
    return 1 if (failed or missing) else 0
