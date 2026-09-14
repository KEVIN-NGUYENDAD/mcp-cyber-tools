#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASSET STORE (Sprint 11: assets.json Consolidation)

Lớp DUY NHẤT được phép biết `state/assets.json` có hình dạng gì.

Vì sao phải có lớp này
----------------------
`assets.json` từng có hai lược đồ sống song song:

    extract_asset_intelligence.py  ghi khoá `assets`
    asset_builder.py               đọc/ghi khoá `all_assets`

Hai khoá, hai bộ ghi, một tệp. Người thắng là người ghi sau cùng, và từ lúc
`extract_asset_intelligence.py` được đưa vào pipeline thì `all_assets` không còn
tồn tại trong tệp nữa.

Nhưng hỏng hóc không hiện ra như một lỗi. Nó hiện ra như **sự yên lặng**:

    asset_manager.py --list-all  ->  "No assets found"
    asset_manager.py --health    ->  "[OK] No assets with risk score >= 50"

Mạng có 11 thiết bị. Dòng thứ hai in chữ `[OK]` và in nó CHÍNH VÌ không đọc
được gì. Một tình trạng sức khoẻ xanh suy ra từ một lần đọc trượt lược đồ —
đọc y hệt một mạng thật sự sạch.

Thủ phạm không phải cái tên khoá. Thủ phạm là dòng này, lặp ở mọi nơi tiêu thụ:

    data.get('all_assets', [])

Giá trị mặc định `[]` biến "lược đồ sai" thành "không có tài sản nào". Đó là
cùng một cái bẫy EMPTY-vs-BLIND mà Sprint 8-9 đã gỡ cho cảm biến, chỉ khác là
lần này nó nằm ở tầng tệp state.

Hợp đồng
--------
- `assets` là khoá chính thức. `all_assets` là di sản, CHỈ đọc, và mỗi lần đọc
  trúng nó đều được đánh dấu để không ai quên nó vẫn còn đó.
- Đọc trượt lược đồ thì NÉM LỖI, không trả về danh sách rỗng. Rỗng phải có
  nghĩa là "đã đọc được, không có tài sản nào" — không bao giờ mang nghĩa khác.
- Mọi lần ghi đều đi qua `write_assets()`, nên tệp không thể mọc thêm lược đồ
  thứ hai lần nữa.
