#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PORTAL FIELD AUDIT (Sprint 13)

Đối chiếu từng trường mà `web/app.js` ĐỌC với những trường thật sự CÓ trong tệp
state tương ứng.

Vì sao cần
----------
Cùng một lỗi đã được tìm thấy ở bốn nơi khác nhau trong repo này:

    asset_manager.py   đọc `all_assets`      -> "No assets found" trên mạng 11 máy
    portal Asset Center đọc `type`/`status`  -> 11 thiết bị đều "Offline"
    Telegram alert     đọc `id`/`threat_name` -> "Incident: undefined"
    credential hunt    đọc trường sai        -> 15 CRITICAL giả

Cả bốn đều im lặng. `data.get('x', default)` và `obj?.x || fallback` biến "trường
không tồn tại" thành một giá trị trông hợp lệ, và cái giá trị đó đi thẳng lên
màn hình như một sự thật đã đo được.

Portal là nơi nguy hiểm nhất trong bốn: nó là thứ người dùng nhìn mỗi ngày, và
nó không có ai kiểm lại.

Cách làm
--------
Không phân tích cú pháp JS đầy đủ — chỉ cần bắt đúng dạng `stateData.<nguồn>`
rồi truy các trường đọc từ nó. Chấp nhận bỏ sót; mục tiêu là bắt được lớp lỗi
"đọc trường không tồn tại", không phải chứng minh toàn bộ mã đúng.

Cảnh báo có ba mức:
    MISSING   trường không có trong state, và tệp state đọc được  -> gần như
              chắc chắn là lỗi
    UNKNOWN   không kiểm được (tệp state chưa có, hoặc mảng rỗng)
    OK        có thật
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
APP_JS = os.path.join(PROJECT_ROOT, 'web', 'app.js')

# stateData.<khoá> -> tệp state. Lấy từ loadAllData() trong web/app.js.
SOURCE_FILES = {
    'assets': 'assets.json',
    'shadowAssets': 'shadow_assets.json',
    'incidents': 'incidents.json',
    'risk': 'risk_score.json',
    'health': 'system_health.json',
    'defender': 'defender_status.json',
    'firewall': 'firewall_status.json',
    'alerts': 'notification_history.json',
    'waap': 'waap_status.json',
    'domain': 'domain_status.json',
    'threatPersistence': 'hunting_persistence.json',
    'threatLateral': 'hunting_lateral_movement.json',
    'threatCredential': 'hunting_credential_dumping.json',
    'threatProcesses': 'hunting_suspicious_processes.json',
    'sensorCoverage': 'sensor_coverage.json',
}

# Trường do chính portal gắn vào sau khi tải, không đến từ tệp state.
PORTAL_ADDED = set(['_fetched_at', '_source_timestamp'])

# `stateData.<nguon>` theo sau la mot chuoi truy cap truong.
ACCESS_RE = re.compile(
    r'stateData\.([A-Za-z]+)((?:\??\.[A-Za-z_][A-Za-z0-9_]*)+)')


JS_BUILTINS = set((
    'length', 'map', 'filter', 'slice', 'find', 'forEach', 'reduce', 'sort',
    'join', 'push', 'includes', 'indexOf', 'some', 'every', 'concat', 'split',
    'toUpperCase', 'toLowerCase', 'toFixed', 'toString', 'trim', 'replace',
    'substring', 'startsWith', 'endsWith', 'padStart', 'reverse', 'keys',
    'values', 'entries', 'flat', 'at', 'charAt', 'match', 'test', 'getTime',
    'toLocaleString', 'toLocaleDateString', 'toISOString', 'value',
))


def load_state(filename):
    path = os.path.join(STATE_DIR, filename)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle), None
    except (ValueError, IOError, OSError) as error:
        return None, str(error)[:100]


def keys_at(data, path_parts):
    """Đi theo đường dẫn trường, trả về (tồn tại, các khoá con có thể có).

    Với list thì soi phần tử đầu: mọi chỉ báo trong một tệp hunting có cùng hình
    dạng, nên một phần tử là đủ để biết trường nào tồn tại.
    """
    current = data
    for index, part in enumerate(path_parts):
        if isinstance(current, list):
            if not current:
                return None, 'mang rong'
            current = current[0]
        if not isinstance(current, dict):
            return None, 'khong phai object tai "%s"' % '.'.join(path_parts[:index])
        if part not in current:
            available = sorted(current.keys())
            return False, available
        current = current[part]
    return True, None


