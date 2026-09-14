# HANDOFF

Sinh tự động bởi `scripts/generate_handoff.py`. **Đừng sửa tay** — mọi con số dưới đây đọc thẳng từ `state/` lúc chạy.

Cập nhật: 2026-09-14T13:29:40.078930

## Sprint vừa xong

| | |
|---|---|
| Commit | `f0b8ba7` |
| Branch | `feature/invalidation-and-run-isolation` |
| Tiêu đề | fix(truth): cut the incidents<->risk feedback loop, stamp every state file with its run |
| Cây làm việc | CÓ THAY ĐỔI CHƯA COMMIT |

## Cổng merge

| | |
|---|---|
| PASS | 94 |
| EMPTY | 5 |
| BLIND | 0 |
| FAIL | 0 |
| Pipeline | 28 stage, 0 thất bại |
| Toàn vẹn bằng chứng | 0 vi phạm / 434 chỉ báo |

## Trạng thái thật (đọc từ state/)

| | |
|---|---|
| Risk Score | 22/100 |
| Risk Level | LOW |
| Sự cố đang mở | 1 |
| └ CRITICAL | 0 |
| └ HIGH | 1 |
| Phát hiện cấp điều hành | 2 |
| └ cảnh báo chất lượng | 0 |
| Rule không kết luận được | 2 |

## Vùng quan sát

| Nguồn / Năng lực | Trạng thái |
|---|---|
| `defender` | covered |
| `firewall` | covered |
| `security_log` | covered |
| `event_logs` | covered |
| `persistence` | covered |
| `processes` | covered |
| `network` | covered |
| `ioc` | covered |
| **Security Log** | covered |
| **Process Creation** | covered |
| **Script Block Logging** | covered |
| **Scheduled Task Execution** | blind |
| **USB Device Activity** | blind |

_Phần cảm biến (đọc được hay không) vừa dò lại. Phần kết quả tool là của lần chạy tool_validator gần nhất (5.2 giờ trước)._

## Việc tiếp theo

1. Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.
2. Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.
3. `npm run gate` trước khi mở PR.

## Tài liệu handoff viết tay

`AI_HANDOFF.md` và `SESSION_STATE.md` là bản viết tay ngày 2026-09-07. Chúng **không được cập nhật theo state** và số liệu trong đó đã sai nhiều lần. Đọc tệp này thay cho chúng.

