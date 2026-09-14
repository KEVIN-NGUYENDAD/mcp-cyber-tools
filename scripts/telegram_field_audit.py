#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM FIELD AUDIT (Sprint 14)

Cùng một câu hỏi như `portal_field_audit.py`, hỏi cho lớp Telegram:

    Mỗi trường mà bot ĐỌC có thật sự tồn tại trong tệp state nó đọc từ đó không?

Vì sao lớp này đáng nghi nhất
------------------------------
Sprint 11.3 sửa đúng MỘT hàm gửi cảnh báo và tìm thấy bốn trường sai trong đó:
`incident.id`, `threat_name`, `host`, `risk_score` — không trường nào có trong
`incidents.json`. Mọi cảnh báo từng gửi đi đều ghi "Incident: undefined".

Còn 11 handler khác (`/status`, `/open`, `/executive`, `/analytics`, `/hunt`,
`/triage`, `/evidence`, `/ioc`, `/network`, `/incidents`, `/start`) chưa ai đọc
lại. Và khác với portal — nơi một ô sai còn nằm cạnh chín ô đúng để so — tin
nhắn Telegram đi tới điện thoại một mình, giữa đêm, không có gì để đối chiếu.

Cách làm
--------
Bot đọc state qua `paths.<khoá>`. Bắt ba dạng:

    const x = JSON.parse(fs.readFileSync(paths.assets...))   -> x là bộ chứa
    x.field                                                   -> trường cấp tệp
    x.collection.map(r => r.field)                            -> trường bản ghi

Chấp nhận bỏ sót. Mục tiêu là bắt lớp lỗi "đọc trường không tồn tại", không phải
chứng minh toàn bộ mã đúng.
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
TELEGRAM_DIR = os.path.join(SCRIPT_DIR, 'telegram')

FILES = ['telegramBot.js', 'alertDelivery.js', 'incidentAlerter.js']

# paths.<khoá> -> tệp state. Lấy từ scripts/telegram/paths.js.
PATH_FILES = {
    'incidents': 'incidents.json',
    'socIntelligence': 'soc_intelligence.json',
    'assets': 'assets.json',
    'riskScore': 'risk_score.json',
    'waapStatus': 'waap_status.json',
    'domainStatus': 'domain_status.json',
    'notificationHistory': 'notification_history.json',
    'processedIncidents': 'processed_incidents.json',
    'approvalAudit': 'approval_audit.json',
    'dumping': 'hunting_credential_dumping.json',
    'movement': 'hunting_lateral_movement.json',
    'persistence': 'hunting_persistence.json',
    'processes': 'hunting_suspicious_processes.json',
    'timeline': 'timeline.json',
}

# Mảng bản ghi trong mỗi tệp: tệp -> khoá chứa mảng.
RECORD_KEY = {
    'incidents.json': 'incidents',
    'assets.json': 'assets',
    'hunting_credential_dumping.json': 'indicators',
    'hunting_lateral_movement.json': 'indicators',
    'hunting_persistence.json': 'indicators',
    'hunting_suspicious_processes.json': 'indicators',
    'notification_history.json': 'alerts',
    'timeline.json': 'events',
}

JS_BUILTINS = set((
    'length', 'map', 'filter', 'slice', 'find', 'forEach', 'reduce', 'sort',
    'join', 'push', 'includes', 'indexOf', 'some', 'every', 'concat', 'split',
    'toUpperCase', 'toLowerCase', 'toFixed', 'toString', 'trim', 'replace',
    'substring', 'startsWith', 'endsWith', 'padStart', 'padEnd', 'reverse',
    'keys', 'values', 'entries', 'flat', 'at', 'charAt', 'match', 'test',
    'getTime', 'toLocaleString', 'toLocaleDateString', 'toISOString', 'repeat',
))