"""

from __future__ import print_function

import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(PROJECT_ROOT, 'state')
ASSETS_FILE = os.path.join(STATE_DIR, 'assets.json')

CANONICAL_KEY = 'assets'
LEGACY_KEY = 'all_assets'

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from state_manager import write_state_atomic
except ImportError:  # pragma: no cover - chỉ xảy ra khi chạy lẻ ngoài repo
    write_state_atomic = None


class AssetStoreError(Exception):
    """Không đọc/ghi được kho tài sản. Người gọi PHẢI xử lý, không được nuốt.

    Cố ý không có giá trị mặc định đi kèm: mọi giá trị mặc định ở đây đều sẽ bị
    một nơi nào đó hiểu nhầm thành "mạng sạch".
    """


def _load_raw(path=None):
    path = path or ASSETS_FILE
    if not os.path.exists(path):
        raise AssetStoreError('Không tìm thấy %s — chưa chạy '
                              'extract_asset_intelligence.py lần nào?' % path)
    try:
        with open(path, 'r') as handle:
            return json.load(handle)
    except ValueError as error:
        raise AssetStoreError('%s không phải JSON hợp lệ: %s' % (path, error))
    except (IOError, OSError) as error:
        raise AssetStoreError('Không đọc được %s: %s' % (path, error))


def read_assets(path=None):
    """Danh sách tài sản, hoặc ném AssetStoreError. Không bao giờ đoán.

    Trả về: (assets, meta) với meta gồm timestamp, khoá đã dùng, và cờ legacy.
    """
    data = _load_raw(path)
    if not isinstance(data, dict):
        raise AssetStoreError('assets.json phải là một object, đang là %s'
                              % type(data).__name__)

    # Cả hai khoá cùng có mặt = đúng cái trạng thái Sprint 11 vừa dẹp. Chọn đại
    # một khoá ở đây là cách hỏng cũ quay lại: nửa số nơi tiêu thụ đọc khoá này,
    # nửa kia đọc khoá kia, và không ai thấy gì bất thường cho tới khi hai con số
    # lệch nhau trong một báo cáo.
    if CANONICAL_KEY in data and LEGACY_KEY in data:
        raise AssetStoreError(
            'assets.json có CẢ HAI khoá "%s" (%s mục) và "%s" (%s mục). '
            'Đây là lược đồ kép đã bị loại bỏ ở Sprint 11 — một bộ ghi nào đó '
            'đang viết sai. Sửa bộ ghi đó, đừng chọn một khoá ở đây.'
            % (CANONICAL_KEY, len(data.get(CANONICAL_KEY) or []),
               LEGACY_KEY, len(data.get(LEGACY_KEY) or [])))

    if CANONICAL_KEY in data:
        key = CANONICAL_KEY
    elif LEGACY_KEY in data:
        key = LEGACY_KEY
    else:
        # Đây chính là chỗ ngày xưa lặng lẽ trả về [].
        raise AssetStoreError(
            'assets.json không có khoá "%s" (cũng không có "%s" di sản). '
            'Các khoá hiện có: %s. Đây là lược đồ sai, KHÔNG phải mạng rỗng.'
            % (CANONICAL_KEY, LEGACY_KEY, ', '.join(sorted(data.keys())) or '(không có)'))

    assets = data.get(key)
    if assets is None:
        assets = []
    if not isinstance(assets, list):
        raise AssetStoreError('assets.json khoá "%s" phải là list, đang là %s'
                              % (key, type(assets).__name__))

    meta = {
        'key_used': key,
        'legacy': key == LEGACY_KEY,
        'timestamp': data.get('timestamp'),
        'total_assets': data.get('total_assets'),
        'path': path or ASSETS_FILE,
    }
    return assets, meta


def read_assets_safe(path=None):
    """Cho người gọi không được phép chết. Trả về (assets, meta, error).

    Khác `read_assets` ở chỗ không ném — nhưng KHÁC HẲN cách cũ ở chỗ khi lỗi
    thì `error` có giá trị, và người gọi bắt buộc phải nhìn thấy nó trước khi
    kết luận bất cứ điều gì từ danh sách rỗng.
    """
    try:
        assets, meta = read_assets(path)
        return assets, meta, None
    except AssetStoreError as error:
        return [], {'key_used': None, 'legacy': False, 'path': path or ASSETS_FILE}, str(error)


def write_assets(assets, extra=None, path=None):
    """Ghi kho tài sản. Đường ghi DUY NHẤT, và luôn ghi khoá chính thức.

    `extra` để gắn thêm trường cấp cao (ví dụ `trust_scored_at`). Nó không được
    phép ghi đè `assets`/`all_assets`: cửa duy nhất tạo ra lược đồ thứ hai.
    """
    if not isinstance(assets, list):
        raise AssetStoreError('write_assets cần một list, nhận %s'
                              % type(assets).__name__)

    payload = {
        'timestamp': datetime.now().isoformat(),
        'total_assets': len(assets),
        CANONICAL_KEY: assets,
    }
    for key, value in (extra or {}).items():
        if key in (CANONICAL_KEY, LEGACY_KEY):
            raise AssetStoreError(
                'Không được ghi khoá "%s" qua `extra` — đó là cách lược đồ thứ '
                'hai đã sinh ra lần trước.' % key)
        payload[key] = value

    target = path or ASSETS_FILE
    if write_state_atomic is None:
        raise AssetStoreError('state_manager.write_state_atomic không khả dụng')
    write_state_atomic(target, payload, indent=2)
    return payload


def describe(path=None):
    """Kho tài sản đang ở tình trạng nào — cho CLI và cho kiểm định."""
    assets, meta, error = read_assets_safe(path)
    return {
        'ok': error is None,
        'error': error,
        'count': len(assets),
        'key_used': meta.get('key_used'),
        'legacy_schema': meta.get('legacy'),
        'timestamp': meta.get('timestamp'),
        'trust_scored': sum(1 for a in assets
                            if isinstance(a.get('trust_score'), (int, float))),
        'path': meta.get('path'),
    }


def main():
    info = describe()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0 if info['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
