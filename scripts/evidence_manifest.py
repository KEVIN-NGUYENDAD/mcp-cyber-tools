#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVIDENCE MANIFEST (Sprint B — AQ-006)

`/evidence` trong Telegram bot khẳng định bốn điều:

    Status: VERIFIED
    Hash Verification: PASSED
    Tamper-proof container
    Digital signature verified

Cả bốn dòng đó có đúng MỘT đầu vào:

    const custodyValid = reportCount > 0;

Không một hàm băm nào được tính ở bất cứ đâu trong repo. Không một chữ ký nào
được xác minh. Và `reportCount` đếm nhầm luôn cả nguồn: nó đếm cảnh báo trong
`notification_history.json`, không phải hiện vật bằng chứng.

Vì sao đây là lời nói dối nguy hiểm nhất trong hệ thống
--------------------------------------------------------
Chain of custody là thứ quyết định một bằng chứng có dùng được hay không. Một
dòng "Digital signature verified" sinh ra từ phép so `> 0` không chỉ sai — nó
sai đúng vào chỗ mà người đọc tin tưởng nhất và ít có khả năng tự kiểm nhất.

Cách chữa KHÔNG phải là xoá hết
--------------------------------
Xoá bốn dòng đó là trung thực nhưng lãng phí: 349 hiện vật thật đang nằm trên
đĩa, và băm chúng là việc rẻ. Cái không làm được là khẳng định về QUÁ KHỨ — băm
một tệp bây giờ không nói gì về việc nó có bị sửa trước đó hay không, vì không có
mốc nào để so.

Nên tệp này dựng đúng cái mốc đó: lần đầu thấy một hiện vật thì ghi lại băm của
nó; những lần sau thì SO. Từ đó "phát hiện sửa đổi" trở thành một phép đo thật,
trong phạm vi đã tuyên bố: kể từ lần đầu hệ thống nhìn thấy tệp.

Thứ vẫn KHÔNG có là chữ ký số. Không có khoá, không có CA, không có gì để ký.
Manifest nói thẳng điều đó thay vì để một dấu ✅ nói hộ.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
MANIFEST_FILE = os.path.join(STATE_DIR, 'evidence_manifest.json')

# Cùng thư mục mà `modules/reportGenerator.js` ghi vào.
REPORTS_DIR = os.path.join(os.path.expanduser('~'), 'Documents',
                           'cyber-tools-reports')

VERSION = '1.0.0'
CHUNK = 65536


def sha256(path):
    digest = hashlib.sha256()
    try:
        with open(path, 'rb') as handle:
            while True:
                block = handle.read(CHUNK)
                if not block:
                    break
                digest.update(block)
    except (IOError, OSError):
        return None
    return digest.hexdigest()


def read_manifest():
    try:
        with io.open(MANIFEST_FILE, encoding='utf-8') as handle:
            data = json.load(handle)
    except (ValueError, IOError, OSError):
        return {}
    return data.get('artifacts') or {}


def build():
    now = datetime.now().isoformat()
    known = read_manifest()

    if not os.path.isdir(REPORTS_DIR):
        return {
            'version': VERSION,
            'generated_at': now,
            'reports_dir': REPORTS_DIR,
            'readable': False,
            'reason': 'Thư mục hiện vật không tồn tại — chưa có bằng chứng nào '
                      'được thu thập trên máy này.',
            'total': 0, 'new': 0, 'verified': 0,
            'changed': [], 'missing': [],
            'signature_status': 'NOT_IMPLEMENTED',
            'artifacts': {},
        }

    artifacts = {}
    changed = []
    new_count = 0
    verified = 0
    total_bytes = 0

    for name in sorted(os.listdir(REPORTS_DIR)):
        path = os.path.join(REPORTS_DIR, name)
        if not os.path.isfile(path):
            continue
        digest = sha256(path)
        if digest is None:
            continue
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        total_bytes += size

        previous = known.get(name)
        if previous is None:
            # Lần đầu thấy. Ghi mốc, KHÔNG tính là đã xác minh: chưa có gì để so.
            artifacts[name] = {'sha256': digest, 'size': size,
                               'first_seen': now, 'last_verified': now}
            new_count += 1
            continue

        artifacts[name] = dict(previous)
        artifacts[name]['size'] = size
        if previous.get('sha256') == digest:
            artifacts[name]['last_verified'] = now
            verified += 1
        else:
            # Nội dung đã đổi kể từ lần đầu ghi nhận. Đây là một sự thật, không
            # phải một cáo buộc: tệp có thể được ghi đè hợp lệ. Nhưng nó phải
            # hiện ra, chứ không được lặng lẽ nhận băm mới.
            changed.append({'file': name,
                            'recorded': previous.get('sha256'),
                            'current': digest,
                            'first_seen': previous.get('first_seen')})
            artifacts[name]['sha256_current'] = digest
            artifacts[name]['changed_at'] = now

    missing = [name for name in known if name not in artifacts]

    return {
        'version': VERSION,
        'generated_at': now,
        'reports_dir': REPORTS_DIR,
        'readable': True,
        'total': len(artifacts),
        'new': new_count,
        'verified': verified,
        'total_bytes': total_bytes,
        'changed': changed,
        'missing': missing,
        # Phạm vi của lời khẳng định, viết ra cùng chỗ với lời khẳng định.
        'integrity_scope': ('SHA-256 so với lần ĐẦU TIÊN hệ thống nhìn thấy mỗi '
                            'tệp. Không nói gì về giai đoạn trước đó.'),
        'signature_status': 'NOT_IMPLEMENTED',
        'signature_note': ('Không có khoá ký, không có CA, không có gì để xác '
                           'minh. Bản cũ in "Digital signature verified" — dòng '
                           'đó không có hiện thực nào phía sau.'),
        'artifacts': artifacts,
    }


def main():
    manifest = build()
    if not os.path.isdir(STATE_DIR):
        os.makedirs(STATE_DIR)
    with io.open(MANIFEST_FILE, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(manifest, indent=2, ensure_ascii=False))

    print(json.dumps({
        'status': 'success',
        'total': manifest['total'],
        'new': manifest['new'],
        'verified': manifest['verified'],
        'changed': len(manifest['changed']),
        'missing': len(manifest['missing']),
        'signature_status': manifest['signature_status'],
    }, indent=2, ensure_ascii=False))

    # Hiện vật đổi nội dung là thứ cần biết, không phải lỗi của stage. Chỗ báo
    # động đúng là báo cáo, không phải mã thoát.
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