# `X = JSON.parse(fs.readFileSync(paths.Y ...`, có hoặc không có từ khoá khai báo.
#
# Bot phần lớn KHAI BÁO biến trước (`let riskScore = { overall_score: 0 }`) rồi
# mới gán bên trong một nhánh `if (fs.existsSync(...))`. Đòi `const X =` thì bỏ
# sót gần hết — và một bộ kiểm bỏ sót gần hết còn tệ hơn không có, vì nó in ra
# một con số xanh.
BIND_RE = re.compile(
    r'\b(?:(?:const|let|var)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'JSON\.parse\(\s*fs\.readFileSync\(\s*paths\.([A-Za-z][A-Za-z0-9_]*)')

MEMBER_TEMPLATE = r'\b%s\??\.([A-Za-z_][A-Za-z0-9_]*)'

# `X.collection.<method>(V => ...)` hoặc `for (const V of X.collection)`
ITER_TEMPLATE = (r'%s\??\.([A-Za-z_][A-Za-z0-9_]*)'
                 r'\s*(?:\|\|\s*\[\]\s*\))?\s*\.\s*(?:map|filter|forEach|find|'
                 r'slice|sort|reduce|some|every)\s*\(\s*\(?\s*'
                 r'([A-Za-z_][A-Za-z0-9_]*)')


def load_state(filename):
    path = os.path.join(STATE_DIR, filename)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle), None
    except (ValueError, IOError, OSError) as error:
        return None, str(error)[:90]


def record_keys(data, collection):
    rows = data.get(collection) if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        return None
    keys = set()
    for row in rows[:50]:
        if isinstance(row, dict):
            keys |= set(row.keys())
    return keys or None


def audit_file(filename):
    path = os.path.join(TELEGRAM_DIR, filename)
    with io.open(path, encoding='utf-8') as handle:
        lines = handle.read().splitlines()

    findings = []
    seen = set()

    for number, line in enumerate(lines, 1):
        bind = BIND_RE.search(line)
        if not bind:
            continue
        variable, path_key = bind.group(1), bind.group(2)
        if path_key not in PATH_FILES:
            continue

        state_file = PATH_FILES[path_key]
        data, error = load_state(state_file)
        container_keys = set(data.keys()) if isinstance(data, dict) else set()

        # Phạm vi: tới hết handler (xấp xỉ bằng dòng trống + khối mới).
        window = []
        # Cua so 90 dong la mot gia tri doan. Sprint 17 them ~22 dong vao
        # handleExecutive va so truy cap quet duoc TUT tu 18 xuong 16 — bo kiem
        # van xanh vi no chi doi >= 10. Mot bo kiem thu hep pham vi ma van bao
        # dat la mot bo kiem dang ngung kiem. Cua so nay phai rong hon handler
        # dai nhat, va ranh gioi that su van la dong khai bao handler ke tiep.
        for candidate in lines[number:number + 200]:
            if re.match(r'^  (?:async )?[A-Za-z_]\w*\(', candidate):
                break
            window.append(candidate)
        body = '\n'.join(window)

        def record(level, field, detail):
            signature = (filename, variable, field)
            if signature in seen:
                return
            seen.add(signature)
            findings.append({
                'level': level, 'file': filename, 'line': number,
                'state': state_file, 'field': '%s.%s' % (variable, field),
                'detail': detail,
            })

        # -- trường cấp tệp -------------------------------------------------
        for field in re.findall(MEMBER_TEMPLATE % re.escape(variable), body):
            if field in JS_BUILTINS:
                continue
            if data is None:
                record('UNKNOWN', field, 'khong doc duoc state: %s' % error)
            elif field in container_keys:
                record('OK', field, '')
            else:
                record('MISSING', field,
                       'tep co: %s' % ', '.join(sorted(container_keys)[:8]))

        # -- trường bản ghi -------------------------------------------------
        for collection, item in re.findall(
                ITER_TEMPLATE % re.escape(variable), body):
            if collection in JS_BUILTINS or data is None:
                continue
            keys = record_keys(data, collection)
            expected = RECORD_KEY.get(state_file)
            if keys is None:
                for field in re.findall(MEMBER_TEMPLATE % re.escape(item), body):
                    if field not in JS_BUILTINS:
                        record('UNKNOWN', '%s[].%s' % (collection, field),
                               'mang "%s" rong hoac khong ton tai (mong doi "%s")'
                               % (collection, expected))
                continue
            for field in re.findall(MEMBER_TEMPLATE % re.escape(item), body):
                if field in JS_BUILTINS:
                    continue
                label = '%s[].%s' % (collection, field)
                if field in keys:
                    record('OK', label, '')
                else:
                    record('MISSING', label,
                           'ban ghi co: %s' % ', '.join(sorted(keys)[:10]))

    return findings


# --------------------------------------------------------------------------
# Lượt hai: khẳng định KHÔNG đọc trường nào
# --------------------------------------------------------------------------
#
# Lượt một kiểm các TRƯỜNG được đọc. Một dòng bịa đặt không đọc trường nào cả,
# nên nó đạt điểm audit tuyệt đối — đó là lỗ hổng cấu trúc của chính bộ audit
# này, và nó đã để lọt hai thứ suốt nhiều sprint:
#
#     "Digital signature verified"     <- khong co khoa ky nao trong repo
#     "Persistence Mechanisms (23%)"   <- bon hang so, mot muc khong ton tai
#
# Lượt hai đi tìm đúng loại câu đó: phần trăm viết cứng và từ vựng khẳng định
# đã-xác-minh, trong chuỗi template, không kèm một biểu thức `${...}` nào.

CLAIM_WORDS = (
    'signature verified', 'tamper-proof', 'tamper proof', 'hash verification',
    'chain of custody complete', 'verified ✅',
)

# `(23%)` — phần trăm viết cứng trong một dòng không có biểu thức nào.
HARDCODED_PERCENT_RE = re.compile(r'\(\s*\d{1,3}\s*%\s*\)')


def audit_claims(filename):
    """Dòng khẳng định mà không có dữ liệu nào phía sau."""
    path = os.path.join(TELEGRAM_DIR, filename)
    with io.open(path, encoding='utf-8') as handle:
        lines = handle.read().splitlines()

    findings = []
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        # Có `${...}` nghĩa là dòng này lấy giá trị từ đâu đó — không phải đích.
        if '${' in line:
            continue
        lowered = line.lower()

        for word in CLAIM_WORDS:
            if word in lowered:
                findings.append({
                    'level': 'CLAIM', 'file': filename, 'line': number,
                    'state': '-', 'field': word,
                    'detail': 'khang dinh da xac minh, khong co du lieu phia sau: '
                              + stripped[:70]})
                break
        else:
            if HARDCODED_PERCENT_RE.search(line):
                findings.append({
                    'level': 'CLAIM', 'file': filename, 'line': number,
                    'state': '-', 'field': 'hardcoded %',
                    'detail': 'phan tram viet cung: ' + stripped[:70]})
    return findings


def audit():
    findings = []
    for filename in FILES:
        findings.extend(audit_file(filename))
        findings.extend(audit_claims(filename))
    return findings


def main():
    findings = audit()
    missing = [f for f in findings if f['level'] == 'MISSING']
    unknown = [f for f in findings if f['level'] == 'UNKNOWN']
    ok = [f for f in findings if f['level'] == 'OK']

    claims = [f for f in findings if f['level'] == 'CLAIM']
    if claims:
        print('KHANG DINH KHONG CO DU LIEU PHIA SAU (%d):' % len(claims))
        for finding in claims:
            print('  %s:%-5d %s' % (finding['file'], finding['line'],
                                    finding['detail'][:100]))
        print('')

    if missing:
        print('TRUONG KHONG TON TAI (%d):' % len(missing))
        for finding in missing:
            print('  %s:%-5d %s' % (finding['file'], finding['line'],
                                    finding['field']))
            print('        %s -> %s' % (finding['state'], finding['detail'][:110]))
    if unknown:
        print('')
        print('KHONG KIEM DUOC (%d):' % len(unknown))
        for finding in unknown[:12]:
            print('  %s:%-5d %-34s %s' % (finding['file'], finding['line'],
                                          finding['field'], finding['detail'][:60]))

    print('')
    print('TONG: %d muc | %d truong dung | %d khong ton tai | %d khong kiem duoc '
          '| %d khang dinh khong co du lieu'
          % (len(findings), len(ok), len(missing), len(unknown), len(claims)))
    return 1 if (missing or claims) else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
