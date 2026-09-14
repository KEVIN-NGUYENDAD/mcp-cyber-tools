#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRUST SCORE ENGINE (Sprint 11: assets.json Consolidation)

Gắn `trust_score` cho từng tài sản trong `state/assets.json`.

Hai thứ đã hỏng trước Sprint 11
-------------------------------
1. **Sai lược đồ.** File này đọc khoá `all_assets`; tệp sống dùng khoá `assets`.
   Nên nó thoát ngay ở dòng đầu với "Error: Invalid assets.json format", và
   `trust_score` chưa bao giờ tồn tại trong tệp. Nay mọi truy cập đi qua
   `asset_store.py` — lớp duy nhất biết tệp có hình dạng gì.

2. **Chấm điểm trên những trường không tồn tại.** Kể cả khi lược đồ đúng, bốn
   trong năm thành phần vẫn hỏng: nó đọc `mac`, `status`, `type`, `risk_score`
   — không trường nào có trong lược đồ chính thức (`ip`, `hostname`, `os`,
   `device_type`, `vulnerability_count`, `critical`/`high`/`medium`/`low`).

   Cái này nguy hiểm hơn hỏng số 1. Hỏng số 1 im lặng và không ghi gì. Hỏng số 2
   thì VẪN RA SỐ: MAC không có -> 0/40 điểm, `status` không có -> 0/10 điểm, và
   mọi thiết bị hoàn toàn bình thường đều nhận về một điểm tin cậy thấp trông
   rất thuyết phục. Đây đúng là lỗi mà Sprint 6 đã gặp ở `shadow_asset_detector.py`
   (lấy MAC từ nơi không có MAC), chỉ đổi chỗ.

Cách sửa: mỗi thành phần tự khai báo có QUAN SÁT ĐƯỢC hay không
---------------------------------------------------------------
Thành phần không quan sát được thì rời khỏi CẢ tử số lẫn MẪU SỐ, thay vì âm
thầm đóng góp 0 điểm. Điểm cuối là phần trăm trên số điểm THỰC SỰ chấm được, và
`trust_basis` ghi lại chấm được bao nhiêu trên bao nhiêu.

