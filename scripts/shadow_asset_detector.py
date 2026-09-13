#!/usr/bin/env python3
"""
SHADOW ASSET DETECTOR (viết lại ở Sprint 6.1)

Shadow asset = thiết bị đang hiện diện trên mạng nhưng không có trong kho tài sản.

Bản trước không chạy được vì ba lý do, cả ba đều đã sửa ở đây:

  1. Nó đọc `assets.json` khoá `all_assets`; tệp sống dùng khoá `assets`. Cùng
     đúng một lỗi đã giết `risk_engine.py` ở Sprint 6.
  2. Nó lấy MAC từ chính `assets.json` — nơi không hề có trường `mac`. Nay MAC
     đến từ `arp -a` thật, qua ioc_attribution.arp_devices().
  3. Nó GHI ĐÈ `assets.json` bằng open(w) không atomic, tức là biến mình thành
     writer thứ hai của tệp đó. Nay nó chỉ ghi `shadow_assets.json`.

Hai loại shadow được phân biệt rõ, vì hai loại này đòi hai hành động khác nhau:

  UNKNOWN_DEVICE  - ARP thấy, kho tài sản không có. Thiết bị lạ trong mạng.
  UNVERIFIED_L2   - kho tài sản có, ARP không thấy. Không xác minh được ở lớp 2.

Loại thứ nhất là mối lo an ninh. Loại thứ hai thường chỉ là máy đang tắt — nên
nó KHÔNG được báo ở mức cao, dù bản cũ từng gắn cờ y hệt nhau.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from state_manager import write_state_atomic
import ioc_attribution

DETECTOR_VERSION = '2.0.0'


class ShadowAssetDetector:

    def __init__(self):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.assets_file = self.state_dir / 'assets.json'
        self.shadow_log_file = self.state_dir / 'shadow_assets.json'
        self.inventory = {}
        self.arp = {}
        self.notes = []

    def load_inputs(self):
        """Nạp kho tài sản và bảng ARP. Thiếu một trong hai vẫn chạy được."""
        if self.assets_file.exists():
            try:
                with open(self.assets_file, encoding='utf-8') as f:
                    data = json.load(f)
                # Chấp nhận cả hai schema đang tồn tại; ưu tiên schema sống.
                assets = data.get('assets') or data.get('all_assets') or []
                self.inventory = dict(
                    (a['ip'], a) for a in assets if a.get('ip')
                )
            except (ValueError, OSError) as exc:
                self.notes.append('Không đọc được assets.json: {}'.format(exc))
        else:
            self.notes.append('assets.json không tồn tại — không có đường cơ sở.')

        self.arp = ioc_attribution.arp_devices()
        if not self.arp:
            self.notes.append(
                'arp -a không trả về thiết bị nào. Không phát hiện được thiết bị '
                'lạ ở lớp 2 trong chu kỳ này.'
            )

    def detect(self):
        """Đối chiếu ARP với kho tài sản."""
        shadows = []

        # (1) ARP thấy nhưng kho không có → thiết bị lạ.
        for ip in sorted(self.arp):
            if ip in self.inventory:
                continue
            device = self.arp[ip]
            shadows.append({
                'ip': ip,
                'mac': device['mac'],
                'hostname': 'Unknown',
                'type': 'Unknown',
                'shadow_class': 'UNKNOWN_DEVICE',
                'severity': 'HIGH',
                'confidence': 'HIGH',
                'trust_score': 0,
                'detected_at': datetime.now().isoformat(),
                'detection_method': 'ARP',
                'reason': 'Thiết bị trả lời ARP nhưng không có trong kho tài sản',
                'evidence': {
                    'arp_entry': '{} -> {} ({})'.format(ip, device['mac'],
                                                        device['type']),
                    'in_inventory': False,
                },
                'recommended_action': 'Quét Nessus có mục tiêu vào {}'.format(ip),
            })

        # (2) Kho có nhưng ARP không thấy → chưa xác minh được ở lớp 2.
        #     Máy tắt cũng rơi vào đây, nên mức độ để thấp một cách có chủ ý.
        for ip in sorted(self.inventory):
            if ip in self.arp:
                continue
            asset = self.inventory[ip]
            shadows.append({
                'ip': ip,
                'mac': 'Unknown',
                'hostname': asset.get('hostname', ip),
                'type': asset.get('device_type') or asset.get('type', 'Unknown'),
                'shadow_class': 'UNVERIFIED_L2',
                'severity': 'LOW',
                'confidence': 'LOW',
                'trust_score': None,
                'detected_at': datetime.now().isoformat(),
                'detection_method': 'inventory-vs-ARP',
                'reason': ('Có trong kho tài sản nhưng không trả lời ARP — '
                           'không xác minh được MAC ở lớp 2 (máy tắt cũng cho '
                           'kết quả này)'),
                'evidence': {
                    'arp_entry': None,
                    'in_inventory': True,
                    'last_seen': asset.get('last_seen'),
                },
                'recommended_action': 'Xác minh thiết bị còn hoạt động trước khi điều tra',
            })

        return shadows

    def build_report(self, shadows):
        unknown = [s for s in shadows if s['shadow_class'] == 'UNKNOWN_DEVICE']
        unverified = [s for s in shadows if s['shadow_class'] == 'UNVERIFIED_L2']

        return {
            'scan_time': datetime.now().isoformat(),
            'detector': 'shadow_asset_detector',
            'detector_version': DETECTOR_VERSION,
            'data_source': ioc_attribution.SOURCE_OBSERVED,
            'method': 'arp -a đối chiếu state/assets.json',
            'total_assets': len(self.inventory),
            'arp_devices_seen': len(self.arp),
            'shadows_detected': len(unknown),
            'unverified_count': len(unverified),
            'by_class': {
                'UNKNOWN_DEVICE': len(unknown),
                'UNVERIFIED_L2': len(unverified),
            },
            'notes': self.notes,
            # `shadows` chỉ chứa thiết bị lạ thật sự — đây là mảng mà
            # correlation_engine và portal đọc, nên không trộn nhiễu vào.
            'shadows': unknown,
            'unverified_assets': unverified,
        }

    def run(self):
        self.load_inputs()
        shadows = self.detect()
        report = self.build_report(shadows)
        write_state_atomic(self.shadow_log_file, report, indent=2)
        return report


def main():
    detector = ShadowAssetDetector()
    report = detector.run()
    print(json.dumps({
        'status': 'success',
        'total_assets': report['total_assets'],
        'arp_devices_seen': report['arp_devices_seen'],
        'shadows_detected': report['shadows_detected'],
        'unverified_count': report['unverified_count'],
        'notes': report['notes'],
    }, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == '__main__':
    main()
