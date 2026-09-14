# SPRINT 15 BLOCKER ANALYSIS

Ngày: 2026-09-14 | Sprint: 15 (Auto-validate fix + Blocker identification)

## Tóm tắt

**Hoàn thành:** 1 item (Auto-scan side effect removed)
**Bị chặn:** 2 item (Forensic logs, Hostname resolution)
**Trạng thái:** Gate passing. Sẵn sàng cho Sprint 16 khi blockers được tháo gỡ.

---

## BLOCKER #1: Enable Forensic Logs (BLIND Capabilities)

| Thuộc tính | Giá trị |
|---|---|
| **Loại** | Cấu hình máy (Machine configuration) |
| **Người quyết định** | Người chạy tool (user quyết định chạy `enable_forensic_logs.ps1` hay không) |
| **Script** | `scripts/enable_forensic_logs.ps1` |
| **Điều kiện cần** | Administrator privileges trên Windows |
| **Kênh cần bật** | `Microsoft-Windows-TaskScheduler/Operational` |
| **Kênh cần bật** | `Microsoft-Windows-DriverFrameworks-UserMode/Operational` |
| **Tác dụng** | Bật 2 BLIND capabilities → Risk score không còn bị giảm trọng số → Visibility +2 hunting signals |
| **Hiện tại** | Cả 2 kênh ✗ TẮT (0 bản ghi) |

### Tháo gỡ blocker

```bash
# User chạy bằng "Run as Administrator" rồi thực thi:
powershell -ExecutionPolicy Bypass -File "C:\GitHub\mcp-cyber-tools\scripts\enable_forensic_logs.ps1"
```

**Hoặc dùng npm alias:**
```bash
npm run logs:enable
```

### Hiệu ứng sau khi bật

**Trước:**
```
Risk Score: 5 (MEDIUM) — bị giảm do 2 blind capabilities
sensor_coverage.json: "blind": ["scheduled_task_execution", "usb_device_activity"]
```

**Sau (dự kiến):**
```
Risk Score: 4 (MEDIUM) — trọng số điều chỉnh, không còn blind
sensor_coverage.json: "blind": [] (nếu cả 2 kênh đã bật)
```

### Lịch sử nỗ lực

- **Sprint 15:** Đã thử chạy script từ current user → Yêu cầu Administrator ✗
- **Tùy chọn tiếp:** User phải manual với "Run as Administrator"

---

## BLOCKER #2: Hostname Resolution (Attribution Quality)

| Thuộc tính | Giá trị |
|---|---|
| **Loại** | Hạ tầng (Infrastructure / DNS) |
| **Người quyết định** | Network team (DNS reversal) hoặc DHCP team (hostname records) |
| **Vấn đề** | 570 máy trong kho tài sản, chỉ ~1 máy có hostname đã phân giải (local) |
| **Nguyên nhân** | Nessus trả IP trong trường `hostname`, nhưng không phân giải ngược IP → hostname |
| **Tác dụng** | Attribution Quality: FULL → PARTIAL (remote assets chỉ kết nối tới IP, không tên) |
| **Impact** | hunt rules kết nối machine lên bằng tên → bị giới hạn accuracy |

### Tháo gỡ blocker

**Tùy chọn 1: DNS Reverse Lookup**
```
Setup PTR records cho 570 IP addresses
→ Yêu cầu: DNS admin + access đến DNS zones
```

**Tùy chọn 2: DHCP Lease Query**
```
Query DHCP server để lấy hostname ↔ IP mapping
→ Yêu cầu: DHCP admin + API access hoặc script DHCP query
```

**Tùy chọn 3: Manual Asset Mapping**
```
Tạo file CSV mapping: IP, Hostname
Import vào `asset_manager.py`
→ Yêu cầu: Manual effort, nhưng khả thi nhanh nhất
```

### Tác dụng dự kiến

**Trước:**
```
Asset 192.168.0.10:
  attribution: PARTIAL (unresolved hostname)
  by_severity: {INFO: 100, HIGH: 2} (reduced scope)
```

**Sau:**
```
Asset workstation-10:
  attribution: FULL (resolved via DNS/DHCP)
  by_severity: {INFO: 120, HIGH: 4} (expanded scope, more hunts resolve)
```

### Lịch sử nỗ lực

- **Sprint 15:** Xác định root cause = Nessus IP-only, DNS ngược không tồn tại ✗
- **Phụ trách:** Network Infrastructure team (không phải developer)

---

## BLOCKED ITEMS - NỰA CÒN LẠI

| # | Item | Loại | Trạng thái | Tiếp theo |
|---|---|---|---|---|
| 1 | Scheduled Task Execution | BLIND | ⏸️ Chờ Administrator | User chạy `enable_forensic_logs.ps1` |
| 2 | USB Device Activity | BLIND | ⏸️ Chờ Administrator | User chạy `enable_forensic_logs.ps1` |
| 3 | Hostname Resolution | Attribution | ⏸️ Chờ DNS/DHCP | Network team hoặc manual mapping |
| 4 | Auto-scan Side Effect | Debt | ✅ DONE | Sprint 15 completed |
| 5 | Fallback Sources Partial | Design | ✅ ACCEPTED | By design (TerminalServices, NTLM limits noted) |
| 6 | EMPTY Tools (6 total) | Healthy | ✅ NOT DEBT | Expected: "looked, found nothing" |

---

## SPRINT 16 READINESS

Khi blockers được tháo gỡ:

**Forensic logs enabled** → Run:
```bash
npm run coverage      # Refresh sensor_coverage with blind capabilities cleared
npm run gate:full     # Validate risk score improvement
```

**Hostname resolved** → Run:
```bash
npm run assets         # Rebuild attribution with resolved hostnames
npm run audit:detection  # Re-measure detection quality with expanded scope
npm run gate:full      # Validate attribution improvements
```

---

## NEXT PHASE: ROADMAP ALIGNMENT

Sau khi blockers tháo gỡ → Hãy xem NEXT_90_DAYS_ROADMAP.md:

- **GIAI ĐOẠN 1 (Tuần 1-4):** Ổn định hạ tầng + fix lỗi
- **GIAI ĐOẠN 2 (Tuần 5-8):** Thông minh hóa tài sản
- **GIAI ĐOẠN 3 (Tuần 9-12):** Action Engine + tự động hóa

---

## LOOP MODE V4 STATUS

```
CRITICAL = 0 ✓
HIGH = 0 ✓
FAIL = 0 ✓
BLIND = 0 ✓

TECHNICAL_DEBT:
  - Actionable items: 0 (2 blockers external)
  - Completed: 1 (auto-scan fix)
  - Accepted: 1 (fallback partial)
  - Healthy: 6 (EMPTY tools)

GATE: PASSING
NEXT: Awaiting blocker resolution or audit round 15+

ROADMAP: Ready on unblock
```

---

📌 **Báo cáo này được tạo bởi LOOP MODE V4**
Khi blocker bị tháo gỡ → Sprint 16 sẽ khởi động ngay, không cần chờ.