Không quan sát được không phải là điểm xấu. Một chiếc điện thoại bình thường và
một thiết bị lạ trông giống hệt nhau khi ta chưa nhìn — và cách duy nhất để
không nhầm hai thứ đó là nói thẳng ra rằng ta chưa nhìn.
"""

from __future__ import print_function

import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from state_manager import write_state_atomic  # noqa: E402
import asset_store  # noqa: E402

TRUST_HISTORY_FILE = os.path.join(asset_store.STATE_DIR, 'asset_trust_history.json')

# Dưới ngưỡng này thì điểm không đủ cơ sở để mang một nhãn nào cả.
MIN_BASIS_POINTS = 40


def _component(name, score, maximum, observable, reason):
    return {'name': name, 'score': score, 'max': maximum,
            'observable': observable, 'reason': reason}


class TrustScoreEngine(object):

    def __init__(self):
        self.trust_history_file = TRUST_HISTORY_FILE

    # -- lịch sử ----------------------------------------------------------

    def load_trust_history(self):
        if not os.path.exists(self.trust_history_file):
            return {}
        try:
            with open(self.trust_history_file, 'r') as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (ValueError, IOError, OSError):
            # Lịch sử hỏng thì coi như chưa có lịch sử — nhưng KHÔNG im lặng.
            print('[WARN] asset_trust_history.json không đọc được, '
                  'chấm lại từ đầu', file=sys.stderr)
            return {}

    # -- từng thành phần --------------------------------------------------

    def mac_consistency(self, asset, entry):
        """40 điểm: MAC có ổn định không.

        Lược đồ chính thức KHÔNG có trường `mac`. Trả về không-quan-sát-được
        thay vì 0: một thiết bị không có MAC trong hồ sơ không phải một thiết bị
        đáng ngờ, nó là một thiết bị ta chưa hỏi đúng nguồn.
        """
        mac = (asset.get('mac') or '').strip()
        if not mac or mac.lower() == 'unknown':
            return _component('mac_consistency', 0, 40, False,
                              'assets.json không mang trường MAC')
        changes = entry.get('mac_changes', 0)
        if changes == 0:
            return _component('mac_consistency', 40, 40, True, 'MAC ổn định')
        if changes == 1:
            return _component('mac_consistency', 30, 40, True, 'đổi MAC 1 lần')
        if changes <= 3:
            return _component('mac_consistency', 20, 40, True,
                              'đổi MAC %d lần' % changes)
        return _component('mac_consistency', max(0, 40 - changes * 5), 40, True,
                          'đổi MAC %d lần' % changes)

    def ip_stability(self, asset, entry):
        """20 điểm: IP có ổn định không. Cần ít nhất 2 lần quan sát mới có nghĩa."""
        observations = entry.get('observations', 0)
        if observations < 2:
            return _component('ip_stability', 0, 20, False,
                              'mới thấy lần đầu — chưa có gì để so')
        changes = entry.get('ip_changes', 0)
        if changes == 0:
            return _component('ip_stability', 20, 20, True, 'IP ổn định')
        if changes == 1:
            return _component('ip_stability', 15, 20, True, 'đổi IP 1 lần')
        if changes <= 2:
            return _component('ip_stability', 10, 20, True,
                              'đổi IP %d lần' % changes)
        return _component('ip_stability', max(0, 20 - changes * 3), 20, True,
                          'đổi IP %d lần' % changes)

    def identification(self, asset, entry):
        """15 điểm: máy có được nhận dạng rõ không.

        Đọc `device_type` (lược đồ chính thức), không phải `type` (bản cũ đọc
        trường này và không bao giờ tìm thấy).
        """
        device_type = (asset.get('device_type') or '').strip()
        os_name = (asset.get('os') or '').strip()
        known_type = device_type and device_type.lower() != 'unknown'
        known_os = os_name and os_name.lower() != 'unknown'

        if not known_type and not known_os:
            return _component('identification', 0, 15, True,
                              'không nhận dạng được cả loại lẫn hệ điều hành')
        if known_type and known_os:
            return _component('identification', 15, 15, True,
                              '%s / %s' % (device_type, os_name))
        return _component('identification', 9, 15, True,
                          'nhận dạng một phần (%s)' % (device_type or os_name))

    def vulnerability_trend(self, asset, entry):
        """15 điểm: số lỗ hổng đang ổn định hay đang xấu đi.

        So sánh với lịch sử CỦA CHÍNH NÓ, không tự tính một điểm rủi ro mới:
        `calculate_risk_score.py` là nơi duy nhất được phép chấm rủi ro, và repo
        này đã trả giá ba lần cho việc có hai nơi trả lời cùng một câu hỏi.
        """
        history = entry.get('vulnerability_counts', [])
        if not history:
            return _component('vulnerability_trend', 0, 15, False,
                              'chưa có lần quét trước để so')
        current = asset.get('vulnerability_count', 0) or 0
        window = history[-10:]
        average = sum(window) / float(len(window))
        if current <= average * 1.1:
            return _component('vulnerability_trend', 15, 15, True,
                              'ổn định hoặc giảm (%d so với TB %.1f)' % (current, average))
        if current <= average * 1.5:
            return _component('vulnerability_trend', 10, 15, True,
                              'tăng nhẹ (%d so với TB %.1f)' % (current, average))
        return _component('vulnerability_trend', 3, 15, True,
                          'tăng mạnh (%d so với TB %.1f)' % (current, average))

    def discovery_consistency(self, asset, entry):
        """10 điểm: có được nhìn thấy đều đặn không. Luôn quan sát được."""
        observations = entry.get('observations', 1)
        if observations >= 10:
            return _component('discovery_consistency', 10, 10, True,
                              '%d lần quan sát' % observations)
        if observations >= 5:
            return _component('discovery_consistency', 8, 10, True,
                              '%d lần quan sát' % observations)
        if observations >= 3:
            return _component('discovery_consistency', 5, 10, True,
                              '%d lần quan sát' % observations)
        return _component('discovery_consistency', 2, 10, True,
                          'mới %d lần quan sát' % observations)

    # -- tổng hợp ---------------------------------------------------------

    def score_asset(self, asset, entry):
        components = [
            self.mac_consistency(asset, entry),
            self.ip_stability(asset, entry),
            self.identification(asset, entry),
            self.vulnerability_trend(asset, entry),
            self.discovery_consistency(asset, entry),
        ]
        usable = [c for c in components if c['observable']]
        basis = sum(c['max'] for c in usable)
        earned = sum(c['score'] for c in usable)

        if basis == 0:
            return None, 'UNSCORED', components, basis

        score = int(round(100.0 * earned / basis))
        # Một điểm 100 chấm trên 10 điểm khả dụng không cùng nghĩa với một điểm
        # 100 chấm trên 100. Nhãn phải nói ra điều đó, không phải chỉ con số.
        if basis < MIN_BASIS_POINTS:
            return score, 'INSUFFICIENT_DATA', components, basis
        return score, self.trust_level(score), components, basis

    @staticmethod
    def trust_level(score):
        if score >= 85:
            return 'CRITICAL_ASSET'
        if score >= 70:
            return 'TRUSTED'
        if score >= 50:
            return 'MONITORED'
        if score >= 30:
            return 'SUSPICIOUS'
        return 'UNKNOWN'

    # -- chạy -------------------------------------------------------------

    def run(self):
        try:
            assets, meta = asset_store.read_assets()
        except asset_store.AssetStoreError as error:
            print('[FAIL] %s' % error, file=sys.stderr)
            return False

        if meta['legacy']:
            print('[WARN] assets.json vẫn dùng khoá di sản "all_assets"; '
                  'ghi lại bằng khoá chính thức "assets"', file=sys.stderr)

        history = self.load_trust_history()
        now = datetime.now().isoformat()
        levels = {}

        for asset in assets:
            ip = asset.get('ip')
            if not ip:
                continue
            entry = history.setdefault(ip, {
                'mac_changes': 0,
                'ip_changes': 0,
                'first_seen': now,
                'observations': 0,
                'vulnerability_counts': [],
            })
            entry['observations'] = entry.get('observations', 0) + 1
            entry.setdefault('first_seen', now)

            score, level, components, basis = self.score_asset(asset, entry)

            asset['trust_score'] = score
            asset['trust_level'] = level
            asset['trust_basis'] = {
                'points_available': basis,
                'points_possible': 100,
                'unobservable': [c['name'] for c in components if not c['observable']],
                'components': components,
            }
            asset['first_seen'] = entry.get('first_seen', now)
            asset['trust_scored_at'] = now
            levels[level] = levels.get(level, 0) + 1

            # Ghi lịch sử SAU khi chấm: lần quét này không được tự làm bằng
            # chứng cho chính nó.
            counts = entry.setdefault('vulnerability_counts', [])
            counts.append(asset.get('vulnerability_count', 0) or 0)
            del counts[:-20]

        try:
            asset_store.write_assets(assets, extra={'trust_scored_at': now})
        except asset_store.AssetStoreError as error:
            print('[FAIL] không ghi được assets.json: %s' % error, file=sys.stderr)
            return False

        try:
            write_state_atomic(self.trust_history_file, history, indent=2)
        except Exception as error:  # noqa: BLE001 - báo rồi trả False, không nuốt
            print('[FAIL] không ghi được lịch sử tin cậy: %s' % error, file=sys.stderr)
            return False

        scored = sum(1 for a in assets if isinstance(a.get('trust_score'), int))
        print('[OK] Chấm tin cậy cho %d/%d tài sản' % (scored, len(assets)))
        for level in sorted(levels):
            print('     %-18s %d' % (level, levels[level]))
        thin = [a['ip'] for a in assets
                if (a.get('trust_basis') or {}).get('points_available', 0) < MIN_BASIS_POINTS]
        if thin:
            print('     %d tài sản chấm trên dưới %d điểm khả dụng: %s'
                  % (len(thin), MIN_BASIS_POINTS, ', '.join(thin[:5])
                     + ('...' if len(thin) > 5 else '')))
        return True


def main():
    if TrustScoreEngine().run():
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
