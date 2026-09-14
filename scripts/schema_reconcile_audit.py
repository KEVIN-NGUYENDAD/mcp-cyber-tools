# -*- coding: utf-8 -*-
"""
SCHEMA RECONCILE AUDIT (AQ-041) — hai đầu của một phép ánh xạ phải cộng ra
cùng một số.

Lớp lỗi mà bộ này soi
----------------------
AQ-020, AQ-021 và AQ-002 được ba vòng audit ghi riêng rẽ, nhưng chúng là một
họ: **một phép ánh xạ sai giữa hai lược đồ, và không ai đối chiếu hai đầu.**

Không mục nào trong ba mục đó thuộc dạng `.get(khoá, mặc định)`, nên
`pipeline_field_audit.py` không nhìn thấy chúng — nó soi tên trường, còn đây là
lỗi về GIÁ TRỊ. Cũng không mục nào là một trường đọc sai, nên `portal_field_audit`
không thấy. Cả hai bộ đều đúng và đều mù với họ lỗi này.

Phép kiểm ở đây không đọc tên trường nào cả. Nó cộng hai đầu rồi so. Đó là lý do
nó bắt được lỗi khoá int/str của AQ-020: bản cũ cho `severity_breakdown` tổng 0
đứng cạnh `total_findings: 19`, và không cái tên nào trong hai cái đó sai.

Ba bất biến, và vì sao chỉ còn hai
-----------------------------------
AQ-041 đề nghị ba. Cái thứ ba — `%FULL attribution <= %asset có hostname` — đã
được kiểm bằng dữ liệu và **tiền đề của nó sai**; xem `INVARIANTS` bên dưới.
Thay vì bỏ im, bộ này giữ lại phép đo ấy dưới dạng một hàng PHẠM VI: nó ghi
hostname đến từ đâu, để lần sau không ai phải suy ra điều đó từ code.
"""

from __future__ import print_function

import io
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')

HUNTS = ('hunting_lateral_movement', 'hunting_persistence',
         'hunting_suspicious_processes', 'hunting_credential_dumping')


def _read(name):
    try:
        with io.open(os.path.join(STATE_DIR, name), encoding='utf-8') as handle:
            return json.load(handle)
    except (ValueError, IOError, OSError):
        return None


def check_crypto(findings, scope):
    """AQ-020. Tổng phân phối severity phải bằng số finding."""
    crypto = _read('crypto_inventory.json')
    if crypto is None:
        scope['crypto'] = 'KHONG DOC DUOC'
        return

    breakdown = crypto.get('severity_breakdown') or {}
    total = crypto.get('total_findings')
    counted = sum(v for v in breakdown.values() if isinstance(v, int))
    scope['crypto'] = '%d/%s phan loai, score %s' % (
        counted, total, crypto.get('score'))

    if not isinstance(total, int):
        findings.append({
            'level': 'NO_TOTAL', 'field': 'crypto_inventory.total_findings',
            'detail': 'khong co total_findings de doi chieu'})
        return

    if counted != total:
        findings.append({
            'level': 'SUM_MISMATCH', 'field': 'crypto_inventory.severity_breakdown',
            'detail': 'severity_breakdown tong %d, total_findings %d — %d finding '
                      'khong nam trong hang nao, nen diem crypto tinh thieu chung'
                      % (counted, total, abs(total - counted))})

    # Điểm hằng số là triệu chứng riêng của cùng một lỗi: nếu breakdown rỗng thì
    # mọi phép trừ nhân với 0 và điểm luôn là 100. Một điểm số không bao giờ đổi
    # đọc lên giống hệt một hệ thống sạch.
    if crypto.get('score') == 100 and total and counted == 0:
        findings.append({
            'level': 'CONSTANT_SCORE', 'field': 'crypto_inventory.score',
            'detail': 'score 100 tren %d finding chua phan loai — diem khong '
                      'phai ket qua cua phep tinh nao' % total})


