# SQLite Mirror — Trạng thái

Viết tay ngày 2026-09-14 · Nhánh `feature/invalidation-and-run-isolation` · `4bf2655`
Sprint DB-1 · `scripts/sqlite_mirror.py` (635 dòng) · `tests/sqlite_mirror/` (29 ca)

> **Các con số trong tài liệu này là ảnh chụp, không tự làm mới.**
> Nguồn sống là `state/sqlite_mirror.json`, sinh ra mỗi lần chạy `npm run db:mirror`
> hoặc `npm run db:verify`. Nếu hai chỗ lệch nhau thì tệp JSON đúng, tài liệu này cũ.

---

## 1. Trạng thái ba lớp — đừng đọc gộp

| Lớp | Trạng thái | Nghĩa là |
|---|---|---|
| **Mirror** | ✅ **ĐANG CHẠY** | `state/sentinelops.db` tồn tại, 3 nguồn khớp 100% ở lần chạy cuối |
| **Cutover** | ❌ **CHƯA** | Chưa có một dòng mã nào ĐỌC từ SQLite. Không thành phần nào phụ thuộc vào nó |
| **PostgreSQL** | ❌ **CHƯA** | Chưa bắt đầu, và điều kiện kích hoạt trong roadmap **chưa đạt** (mục 6) |

Ba lớp này hay bị gộp thành "đã có database". Chưa. Hiện có một **bản sao chỉ-đọc, dựng lại
theo yêu cầu**, chưa ai dùng. Giá trị của nó bây giờ là truy vấn ad-hoc để đo accuracy —
đúng lý do roadmap xếp nó P0 — chứ không phải là một tầng lưu trữ.

---

## 2. Bản sao tại lần chạy cuối

```
sqlite       : 3.31.1
journal_mode : wal            (thuộc tính của TỆP — bền qua các lần mở)
busy_timeout : 5000 ms        (thuộc tính của KẾT NỐI — phải đặt lại mỗi lần mở)
json_extract : KHÔNG có       (cần SQLite >= 3.38; xem mục 5)
tệp          : state/sentinelops.db — 60 KB
run_scope    : STANDALONE, run_id null (xem mục 5)
```

| Nguồn | JSON | SQLite | Khớp | Match % |
|---|---|---|---|---|
| `assets.json` (21 KB) | 11 | 11 | 11 | **100.0%** |
| `incidents.json` (3.9 KB) | 3 | 3 | 3 | **100.0%** |
| `executive_findings.json` (7.8 KB) | 2 | 2 | 2 | **100.0%** |
| **Tổng** | **16** | **16** | **16** | **100.0%** |

Không có ghi chú: mọi bản ghi JSON có mặt trong SQLite, `raw_json` khớp byte, mọi cột đã
tách khớp giá trị nguồn.

**Match % không phải phép đếm số hàng đã chèn.** Nó mở một kết nối thứ hai `mode=ro`, đọc
ngược từng hàng, và đòi cả ba điều: khoá chính có mặt, `raw_json` khớp từng byte, và **từng
cột đã tách** khớp giá trị trong JSON. Đếm hàng chèn được thì lúc nào cũng ra 100% — đó là
phép đo tự xác nhận chính mình.

---

## 3. Lược đồ

Bốn bảng. Ba bảng dữ liệu + một bảng siêu dữ liệu.

| Bảng | Khoá chính | Hàng | Nguồn |
|---|---|---|---|
| `assets` | `asset_id` | 11 | `state/assets.json` |
| `incidents` | `incident_id` | 3 | `state/incidents.json` |
| `executive_findings` | `finding_id` | 2 | `state/executive_findings.json` |
| `mirror_sources` | `source` | 3 | siêu dữ liệu: sha256 nguồn, run_id nguồn, số khai báo vs số thật, số bản ghi không khoá, số khoá trùng |

Mỗi bảng dữ liệu có ba cột cuối giống nhau:

- `raw_json TEXT NOT NULL` — bản ghi gốc nguyên vẹn. Các cột tách ra chỉ để truy vấn; khi
  chúng và `raw_json` bất đồng thì `raw_json` là bên đúng, và `verify` sẽ báo đỏ.
- `row_sha256 TEXT NOT NULL` — băm của `raw_json`, để so byte mà không phải đọc cả chuỗi.
- `mirrored_at TEXT NOT NULL` — không phải thời điểm dữ liệu xảy ra, mà là thời điểm bản
  sao được dựng. Hai thứ này lệch nhau chính là định nghĩa của "bản sao cũ".

**Các cột tách được khai KHÔNG có kiểu** (BLOB affinity), cố ý. Khai `TEXT` thì type
affinity của SQLite ép số nguyên `39` thành chuỗi `'39'`, và `WHERE critical > 0` lặng lẽ
biến thành so sánh chuỗi. Nếu cần chuyển sang kiểu tường minh (ví dụ khi sang PostgreSQL)
thì phải khai `INTEGER`/`REAL` cho đúng từng cột, không được để `TEXT`.

