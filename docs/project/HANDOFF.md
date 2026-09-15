# HANDOFF

Sinh tự động bởi `scripts/generate_handoff.py`. **Đừng sửa tay** — mọi con số dưới đây đọc thẳng từ `state/` lúc chạy.

Cập nhật: 2026-09-14T20:02:47.964767

## Trạng thái kho lúc chạy cổng

| | |
|---|---|
| Commit lúc chạy | `1d5cda6` |
| Branch | `feature/invalidation-and-run-isolation` |
| Tiêu đề | fix: AQ-034 expose pipeline field audit coverage scope in TECHNICAL_DEBT |
| Cây làm việc | CÓ THAY ĐỔI CHƯA COMMIT |

Cây làm việc có thay đổi chưa commit, nên commit ở trên là của sprint
**trước**; công của sprint này chưa có định danh. Đó là thứ tự đúng —
cổng chạy trước khi commit — không phải một con số trễ.

## Cổng merge

| | |
|---|---|
| **Đủ điều kiện merge** | **CÓ** |

| | |
|---|---|
| PASS | 93 |
| EMPTY | 6 |
| BLIND | 0 |
| FAIL | 0 |
| Pipeline | 33 stage, 0 thất bại |
| Toàn vẹn bằng chứng | 0 vi phạm / 570 chỉ báo _(vừa đo)_ |

## Trạng thái thật (đọc từ state/)

| | |
|---|---|
| Risk Score | 5/100 |
| Risk Level | MEDIUM |
| Sự cố đang mở | 1 |
| └ CRITICAL | 0 |
| └ HIGH | 1 |
| Phát hiện cấp điều hành | 2 |
| └ cảnh báo chất lượng | 0 |
| Rule không kết luận được | 2 |

## Vùng quan sát

Hai bảng dưới đây trả lời hai câu hỏi khác nhau, và một bảng xanh không
bù được cho bảng kia đỏ.

### Mù nguồn — nguồn có mở để đọc được không

| Nguồn | Trạng thái |
|---|---|
| `defender` | covered |
| `firewall` | covered |
| `security_log` | covered |
| `event_logs` | covered |
| `persistence` | covered |
| `processes` | covered |
| `network` | covered |
| `ioc` | covered |

### Mù năng lực — thứ ta cần có được ghi lại không

| Năng lực | Trạng thái | Cách sửa |
|---|---|---|
| Security Log | covered | — |
| Process Creation | covered | — |
| Script Block Logging | covered | — |
| Scheduled Task Execution | **blind** | scripts\enable_forensic_logs.ps1 (cần Administrator) |
| USB Device Activity | **blind** | scripts\enable_forensic_logs.ps1 (cần Administrator) |

> **2 năng lực đang mù.** Một nguồn `covered` KHÔNG có nghĩa là kỹ
> thuật tương ứng quan sát được: `persistence` mở được, nhưng
> *Scheduled Task Execution* thì không được ghi ở đâu cả. Điểm rủi ro
> đã rút trọng số tương ứng và không được phép xuống `LOW`.

_Cả hai nửa vừa đo trong cùng một lần chạy tool_validator._

## Việc tiếp theo

1. Đọc `docs/project/AUDIT_QUEUE.md` — còn CRITICAL/HIGH thì sửa trước.
2. Đọc `docs/project/TECHNICAL_DEBT.md` — nợ đo được và nợ ghi nhận.
3. `npm run gate` trước khi mở PR.

## Tài liệu handoff viết tay

`AI_HANDOFF.md` và `SESSION_STATE.md` là bản viết tay ngày 2026-09-07. Chúng **không được cập nhật theo state** và số liệu trong đó đã sai nhiều lần. Đọc tệp này thay cho chúng.

