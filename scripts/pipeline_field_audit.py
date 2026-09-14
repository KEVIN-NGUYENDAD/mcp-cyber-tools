#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE FIELD AUDIT (Sprint B)

Cùng một câu hỏi như `portal_field_audit.py` và `telegram_field_audit.py`, hỏi
cho lớp cuối cùng chưa ai soi: **Python**.

    Mỗi trường mà pipeline ĐỌC có thật sự tồn tại trong tệp state nó đọc từ đó
    không? Và khi không tồn tại, chuyện gì xảy ra?

Vì sao lớp này là lớp nguy hiểm nhất trong ba lớp
--------------------------------------------------
Portal và Telegram *hiển thị* số. Python *tính* ra chúng. Một trường đọc sai ở
lớp hiển thị làm hỏng một ô; một trường đọc sai ở lớp tính toán làm hỏng con số
rồi con số đó đi tiếp vào portal, Telegram, báo cáo, và bảng nợ kỹ thuật — tất
cả cùng hiển thị đúng một giá trị sai, nhất quán, và vì thế thuyết phục.

Chuyện đã xảy ra đúng như vậy:

    calculate_risk_score.py:115   score = waap.get('score', 50)
    state/waap_score.json         -> không có khoá `score`; tên thật là `health_score`

`calculate_waap_score.py` đổi tên khoá, consumer không đổi theo, và `50` nhận lấy
chỗ trống. Điểm thật là 80. Suốt nhiều sprint, **38% điểm rủi ro là một hằng số
fallback đeo nhãn số đo** — và merge gate xanh toàn tập, vì cả hai bộ audit hiện
có đều chỉ soi JavaScript.

Vì sao đích ngắm là `.get(key, default)` chứ không phải `.get(key)`
-------------------------------------------------------------------
`data.get('x')` thiếu khoá thì trả `None`, và `None` thường làm vỡ thứ gì đó ở
ngay dòng sau — một lỗi ồn ào, được sửa trong vòng một phút.

`data.get('x', 50)` thiếu khoá thì trả `50`, và `50` trông y hệt một phép đo. Nó
không bao giờ vỡ. Nó chỉ sai, im lặng, mãi mãi.

