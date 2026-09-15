# AUDIT_QUEUE_ACTIVE.md
**Last updated:** 2026-09-14 · **Status:** LOOP MODE · **Context:** Distilled for token efficiency

---

## TOP 5 CRITICAL (Open)

| ID | Root Cause | Impact | Status |
|---|---|---|---|
| **AQ-019 / AQ-031** | `ioc_quality.py:308` miễn trừ HIGH khỏi noise; behavior intact, data varies | Risk oscillates 10→3 without code change; 436→356→266 indicators across runs | ✅ Vòng 7: fixture khoá ROUTINE_HINTS lọc ở mọi mức (SYSTEM SID HIGH/CRITICAL), tách khỏi DEV_HINTS — `tests/ioc_quality/test_ioc_quality.py`, chạy trong `test:detection` / gate |
| **AQ-020 / AQ-032** | `collect_crypto_inventory.py:137` ghi int, dòng 147 đọc chuỗi; `severity_counts[0]=17, [2]=2` pero `MEDIUM=0` | `crypto_score` hằng 100; `total_findings 19` cạnh `severity_breakdown sum 0` | ✅ Vòng 7: `normalize_severity()` chuẩn hoá tại điểm đọc + bất biến tự kiểm (`sum(breakdown) == len(findings)`) đã có trong code; fixture khoá lại bằng `tests/crypto_inventory/test_crypto_inventory.py`, chạy trong `test:detection` / gate |
| **AQ-021** | Nessus state: `total 64`; assets.json: `sum 399`; daily_brief: in cả hai | Brief tự mâu thuẫn 3.4×; scan 158h tuổi, `scanner_status: running` | ✅ Vòng 7: không phải lỗi đếm — 64 (plugin) và 399 (lượt host×plugin) đều đúng, khác đơn vị (`total_unit`/`total_instances` đã có từ vòng trước trong `nessus_status.json`); `generate_daily_brief.py` giờ in cả hai kèm nhãn + `scan_stale` (ngưỡng 48h); `get_scanner_status()` đổi nhãn `'on' → 'online'` (không còn `'running'`, tên trạng thái LIÊN KẾT scanner, không phải job đang chạy) — `tests/nessus_snapshot/test_nessus_snapshot.py`, chạy trong `test:detection` / gate |
| **AQ-013 / AQ-026** | `sprint_gate.py:181` + `generate_handoff.py:112` đọc `s.get('success', True)` nhưng writer dùng `status` | Pipeline luôn 0 fail; cổng merge không thể nói không | ✅ Vòng 6: đã sửa (status is None → BLOCKER) |
| **AQ-002** | `attribution.full == 602/602` nhưng `hostname == 'unresolved'` trên 11/11 assets | Claim FULL attribution trong khi toàn bộ target host unknown | ❌ Chờ audit chi tiết |

---

## TOP 5 HIGH (Open)

| ID | Root Cause | Impact | Status |
|---|---|---|---|
| **AQ-030 / AQ-007** | `render.yaml`: `node web-server.js`; bộ ghi HTML ở `send_daily_brief_telegram.py:278`, không trong pipeline | Portal `web/app.js` (đã sửa 86/86 XSS) không được deploy; user mở `latest.html` (09-13) | ❌ Chọn entrypoint, đưa brief HTML vào pipeline |
| **AQ-033 / AQ-028 / AQ-022** | `generate_handoff.py` là lệnh thủ công, không run sau merge/pipeline; đọc cache `tool_validation.json` | HANDOFF.md mô tả sprint trước; Risk 10→3, indicators 602→497 không phản ánh | ❌ Handoff thành stage + live read |
| **AQ-023** | `analyze_firewall()` chỉ return 20 hoặc 90; không đọc 3 profile + `blocked_connections` | Hằng số được trình bày như số đo | ✅ Vòng 6: sửa, chấm theo profile; enabled is None → None |
| **AQ-034 / AQ-025** | `pipeline_field_audit.py` scope 76 file nhưng coverage 17.1% (106/619 calls); TECHNICAL_DEBT.md in `0` trần | Công cụ tự in phạm vi; tiêu đề bỏ dòng đó | ❌ In mẫu số; phát hiện hàm nạp state theo cấu trúc |
| **AQ-024** | `web/app.js:1630-1631` dùng `\|\| 'MEDIUM'`; không lọc suppressed (208); không sort top-10 | Portal in 577 mối đe doạ (giá trị cache); sự thật 369; chỉ báo thiếu severity bịa "MEDIUM" | 🔶 Số đếm sửa; default severity vẫn bịa |

---

## AQ-035 · NEW CRITICAL
**Issue:** `state/` không atomicity. Lúc audit: `risk_score.json` (08:11:54, lần N) khai `credential_dumping 6C` nhưng `hunting_credential_dumping.json` (08:12:27, lần N+1) = 0 chỉ báo. Risk 31/HIGH đang trích dẫn 6 chỉ báo không tồn tại.

**Root:** Pipeline ghi stage-by-stage vào `state/` mà không `run_id` hoặc ảnh chụp nguyên tử. Lần N+1 bắt đầu trong lúc N chưa xong.

**Suggested:** SPRINT RUN-ISOLATION — mỗi run sinh `run_id`; tệp mang `run_id + pipeline_started_at`; consumer kiểm đồng nhất; lock file; sprint_gate kiểm multiple run_id.

---

## OPEN DEBT SUMMARY

**Trạng thái tích luỹ:**
- ✅ Closed (vòng 1–6): AQ-001, 003, 006, 008, 009, 010, 012, 014, 015, 026, 023, 013
- ✅ Closed (vòng 7): AQ-019/031, AQ-020/032, AQ-021
- ❌ Open CRITICAL: 2 (AQ-002, AQ-035)
- ❌ Open HIGH: 5 (AQ-030, 033, 024, 034, AQ-016–018, 029 remainder)
- **Total:** ~10 items, **2 CRITICAL + 8 HIGH**

**Next Audit Focus:**
1. **AQ-035:** Run isolation — state consistency
2. **AQ-002:** Attribution vs hostname
3. **AQ-030/007:** Portal entrypoint không được deploy
4. **AQ-033/028/022:** Handoff thành stage + live read
5. **AQ-034/025:** Pipeline field audit mẫu số

---

*Token-efficient tracking. Full AUDIT_QUEUE.md archived; historical rounds 1–6 summarized in HANDOFF drift notes.*
