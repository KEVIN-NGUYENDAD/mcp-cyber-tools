#!/usr/bin/env python3
"""
IOC ATTRIBUTION (Sprint 6.1)

Sprint 5 để lại một lỗ hổng: các IOC từ hunting không gắn được với thiết bị nào,
nên correlation Rule 1 luôn trả về 0. Module này cung cấp hợp đồng dữ liệu chung
để bốn script hunting khai báo *nguồn gốc* và *phạm vi* của mỗi chỉ báo.

Nguyên tắc nền: KHÔNG gắn IOC mô phỏng vào IP thật.

Gắn một chỉ báo giả lập vào 192.168.0.10 sẽ tạo ra "bằng chứng" rằng thiết bị đó
bị xâm nhập. Xuống hạ nguồn, correlation engine nâng nó thành CRITICAL, risk
engine cộng điểm, Telegram bắn cảnh báo, và người trực ca đi cô lập một máy hoàn
toàn bình thường. Vì vậy ở đây tách bạch hai khái niệm:

  hunt_scope        - phạm vi cuộc săn ĐÃ CHẠY. Sự thật, luôn điền được.
  affected_systems  - nơi CÓ bằng chứng. Chỉ điền khi bằng chứng có thật.

Chỉ báo `SIMULATED` có hunt_scope nhưng affected_systems rỗng — và đó là kết quả
đúng, không phải lỗi cần vá.
"""

import json
import subprocess
from pathlib import Path

# Nguồn gốc dữ liệu của một chỉ báo
SOURCE_SIMULATED = 'SIMULATED'       # nội dung hardcode trong script, không quan sát được
SOURCE_DERIVED = 'DERIVED'           # suy ra từ state file có thật
SOURCE_OBSERVED = 'OBSERVED'         # đọc trực tiếp từ telemetry của máy
SOURCE_LIVE = 'LIVE_OBSERVED'        # thu qua MCP tool, chạy trên máy thật, ngay lúc này

# Một cuộc săn không quan sát được KHÁC với một cuộc săn không thấy gì.
COVERAGE_OBSERVED = 'OBSERVED'           # đã đọc được nguồn, kết quả đáng tin
COVERAGE_NOT_OBSERVABLE = 'NOT_OBSERVABLE'   # không đọc được nguồn - chưa kết luận được gì

STATE_DIR = Path(__file__).parent.parent / 'state'


def load_inventory_ips():
    """Danh sách IP trong kho tài sản (schema sống: khoá 'assets')."""
    fp = STATE_DIR / 'assets.json'
    if not fp.exists():
        return []
    try:
        with open(fp, encoding='utf-8') as f:
            data = json.load(f)
    except (ValueError, OSError):
        return []

    # Chấp nhận cả hai schema đang tồn tại trong repo. Đây không phải là chỗ để
    # sửa chuyện đó, nhưng cũng không phải chỗ để chết vì nó.
    assets = data.get('assets') or data.get('all_assets') or []
    ips = []
    for asset in assets:
        ip = asset.get('ip')
        if ip and ip not in ips:
            ips.append(ip)
    return ips


