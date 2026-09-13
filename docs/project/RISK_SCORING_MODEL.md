# RISK SCORING MODEL — Schema chuẩn cho `state/risk_score.json`

**Sprint**: 6 (Risk Engine Consolidation)
**Ngày**: 2026-09-13
**Trạng thái**: LOCKED — một engine, một output, một thang điểm

---

## 1. Engine duy nhất

```
scripts/calculate_risk_score.py  →  state/risk_score.json
```

Đây là script **duy nhất** được phép ghi `state/risk_score.json`. Bất kỳ script
nào khác ghi vào tệp này đều là lỗi hồi quy.

`risk_engine.py` đã bị **xoá** trong Sprint 6. `nessus_pipeline.py` trước đây gọi
nó trực tiếp, nay uỷ quyền sang engine chuẩn qua subprocess.

---

## 2. Thang điểm: rủi ro tăng dần

**`overall_score` càng cao = càng nguy hiểm.**

| Điểm | `risk_level` |
|---|---|
| 80–100 | `CRITICAL` |
| 60–79 | `HIGH` |
| 40–59 | `MEDIUM` |
| 0–39 | `LOW` |

Trước Sprint 6 engine dùng thang ngược (80+ = LOW) trong khi **toàn bộ** consumer
— portal, `web/server.js`, Telegram bot — đều đọc theo thang tăng dần. Hậu quả:
điểm 74 hiển thị là "🟠 HIGH" ở mọi nơi trong khi engine muốn nói "khá an toàn".
Sprint 6 đảo engine, không đảo consumer — một chỗ sửa thay vì sáu.

---

## 3. Schema

```json
{
  "overall_score": 56,
  "risk_level": "HIGH",
  "critical_count": 14,
  "high_count": 22,
  "factors": [
    {
      "name": "threat_hunting",
      "health": 0,
      "weight": 0.25,
      "risk_contribution": 25.0,
      "detail": "persistence: 1C/3H; credential_dumping: 4C/1H"
    }
  ],
  "generated_at": "2026-09-13T16:02:11.482913",

  "engine": "calculate_risk_score",
  "engine_version": "2.0.0",
  "scale": "risk_ascending",
  "scale_description": "overall_score cao = rủi ro cao",
  "notes": ["Severity floor áp dụng: ..."],

  "timestamp": "...",
  "threat_level": "HIGH",
  "component_scores": { "threat_hunting": 0, "incidents": 0, "asset": 100 },
  "weights": { "threat_hunting": 0.25, "incidents": 0.25 }
}
```

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `overall_score` | int 0–100 | Rủi ro tổng, cao = nguy hiểm |
| `risk_level` | string | `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`, **đã áp severity floor** |
| `critical_count` | int | Số phát hiện CRITICAL (sự cố + hunting) |
| `high_count` | int | Số phát hiện HIGH (sự cố + hunting) |
| `factors` | array | Từng thành phần: `health`, `weight`, `risk_contribution`, `detail` |
| `generated_at` | ISO8601 | Thời điểm sinh |

**Tương thích ngược** (giữ lại để consumer cũ không vỡ): `timestamp`,
`threat_level` (alias của `risk_level`), `component_scores`, `weights`.

> `critical_count` / `high_count` đếm **phát hiện** (incidents + hunting), không
> đếm lỗ hổng Nessus. Hai thứ khác đơn vị; cộng chung là sai. Số lỗ hổng nằm
> trong `factors[name=asset].detail`.

---

## 4. Mô hình tính

Mỗi thành phần tự chấm **sức khoẻ** 0–100 (cao = tốt). Engine lấy trung bình có
trọng số rồi đảo:

```
overall_score = 100 − Σ(weight × health)
```

| Thành phần | Trọng số | Nguồn |
|---|---:|---|
| `threat_hunting` | 0.25 | 4 tệp `hunting_*.json` |
| `incidents` | 0.25 | `incidents.json` |
| `asset` | 0.20 | `assets.json` (Nessus) |
| `waap` | 0.10 | `waap_score.json` |
| `crypto` | 0.06 | `crypto_inventory.json` |
| `defender` | 0.06 | `defender_status.json` |
| `firewall` | 0.04 | `firewall_status.json` |
| `security_events` | 0.04 | `security_events.json` |
| | **1.00** | |