# Bộ sưu tập bản ghi: `stateData.<nguồn>` -> đường dẫn tới mảng bản ghi.
# Đây mới là nơi lỗi thật đã xảy ra. Portal hiếm khi đọc `stateData.x.y` trực
# tiếp; nó gán mảng ra biến rồi đọc trường TRÊN TỪNG BẢN GHI — và `asset.type`,
# `asset.status`, `incident.id` đều là những trường chưa bao giờ tồn tại.
RECORD_COLLECTIONS = {
    'assets': ('assets.json', ['assets']),
    'shadowAssets': ('shadow_assets.json', ['shadows']),
    'incidents': ('incidents.json', ['incidents']),
    'threatPersistence': ('hunting_persistence.json', ['indicators']),
    'threatLateral': ('hunting_lateral_movement.json', ['indicators']),
    'threatCredential': ('hunting_credential_dumping.json', ['indicators']),
    'threatProcesses': ('hunting_suspicious_processes.json', ['indicators']),
}

# `const X = stateData.<nguon>...` — bắt biến giữ mảng bản ghi.
BIND_RE = re.compile(
    r'\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[^;\n]*'
    r'stateData\.([A-Za-z]+)')

# Trường đọc trên một phần tử: `x.field` hoặc `x?.field`.
MEMBER_RE_TEMPLATE = r'\b%s\??\.([A-Za-z_][A-Za-z0-9_]*)'

# Thuộc tính/phương thức của JS, không phải trường dữ liệu.


def record_keys(filename, path_parts):
    """Tập khoá thật của một bản ghi trong bộ sưu tập, hoặc None nếu chưa biết."""
    data, error = load_state(filename)
    if data is None:
        return None, 'khong doc duoc state: %s' % error
    current = data
    for part in path_parts:
        if not isinstance(current, dict) or part not in current:
            return None, 'khong tim thay "%s"' % part
        current = current[part]
    if not isinstance(current, list):
        return None, 'khong phai mang'
    if not current:
        return None, 'mang rong — chua co ban ghi de doi chieu'
    keys = set()
    for record in current[:50]:
        if isinstance(record, dict):
            keys |= set(record.keys())
    return (keys, None) if keys else (None, 'ban ghi khong phai object')


def audit_record_fields(source):
    """Trường đọc trên từng bản ghi, đối chiếu với khoá thật."""
    findings = []
    seen = set()
    lines = source.splitlines()

    for number, line in enumerate(lines, 1):
        if line.strip().startswith('//'):
            continue
        bind = BIND_RE.search(line)
        if not bind:
            continue
        variable, source_key = bind.group(1), bind.group(2)
        if source_key not in RECORD_COLLECTIONS:
            continue

        filename, path_parts = RECORD_COLLECTIONS[source_key]
        keys, problem = record_keys(filename, path_parts)

        # Cùng một tên biến có thể trỏ vào BỘ CHỨA (`stateData.assets`) chứ
        # không phải một bản ghi. `stateData.assets?.timestamp` là hợp lệ —
        # timestamp nằm ở cấp tệp. Lấy luôn khoá cấp tệp để không báo nhầm.
        container, _ = load_state(filename)
        container_keys = set(container.keys()) if isinstance(container, dict) else set()

        # Phạm vi tra cứu: từ dòng gán tới hết hàm (xấp xỉ bằng 120 dòng hoặc
        # tới dòng bắt đầu một hàm mới). Đủ chặt để không bắt nhầm biến khác.
        window = []
        for candidate in lines[number:number + 120]:
            if re.match(r'^(function |async function |const \w+ = \(|// =====)',
                        candidate):
                break
            if candidate.strip().startswith('//'):
                continue
            window.append(candidate)

        member_re = re.compile(MEMBER_RE_TEMPLATE % re.escape(variable))
        singular = variable[:-1] if variable.endswith('s') else None
        patterns = [member_re]
        if singular and len(singular) > 2:
            patterns.append(re.compile(MEMBER_RE_TEMPLATE % re.escape(singular)))

        for pattern in patterns:
            for body_line in window:
                for field in pattern.findall(body_line):
                    if field in JS_BUILTINS or field in container_keys:
                        continue
                    if field in PORTAL_ADDED or field == 'json':
                        continue
                    signature = (source_key, variable, field)
                    if signature in seen:
                        continue
                    seen.add(signature)

                    if keys is None:
                        findings.append({
                            'level': 'UNKNOWN', 'line': number,
                            'source': source_key, 'field': '%s.%s' % (variable, field),
                            'file': filename, 'detail': problem,
                        })
                    elif field in keys:
                        findings.append({
                            'level': 'OK', 'line': number, 'source': source_key,
                            'field': '%s.%s' % (variable, field),
                            'file': filename, 'detail': '',
                        })
                    else:
                        findings.append({
                            'level': 'MISSING', 'line': number,
                            'source': source_key,
                            'field': '%s.%s' % (variable, field),
                            'file': filename,
                            'detail': 'ban ghi co: %s' % ', '.join(sorted(keys)[:10]),
                        })
    return findings


