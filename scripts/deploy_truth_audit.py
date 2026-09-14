# -*- coding: utf-8 -*-
"""
DEPLOY TRUTH AUDIT (AQ-007 / AQ-030) — bản được kiểm và bản được phục vụ phải
là một.

Lỗi mà bộ này tồn tại để chặn
------------------------------
Sáu vòng audit liên tiếp ghi cùng một điều và không vòng nào sửa:

    render.yaml   startCommand : node web-server.js
    package.json  "start"      : node web/server.js

Hai tệp, hai điểm vào, không ai đối chiếu. `web-server.js` chỉ phục vụ
`daily_brief/`; nó không biết tới `web/app.js`. Nên toàn bộ công portal của bốn
sprint — `portal_escape_audit` 86/86, `riskView()`, lọc `suppressed`, xoá năm
bản sao công thức WAAP — nằm trong một tệp mà Render không chạy.

Điều đáng chú ý: **mọi bộ audit đều xanh trong suốt sáu vòng đó.**
`portal_field_audit` soi `web/app.js`. `portal_escape_audit` soi `web/app.js`.
Cả hai soi đúng tệp, và cả hai đều đúng — chỉ là tệp đó không phải tệp người
dùng mở. Một bộ kiểm chất lượng của artifact không phát hiện được rằng artifact
ấy không được triển khai; câu hỏi "cái gì đang chạy" nằm ngoài mọi câu hỏi
"cái này có đúng không".

Nên bộ này không kiểm nội dung. Nó kiểm **danh tính**: tệp mà các bộ khác soi có
đúng là tệp mà cấu hình triển khai khởi động không.

Vì sao không parse YAML
------------------------
`render.yaml` ở đây phẳng và `pyyaml` không có trong môi trường chạy gate. Thêm
một phụ thuộc để đọc năm dòng thì đổi một rủi ro lấy một rủi ro khác. Các hàm
dưới đây đọc đúng những khoá cần và nói rõ khi không đọc được — không đoán.
"""

from __future__ import print_function

import json
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RENDER_YAML = os.path.join(PROJECT_ROOT, 'render.yaml')
PACKAGE_JSON = os.path.join(PROJECT_ROOT, 'package.json')

# `node x.js`, `npm start`, `npm run start` — ba cách viết gặp trong thực tế.
NODE_CMD = re.compile(r'^node\s+(\S+)')
NPM_CMD = re.compile(r'^npm\s+(?:run\s+)?(\S+)')


def _read(path):
    try:
        with open(path, encoding='utf-8') as handle:
            return handle.read()
    except (IOError, OSError):
        return None


