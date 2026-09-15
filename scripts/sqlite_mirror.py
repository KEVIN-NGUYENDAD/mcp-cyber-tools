#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLITE MIRROR (Sprint DB-1) — bản sao đọc được bằng SQL của ba tệp state.

    JSON là Source of Truth. Tệp `state/sentinelops.db` là BẢN SAO.

Câu đó không phải một lời hứa trong tài liệu, nó là một ràng buộc có chỗ thi
hành trong mã:

* Bộ này chỉ ĐỌC `state/*.json` và chỉ GHI `sentinelops.db`. Không có đường
  nào đi ngược. Không có hàm nào trong tệp này mở một tệp JSON ở chế độ ghi.
* Mỗi lần chạy là một lần DỰNG LẠI trọn vẹn từng bảng (`DELETE` rồi `INSERT`
  trong cùng một transaction), không phải `INSERT OR REPLACE` chồng lên bản
  cũ. Khác biệt này quan trọng: một bản ghi bị XOÁ khỏi JSON mà vẫn nằm lại
  trong DB thì bản sao đã tự sinh ra dữ liệu, và một truy vấn SQL sẽ đếm nó.
  Dựng lại làm cho "JSON không còn" và "DB không còn" là cùng một sự kiện.

Vì sao có cột `raw_json` bên cạnh các cột đã tách
--------------------------------------------------
Các cột đã tách (`severity`, `trust_score`, ...) là thứ khiến bản sao này có
ích — chúng cho phép `WHERE severity = 'HIGH'`. Nhưng tách cột là một phép
ánh xạ do người viết, và phép ánh xạ nào cũng bỏ sót: `trust_basis` của asset
là một cây năm nhánh, `entities` của finding là một object tự do. Nếu chỉ giữ
cột đã tách thì bản sao lặng lẽ nghèo hơn nguồn.

`raw_json` giữ nguyên văn bản ghi. Nhờ nó, phép kiểm ở dưới so được BYTE chứ
không chỉ so được vài cột mà chính người viết đã chọn ra.

Nhưng GIỮ được không có nghĩa là TRUY VẤN được bằng SQL. SQLite đi kèm Python
3.7.9 trên máy này là 3.31.1, biên dịch không có JSON1 — `json_extract()` ném
`no such function`. Phần nằm ngoài các cột đã tách vẫn lấy ra được, nhưng phải
parse ở phía đọc chứ không lọc được trong câu `WHERE`. Bộ này IN RA khả năng
đó ở đầu báo cáo thay vì để ai đó phát hiện lúc câu truy vấn của họ ném: một
năng lực vắng mặt được khai báo thì khác một năng lực vắng mặt lúc chạy.
(JSON1 bật mặc định từ SQLite 3.38; nâng Python là đủ.)

Vì sao Match % không được tính bằng cách đếm hàng vừa chèn
-----------------------------------------------------------
Cám dỗ rõ ràng: chèn N hàng, `SELECT COUNT(*)` ra N, in `100%`. Con số đó
không kiểm chứng điều gì cả — nó là cùng một biến đếm được in ra hai lần,
luôn luôn xanh, kể cả khi mọi cột đều rỗng.

Nên phép kiểm ở đây mở một KẾT NỐI THỨ HAI ở chế độ chỉ-đọc (`mode=ro`), đọc
ngược từng hàng ra khỏi SQLite, và với mỗi bản ghi JSON kiểm ba điều:

  1. khoá chính của nó có mặt trong DB;
  2. `sha256(raw_json đọc từ DB)` == `sha256(bản ghi tuần tự hoá từ JSON)`;
  3. TỪNG cột đã tách bằng đúng giá trị tương ứng trong JSON.

(2) bắt mất mát trên đường vòng qua SQLite (encoding, cắt cụt). (3) bắt lỗi
ánh xạ cột — loại lỗi mà (2) không thấy, vì `raw_json` vẫn đúng trong khi
`incidents.severity` lấy nhầm từ `status`.

Một bản ghi chỉ được tính là KHỚP khi cả ba đều đúng.