Cho nên bộ này báo động đúng ở chỗ có giá trị mặc định, và chỉ khi khoá đó thật
sự không có trong tệp state tương ứng.
"""

from __future__ import print_function

import ast
import io
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')

# Bốn tệp được chỉ đích danh, cộng những tệp cùng lớp: chúng đều tính ra con số
# mà người khác đọc.
FILES = [
    'calculate_risk_score.py',
    'generate_priority_queue.py',
    'correlation_engine.py',
    'daily_brief_generator.py',
    'generate_daily_brief.py',
    'generate_incidents.py',
    'calculate_waap_score.py',
    'asset_builder.py',
    'ioc_quality.py',
]

# Khoá được phép thiếu: chúng là bộ đếm hoặc danh sách mà "không có" và "bằng 0"
# thật sự cùng nghĩa. Danh sách này phải NGẮN và mỗi mục phải tự biện minh được.
BENIGN_DEFAULTS = {
    # Đếm: không có mục nào và đếm được 0 mục là một.
    'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO',
    'critical', 'high', 'medium', 'low', 'info',
    'count', 'total', 'threat_count', 'quarantined_count',
    'vulnerability_count', 'failed_logons', 'critical_events',
    'warning_events', 'mac_changes', 'observations',
}


class StateBinding(ast.NodeVisitor):
    """Biến nào đang giữ nội dung của tệp state nào."""

    LOADERS = ('load_state', 'read_state_safe', 'read_json', '_read_json')

    def __init__(self):
        self.bindings = {}     # tên biến -> tên tệp state
        self.gets = []         # (biến, khoá, có_default, dòng)

    # -- nhận diện phép gán từ một loader --------------------------------
    def visit_Assign(self, node):
        filename = self._state_file(node.value)
        if filename:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.bindings[target.id] = filename
        self.generic_visit(node)

    def _state_file(self, value):
        if not isinstance(value, ast.Call):
            return None
        name = None
        if isinstance(value.func, ast.Attribute):
            name = value.func.attr
        elif isinstance(value.func, ast.Name):
            name = value.func.id
        if name not in self.LOADERS:
            return None
        for arg in list(value.args) + [k.value for k in value.keywords]:
            found = self._string_json(arg)
            if found:
                return found
        return None

    @staticmethod
    def _string_json(node):
        """Chuỗi `*.json` xuất hiện ở đâu đó trong biểu thức đối số."""
        for child in ast.walk(node):
            if isinstance(child, ast.Str) and child.s.endswith('.json'):
                return child.s
            # Python 3.8+ dùng ast.Constant
            if isinstance(child, ast.Constant) and isinstance(child.value, str) \
                    and child.value.endswith('.json'):
                return child.value
        return None

    # -- nhận diện `X.get('key', default)` --------------------------------
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get' \
                and isinstance(node.func.value, ast.Name) and node.args:
            key = self._literal(node.args[0])
            if key is not None:
                self.gets.append((node.func.value.id, key,
                                  len(node.args) > 1, node.lineno))
        self.generic_visit(node)

    @staticmethod
    def _literal(node):
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


def load_state(filename):
    path = os.path.join(STATE_DIR, filename)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle), None
    except (ValueError, IOError, OSError) as error:
        return None, str(error)[:90]


def audit_file(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(path):
        return [{'level': 'UNKNOWN', 'file': filename, 'line': 0,
                 'state': '-', 'field': '-', 'detail': 'không có tệp này'}]

    with io.open(path, encoding='utf-8') as handle:
        source = handle.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [{'level': 'UNKNOWN', 'file': filename, 'line': 0,
                 'state': '-', 'field': '-',
                 'detail': 'không phân tích được: %s' % error}]

    visitor = StateBinding()
    visitor.visit(tree)

    findings = []
    seen = set()
    for variable, key, has_default, line in visitor.gets:
        state_file = visitor.bindings.get(variable)
        if not state_file:
            continue
        signature = (filename, state_file, key)
        if signature in seen:
            continue
        seen.add(signature)

        data, error = load_state(state_file)
        if data is None:
            findings.append({'level': 'UNKNOWN', 'file': filename, 'line': line,
                             'state': state_file, 'field': '%s.%s' % (variable, key),
                             'detail': 'không đọc được state: %s' % error})
            continue
        if not isinstance(data, dict):
            continue

        if key in data:
            findings.append({'level': 'OK', 'file': filename, 'line': line,
                             'state': state_file,
                             'field': '%s.%s' % (variable, key), 'detail': ''})
        elif has_default and key not in BENIGN_DEFAULTS:
            # Đây là lớp lỗi đang săn: khoá không tồn tại, và một giá trị mặc
            # định đang thế chỗ nó mà không ai biết.
            findings.append({'level': 'FABRICATED', 'file': filename, 'line': line,
                             'state': state_file,
                             'field': '%s.%s' % (variable, key),
                             'detail': 'tệp có: %s'
                                       % ', '.join(sorted(data.keys())[:8])})
        else:
            findings.append({'level': 'MISSING', 'file': filename, 'line': line,
                             'state': state_file,
                             'field': '%s.%s' % (variable, key),
                             'detail': 'khoá không tồn tại (không có giá trị '
                                       'mặc định — sẽ ra None)'})
    return findings


def coverage(filename):
    """Bao nhiêu lời gọi `.get(key, default)` trong tệp này, tổng cộng.

    Bộ audit chỉ lần được những biến gán TRỰC TIẾP từ một loader. Nhiều chỗ đọc
    state qua `self.state[...]`, qua tham số hàm, hoặc qua một lớp bọc — bộ này
    không thấy. Con số đó phải in ra cạnh số đã kiểm.

    Sprint 17 vừa dạy đúng bài này: `telegram_field_audit` lặng lẽ tụt từ 18
    xuống 16 truy cập vì cửa sổ quét không còn với tới cuối handler, và bộ kiểm
    vẫn xanh vì nó chỉ đòi `>= 10`. Một bộ audit không khai phạm vi của chính nó
    thì con số nó in ra đọc như "đã kiểm hết".
    """
    path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(path):
        return 0
    with io.open(path, encoding='utf-8') as handle:
        try:
            tree = ast.parse(handle.read())
        except SyntaxError:
            return 0
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)                 and node.func.attr == 'get' and len(node.args) > 1:
            total += 1
    return total


def audit():
    findings = []
    for filename in FILES:
        findings.extend(audit_file(filename))
    return findings


def main():
    findings = audit()
    fabricated = [f for f in findings if f['level'] == 'FABRICATED']
    missing = [f for f in findings if f['level'] == 'MISSING']
    unknown = [f for f in findings if f['level'] == 'UNKNOWN']
    ok = [f for f in findings if f['level'] == 'OK']

    if fabricated:
        print('SO LIEU GIA — khoa khong ton tai, gia tri mac dinh thay cho (%d):'
              % len(fabricated))
        for finding in fabricated:
            print('  %s:%-5d %s' % (finding['file'], finding['line'],
                                    finding['field']))
            print('        %s -> %s' % (finding['state'], finding['detail'][:110]))
    if missing:
        print('')
        print('KHOA KHONG TON TAI, khong co mac dinh (%d):' % len(missing))
        for finding in missing[:12]:
            print('  %s:%-5d %-34s %s' % (finding['file'], finding['line'],
                                          finding['field'], finding['state']))
    if unknown:
        print('')
        print('KHONG KIEM DUOC (%d):' % len(unknown))
        for finding in unknown[:12]:
            print('  %s:%-5d %-30s %s' % (finding['file'], finding['line'],
                                          finding['field'],
                                          finding['detail'][:60]))

    total_gets = sum(coverage(name) for name in FILES)
    traced = len(findings)
    print('')
    print('TONG: %d truy cap | %d dung | %d so lieu gia | %d thieu khoa | '
          '%d khong kiem duoc'
          % (traced, len(ok), len(fabricated), len(missing), len(unknown)))
    print('PHAM VI: lan duoc %d / %d loi goi `.get(key, default)` trong %d tep. '
          '%d loi goi con lai doc state qua duong khac (self.state[...], tham so '
          'ham, lop boc) va bo audit nay KHONG thay.'
          % (traced, total_gets, len(FILES), max(0, total_gets - traced)))
    return 1 if fabricated else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