def audit():
    with io.open(APP_JS, encoding='utf-8') as handle:
        source = handle.read()

    lines = source.splitlines()
    findings = []
    seen = set()

    for number, line in enumerate(lines, 1):
        if line.strip().startswith('//'):
            continue
        for match in ACCESS_RE.finditer(line):
            source_key = match.group(1)
            chain = [p for p in re.split(r'\??\.', match.group(2)) if p]
            if not chain or source_key not in SOURCE_FILES:
                continue
            if chain[0] in PORTAL_ADDED:
                continue

            signature = (source_key, tuple(chain))
            if signature in seen:
                continue
            seen.add(signature)

            filename = SOURCE_FILES[source_key]
            data, error = load_state(filename)
            if data is None:
                findings.append({
                    'level': 'UNKNOWN', 'line': number, 'source': source_key,
                    'field': '.'.join(chain), 'file': filename,
                    'detail': 'khong doc duoc state: %s' % error,
                })
                continue

            # `.toUpperCase()` tren mot chuoi, `.length` tren mot mang — dung
            # JS, khong phai tra khoa. Bo qua de dau ra cua cong cu nay sach:
            # mot bo kiem keu bao dong gia se bi nguoi ta thoi doc.
            if chain[-1] in JS_BUILTINS:
                chain = chain[:-1]
                if not chain:
                    continue

            exists, extra = keys_at(data, chain)
            if exists is True:
                findings.append({
                    'level': 'OK', 'line': number, 'source': source_key,
                    'field': '.'.join(chain), 'file': filename, 'detail': '',
                })
            elif exists is None:
                findings.append({
                    'level': 'UNKNOWN', 'line': number, 'source': source_key,
                    'field': '.'.join(chain), 'file': filename,
                    'detail': str(extra),
                })
            else:
                findings.append({
                    'level': 'MISSING', 'line': number, 'source': source_key,
                    'field': '.'.join(chain), 'file': filename,
                    'detail': 'co san: %s' % ', '.join(list(extra)[:8]),
                })

    findings.extend(audit_record_fields(source))
    return findings


def main():
    findings = audit()
    missing = [f for f in findings if f['level'] == 'MISSING']
    unknown = [f for f in findings if f['level'] == 'UNKNOWN']
    ok = [f for f in findings if f['level'] == 'OK']

    if missing:
        print('TRUONG KHONG TON TAI (%d):' % len(missing))
        for finding in missing:
            print('  app.js:%-5d stateData.%s.%s' % (
                finding['line'], finding['source'], finding['field']))
            print('        %s -> %s' % (finding['file'], finding['detail'][:110]))
    if unknown:
        print('')
        print('KHONG KIEM DUOC (%d):' % len(unknown))
        for finding in unknown[:15]:
            print('  app.js:%-5d stateData.%s.%s  (%s)' % (
                finding['line'], finding['source'], finding['field'],
                finding['detail'][:60]))

    print('')
    print('TONG: %d truy cap | %d dung | %d khong ton tai | %d khong kiem duoc'
          % (len(findings), len(ok), len(missing), len(unknown)))
    return 1 if missing else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