Nguồn rỗng thì Match % là `n/a`, không phải 100%
-------------------------------------------------
Không bản ghi nào để so thì không có gì được chứng minh. In `100%` ở đó là
đúng loại default-xanh mà hàng đợi audit này đã đóng nhiều lần: một ô xanh
không phân biệt được "đã kiểm, sạch" với "không có gì để kiểm". `n/a` phân
biệt được.

Bản ghi không có khoá chính thì KHÔNG được chèn
------------------------------------------------
Một incident thiếu `incident_id` không có định danh. Bịa cho nó một khoá
(hash nội dung, số thứ tự) làm bản sao trông đầy đủ trong khi định danh đó
không tồn tại ở nguồn và không join được với bất cứ thứ gì. Nên: không chèn,
đếm riêng vào `unkeyed`, và Match % tụt xuống đúng bằng phần đã mất. Con số
tụt là con số thật xuất hiện, không phải chất lượng giảm.

WAL và busy_timeout
--------------------
`journal_mode=WAL` cho phép đọc trong lúc đang ghi — pipeline dựng lại bản sao
ở stage cuối trong khi một truy vấn khác đang mở. `busy_timeout=5000` thay
một `database is locked` ném ngay lập tức bằng năm giây chờ; trên Windows,
khoá tệp đến và đi trong vài mili-giây, và chờ là cách xử lý đúng.

WAL là thuộc tính của TỆP, ghi vào header và tồn tại qua các lần mở
(persistent). `busy_timeout` là thuộc tính của KẾT NỐI và phải đặt lại mỗi lần
mở — nên nó nằm trong `_connect()`, không nằm trong phần khởi tạo schema.

Chạy:
    python scripts/sqlite_mirror.py              # dựng lại + báo cáo
    python scripts/sqlite_mirror.py --verify     # chỉ kiểm bản sao hiện có
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_manager import read_state_safe, write_state_atomic  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, 'state')
DB_PATH = os.path.join(STATE_DIR, 'sentinelops.db')
REPORT_PATH = os.path.join(STATE_DIR, 'sqlite_mirror.json')

BUSY_TIMEOUT_MS = 5000


# --------------------------------------------------------------------------
# Ánh xạ nguồn -> bảng.
#
# `array` là khoá chứa mảng bản ghi; `declared` là khoá mà chính tệp nguồn tự
# khai số lượng. Hai con số đó phải bằng nhau, và khi lệch thì bộ này nói ra —
# một tệp tự mâu thuẫn về số bản ghi của chính nó là chuyện đáng biết trước
# khi ai đó đi tính tỉ lệ trên nó.
# --------------------------------------------------------------------------
SOURCES = [
    {
        'name': 'assets.json',
        'table': 'assets',
        'array': 'assets',
        'declared': 'total_assets',
        'pk': 'asset_id',
        'columns': [
            'asset_id', 'ip', 'hostname', 'hostname_source', 'os',
            'device_type', 'first_seen', 'last_seen', 'vulnerability_count',
            'critical', 'high', 'medium', 'low', 'info', 'mac', 'mac_source',
            'trust_score', 'trust_level',
        ],
    },
    {
        'name': 'incidents.json',
        'table': 'incidents',
        'array': 'incidents',
        # `total_records`, KHÔNG phải `total_incidents`. Hai khoá đó đếm hai
        # thứ khác nhau và chỉ một cái đếm mảng: lúc viết bộ này, tệp khai
        # `total_incidents: 1` cạnh `total_records: 3` — vì `total_incidents`
        # đếm sự cố còn OPEN, hai bản ghi kia đã INVALIDATED. Lấy nhầm khoá
        # thì bộ kiểm tố cáo tệp nguồn tự mâu thuẫn trong khi nó nhất quán.
        'declared': 'total_records',
        'pk': 'incident_id',
        'columns': [
            'incident_id', 'severity', 'status', 'title', 'description',
            'asset_scope', 'recommended_action', 'created_at', 'fingerprint',
            'source_state', 'source_key', 'source_run_id', 'last_seen_run_id',
            'last_seen_at',
        ],
    },
    {
        'name': 'executive_findings.json',
        'table': 'executive_findings',
        'array': 'findings',
        'declared': 'total_findings',
        'pk': 'finding_id',
        'columns': [
            'finding_id', 'rule_id', 'rule_name', 'severity',
            'severity_ceiling', 'severity_capped_from', 'title', 'summary',
            'rule_confidence', 'evidence_quality', 'confidence_score',
            'confidence', 'attribution_quality', 'evidence_completeness',
            'detected_at',
        ],
    },
]