def check_vulnerability_units(findings, scope):
    """AQ-021. `assets[]` cộng theo lượt; `nessus_status` đếm plugin riêng biệt.

    Hai đơn vị khác nhau, và ba vòng audit đọc chênh lệch giữa chúng như một
    con số sai. Phép kiểm đúng không phải "hai số phải bằng nhau" — mà là "mỗi
    số phải khai đơn vị của nó, và số cùng đơn vị thì phải khớp".
    """
    assets_state = _read('assets.json')
    nessus = _read('nessus_status.json')
    if assets_state is None or nessus is None:
        scope['vulns'] = 'KHONG DOC DUOC'
        return

    assets = assets_state.get('assets') or assets_state
    if isinstance(assets, dict):
        assets = list(assets.values())
    if not isinstance(assets, list):
        scope['vulns'] = 'assets.json khong phai danh sach'
        return

    per_asset = sum(int(a.get('vulnerability_count') or 0)
                    for a in assets if isinstance(a, dict))
    instances = nessus.get('total_instances')
    plugins = nessus.get('distinct_plugins', nessus.get('total'))
    scope['vulns'] = 'assets %d luot | nessus %s plugin, %s luot' % (
        per_asset, plugins, instances)

    if nessus.get('total_unit') is None:
        findings.append({
            'level': 'UNIT_UNDECLARED', 'field': 'nessus_status.total',
            'detail': 'nessus_status.total khong khai don vi, nen khong doi '
                      'chieu duoc voi assets[].vulnerability_count'})
        return

    if instances is None:
        findings.append({
            'level': 'UNIT_MISSING', 'field': 'nessus_status.total_instances',
            'detail': 'thieu total_instances — day la don vi duy nhat cung he '
                      'voi assets[].vulnerability_count'})
        return

    # Quét mạng và kho tài sản có thể lệch nhau vì lý do chính đáng (host mới,
    # host rời mạng giữa hai lần chạy). Nên đây là kiểm BẬC ĐỘ LỚN, không phải
    # kiểm bằng nhau tuyệt đối: cái cần bắt là chênh 6.2 lần, không phải chênh 3.
    if instances and per_asset:
        ratio = max(per_asset, instances) / float(min(per_asset, instances))
        if ratio >= 2.0:
            findings.append({
                'level': 'UNIT_MISMATCH', 'field': 'assets[].vulnerability_count',
                'detail': 'assets cong %d luot, nessus khai %d luot — chenh %.1f '
                          'lan tren cung mot ban quet, hai ben dang dem hai thu '
                          'khac nhau' % (per_asset, instances, ratio)})


def check_attribution(findings, scope):
    """AQ-002, và vì sao bất biến mà AQ-041 đề nghị không dùng được.

    AQ-041 đề nghị: `%FULL attribution <= %asset co hostname_source != unresolved`.
    Đo trên dữ liệu thật thì tiền đề sai. `assets.json` là kho dựng từ MỘT LẦN
    QUÉT MẠNG — 11 host, cả 11 `unresolved`. Nhưng 616/618 hệ thống được quy kết
    `FULL` không nằm trong tập đó: chúng là chính máy đang chạy, và hostname của
    chúng đến từ `local_host_identity()`, không từ kho.

    Bắt máy cục bộ phải chờ một lần quét mạng xác nhận tên của chính nó là vứt
    đi nguồn đáng tin nhất đang có. Và đúng luật: mọi peer ở xa không phân giải
    được đều đang là `PARTIAL`, không một cái nào `FULL`.

    Nên phép kiểm ở đây là phép kiểm mà bằng chứng ủng hộ: `FULL` phải đi kèm
    một hostname có nguồn ghi rõ. `FULL` mà nguồn là `unresolved` mới là bịa.
    """
    sources = {}
    full_unresolved = 0
    graded = 0

    for name in HUNTS:
        data = _read('%s.json' % name)
        if data is None:
            continue
        for indicator in data.get('indicators') or []:
            quality = indicator.get('attribution_quality')
            systems = (indicator.get('attribution') or {}).get('systems') or []
            if quality:
                graded += 1
            for system in systems:
                source = system.get('hostname_source') or 'khong khai'
                sources[source] = sources.get(source, 0) + 1
                if quality == 'FULL' and source in ('unresolved', 'khong khai'):
                    full_unresolved += 1

    scope['attribution'] = '%d chi bao xep hang | nguon hostname: %s' % (
        graded, ', '.join('%s %d' % (k, v) for k, v in sorted(sources.items())))

    if full_unresolved:
        findings.append({
            'level': 'ATTRIBUTION_UNBACKED', 'field': 'attribution_quality',
            'detail': '%d he thong duoc xep FULL nhung hostname khong phan giai '
                      'duoc — FULL nghia la da biet ten may, va o day khong ai '
                      'biet' % full_unresolved})


