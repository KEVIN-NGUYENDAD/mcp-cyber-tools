# Technical Debt

Sinh tự động bởi `scripts/sprint_gate.py`. Đừng sửa tay — sửa nguồn.

Cập nhật: 2026-09-14T07:01:00

## Cổng merge

| | |
|---|---|
| Đủ điều kiện merge | **CÓ** |
| PASS | 93 |
| EMPTY | 6 |
| BLIND | 0 |
| FAIL | 0 |
| Bộ kiểm phát hiện | ĐẠT |
| Toàn vẹn bằng chứng | 0 vi phạm / 610 chỉ báo |
| Pipeline | 26 stage, 0 thất bại |
| Trường portal đọc sai | 0 |
| Trường Telegram đọc sai | 0 |

## Nợ đo được trong lần chạy này

| Hạng mục | Chi tiết | Mức |
|---|---|---|
| Tool EMPTY | 6 tool đọc được nguồn nhưng không có bản ghi nào khớp | Không phải nợ — đây là "đã nhìn, không có gì". Ghi ra để không ai nhầm nó với BLIND. |

## Nợ đã ghi nhận nhưng chưa trả

Những món này không suy ra được từ số liệu — chúng là quyết định đã
hoãn lại, kèm lý do. Danh sách nằm trong `scripts/tool_validator.py`.

| # | Món nợ | Vì sao chưa trả |
|---:|---|---|
| 1 | Log `Microsoft-Windows-TaskScheduler/Operational` và `Microsoft-Windows-DriverFrameworks-UserMode/Operational` đang TẮT | Bật chúng là thay đổi cấu hình máy. Cho tới lúc đó, "không có bản ghi nào" ở hai nguồn này nghĩa là chưa ai từng ghi, không phải không có gì xảy ra. |
| 2 | Nguồn thay thế chỉ che được MỘT PHẦN vùng mù: TerminalServices thấy phiên chứ không thấy chi tiết xác thực; NTLM thấy NTLM chứ không thấy Kerberos | Đây là giới hạn của chính các log đó, không sửa được bằng mã. Mọi bản ghi từ nguồn thay thế đều mang cờ `Fallback = true` để không ai nhầm bớt mù với hết mù. |
| 3 | `state/sensor_coverage.json` không tự làm mới theo pipeline | tool_validator.py gọi thật 99 tool và có tác dụng phụ (ghi báo cáo, quét). Portal hiển thị tuổi của dữ liệu và cảnh báo khi quá 24 giờ. |

Đã trả (đo được trong lần chạy này):

- ✅ Log Security vẫn đóng — 5 tool còn mù, và chưa thể biết audit 4688 bật hay tắt
- ✅ Script Block Logging chỉ PARTIAL: log `PowerShell/Operational` đọc được và có sự kiện 4104, nhưng chính sách `EnableScriptBlockLogging` đang TẮT

