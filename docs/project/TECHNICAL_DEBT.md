# Technical Debt

Sinh tự động bởi `scripts/sprint_gate.py`. Đừng sửa tay — sửa nguồn.

Cập nhật: 2026-09-14T07:41:12

## Cổng merge

| | |
|---|---|
| Đủ điều kiện merge | **CÓ** |
| PASS | 94 |
| EMPTY | 5 |
| BLIND | 0 |
| FAIL | 0 |
| Bộ kiểm phát hiện | ĐẠT |
| Toàn vẹn bằng chứng | 0 vi phạm / 602 chỉ báo |
| Pipeline | 27 stage, 0 thất bại |
| Trường portal đọc sai | 0 |
| Trường Telegram đọc sai | 0 |

## Nợ đo được trong lần chạy này

| Hạng mục | Chi tiết | Mức |
|---|---|---|
| Tool EMPTY | 5 tool đọc được nguồn nhưng không có bản ghi nào khớp | Không phải nợ — đây là "đã nhìn, không có gì". Ghi ra để không ai nhầm nó với BLIND. |
| Năng lực: Scheduled Task Execution | Kênh Microsoft-Windows-TaskScheduler/Operational đang TẮT — việc tác vụ được tạo, sửa và CHẠY không được ghi ở đâu cả. Không có kênh này, huntSuspiciousTasks chỉ thấy tác vụ đang còn tồn tại — không thấy tác vụ đã chạy x | BLIND |
| Năng lực: USB Device Activity | Kênh Microsoft-Windows-DriverFrameworks-UserMode/Operational đang TẮT — việc thiết bị USB được cắm vào không được ghi ở đâu cả. usbLogs không có nguồn nào khác cho câu hỏi "cái gì đã được cắm vào máy này, lúc nào". | BLIND |

## Nợ đã ghi nhận nhưng chưa trả

Những món này không suy ra được từ số liệu — chúng là quyết định đã
hoãn lại, kèm lý do. Danh sách nằm trong `scripts/tool_validator.py`.

| # | Món nợ | Vì sao chưa trả |
|---:|---|---|
| 1 | Log `Microsoft-Windows-TaskScheduler/Operational` và `Microsoft-Windows-DriverFrameworks-UserMode/Operational` đang TẮT | Bật chúng là thay đổi cấu hình máy, nên phải do người quyết định chạy: MỘT LẦN `scripts/enable_forensic_logs.ps1` dưới quyền Administrator. Cho tới lúc đó, "không có bản ghi nào" ở hai nguồn này nghĩa là chưa ai từng ghi, không phải không có gì xảy ra — và hai năng lực `scheduled_task_execution`, `usb_device_activity` giữ ô ❌ BLIND thay vì im lặng. |
| 2 | Không máy nào trong kho tài sản có tên đã phân giải — mọi quy kết về máy ở xa vì thế dừng ở mức PARTIAL | Nessus trả IP trong chính trường `hostname` của nó, và bản cũ chép giá trị đó sang cả hai cột: một cột "Hostname" hiện `192.168.0.10` trông như đã phân giải được tên. Sprint 17 gọi thẳng nó là chưa phân giải, nên con số quy kết tụt xuống — đó là số thật xuất hiện, không phải chất lượng giảm. Máy cục bộ vẫn đủ tên vì nó tự biết tên mình. Trả nợ cần một nguồn tên thật (DNS ngược, DHCP, hoặc một kho khác), là quyết định về hạ tầng. |
| 3 | Nguồn thay thế chỉ che được MỘT PHẦN vùng mù: TerminalServices thấy phiên chứ không thấy chi tiết xác thực; NTLM thấy NTLM chứ không thấy Kerberos | Đây là giới hạn của chính các log đó, không sửa được bằng mã. Mọi bản ghi từ nguồn thay thế đều mang cờ `Fallback = true` để không ai nhầm bớt mù với hết mù. |
| 4 | Làm mới tự động nửa KẾT QUẢ TOOL kéo theo một lần `defenderQuickScan` mỗi ngày | Sprint 16 cho pipeline tự khởi chạy tool_validator ở nền khi nửa tool quá 20 giờ — không còn phải chạy tay. Nhưng validator gọi THẬT cả 99 tool, và một trong số đó khởi động quét nhanh Defender. Đó là tác dụng phụ có thật của việc tự động hoá, và chỗ của nó là bảng nợ chứ không phải một dòng chú thích không ai đọc. Tắt bằng cách bỏ cờ `--auto-validate` ở stage 18A. |

Đã trả (đo được trong lần chạy này):

- ✅ Log Security vẫn đóng — 5 tool còn mù, và chưa thể biết audit 4688 bật hay tắt
- ✅ Script Block Logging chỉ PARTIAL: log `PowerShell/Operational` đọc được và có sự kiện 4104, nhưng chính sách `EnableScriptBlockLogging` đang TẮT