def check_suppressed_severity(findings, scope):
    """AQ-045. `by_severity` cấp tệp phải đếm tập ĐÃ LỌC tiếng ồn.

    Cuộc săn đếm `by_severity` ở stage sớm, trên toàn bộ chỉ báo;
    `ioc_quality` gắn cờ `suppressed` ở stage sau. Cuộc săn không thể biết chỉ
    báo nào sẽ bị hạ xuống tiếng ồn, nên con số nó công bố là số TRƯỚC lọc — và
    `calculate_risk_score` đọc đúng con số đó.

    Đã đo: 6 chỉ báo `ROUTINE_OS_ACTIVITY` giữ nhãn `HIGH` trong bảng tổng kết,
    chiếm 78% điểm rủi ro của cả hệ thống (18.0 / 23).

    Phép kiểm cùng hình dạng với hai phép trên: cộng hai đầu rồi so.
    """
    checked = []
    for name in HUNTS:
        data = _read('%s.json' % name)
        if data is None:
            continue
        indicators = data.get('indicators') or []
        published = data.get('by_severity')
        if published is None:
            continue

        kept = len([i for i in indicators if not i.get('suppressed')])
        counted = sum(v for v in published.values() if isinstance(v, int))
        checked.append('%s %d/%d' % (name.replace('hunting_', ''), counted, kept))

        if counted != kept:
            findings.append({
                'level': 'SUPPRESSED_COUNTED', 'field': '%s.by_severity' % name,
                'detail': 'by_severity tong %d nhung chi co %d chi bao khong bi '
                          'loc — %d chi bao da duoc ket luan la tieng on van dang '
                          'duoc cham diem' % (counted, kept, counted - kept)})

        # Một chỉ báo bị lọc mà vẫn giữ nhãn CRITICAL/HIGH trong bảng công bố là
        # đúng cái đẩy risk lên. Bắt riêng, vì nó nói rõ hậu quả hơn phép so tổng.
        noisy_high = len([i for i in indicators
                          if i.get('suppressed')
                          and i.get('severity') in ('CRITICAL', 'HIGH')])
        if noisy_high and (published.get('HIGH') or published.get('CRITICAL')):
            kept_high = len([i for i in indicators
                             if not i.get('suppressed')
                             and i.get('severity') in ('CRITICAL', 'HIGH')])
            if not kept_high:
                findings.append({
                    'level': 'NOISE_SCORED', 'field': '%s.by_severity' % name,
                    'detail': 'khai CRITICAL/HIGH trong khi 0 chi bao khong-bi-loc '
                              'o muc do; %d muc do deu mang suppressed' % noisy_high})

    scope['suppressed'] = ' | '.join(checked) if checked else '-'


INVARIANTS = (check_crypto, check_vulnerability_units, check_attribution,
              check_suppressed_severity)


def audit():
    """Trả `(findings, scope)`. `findings` rỗng = hai đầu mọi phép cộng khớp."""
    findings, scope = [], {}
    for invariant in INVARIANTS:
        invariant(findings, scope)
    return findings, scope


def main():
    findings, scope = audit()
    for key in ('crypto', 'vulns', 'attribution', 'suppressed'):
        print('PHAM VI %-12s %s' % (key, scope.get(key, '-')))
    for finding in findings:
        print('%-22s %-34s %s'
              % (finding['level'], finding['field'], finding['detail']))
    print('TONG: %d vi pham' % len(findings))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
