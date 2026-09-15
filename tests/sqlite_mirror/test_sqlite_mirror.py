# -*- coding: utf-8 -*-
"""
SQLite Mirror (Sprint DB-1) — khoá lại bản sao `state/sentinelops.db`.

Hai lớp ca kiểm, vì "bản sao khớp 100%" có thể đúng vì hai lý do rất khác
nhau và chỉ một trong hai đáng tin:

  (a) bản sao thật sự trung thành;
  (b) bộ kiểm không biết cách đỏ.

Phần lớn tệp này là lớp (b): làm hỏng bản sao theo bốn kiểu khác nhau và đòi
`verify_source()` tụt xuống dưới 100%. Một bộ đối chiếu chưa bao giờ được thấy
đỏ thì con số 100% của nó không mang thông tin.

Hai ca dưới đây khoá đúng hai lỗi ĐÃ XẢY RA lúc viết bộ mirror, không phải hai
lỗi tưởng tượng:

* `kieu du lieu duoc giu nguyen` — cột khai `TEXT` khiến SQLite lưu `39` thành
  `'39'` (type affinity). Bản sao trả chuỗi ở chỗ nguồn có số, và
  `WHERE critical > 0` biến thành so sánh chuỗi. Bắt được ở lần chạy đầu tiên
  vì bộ kiểm so TỪNG cột, không chỉ so số lượng hàng.

* `doi KIEU cot cung dung lai bang` — bản vá đầu tiên cho lỗi trên không có
  tác dụng, vì `ensure_schema()` so chữ ký bảng bằng TÊN cột. Tên không đổi
  khi kiểu đổi, nên bảng `TEXT` cũ sống sót thêm một lần chạy nữa và triệu
  chứng y hệt. Chữ ký phải gồm kiểu.

Bộ này chạy trên tệp fixture tổng hợp trong `_fixture/`, KHÔNG chạm vào
`state/` thật — trừ đúng một ca đọc cấu hình WAL của bản sao thật, vì WAL là
thuộc tính của tệp trên đĩa và một fixture không chứng minh được nó.
"""
from __future__ import print_function

import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
for path in (os.path.join(PROJECT_ROOT, 'scripts'),
             os.path.join(PROJECT_ROOT, 'tests', 'detection_quality')):
    if path not in sys.path:
        sys.path.insert(0, path)

from harness import Suite  # noqa: E402
import sqlite_mirror as M  # noqa: E402

# AQ-048. Thu muc CO DINH: neu mot lan chay truoc de lai mot handle SQLite
# chua dong thi `rmtree` nem `PermissionError [WinError 32]` ngay dau ham `run()`,
# va ca bo kiem nay khong chay duoc — mot su co ha tang doc len giong het mot bat
# bien vo. Thu muc tam thi moi lan chay co cho rieng, khong ai dam len ai.
FIXTURE_DIR = tempfile.mkdtemp(prefix='sqlite_mirror_')

ASSETS_DOC = {
    'timestamp': '2026-09-14T00:00:00',
    'total_assets': 2,
    'run_id': 'RUN-TEST',
    'assets': [
        {'asset_id': 'A-1', 'ip': '10.0.0.1', 'hostname': None,
         'vulnerability_count': 39, 'critical': 0, 'high': 2,
         'trust_score': 100, 'trust_level': 'IDENTITY_VERIFIED',
         'trust_basis': {'points_possible': 100, 'components': [{'name': 'mac'}]}},
        {'asset_id': 'A-2', 'ip': '10.0.0.2', 'hostname': 'kevin-pc',
         'vulnerability_count': 5, 'critical': 1, 'high': 0,
         'trust_score': 60, 'trust_level': 'PARTIAL'},
    ],
}

ASSETS_SRC = {
    'name': 'assets.json', 'table': 'assets', 'array': 'assets',
    'declared': 'total_assets', 'pk': 'asset_id',
    'columns': ['asset_id', 'ip', 'hostname', 'vulnerability_count',
                'critical', 'high', 'trust_score', 'trust_level'],
}


