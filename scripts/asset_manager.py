#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASSET COMMAND CENTER CLI (Sprint 11: assets.json Consolidation)

Đọc `state/assets.json` qua `asset_store.py` và trả lời các câu hỏi tồn kho.

Vì sao file này phải viết lại
-----------------------------
Bản cũ đọc khoá `all_assets` — khoá mà tệp sống không có. Nó không báo lỗi. Nó
in ra:

    --list-all   ->  "No assets found"
    --risky      ->  "[OK] No assets with risk score >= 50"

trên một mạng có 11 thiết bị. Dòng thứ hai là dòng nguy hiểm: nó in `[OK]` và
in CHÍNH VÌ không đọc được gì. Một lần đọc trượt lược đồ đội lốt một mạng sạch.

Nó còn đọc hàng loạt trường không tồn tại trong lược đồ chính thức: `type`,
`status`, `risk_score`, `mac`, `vulnerabilities{}`. Mỗi trường như vậy lặng lẽ
rơi về giá trị mặc định, và bảng in ra trông đầy đủ trong khi mọi cột đều rỗng.

Ba nguyên tắc của bản mới:
  1. Đọc qua `asset_store` — lược đồ sai thì DỪNG và nói ra, không in `[OK]`.
  2. Chỉ đọc trường có thật: `ip`, `hostname`, `os`, `device_type`,
     `vulnerability_count`, `critical`/`high`/`medium`/`low`/`info`.
  3. Không tự chấm rủi ro. `calculate_risk_score.py` là nơi duy nhất được phép
     làm việc đó; ở đây chỉ đếm lỗ hổng theo mức nghiêm trọng đã có sẵn.