---

## 4. Ranh giới: JSON là Source of Truth

Điều này được **thi hành trong mã**, không chỉ ghi trong tài liệu:

1. Không hàm nào trong `sqlite_mirror.py` mở tệp JSON để ghi. Chiều duy nhất là JSON → DB.
2. Mỗi lần chạy là `DELETE` + `INSERT` toàn bộ trong một transaction, **không** phải
   upsert. Nhờ vậy "biến khỏi JSON" và "biến khỏi DB" là cùng một sự kiện. Upsert sẽ để
   lại bản ghi đã xoá nằm trong DB vĩnh viễn.
3. `state/sentinelops.db` (và `-wal`, `-shm`) nằm trong `.gitignore`. Commit một tệp nhị
   phân dẫn xuất tức là tạo bản thứ hai của sự thật trong lịch sử git — nó sẽ phân kỳ ngay
   lần đầu có PR sửa JSON mà không dựng lại, và git không merge được nhị phân.
4. Có một ca kiểm khẳng định tệp JSON nguồn **giống nhau từng byte** sau khi mirror + verify.

---

## 5. Những điều bản sao này KHÔNG bảo đảm

| Giới hạn | Hệ quả |
|---|---|
| **Không tự làm mới.** Không trigger, không watcher, không nằm trong pipeline. | Sửa JSON mà không chạy `db:mirror` thì DB cũ. `db:verify` **phát hiện** được (lệch `row_sha256`), nhưng không **ngăn** được. |
| **Không được đóng dấu run.** Báo cáo ra `run_scope: STANDALONE`, `run_id: null`. | Bản sao không gắn với một lần chạy pipeline nào. Đây là STANDALONE (chạy độc lập, đúng như thiết kế), **không phải** UNSTAMPED (lẽ ra phải có dấu mà thiếu). |
| **`json_extract()` không có** trên SQLite 3.31.1 đi kèm Python 3.7.9 (JSON1 mặc định từ 3.38). | `raw_json` giữ đủ `trust_basis`, `entities`, nhưng phải parse ở phía đọc — không lọc được trong `WHERE`. Chỉ các cột đã tách mới truy vấn được bằng SQL. Giới hạn này được **in ở đầu báo cáo**, để không ai gặp nó lần đầu dưới dạng một câu truy vấn ném lỗi. |
| **Chỉ 3 nguồn.** | `risk_score.json`, `shadow_assets.json`, `priority_queue.json`, … không có trong DB. Sprint DB-1 giới hạn đúng ba tệp. |
| **Bản ghi không có khoá thì không được chèn**, khoá trùng thì chỉ giữ bản cuối. | Cả hai được đếm vào `mirror_sources` và in ra báo cáo. Bộ này **không** bịa khoá thay thế — một khoá bịa sẽ khiến bản ghi hỏng trông như bản ghi tốt. |

---

## 6. Chưa cutover — và cái giá đã đo được

Cutover nghĩa là để một thành phần **đọc từ SQLite thay vì đọc JSON**. Chưa có gì làm việc đó.

Chi phí đã đo, không ước lượng:

```
37 tệp mã sản phẩm (scripts/ + web/) nhắc tới assets.json, incidents.json
   hoặc executive_findings.json — cộng 6 tệp kiểm = 43
```

Trong đó có Portal (`web/app.js`, `web/server.js`, `web/index.html`), Telegram
(`scripts/telegram/*`), và Correlation (`scripts/correlation_engine.py`) — đúng ba thứ
Sprint DB-1 cấm chạm. Cutover không thể là một sprint nhỏ.

**Trước khi cutover, cần có ít nhất:**

1. Bản sao được dựng lại **tự động** khi JSON đổi (hoặc một cổng chặn không cho đọc bản cũ).
   Đọc từ một bản sao có thể cũ mà không biết là tệ hơn đọc JSON.
2. Một chiến lược cho `json_extract` — nâng SQLite hoặc tách thêm cột. Hôm nay nhiều truy
   vấn hữu ích không viết được bằng SQL.
3. Quyết định ai là writer (xem mục 7 — hôm nay mỗi tệp có đúng một **đường ghi**, nhưng
   `assets.json` có hai script đi qua đường đó). Cutover mà không giữ được tính chất "ghi
   tuần tự, một đường" thì mất luôn lý do SQLite còn đủ dùng.

---

## 7. Chưa PostgreSQL — điều kiện kích hoạt chưa đạt

`docs/project/PRODUCT_ROADMAP.md` đặt điều kiện: **PostgreSQL chỉ khi >1 writer hoặc dữ
liệu vượt SQLite.** Đo hôm nay:

| Điều kiện | Ngưỡng | Thực tế | Đạt? |
|---|---|---|---|
| Writer **đồng thời** | > 1 | 0 — mọi ghi đều tuần tự trong pipeline | ❌ |
| Khối lượng dữ liệu | vượt SQLite | 16 hàng, 60 KB | ❌ |

Đo cho chính xác, vì chỗ này dễ đọc nhầm: mỗi tệp có đúng một **đường ghi**, nhưng không
phải mỗi tệp chỉ có một script.

| Tệp | Đường ghi | Script gọi |
|---|---|---|
| `incidents.json` | `generate_incidents.py` | 1 |
| `executive_findings.json` | `correlation_engine.py` | 1 |
| `assets.json` | `asset_store.write_assets()` | 2 — `asset_builder.py`, `extract_asset_intelligence.py` |

Hai script cùng ghi `assets.json`, nhưng **tuần tự** trong pipeline, không đồng thời — nên
điều kiện ">1 writer" của roadmap (nghĩa là tranh ghi đồng thời) vẫn chưa đạt. Điều đáng
theo dõi là nếu có script thứ ba ghi `assets.json` mà **không** đi qua `asset_store`, thì
điều kiện này đạt trước khi ai kịp nhận ra.

Cả hai đều còn cách rất xa. Mở PostgreSQL bây giờ là thêm một tiến trình phải chạy, một
chuỗi kết nối phải giữ bí mật, và một tầng nữa có thể sai — để phục vụ 16 hàng.

**Nếu sau này chuyển, phần nào chuyển được và phần nào không:**

- Chuyển thẳng được: cấu trúc bảng, khoá chính, kỷ luật dựng lại toàn bộ trong một
  transaction, `row_sha256`, `mirror_sources`.
- Phải viết lại: cột **không khai kiểu** (mục 3) — PostgreSQL không có type affinity, mọi
  cột phải khai kiểu tường minh. `raw_json TEXT` nên thành `jsonb`, và khi đó giới hạn
  `json_extract` ở mục 5 tự biến mất.
- Không cần mang theo: `WAL`, `busy_timeout` — đó là cách SQLite xử lý ghi đồng thời trong
  một tệp; PostgreSQL giải quyết việc đó bằng cơ chế khác.

---

## 8. Lệnh

```bash
npm run db:mirror
```

```bash
npm run db:verify
```

`db:mirror` dựng lại rồi kiểm. `db:verify` chỉ kiểm bản sao hiện có, không ghi gì vào DB.
Cả hai in cùng một bảng và ghi `state/sqlite_mirror.json`. **Thoát 1** khi có nguồn nào
dưới 100% hoặc có hàng mồ côi. Nguồn rỗng ra `n/a`, không tính là thất bại — nó chưa nói
được điều gì, và ghi chú nói ra đúng như vậy.

---

## 9. Vì sao tin được con số 100%

29 ca kiểm trong `tests/sqlite_mirror/`, đã đăng ký vào cổng chặn
(`tests/detection_quality/run_all.py`). Suite toàn dự án: **451/451**.

Bộ kiểm không chỉ kiểm bản sao — nó kiểm **chính bộ kiểm có biết đỏ hay không**. Bốn kịch
bản phá hoại: đổi một cột, đổi `raw_json`, xoá một hàng, chèn một hàng mồ côi. Cả bốn phải
làm `verify` báo đỏ, nếu không thì 100% ở lần chạy sạch chẳng chứng minh điều gì.

Nhờ tầng đó, bộ kiểm bắt được **3 lỗi trong chính mã của sprint này**:

1. Cột khai `TEXT` → affinity ép `39` thành `'39'`. Sửa: bỏ khai kiểu.
2. Bản vá (1) **không có tác dụng** — `ensure_schema` so chữ ký bảng bằng *tên* cột, mà tên
   không đổi khi kiểu đổi, nên bảng `TEXT` cũ sống sót. Sửa: chữ ký gồm cả kiểu.
3. `_connect(path=DB_PATH)` đóng băng giá trị mặc định lúc import, nên khi bộ kiểm trỏ
   `DB_PATH` sang fixture thì **nó vẫn ghi đè bản sao thật**, rồi xoá fixture không để lại
   dấu vết. Sửa: `path=None`, tra `DB_PATH` lúc gọi. Ca kiểm khoá lỗi này được đặt **đầu
   tiên** trong tệp, vì mọi ca sau nó đều vô nghĩa nếu nó hỏng.

Lỗi (3) là loại nguy hiểm nhất: một bộ kiểm phá hỏng đúng thứ nó đang kiểm, mà vẫn báo xanh.

---

## 10. Nhật ký

| Ngày | Việc |
|---|---|
| 2026-09-14 | Sprint DB-1: tạo mirror, WAL + busy_timeout, 3 nguồn, 100%, 29 ca kiểm. Không chạm Portal / Telegram / Correlation. |