def write_doc(doc, name='assets.json'):
    with io.open(os.path.join(FIXTURE_DIR, name), 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(doc, ensure_ascii=False))


def rebuild(src=ASSETS_SRC):
    conn = M._connect()
    try:
        M.enable_wal(conn)
        M.ensure_schema(conn)
        return M.mirror_source(conn, src, 'test')
    finally:
        conn.close()


def tamper(sql):
    conn = M._connect()
    conn.execute(sql)
    conn.commit()
    conn.close()


def run():
    suite = Suite('SQLite mirror cua state/*.json (Sprint DB-1)')

    # -- 1. Ban sao THAT: WAL va busy_timeout ------------------------------
    # WAL la thuoc tinh cua TEP va ton tai qua cac lan mo; mot fixture moi tao
    # khong chung minh duoc rang ban sao that dang bat no.
    real_db = M.DB_PATH
    if os.path.exists(real_db):
        conn = M._connect(real_db)
        try:
            mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
            busy = conn.execute('PRAGMA busy_timeout').fetchone()[0]
        finally:
            conn.close()
        suite.check_equal('ban sao that dang o journal_mode WAL',
                          mode.lower(), 'wal')
        suite.check_equal('busy_timeout dat tren moi ket noi moi',
                          busy, M.BUSY_TIMEOUT_MS)
    else:
        # Vang mat duoc khai bao, khong duoc lap bang mot ca xanh.
        suite.check('ban sao that ton tai de kiem WAL', False,
                    'chua chay `npm run db:mirror` -> %s' % real_db)

    old_state, old_db = M.STATE_DIR, M.DB_PATH
    if os.path.exists(FIXTURE_DIR):
        shutil.rmtree(FIXTURE_DIR, ignore_errors=True)
    if not os.path.exists(FIXTURE_DIR):
        os.makedirs(FIXTURE_DIR)
    M.STATE_DIR = FIXTURE_DIR
    M.DB_PATH = os.path.join(FIXTURE_DIR, 'test.db')

    try:
        # -- 1b. Gan lai DB_PATH phai THAT SU doi huong ket noi -----------
        # Ca nay ton tai vi lan dau chay, no KHONG doi huong: `_connect` khai
        # `path=DB_PATH`, va Python tinh gia tri mac dinh mot lan luc dinh
        # nghia ham. Ca bo kiem duoi day tuong minh dang ghi vao fixture va
        # that ra ghi de ban sao THAT, roi xoa fixture va khong de lai dau
        # vet. Kiem truoc moi thu khac, vi neu no sai thi moi ca sau deu do
        # trong khi bao xanh.
        probe = M._connect()
        try:
            actual = probe.execute('PRAGMA database_list').fetchone()[2]
        finally:
            probe.close()
        suite.check('gan lai DB_PATH doi huong ket noi (khong bi dong bang '
                    'vao gia tri mac dinh luc import)',
                    os.path.abspath(actual) == os.path.abspath(M.DB_PATH),
                    'ket noi mo %s, cho doi %s' % (actual, M.DB_PATH))

        write_doc(ASSETS_DOC)
        rebuild()

        # -- 2. Vong tron sach: moi ban ghi khop --------------------------
        v = M.verify_source(ASSETS_SRC)
        suite.check_equal('vong tron sach -> match 100%', v['match_pct'], 100.0)
        suite.check_equal('json_count', v['json_count'], 2)
        suite.check_equal('sqlite_count', v['sqlite_count'], 2)
        suite.check('khong co hang mo coi', v['orphan'] == [], str(v['orphan']))

        # -- 3. Kieu du lieu duoc giu nguyen (LOI DA XAY RA) --------------
        # Cot khai TEXT thi `39` thanh `'39'`. Bản sao tra chuoi o cho nguon
        # co so khong con la ban sao.
        conn = M._connect(readonly=True)
        try:
            row = conn.execute("SELECT vulnerability_count, critical, ip "
                               "FROM assets WHERE asset_id = 'A-1'").fetchone()
            n_gt = conn.execute('SELECT COUNT(*) FROM assets '
                                'WHERE vulnerability_count > 9').fetchone()[0]
        finally:
            conn.close()
        suite.check('so nguyen van la so nguyen, khong bi affinity ep thanh chuoi',
                    isinstance(row[0], int) and row[0] == 39,
                    '%r (%s)' % (row[0], type(row[0]).__name__))
        suite.check('chuoi van la chuoi', isinstance(row[2], str), repr(row[2]))
        # Neu la chuoi thi '5' > '9' sai va con so nay se la 2.
        suite.check_equal('WHERE so hoc so bang SO, khong bang chuoi', n_gt, 1)

        # -- 4. Bo kiem biet DO: bon kieu hong khac nhau ------------------
        rebuild()
        tamper("UPDATE assets SET critical = 999 WHERE asset_id = 'A-1'")
        v = M.verify_source(ASSETS_SRC)
        suite.check('doi mot cot -> bao field_mismatch',
                    [f['key'] for f in v['field_mismatch']] == ['A-1'],
                    str(v['field_mismatch']))
        suite.check('... va match tut duoi 100', v['match_pct'] == 50.0,
                    str(v['match_pct']))

        rebuild()
        tamper("UPDATE assets SET raw_json = raw_json || ' ' "
               "WHERE asset_id = 'A-1'")
        v = M.verify_source(ASSETS_SRC)
        suite.check('doi raw_json -> bao hash_mismatch',
                    v['hash_mismatch'] == ['A-1'], str(v['hash_mismatch']))

        rebuild()
        tamper("DELETE FROM assets WHERE asset_id = 'A-1'")
        v = M.verify_source(ASSETS_SRC)
        suite.check('xoa mot hang -> bao missing', v['missing'] == ['A-1'],
                    str(v['missing']))

        rebuild()
        tamper("INSERT INTO assets (asset_id, raw_json, row_sha256, mirrored_at) "
               "VALUES ('A-GHOST', '{}', 'x', 't')")
        v = M.verify_source(ASSETS_SRC)
        suite.check('hang co trong DB ma khong con trong JSON -> bao orphan',
                    v['orphan'] == ['A-GHOST'], str(v['orphan']))

        # -- 5. Dung lai XOA ban ghi da bien khoi JSON --------------------
        # `INSERT OR REPLACE` khong xoa; ban sao se giu lai ban ghi nguon da
        # bo, va mot cau COUNT(*) se dem no. Dung lai tron ven moi lam cho
        # "JSON khong con" va "DB khong con" la cung mot su kien.
        shrunk = json.loads(json.dumps(ASSETS_DOC))
        shrunk['assets'] = shrunk['assets'][:1]
        shrunk['total_assets'] = 1
        write_doc(shrunk)
        rebuild()
        v = M.verify_source(ASSETS_SRC)
        suite.check_equal('ban ghi bi xoa khoi JSON cung bien khoi SQLite',
                          v['sqlite_count'], 1)
        suite.check('... va khong de lai hang mo coi', v['orphan'] == [],
                    str(v['orphan']))
        write_doc(ASSETS_DOC)

        # -- 6. Nguon rong -> n/a, KHONG phai 100% ------------------------
        write_doc({'assets': [], 'total_assets': 0}, 'empty.json')
        empty_src = dict(ASSETS_SRC, name='empty.json')
        v = M.verify_source(empty_src)
        suite.check('0 ban ghi -> match_pct None (n/a), khong phai 100',
                    v['match_pct'] is None, repr(v['match_pct']))

        # -- 7. Tep vang mat -> present False, ghi chu noi dung su that ---
        # Duong nay tung mac default-xanh: `render()` doan `present` tu ket
        # qua dung lai, va o che do --verify ket qua do rong, nen mot tep
        # KHONG TON TAI doc ra thanh "co tep, 0 ban ghi".
        v = M.verify_source(dict(ASSETS_SRC, name='khong_he_co.json'))
        suite.check('tep vang mat -> present False', v['present'] is False,
                    repr(v['present']))
        _, _, notes = M.render([], [v], 'wal', 5000, '3.31.1', False)
        suite.check('ghi chu noi KHONG TON TAI, khong noi "0 ban ghi"',
                    len(notes) == 1 and 'khong ton tai trong state/' in notes[0],
                    str(notes))

        # -- 8. Doi KIEU cot cung phai dung lai bang (LOI DA XAY RA) ------
        # Chu ky bang so bang TEN cot thi doi kieu khong bi phat hien, va
        # bang cu song sot voi affinity cu. Chu ky phai gom kieu.
        conn = M._connect()
        try:
            conn.execute('DROP TABLE assets')
            conn.execute('CREATE TABLE assets (%s, raw_json TEXT NOT NULL, '
                         'row_sha256 TEXT NOT NULL, mirrored_at TEXT NOT NULL)'
                         % ', '.join(
                             ('%s TEXT PRIMARY KEY' % c) if c == 'asset_id'
                             else ('%s TEXT' % c) for c in ASSETS_SRC['columns']))
            conn.commit()
            M.ensure_schema(conn)
            sig = M.table_signature(conn, 'assets')
        finally:
            conn.close()
        suite.check('bang khai TEXT bi dung lai thanh khong-kieu',
                    all(t == '' for name, t in sig
                        if name in ASSETS_SRC['columns']), str(sig))
        rebuild()
        v = M.verify_source(ASSETS_SRC)
        suite.check_equal('sau khi di tru, match tro lai 100%',
                          v['match_pct'], 100.0)

        # -- 9. Mirror KHONG BAO GIO ghi nguoc vao JSON -------------------
        # Rang buoc trung tam cua sprint: JSON la Source of Truth.
        path = os.path.join(FIXTURE_DIR, 'assets.json')
        with open(path, 'rb') as fh:
            before = fh.read()
        rebuild()
        M.verify_source(ASSETS_SRC)
        with open(path, 'rb') as fh:
            after = fh.read()
        suite.check('dung lai + kiem: tep JSON nguon khong doi mot byte',
                    before == after, 'JSON bi ghi nguoc')

        # -- 10. Ban ghi khong co khoa chinh: khong bia khoa --------------
        doc = json.loads(json.dumps(ASSETS_DOC))
        doc['assets'].append({'ip': '10.0.0.3', 'trust_score': 1})  # thieu PK
        doc['total_assets'] = 3
        write_doc(doc)
        build = rebuild()
        suite.check_equal('ban ghi thieu khoa chinh -> dem vao unkeyed',
                          build['unkeyed'], 1)
        suite.check_equal('... va KHONG duoc chen (khong bia khoa)',
                          build['sqlite_count'], 2)
        v = M.verify_source(ASSETS_SRC)
        suite.check('... va match tut xuong dung phan da mat',
                    v['match_pct'] is not None and v['match_pct'] < 100.0,
                    str(v['match_pct']))

        # -- 11. Khoa trung trong JSON duoc khai, khong bi nuot -----------
        doc = json.loads(json.dumps(ASSETS_DOC))
        doc['assets'].append(dict(doc['assets'][0]))  # trung A-1
        doc['total_assets'] = 3
        write_doc(doc)
        build = rebuild()
        suite.check_equal('khoa trung -> dem vao duplicate_key_count',
                          len(build['duplicates']), 1)
        suite.check_equal('... SQLite chi giu mot', build['sqlite_count'], 2)

        # -- 12. Tep tu khai lech so ban ghi thi noi ra -------------------
        doc = json.loads(json.dumps(ASSETS_DOC))
        doc['total_assets'] = 99
        write_doc(doc)
        build = rebuild()
        suite.check('declared lech actual -> bao ra',
                    build['declared_matches_actual'] is False,
                    'declared=%s actual=%s' % (build['declared'],
                                               build['json_count']))
        write_doc(ASSETS_DOC)

    finally:
        M.STATE_DIR, M.DB_PATH = old_state, old_db
        if os.path.exists(FIXTURE_DIR):
            shutil.rmtree(FIXTURE_DIR, ignore_errors=True)

    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    import harness
    sys.exit(harness.render([run()]))