"""

from __future__ import print_function

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import asset_store  # noqa: E402

SHADOW_FILE = os.path.join(asset_store.STATE_DIR, 'shadow_assets.json')


def format_table(headers, rows):
    if not rows:
        return ''
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    sep = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
    out = [sep,
           '| ' + ' | '.join(str(h).ljust(w) for h, w in zip(headers, widths)) + ' |',
           sep]
    for row in rows:
        out.append('| ' + ' | '.join(str(c).ljust(w) for c, w in zip(row, widths)) + ' |')
    out.append(sep)
    return '\n'.join(out)


def severity_total(asset):
    """Số lỗ hổng critical + high. KHÔNG phải điểm rủi ro."""
    return (asset.get('critical', 0) or 0) + (asset.get('high', 0) or 0)


class AssetCommandCenter(object):

    def __init__(self):
        self.assets, self.meta, self.error = asset_store.read_assets_safe()
        if self.error:
            # Dừng ở đây. Mọi lệnh bên dưới nếu chạy tiếp đều sẽ in ra một bảng
            # rỗng hoặc một chữ [OK], và cả hai đều là nói dối.
            print('[FAIL] Không đọc được kho tài sản.', file=sys.stderr)
            print('       %s' % self.error, file=sys.stderr)
            sys.exit(1)
        if self.meta.get('legacy'):
            print('[WARN] assets.json vẫn dùng khoá di sản "all_assets". '
                  'Chạy scripts/asset_builder.py để ghi lại bằng khoá chính thức.',
                  file=sys.stderr)

    # -- trạng thái chấm tin cậy ------------------------------------------

    def trust_note(self):
        """Chưa chấm điểm và điểm bằng 0 là hai chuyện khác nhau."""
        scored = sum(1 for a in self.assets
                     if isinstance(a.get('trust_score'), (int, float)))
        if scored == 0:
            return ('Chưa tài sản nào được chấm tin cậy — '
                    'chạy `python scripts/asset_builder.py`.')
        if scored < len(self.assets):
            return '%d/%d tài sản đã được chấm tin cậy.' % (scored, len(self.assets))
        return None

    @staticmethod
    def trust_cell(asset):
        score = asset.get('trust_score')
        if not isinstance(score, (int, float)):
            return 'chưa chấm'
        basis = (asset.get('trust_basis') or {}).get('points_available')
        # In kèm cơ sở: 82 chấm trên 45 điểm khả dụng không cùng nghĩa với 82
        # chấm trên 100, và một con số trần trụi không nói được điều đó.
        return '%s (/%s đ)' % (score, basis) if basis else str(score)

    # -- lệnh --------------------------------------------------------------

    def list_all(self):
        print('\nTỒN KHO TÀI SẢN — %d thiết bị' % len(self.assets))
        note = self.trust_note()
        if note:
            print('  %s' % note)
        if not self.assets:
            print('  Đọc được assets.json và không có thiết bị nào trong đó.')
            return
        rows = []
        for asset in sorted(self.assets, key=lambda a: a.get('ip', '')):
            rows.append([
                asset.get('ip', '?'),
                asset.get('hostname', '-'),
                asset.get('device_type', '-'),
                asset.get('os', '-'),
                asset.get('vulnerability_count', 0),
                severity_total(asset),
                self.trust_cell(asset),
                asset.get('trust_level', '-'),
            ])
        print(format_table(
            ['IP', 'Hostname', 'Loại', 'OS', 'Lỗ hổng', 'Crit+High', 'Tin cậy', 'Mức'],
            rows))

    def list_shadow(self):
        """Shadow đọc từ shadow_assets.json — nguồn duy nhất ghi nó."""
        if not os.path.exists(SHADOW_FILE):
            print('[FAIL] Không tìm thấy %s — chưa chạy shadow_asset_detector.py?'
                  % SHADOW_FILE, file=sys.stderr)
            sys.exit(1)
        try:
            with open(SHADOW_FILE, 'r') as handle:
                data = json.load(handle)
        except (ValueError, IOError, OSError) as error:
            print('[FAIL] Không đọc được %s: %s' % (SHADOW_FILE, error), file=sys.stderr)
            sys.exit(1)

        shadows = data.get('shadows') or []
        unverified = data.get('unverified_assets') or []

        print('\nTHIẾT BỊ LẠ — %d phát hiện, %d chưa xác minh được'
              % (len(shadows), len(unverified)))
        print('  Nguồn: %s (%s)' % (data.get('method', '?'), data.get('scan_time', '?')))

        if shadows:
            print(format_table(
                ['IP', 'MAC', 'Hostname', 'Phân loại'],
                [[s.get('ip', '?'), s.get('mac', '-'), s.get('hostname', '-'),
                  s.get('classification', '-')] for s in shadows]))
        else:
            print('  Không có thiết bị lạ nào trong lần quét gần nhất.')

        if unverified:
            # "Chưa xác minh" KHÔNG phải "sạch". Nói rõ, đừng gộp vào số 0 ở trên.
            print('\n  %d thiết bị trong tồn kho không đối chiếu được ở tầng 2 '
                  '(không có MAC để so) — chưa xác minh, không phải đã loại trừ:'
                  % len(unverified))
            for item in unverified[:10]:
                print('    %-16s %s' % (item.get('ip', '?'), item.get('hostname', '-')))
            if len(unverified) > 10:
                print('    ... và %d thiết bị nữa' % (len(unverified) - 10))

    def trust_report(self):
        note = self.trust_note()
        print('\nBÁO CÁO TIN CẬY')
        if note:
            print('  %s' % note)
        scored = [a for a in self.assets
                  if isinstance(a.get('trust_score'), (int, float))]
        if not scored:
            return

        buckets = {}
        for asset in scored:
            buckets.setdefault(asset.get('trust_level', 'UNKNOWN'), []).append(asset)

        for level in sorted(buckets):
            group = buckets[level]
            print('\n  %s (%d)' % (level, len(group)))
            for asset in sorted(group, key=lambda a: a.get('trust_score', 0), reverse=True):
                basis = (asset.get('trust_basis') or {})
                missing = basis.get('unobservable') or []
                print('    %-16s %-18s %3s điểm trên %s điểm khả dụng%s' % (
                    asset.get('ip', '?'), asset.get('hostname', '-')[:18],
                    asset.get('trust_score'), basis.get('points_available', '?'),
                    ('  [không quan sát được: %s]' % ', '.join(missing)) if missing else ''))

        values = [a['trust_score'] for a in scored]
        print('\n  Trung bình: %.1f  |  Trung vị: %s'
              % (sum(values) / float(len(values)), sorted(values)[len(values) // 2]))
        thin = [a for a in scored
                if (a.get('trust_basis') or {}).get('points_available', 0) < 40]
        if thin:
            print('  %d/%d tài sản chấm trên dưới 40 điểm khả dụng — điểm của chúng '
                  'nói rất ít.' % (len(thin), len(scored)))

    def by_type(self, wanted):
        matched = [a for a in self.assets
                   if (a.get('device_type') or 'Unknown').lower() == wanted.lower()]
        print('\nTÀI SẢN LOẠI "%s" — %d thiết bị' % (wanted, len(matched)))
        if not matched:
            kinds = sorted(set((a.get('device_type') or 'Unknown') for a in self.assets))
            print('  Không có. Các loại đang có: %s' % ', '.join(kinds))
            return
        print(format_table(
            ['IP', 'Hostname', 'OS', 'Lỗ hổng', 'Tin cậy'],
            [[a.get('ip', '?'), a.get('hostname', '-'), a.get('os', '-'),
              a.get('vulnerability_count', 0), self.trust_cell(a)] for a in matched]))

    def risky(self, threshold):
        """Tài sản có >= threshold lỗ hổng critical+high.

        Bản cũ lọc theo `risk_score` — trường không tồn tại — nên luôn ra rỗng
        và luôn in `[OK]`. Ở đây ngưỡng áp lên SỐ LỖ HỔNG thật, và khi không có
        gì vượt ngưỡng thì câu trả lời nói rõ nó dựa trên bao nhiêu tài sản.
        """
        risky = [a for a in self.assets if severity_total(a) >= threshold]
        print('\nTÀI SẢN CÓ >= %d LỖ HỔNG CRITICAL+HIGH' % threshold)
        if not risky:
            print('  Không có, trên %d tài sản đã đọc được.' % len(self.assets))
            return
        print(format_table(
            ['IP', 'Hostname', 'Loại', 'Critical', 'High', 'Tổng lỗ hổng', 'Tin cậy'],
            [[a.get('ip', '?'), a.get('hostname', '-'), a.get('device_type', '-'),
              a.get('critical', 0), a.get('high', 0),
              a.get('vulnerability_count', 0), self.trust_cell(a)]
             for a in sorted(risky, key=severity_total, reverse=True)]))

    def health_check(self):
        print('\n' + '=' * 66)
        print('TÌNH TRẠNG TỒN KHO TÀI SẢN')
        print('=' * 66)
        print('\nNguồn: %s' % self.meta.get('path'))
        print('Cập nhật: %s' % (self.meta.get('timestamp') or 'không rõ'))
        print('Tổng: %d thiết bị' % len(self.assets))

        by_type = {}
        for asset in self.assets:
            key = asset.get('device_type') or 'Unknown'
            by_type[key] = by_type.get(key, 0) + 1
        for key in sorted(by_type):
            print('  %-16s %d' % (key, by_type[key]))

        vulnerable = [a for a in self.assets if severity_total(a) > 0]
        print('\nLỗ hổng:')
        print('  Tài sản có critical/high : %d' % len(vulnerable))
        print('  Tổng critical            : %d'
              % sum(a.get('critical', 0) or 0 for a in self.assets))
        print('  Tổng high                : %d'
              % sum(a.get('high', 0) or 0 for a in self.assets))

        print('\nTin cậy:')
        note = self.trust_note()
        if note:
            print('  %s' % note)
        else:
            levels = {}
            for asset in self.assets:
                levels[asset.get('trust_level', '-')] = \
                    levels.get(asset.get('trust_level', '-'), 0) + 1
            for level in sorted(levels):
                print('  %-18s %d' % (level, levels[level]))

        # Độ phủ dữ liệu: trường nào thực sự có mặt. Một tồn kho đầy thiết bị mà
        # trống trường thì vẫn là một tồn kho không dùng được, và chỗ duy nhất
        # điều đó lộ ra là ở đây.
        print('\nĐộ phủ trường:')
        total = len(self.assets) or 1
        for field in ('hostname', 'os', 'device_type', 'mac', 'vulnerability_count'):
            present = sum(1 for a in self.assets
                          if a.get(field) not in (None, '', 'Unknown', 'unknown'))
            print('  %-20s %3d/%d  (%.0f%%)'
                  % (field, present, len(self.assets), 100.0 * present / total))


def main():
    parser = argparse.ArgumentParser(description='Asset Command Center CLI')
    parser.add_argument('--list-all', action='store_true', help='Liệt kê mọi tài sản')
    parser.add_argument('--list-shadow', action='store_true', help='Thiết bị lạ')
    parser.add_argument('--trust-report', action='store_true', help='Báo cáo tin cậy')
    parser.add_argument('--by-type', metavar='TYPE', help='Lọc theo device_type')
    parser.add_argument('--risky', type=int, metavar='N', nargs='?', const=1,
                        help='Tài sản có >= N lỗ hổng critical+high (mặc định 1)')
    parser.add_argument('--health', action='store_true', help='Tình trạng tồn kho')
    args = parser.parse_args()

    center = AssetCommandCenter()

    if args.list_all:
        center.list_all()
    elif args.list_shadow:
        center.list_shadow()
    elif args.trust_report:
        center.trust_report()
    elif args.by_type:
        center.by_type(args.by_type)
    elif args.risky is not None:
        center.risky(args.risky)
    elif args.health:
        center.health_check()
    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