def arp_devices():
    """Bảng ARP thật: {ip: {'mac':..., 'type':...}}. Rỗng nếu arp không chạy được."""
    try:
        result = subprocess.run(
            ['arp', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0:
        return {}

    import re
    entry_re = re.compile(
        r'^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+'
        r'([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})\s+(\w+)\s*$'
    )
    ignore_mac = set(['ff-ff-ff-ff-ff-ff', '00-00-00-00-00-00'])
    devices = {}
    text = result.stdout.decode('utf-8', 'replace')
    for line in text.splitlines():
        match = entry_re.match(line)
        if not match:
            continue
        ip, mac, entry_type = match.groups()
        mac = mac.lower()
        if ip.startswith('224.') or ip.startswith('239.') \
                or ip == '255.255.255.255' or mac in ignore_mac:
            continue
        devices[ip] = {'mac': mac, 'type': entry_type.lower()}
    return devices


def resolve_hunt_scope():
    """Phạm vi mà một cuộc săn cấp host bao phủ, kèm lý do vì sao biết được.

    Trả về dict để ghi thẳng vào báo cáo hunting — hạ nguồn cần biết cuộc săn
    *đã nhìn vào đâu*, kể cả khi nó không tìm thấy gì.
    """
    inventory = load_inventory_ips()
    arp = arp_devices()
    live = [ip for ip in inventory if ip in arp]

    return {
        'inventory_ips': inventory,
        'arp_visible_ips': sorted(arp.keys()),
        'in_inventory_and_live': live,
        'resolved_at_layer2': len(arp) > 0,
        'method': 'assets.json + arp -a',
    }


def attribute(data_source, affected_systems=None, method=None,
              confidence=None, reason=None):
    """Khối attribution chuẩn gắn vào mỗi chỉ báo.

    `affected_systems` chỉ được điền khi có bằng chứng thật trỏ tới thiết bị đó.
    Với SIMULATED, hàm này cưỡng chế rỗng — gọi sai cũng không tạo ra quy kết giả.
    """
    systems = list(affected_systems or [])
    if data_source == SOURCE_SIMULATED and systems:
        systems = []
        reason = ('Chỉ báo mô phỏng: quy kết thiết bị đã bị loại bỏ để tránh '
                  'tạo bằng chứng giả')

    if not systems and not reason:
        reason = 'Không có bằng chứng gắn với thiết bị cụ thể'

    return {
        'data_source': data_source,
        'affected_systems': systems,
        'attribution': {
            'method': method or ('none' if data_source == SOURCE_SIMULATED
                                 else 'state-correlation'),
            'confidence': confidence or ('NONE' if not systems else 'MEDIUM'),
            'reason': reason,
        },
    }


def apply_to_indicators(indicators, data_source, hunt_scope,
                        affected_key='affected_systems'):
    """Gắn provenance + scope cho cả lô chỉ báo, tại chỗ.

    Giữ nguyên affected_systems mà script đã tự điền (nếu nó là bằng chứng thật),
    nhưng `attribute()` sẽ xoá nếu nguồn là SIMULATED.
    """
    for indicator in indicators:
        existing = indicator.get(affected_key) or indicator.get('affected_assets')
        block = attribute(data_source, affected_systems=existing)
        indicator['data_source'] = block['data_source']
        indicator[affected_key] = block['affected_systems']
        indicator['attribution'] = block['attribution']
        indicator['hunt_scope'] = hunt_scope['in_inventory_and_live']
    return indicators


def coverage_note(data_source, count):
    """Một câu giải thích vì sao lô chỉ báo này quy kết được (hoặc không)."""
    if data_source == SOURCE_SIMULATED:
        return ('{} chỉ báo là dữ liệu MÔ PHỎNG hardcode trong script, không phải '
                'quan sát từ máy thật. Không quy kết thiết bị. Muốn quy kết thật, '
                'hunting phải gọi MCP tool tương ứng.'.format(count))
    return '{} chỉ báo suy ra từ state file có thật.'.format(count)


def local_host_identity():
    """Danh tính máy đang chạy cuộc săn.

    Các cuộc săn host-level (persistence, process, credential) quan sát CHÍNH
    máy này, nên quy kết về nó là sự thật kiểm chứng được - khác hẳn việc gán
    IOC cho một IP nào đó trong mạng.
    """
    import socket
    hostname = 'unknown'
    try:
        hostname = socket.gethostname()
    except Exception:
        pass

    ips = []
    try:
        # Không dùng gethostbyname(hostname): trên Windows nó hay trả 127.0.0.1.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(('8.8.8.8', 80))   # không gửi gói nào, chỉ để lấy route
            ips.append(sock.getsockname()[0])
        finally:
            sock.close()
    except Exception:
        pass

    return {'hostname': hostname, 'ips': ips}


def live_scope(coverage=COVERAGE_OBSERVED, source_detail=None, reason=None):
    """Phạm vi của một cuộc săn LIVE trên máy cục bộ."""
    identity = local_host_identity()
    scope = resolve_hunt_scope()
    scope['local_host'] = identity
    scope['in_inventory_and_live'] = identity['ips'] or scope['in_inventory_and_live']
    scope['coverage'] = coverage
    scope['coverage_reason'] = reason
    scope['source_detail'] = source_detail
    return scope


def coverage_block(observable, source, reason=None):
    """Khối coverage gắn ở cấp báo cáo, để hạ nguồn biết im lặng nghĩa là gì."""
    return {
        'observable': bool(observable),
        'status': COVERAGE_OBSERVED if observable else COVERAGE_NOT_OBSERVABLE,
        'source': source,
        'reason': reason or ('Đã đọc được nguồn' if observable else
                             'Không đọc được nguồn - 0 phát hiện KHÔNG có nghĩa là sạch'),
    }