Bốn tiêu chí bắt buộc của Sprint 6 — IOC, Asset Risk, Incident Severity, Hunting
Findings — chiếm **70%**. Hạ tầng phòng thủ chiếm 30%.

### Severity floor

Trung bình có trọng số **làm loãng** sự cố nghiêm trọng. Đây chính là lỗi khiến
Risk Score = 1 trong khi có 7 sự cố CRITICAL và 21 IOC.

> Còn phát hiện CRITICAL đang mở thì `risk_level` không được thấp hơn `HIGH`.

Khi floor kích hoạt, engine ghi lý do vào `notes`. `overall_score` **không** bị
sửa — chỉ `risk_level` bị nâng, để điểm số vẫn phản ánh trung thực phép tính.

---

## 5. Thứ tự chạy trong pipeline

Risk Assessment chuyển từ **Phase 5** sang **Phase 9B**, ngay sau Incident Engine.

```
Phase 7B  Threat Hunting    → hunting_*.json
Phase 8   Triage Engine     → priority_queue.json
Phase 9   Incident Engine   → incidents.json
Phase 9B  Risk Assessment   → risk_score.json   ← đọc kết quả của Phase 7B + 9
Phase 10  Correlation       → executive_findings.json
```

Bắt buộc phải đổi: incidents chiếm 25% trọng số, nếu risk chạy ở Phase 5 thì nó
luôn chấm sự cố của **chu kỳ trước**.

Đánh đổi đã biết: `generate_incidents.detect_risk_escalation()` (Phase 9) nay đọc
`risk_score.json` của chu kỳ trước. Chấp nhận được — đó là bộ phát hiện *leo
thang*, việc so với trạng thái trước vốn đúng với ý đồ của nó.

---

## 6. Consumer

| Nơi đọc | Trường dùng | Sprint 6 |
|---|---|---|
| `web/app.js` `getThreatLevel`/`getRiskLevel`/`getRiskDetail` | `risk_level`, fallback bands | Ưu tiên `risk_level` |
| `web/app.js` Daily Brief recommendations | `overall_score >= 60` | Đảo từ `< 50` |
| `web/server.js` `/api/status` | `risk_level` | Thêm `risk_level`, giữ alias `threat_level` |
| `scripts/telegram/telegramBot.js` `/status` | `risk_level` | Ưu tiên `risk_level` |
| `scripts/telegram/telegramBot.js` `/executive` | `risk_level` | Ưu tiên `risk_level` |
| `scripts/generate_incidents.py` | `risk_level`, `component_scores` | Không đổi |
| `scripts/generate_priority_queue.py` | `component_scores` | Không đổi |
| `scripts/collect_timeline_events.py` | `risk_level`, `overall_score` | Không đổi |

---

## 7. Điều đã biết mà Sprint 6 không sửa

1. **`assets.json` cũng có hai schema.** `asset_builder.py` (gốc repo, Nessus
   pipeline) ghi khoá `all_assets` với `vulnerabilities` lồng nhau;
   `scripts/extract_asset_intelligence.py` (intelligence pipeline) ghi khoá
   `assets` với `critical`/`high` phẳng. Đây chính là lý do `risk_engine.py`
   luôn trả `overall_score: 0` — nó đọc `all_assets` trên tệp chỉ có `assets`.
   Ngoài phạm vi Sprint 6, nhưng là cùng một loại bệnh.

2. **`generate_daily_brief.py` tự chấm điểm riêng.** Nó cộng dồn phạt
   (`critical → +40`, `high → +20`, …) trong `generate_risk_assessment()` và
   **không** đọc `state/risk_score.json`. Daily Brief vì thế có con số riêng,
   không khớp portal. Đây là engine thứ ba theo nghĩa rộng — nhưng nó không ghi
   `risk_score.json` nên không thuộc nhiệm vụ "loại bỏ ghi đè" của Sprint 6.
