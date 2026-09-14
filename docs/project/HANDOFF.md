# HANDOFF

Sinh tự động bởi `scripts/generate_handoff.py`. **Đừng sửa tay** — mọi con số dưới đây đọc thẳng từ `state/` lúc chạy.

Cập nhật: 2026-09-14T13:48:15.722973

## Trạng thái kho lúc chạy cổng

| | |
|---|---|
| Commit lúc chạy | `fc0441c` |
| Branch | `feature/invalidation-and-run-isolation` |
| Tiêu đề | fix(handoff): stop claiming a commit the file cannot know, and date the stale row |
| Cây làm việc | CÓ THAY ĐỔI CHƯA COMMIT |

Cây làm việc có thay đổi chưa commit, nên commit ở trên là của sprint
**trước**; công của sprint này chưa có định danh. Đó là thứ tự đúng —
cổng chạy trước khi commit — không phải một con số trễ.

## Cổng merge

| | |
|---|---|
| PASS | 93 |
| EMPTY | 6 |
| BLIND | 0 |
| FAIL | 0 |
| Pipeline | 28 stage, 0 thất bại |
| Toàn vẹn bằng chứng | 0 vi phạm / 573 chỉ báo _(vừa đo)_ |

## Trạng thái thật (đọc từ state/)

| | |
|---|---|
| Risk Score | 23/100 |
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

_Cả hai nửa vừa đo trong cùng một lần chạy tool_validator._

## Việc tiếp theo

1. Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.
2. Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.
3. `npm run gate` trước khi mở PR.

## Tài liệu handoff viết tay

`AI_HANDOFF.md` và `SESSION_STATE.md` là bản viết tay ngày 2026-09-07. Chúng **không được cập nhật theo state** và số liệu trong đó đã sai nhiều lần. Đọc tệp này thay cho chúng.

