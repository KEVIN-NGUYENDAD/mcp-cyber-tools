#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUN COHERENCE AUDIT (AQ-039 + AQ-040)

Hai bất biến, một bộ kiểm, vì chúng là một bài toán:

    1. Mọi tệp state của một lần chạy phải mang CÙNG `run_id`.
    2. Mọi sự cố đang mở phải truy được về một quan sát còn tồn tại.

Vì sao chúng là một bài toán
-----------------------------
Vòng 6 đọc state và thấy `risk_score` được tính TRƯỚC cuộc săn mà nó trích dẫn.
Vòng 7 đọc và thấy mọi thứ đúng thứ tự. Không có bản vá nào ở giữa — vòng 6 chỉ
rơi đúng lúc hai lần chạy chồng nhau. Nghĩa là state có thể pha trộn nhiều lần
chạy, và không ai đọc ra được điều đó nếu không có dấu.

Cùng lúc, sáu chỉ báo dương tính giả đã sinh hai sự cố. Chỉ báo được sửa; sự cố
thì không, vì **không có gì nối sự cố về chỉ báo sinh ra nó**. Hai sự cố đó
chiếm một nửa điểm rủi ro, và bằng chứng trong chúng ("Risk Score: 31", "Thành
phần yếu: threat_hunting") đều sai khi đọc lại.

Không có `run_id` thì không có `source_run_id`; không có `source_run_id` thì
không rút lại được artifact của một lần chạy bị vô hiệu. Nên bộ này kiểm cả hai.

Bộ này KHÔNG kiểm gì
---------------------
Nó không đối chiếu từng dòng bằng chứng với state — so khớp văn bản tự do là thứ
báo sai nhiều hơn báo đúng. Nó kiểm điều kiểm được: sự cố có nguồn không, nguồn
còn đó không, và nguồn có phải một con số tính ra thay vì một quan sát không.

Và nó tự khai phạm vi ở dòng `PHAM VI:` — một bộ audit không nói mình soi bao
nhiêu thì con số 0 của nó không đọc được (AQ-034).
"""

from __future__ import print_function

import io
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import generate_incidents  # noqa: E402

# Những tệp phải cùng một lần chạy vì chúng nuôi nhau trong cùng pipeline.
# Danh sách ngắn có chủ đích: đây là các tệp mà một kết luận được rút ra từ sự
# kết hợp của chúng. Tệp thu thập độc lập (ví dụ ảnh chụp WAAP) không thuộc đây.
COHERENT_SET = [
    'risk_score.json',
    'incidents.json',
    'hunting_credential_dumping.json',
    'hunting_lateral_movement.json',
    'hunting_persistence.json',
    'hunting_suspicious_processes.json',
    'executive_findings.json',
]

OPEN_STATUSES = ('OPEN',)


def read_state(filename):
    path = os.path.join(STATE_DIR, filename)
    try:
        with io.open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def run_ids():
    """Mỗi tệp trong tập gắn kết -> `run_id` nó tự khai (hoặc None)."""
    found = {}
    for name in COHERENT_SET:
        data = read_state(name)
        if not isinstance(data, dict):
            found[name] = {'present': False, 'run_id': None}
            continue
        found[name] = {'present': True,
                       'run_id': data.get('run_id'),
                       'run_scope': data.get('run_scope')}
    return found


def audit_runs():
    findings = []
    stamps = run_ids()
    present = [v for v in stamps.values() if v['present']]
    distinct = set(v['run_id'] for v in present if v['run_id'])
    unstamped = [k for k, v in stamps.items() if v['present'] and not v['run_id']]

    if len(distinct) > 1:
        # Đây là lỗi thật sự nguy hiểm: mọi kết luận rút ra từ tập này đang
        # trộn hai lần quan sát khác nhau, và không ai biết dòng nào thuộc đâu.
        findings.append({
            'level': 'MIXED_RUN', 'file': 'state/', 'field': 'run_id',
            'detail': '%d lan chay khac nhau trong cung tap state: %s'
                      % (len(distinct), ', '.join(sorted(distinct))),
        })

    return findings, {
        'files_checked': len(COHERENT_SET),
        'files_present': len(present),
        'files_stamped': len(present) - len(unstamped),
        'unstamped': unstamped,
        'distinct_runs': sorted(distinct),
    }


def audit_incidents():
    """Sự cố đang mở: có nguồn không, nguồn còn không, nguồn có phải quan sát không."""
    findings = []
    data = read_state('incidents.json')
    if not isinstance(data, dict):
        return findings, {'open': 0, 'checked': 0, 'reason': 'khong doc duoc'}

    records = data.get('incidents') or []
    open_records = [i for i in records if (i or {}).get('status') in OPEN_STATUSES]

    checked = 0
    for incident in open_records:
        ident = incident.get('incident_id', '?')
        source = incident.get('source_state')

        if not incident.get('fingerprint') or not source:
            findings.append({
                'level': 'NO_PROVENANCE', 'file': 'incidents.json', 'field': ident,
                'detail': 'su co dang mo khong co dau nguon — khong ra lai duoc '
                          'khi quan sat dung sau no bi rut',
            })
            continue

        if source in generate_incidents.DERIVED_STATE:
            findings.append({
                'level': 'DERIVED_SOURCE', 'file': 'incidents.json', 'field': ident,
                'detail': 'su co sinh tu %s — mot con so tinh ra, khong phai '
                          'quan sat (vong phan hoi AQ-039)' % source,
            })
            continue

        checked += 1
        if read_state(source) is None:
            findings.append({
                'level': 'SOURCE_MISSING', 'file': 'incidents.json', 'field': ident,
                'detail': 'tep nguon %s khong doc duoc, nhung su co van dang mo'
                          % source,
            })

    return findings, {'open': len(open_records), 'checked': checked,
                      'records': len(records),
                      'invalidated': len([i for i in records
                                          if (i or {}).get('status') == 'INVALIDATED'])}


def audit():
    run_findings, run_scope = audit_runs()
    inc_findings, inc_scope = audit_incidents()
    return run_findings + inc_findings, {'runs': run_scope, 'incidents': inc_scope}


def main():
    findings, scope = audit()

    for finding in findings:
        print('%-15s %s: %s' % (finding['level'], finding['field'],
                                finding['detail']))

    runs = scope['runs']
    incidents = scope['incidents']
    print('')
    print('PHAM VI: %d/%d tep trong tap gan ket co dau lan chay; %d su co dang '
          'mo, %d truy nguoc duoc; %d ban ghi da thu hoi.'
          % (runs['files_stamped'], runs['files_present'],
             incidents['open'], incidents['checked'],
             incidents.get('invalidated', 0)))
    if runs['unstamped']:
        # Không đếm là lỗi: một tệp sinh ngoài pipeline hợp lệ không mang lần
        # chạy nào. Nhưng phải in ra, vì mỗi tệp ở đây là một chỗ bất biến 1
        # không nói được gì.
        print('KHONG DAU: %s' % ', '.join(sorted(runs['unstamped'])))
    print('TONG: %d vi pham' % len(findings))
    return 1 if findings else 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    sys.exit(main())