def _scalar(text, key):
    """Giá trị của một khoá scalar trong YAML phẳng, bỏ qua dòng bình luận."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('#') or ':' not in stripped:
            continue
        name, _, value = stripped.partition(':')
        if name.strip().lstrip('- ') == key:
            return value.strip().strip('"\'')
    return None


def _route_paths(text):
    """Các `path:` trong khối `routes:` của render.yaml."""
    paths, inside = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('routes:'):
            inside = True
            continue
        if inside:
            # Thoát khối khi gặp một khoá cùng cấp hoặc nông hơn `routes:`.
            if stripped and not stripped.startswith('-') and ':' in stripped \
                    and not stripped.startswith(('path:', 'matchType:')):
                indent = len(line) - len(line.lstrip())
                if indent <= 4:
                    break
            if stripped.startswith('- path:') or stripped.startswith('path:'):
                paths.append(stripped.split(':', 1)[1].strip().strip('"\''))
    return paths


def resolve_entrypoint(command, scripts):
    """Lệnh khởi động -> tệp .js nó thực sự chạy, đi qua script của npm.

    Trả `(đường_dẫn, lý_do)`; `đường_dẫn` là None khi không lần được — và không
    lần được thì phải nói ra, không được coi như khớp.
    """
    seen = set()
    while command:
        command = command.strip()
        node = NODE_CMD.match(command)
        if node:
            return node.group(1).replace('\\', '/'), None

        npm = NPM_CMD.match(command)
        if npm:
            name = npm.group(1)
            if name in seen:
                return None, 'script npm `%s` gọi vòng' % name
            seen.add(name)
            if name not in scripts:
                return None, 'package.json không có script `%s`' % name
            command = scripts[name]
            continue

        return None, 'không nhận ra lệnh khởi động: %r' % command[:60]
    return None, 'lệnh khởi động rỗng'


def audit():
    """Trả `(findings, scope)`. `findings` rỗng = hai bên khai cùng một tệp."""
    findings = []
    scope = {'render_start': None, 'package_start': None,
             'entrypoint': None, 'routes_checked': 0}

    render = _read(RENDER_YAML)
    package_raw = _read(PACKAGE_JSON)

    if render is None:
        findings.append({'level': 'CONFIG_MISSING', 'field': 'render.yaml',
                         'detail': 'không đọc được render.yaml'})
        return findings, scope
    if package_raw is None:
        findings.append({'level': 'CONFIG_MISSING', 'field': 'package.json',
                         'detail': 'không đọc được package.json'})
        return findings, scope

    try:
        package = json.loads(package_raw)
    except ValueError as error:
        findings.append({'level': 'CONFIG_MISSING', 'field': 'package.json',
                         'detail': 'package.json không parse được: %s' % error})
        return findings, scope

    scripts = package.get('scripts') or {}
    render_start = _scalar(render, 'startCommand')
    package_start = scripts.get('start')
    scope['render_start'] = render_start
    scope['package_start'] = package_start

    if not render_start:
        findings.append({'level': 'CONFIG_MISSING', 'field': 'startCommand',
                         'detail': 'render.yaml không khai startCommand'})
        return findings, scope
    if not package_start:
        findings.append({'level': 'CONFIG_MISSING', 'field': 'scripts.start',
                         'detail': 'package.json không khai script `start`'})
        return findings, scope

    render_entry, render_why = resolve_entrypoint(render_start, scripts)
    package_entry, package_why = resolve_entrypoint(package_start, scripts)

    for label, entry, why in (('render.yaml', render_entry, render_why),
                              ('package.json', package_entry, package_why)):
        if entry is None:
            findings.append({
                'level': 'ENTRYPOINT_UNKNOWN', 'field': label,
                'detail': '%s: %s — không xác định được tệp nào sẽ chạy, nên '
                          'không kết luận được hai bên có khớp hay không'
                          % (label, why)})

    if render_entry and package_entry:
        scope['entrypoint'] = package_entry
        if render_entry != package_entry:
            findings.append({
                'level': 'ENTRYPOINT_MISMATCH', 'field': 'startCommand',
                'detail': 'render.yaml chạy `%s`, package.json khai `%s`. Bộ '
                          'audit portal soi tệp thứ hai; người dùng mở tệp thứ '
                          'nhất.' % (render_entry, package_entry)})

    # Điểm vào phải tồn tại. Một đường dẫn đúng tới tệp không có thì deploy hỏng
    # ở lần khởi động, không ở lần đọc.
    for label, entry in (('render.yaml', render_entry),
                         ('package.json', package_entry)):
        if entry and not os.path.exists(os.path.join(PROJECT_ROOT, entry)):
            findings.append({
                'level': 'ENTRYPOINT_MISSING', 'field': label,
                'detail': '%s trỏ tới `%s`, tệp không tồn tại' % (label, entry)})

    # Mỗi route render.yaml công bố phải có người nhận trong chính tệp sẽ chạy.
    # Đây là nửa còn lại của cùng một câu hỏi: không chỉ "tệp nào chạy" mà "tệp
    # đó có phục vụ những gì nền tảng hứa hay không".
    entry = package_entry if package_entry == render_entry else None
    if entry:
        source = _read(os.path.join(PROJECT_ROOT, entry)) or ''
        handled = set(re.findall(r"app\.(?:get|use|all)\(\s*['\"]([^'\"]+)", source))
        scope['routes_checked'] = 0
        for route in _route_paths(render):
            scope['routes_checked'] += 1
            if route == '/' or '*' in handled:
                continue
            if any(h == route or h.startswith(route.rstrip('/') + '/')
                   for h in handled):
                continue
            findings.append({
                'level': 'ROUTE_UNSERVED', 'field': route,
                'detail': 'render.yaml định tuyến `%s`, nhưng `%s` không có '
                          'handler nào nhận đường này' % (route, entry)})

    return findings, scope


def main():
    findings, scope = audit()
    print('PHAM VI: render.yaml -> %r | package.json -> %r | diem vao %s | '
          '%d route doi chieu'
          % (scope['render_start'], scope['package_start'],
             scope['entrypoint'] or 'KHONG XAC DINH', scope['routes_checked']))
    for finding in findings:
        print('%-19s %-22s %s'
              % (finding['level'], finding['field'], finding['detail']))
    print('TONG: %d vi pham' % len(findings))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