# --------------------------------------------------------------------------
# Tuần tự hoá và chuẩn hoá
# --------------------------------------------------------------------------

def canonical(record):
    """Dạng văn bản duy nhất của một bản ghi — cùng nội dung thì cùng chuỗi.

    `sort_keys` để thứ tự khoá không đổi kết quả; `ensure_ascii=False` để
    tiếng Việt đi qua nguyên vẹn thay vì biến thành `\\uXXXX` (chuỗi escape
    vẫn so sánh được, nhưng `raw_json` trong DB sẽ không đọc được bằng mắt,
    và một bản sao không đọc được thì mất một nửa lý do tồn tại).
    """
    return json.dumps(record, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'))


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def scalar(value):
    """Giá trị lưu được vào một cột SQLite.

    `bool` đổi thành `int` một cách tường minh: SQLite lưu nó thành 0/1 và trả
    về `int`, nên nếu không đổi ở đây thì phép so `True == 1` sẽ đúng một cách
    tình cờ ở Python và sai ở nơi khác. Dict/list — không mong đợi ở một cột
    đã tách, nhưng nếu gặp thì lưu dạng JSON còn hơn ném.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float, str)):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------
# Kết nối
# --------------------------------------------------------------------------

def _connect(path=None, readonly=False):
    # `path=None` rồi mới tra `DB_PATH`, KHÔNG phải `path=DB_PATH`.
    #
    # Python tính giá trị mặc định MỘT LẦN lúc định nghĩa hàm. Viết
    # `path=DB_PATH` thì mọi lời gọi `_connect()` về sau dùng đường dẫn lúc
    # import, và việc gán lại `sqlite_mirror.DB_PATH` không có tác dụng gì.
    #
    # Đây không phải chuyện lý thuyết: bộ kiểm trỏ `DB_PATH` sang một tệp
    # fixture, tưởng mình đang dựng lại bản sao tạm, và thật ra ghi đè BẢN SAO
    # THẬT bằng hai hàng dữ liệu giả — rồi xoá thư mục fixture và không để lại
    # dấu vết nào. Một bộ kiểm làm hỏng thứ nó đang kiểm là trường hợp xấu
    # nhất của lớp lỗi này, vì nó trông như bộ kiểm đã chạy sạch.
    path = path or DB_PATH
    if readonly:
        uri = 'file:%s?mode=ro' % path.replace('?', '%3f').replace('#', '%23')
        conn = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_MS / 1000.0)
    else:
        conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1000.0)
    conn.row_factory = sqlite3.Row
    # Thuộc tính của KẾT NỐI — đặt lại mỗi lần mở, kể cả kết nối chỉ-đọc.
    conn.execute('PRAGMA busy_timeout = %d' % BUSY_TIMEOUT_MS)
    return conn


def enable_wal(conn):
    """Bật WAL và trả về chế độ SQLite THẬT SỰ áp dụng.

    `PRAGMA journal_mode` trả về chế độ đang có hiệu lực, không phải chế độ
    vừa yêu cầu. Trên một số filesystem mạng, yêu cầu `WAL` nhận lại `delete`.
    Đọc giá trị trả về là cách duy nhất biết được điều đó; giả định nó thành
    công là cách để báo cáo khai một tính năng chưa bao giờ bật.
    """
    row = conn.execute('PRAGMA journal_mode = WAL').fetchone()
    return row[0] if row else None


def table_signature(conn, table):
    """(tên, kiểu khai báo) của từng cột — chữ ký để phát hiện schema lệch.

    Phải gồm KIỂU, không chỉ tên. Lần sửa đầu tiên của bộ này so mỗi tên cột,
    nên khi các cột đổi từ `TEXT` sang không-kiểu thì chữ ký vẫn bằng nhau,
    bảng cũ không bị dựng lại, và affinity `TEXT` tiếp tục biến `39` thành
    `'39'` qua một lần chạy nữa. Một phép so schema bỏ qua kiểu không phát
    hiện được thay đổi về kiểu.
    """
    return [(r[1], (r[2] or '').upper())
            for r in conn.execute('PRAGMA table_info(%s)' % table)]


def has_json1(conn):
    """`json_extract()` có dùng được trên bản SQLite này không.

    Hỏi bằng cách GỌI THỬ, không bằng cách so số hiệu phiên bản: JSON1 là một
    tuỳ chọn biên dịch, nên hai bản cùng số hiệu có thể khác nhau ở điểm này.
    """
    try:
        conn.execute("SELECT json_extract('{\"a\":1}', '$.a')").fetchone()
        return True
    except sqlite3.OperationalError:
        return False


def ensure_schema(conn):
    """Tạo bảng, và dựng lại bảng nào có cột lệch với `SOURCES`.

    `CREATE TABLE IF NOT EXISTS` không sửa một bảng đã tồn tại. Nếu ai đó
    thêm một cột vào `SOURCES`, bảng cũ vẫn thiếu cột đó và mọi `INSERT` sẽ
    ném — hoặc tệ hơn, cột mới lặng lẽ không bao giờ được ghi. Bản sao là dữ
    liệu dẫn xuất, dựng lại được trong một giây, nên `DROP` rồi tạo lại là
    phép di trú đúng ở đây: không có gì để mất, và không có bảng nào lệch
    schema sống sót qua một lần chạy.
    """
    for src in SOURCES:
        # Cột KHÔNG khai kiểu -> BLOB affinity: SQLite lưu giá trị đúng lớp
        # lưu trữ được đưa vào, không chuyển đổi. Khai `TEXT` thì `39` được
        # lưu thành `'39'`, và một bản sao trả về chuỗi ở chỗ nguồn có số
        # không còn là bản sao — `WHERE critical > 0` sẽ so chuỗi. Đây chính
        # là lỗi bộ kiểm cột bắt được ở lần chạy đầu tiên.
        cols = ',\n    '.join(
            c if c != src['pk'] else '%s PRIMARY KEY' % c
            for c in src['columns'])
        expected = [(c, '') for c in src['columns']] + [
            ('raw_json', 'TEXT'), ('row_sha256', 'TEXT'),
            ('mirrored_at', 'TEXT')]
        existing = table_signature(conn, src['table'])
        if existing and existing != expected:
            conn.execute('DROP TABLE %s' % src['table'])
        conn.execute(
            'CREATE TABLE IF NOT EXISTS %s (\n    %s,\n'
            '    raw_json TEXT NOT NULL,\n'
            '    row_sha256 TEXT NOT NULL,\n'
            '    mirrored_at TEXT NOT NULL\n)' % (src['table'], cols))

    # Siêu dữ liệu của chính bản sao: mỗi hàng nói một nguồn được sao lúc nào,
    # từ tệp có hash nào, và tệp đó tự khai bao nhiêu bản ghi.
    conn.execute(
        'CREATE TABLE IF NOT EXISTS mirror_sources (\n'
        '    source TEXT PRIMARY KEY,\n'
        '    table_name TEXT NOT NULL,\n'
        '    source_sha256 TEXT,\n'
        '    source_timestamp TEXT,\n'
        '    source_run_id TEXT,\n'
        '    source_run_scope TEXT,\n'
        '    declared_count INTEGER,\n'
        '    json_count INTEGER NOT NULL,\n'
        '    sqlite_count INTEGER NOT NULL,\n'
        '    unkeyed_count INTEGER NOT NULL,\n'
        '    duplicate_key_count INTEGER NOT NULL,\n'
        '    mirrored_at TEXT NOT NULL\n)')
    conn.commit()


# --------------------------------------------------------------------------
# Dựng lại
# --------------------------------------------------------------------------

def load_source(src):
    """Đọc một tệp nguồn. Trả về (payload, danh sách bản ghi, hash tệp)."""
    path = os.path.join(STATE_DIR, src['name'])
    if not os.path.exists(path):
        return None, [], None
    with open(path, 'rb') as f:
        file_sha = hashlib.sha256(f.read()).hexdigest()
    payload = read_state_safe(path)
    records = payload.get(src['array']) if isinstance(payload, dict) else None
    if not isinstance(records, list):
        records = []
    return payload, records, file_sha


def mirror_source(conn, src, mirrored_at):
    payload, records, file_sha = load_source(src)
    if payload is None:
        return {
            'source': src['name'], 'table': src['table'], 'present': False,
            'json_count': 0, 'sqlite_count': 0, 'unkeyed': 0, 'duplicates': [],
            'declared': None, 'declared_matches_actual': None,
        }

    seen = {}
    duplicates = []
    unkeyed = 0
    rows = []

    for record in records:
        if not isinstance(record, dict):
            unkeyed += 1
            continue
        key = record.get(src['pk'])
        if key is None or key == '':
            unkeyed += 1
            continue
        key = str(key)
        if key in seen:
            # Cùng một khoá hai lần: bản sao chỉ giữ được một. Ghi ra để
            # `sqlite_count < json_count` có lời giải thích, thay vì trông
            # như bản sao đánh rơi bản ghi.
            duplicates.append(key)
            continue
        seen[key] = record

        text = canonical(record)
        values = [scalar(record.get(c)) for c in src['columns']]
        values += [text, sha256_text(text), mirrored_at]
        rows.append(values)

    placeholders = ','.join(['?'] * (len(src['columns']) + 3))
    colnames = ','.join(src['columns'] + ['raw_json', 'row_sha256',
                                          'mirrored_at'])

    # Dựng lại trọn vẹn trong MỘT transaction: hoặc bảng mang đúng nội dung
    # JSON hiện tại, hoặc nó không đổi chút nào. Không có trạng thái giữa
    # chừng để một truy vấn song song đọc phải.
    conn.execute('BEGIN IMMEDIATE')
    try:
        conn.execute('DELETE FROM %s' % src['table'])
        conn.executemany(
            'INSERT INTO %s (%s) VALUES (%s)'
            % (src['table'], colnames, placeholders), rows)

        declared = payload.get(src['declared']) if isinstance(payload, dict) else None
        conn.execute(
            'INSERT OR REPLACE INTO mirror_sources (source, table_name, '
            'source_sha256, source_timestamp, source_run_id, '
            'source_run_scope, declared_count, json_count, sqlite_count, '
            'unkeyed_count, duplicate_key_count, mirrored_at) '
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (src['name'], src['table'], file_sha, payload.get('timestamp'),
             payload.get('run_id'), payload.get('run_scope'), declared,
             len(records), len(rows), unkeyed, len(duplicates), mirrored_at))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return {
        'source': src['name'], 'table': src['table'], 'present': True,
        'json_count': len(records), 'sqlite_count': len(rows),
        'unkeyed': unkeyed, 'duplicates': duplicates,
        'declared': declared,
        'declared_matches_actual': (declared is None or declared == len(records)),
        'source_sha256': file_sha,
        'source_run_id': payload.get('run_id'),
    }


# --------------------------------------------------------------------------
# Kiểm chứng — đọc NGƯỢC từ SQLite, so với JSON
# --------------------------------------------------------------------------

def verify_source(src):
    """So từng bản ghi JSON với hàng tương ứng đọc ra từ SQLite.

    Kết nối riêng, chế độ chỉ-đọc, mở lại từ tệp trên đĩa. Không dùng lại đối
    tượng connection đã ghi: một transaction chưa commit sẽ cho phép bộ kiểm
    "thấy" dữ liệu chưa hề nằm trên đĩa.
    """
    payload, records, _ = load_source(src)
    # `present` do chính bộ kiểm khai, không suy từ kết quả dựng lại.
    #
    # Bản đầu tiên để `render()` đoán bằng `build.get('present', True)`. Ở chế
    # độ `--verify` thì `build` rỗng, nên mặc định `True` biến một tệp KHÔNG
    # TỒN TẠI thành "có mặt, 0 bản ghi" — đúng loại default-xanh mà hàng đợi
    # này đã đóng nhiều lần, lần này do tôi viết ra. Vắng mặt phải được đo tại
    # chỗ đọc, không được lấp bằng một giá trị mặc định ở chỗ in.
    result = {
        'source': src['name'], 'present': payload is not None,
        'json_count': len(records), 'sqlite_count': 0,
        'matched': 0, 'missing': [], 'hash_mismatch': [], 'field_mismatch': [],
        'orphan': [], 'match_pct': None,
    }
    if payload is None:
        return result

    conn = _connect(readonly=True)
    try:
        result['sqlite_count'] = conn.execute(
            'SELECT COUNT(*) FROM %s' % src['table']).fetchone()[0]
        db_rows = {}
        for row in conn.execute('SELECT * FROM %s' % src['table']):
            db_rows[str(row[src['pk']])] = row
    finally:
        conn.close()

    json_keys = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        key = record.get(src['pk'])
        if key is None or key == '':
            continue
        key = str(key)
        if key in json_keys:
            continue          # bản trùng: đã tính ở phần dựng lại
        json_keys.add(key)

        row = db_rows.get(key)
        if row is None:
            result['missing'].append(key)
            continue

        if row['raw_json'] != canonical(record):
            result['hash_mismatch'].append(key)
            continue

        bad = [c for c in src['columns'] if row[c] != scalar(record.get(c))]
        if bad:
            result['field_mismatch'].append({'key': key, 'fields': bad})
            continue

        result['matched'] += 1

    # Hàng nằm trong DB mà JSON không còn: bản sao đang tự giữ dữ liệu. Với
    # `DELETE` + `INSERT` thì việc này không xảy ra — nên nếu nó xảy ra, đó là
    # lỗi thật, không phải trạng thái bình thường.
    result['orphan'] = sorted(set(db_rows) - json_keys)

    # Nguồn rỗng: không có gì để chứng minh. `None` -> in `n/a`.
    if len(records) > 0:
        result['match_pct'] = round(100.0 * result['matched'] / len(records), 1)
    return result


# --------------------------------------------------------------------------
# Báo cáo
# --------------------------------------------------------------------------

def render(build, verify, journal_mode, busy_timeout, sqlite_version, json1):
    out = []
    out.append('')
    out.append('SQLITE MIRROR — state/sentinelops.db')
    out.append('=' * 62)
    out.append('  sqlite       : %s' % sqlite_version)
    out.append('  journal_mode : %s%s' % (
        journal_mode, '' if str(journal_mode).lower() == 'wal'
        else '   <-- KHONG phai WAL'))
    out.append('  busy_timeout : %d ms' % busy_timeout)
    out.append('  json_extract : %s' % (
        'co' if json1 else 'KHONG — raw_json phai parse o phia doc, '
                          'khong loc duoc trong WHERE (can SQLite >= 3.38)'))
    out.append('  Source of Truth : state/*.json (ban sao KHONG ghi nguoc)')
    out.append('')
    out.append('%-26s %7s %8s %7s %9s' % ('NGUON', 'JSON', 'SQLITE',
                                          'KHOP', 'MATCH %'))
    out.append('-' * 62)

    total_json = total_db = total_match = 0
    for v in verify:
        pct = 'n/a' if v['match_pct'] is None else '%.1f%%' % v['match_pct']
        out.append('%-26s %7d %8d %7d %9s' % (
            v['source'], v['json_count'], v['sqlite_count'], v['matched'], pct))
        total_json += v['json_count']
        total_db += v['sqlite_count']
        total_match += v['matched']

    out.append('-' * 62)
    overall = None if total_json == 0 else round(100.0 * total_match / total_json, 1)
    out.append('%-26s %7d %8d %7d %9s' % (
        'TONG', total_json, total_db, total_match,
        'n/a' if overall is None else '%.1f%%' % overall))
    out.append('')

    notes = []
    by_name = dict((b['source'], b) for b in build)
    for v in verify:
        b = by_name.get(v['source'], {})
        if not v['present']:
            notes.append('%s: khong ton tai trong state/ -> khong mirror duoc '
                         '(khac voi "co tep, 0 ban ghi")' % v['source'])
        if b.get('unkeyed'):
            notes.append('%s: %d ban ghi KHONG co khoa chinh -> khong mirror '
                         'duoc (khong bia khoa)' % (v['source'], b['unkeyed']))
        if b.get('duplicates'):
            notes.append('%s: %d khoa trung trong JSON -> SQLite chi giu mot: %s'
                         % (v['source'], len(b['duplicates']),
                            ', '.join(b['duplicates'][:5])))
        if b.get('declared_matches_actual') is False:
            notes.append('%s: tep tu khai %s ban ghi, mang co %d'
                         % (v['source'], b.get('declared'), v['json_count']))
        if v['missing']:
            notes.append('%s: %d ban ghi JSON khong co trong SQLite: %s'
                         % (v['source'], len(v['missing']),
                            ', '.join(v['missing'][:5])))
        if v['hash_mismatch']:
            notes.append('%s: %d ban ghi lech noi dung raw_json: %s'
                         % (v['source'], len(v['hash_mismatch']),
                            ', '.join(v['hash_mismatch'][:5])))
        if v['field_mismatch']:
            for fm in v['field_mismatch'][:5]:
                notes.append('%s: %s lech cot %s'
                             % (v['source'], fm['key'], ', '.join(fm['fields'])))
        if v['orphan']:
            notes.append('%s: %d hang trong SQLite khong con trong JSON: %s'
                         % (v['source'], len(v['orphan']),
                            ', '.join(v['orphan'][:5])))
        if v['json_count'] == 0 and v['present']:
            notes.append('%s: 0 ban ghi -> match n/a (khong phai 100%%: '
                         'khong co gi de chung minh)' % v['source'])

    if notes:
        out.append('GHI CHU')
        for n in notes:
            out.append('  - %s' % n)
    else:
        out.append('Khong co ghi chu: moi ban ghi JSON co mat trong SQLite, '
                   'raw_json khop byte, moi cot da tach khop gia tri nguon.')
    out.append('')
    return '\n'.join(out), overall, notes


def main():
    parser = argparse.ArgumentParser(description='SQLite mirror cua state/*.json')
    parser.add_argument('--verify', action='store_true',
                        help='chi kiem ban sao hien co, khong dung lai')
    args = parser.parse_args()

    if not os.path.isdir(STATE_DIR):
        print('state/ khong ton tai: %s' % STATE_DIR)
        return 2

    mirrored_at = datetime.now().isoformat()
    build = []

    conn = _connect()
    try:
        journal_mode = enable_wal(conn)
        json1 = has_json1(conn)
        ensure_schema(conn)
        if not args.verify:
            for src in SOURCES:
                build.append(mirror_source(conn, src, mirrored_at))
        busy_timeout = conn.execute('PRAGMA busy_timeout').fetchone()[0]
    finally:
        conn.close()

    verify = [verify_source(src) for src in SOURCES]
    text, overall, notes = render(build, verify, journal_mode, busy_timeout,
                                  sqlite3.sqlite_version, json1)
    print(text)

    write_state_atomic(REPORT_PATH, {
        'timestamp': mirrored_at,
        'db_path': 'state/sentinelops.db',
        'sqlite_version': sqlite3.sqlite_version,
        'journal_mode': journal_mode,
        'busy_timeout_ms': busy_timeout,
        'json_extract_available': json1,
        'source_of_truth': 'state/*.json',
        'mode': 'verify' if args.verify else 'rebuild',
        'overall_match_pct': overall,
        'sources': verify,
        'build': build,
        'notes': notes,
    })

    # Thoát khác 0 khi bản sao KHÔNG trung thành. Nguồn rỗng (`n/a`) không bị
    # coi là thất bại — nó chưa nói được gì, và ghi chú đã nói ra điều đó.
    failed = [v for v in verify
              if v['match_pct'] is not None and v['match_pct'] < 100.0]
    failed += [v for v in verify if v['orphan']]
    return 1 if failed else 0


if __name__ == '__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
