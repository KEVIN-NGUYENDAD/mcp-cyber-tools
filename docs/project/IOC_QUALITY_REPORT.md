# IOC Quality Report

Sinh tự động bởi `scripts/ioc_quality.py`. Đừng sửa tay — sửa nguồn.

Cập nhật: 2026-09-14T13:50:42.584668

> **`confidence_score` KHÔNG phải mức độ nguy hiểm.** Nó trả lời một câu hẹp hơn nhiều: *quan sát này có đúng như nó tự nói không*. Một lần đăng nhập nền của Windows hoàn toàn có thể đạt 100 điểm tin cậy — đó là một quan sát chắc chắn về một việc hoàn toàn bình thường. Đọc một con số cao ở đây thành "nguy hiểm" là cách nhanh nhất để biến bảng này thành thứ ngược lại với mục đích của nó.

## Tóm tắt

| | |
|---|---|
| Tổng chỉ báo | **572** |
| Còn lại sau lọc tiếng ồn | **370** |
| Bị hạ xuống tiếng ồn | 202 |
| HIGH confidence | 370 |
| MEDIUM confidence | 0 |
| LOW confidence | 0 |
| Quy kết FULL | 368 |
| Quy kết PARTIAL | 2 |
| Quy kết UNATTRIBUTED | 0 |
| Kho tài sản đọc được | 11 máy |

## Theo cuộc săn

| Cuộc săn | Tổng | Tiếng ồn | Điểm TB | Phân bố tin cậy |
|---|---|---|---|---|
| `credential_dumping` | 0 | 0 | None | H 0 / M 0 / L 0 |
| `persistence` | 96 | 0 | 100.0 | H 96 / M 0 / L 0 |
| `lateral_movement` | 428 | 202 | 96.3 | H 226 / M 0 / L 0 |
| `suspicious_processes` | 48 | 0 | 97.3 | H 48 / M 0 / L 0 |

## High Confidence (≥ 75) — 370 chỉ báo

| Điểm | Số | Cuộc săn | Loại | Mức | Lớp bằng chứng | Bằng chứng | Quy kết |
|---|---|---|---|---|---|---|---|
| 100 | 143 | `lateral_movement` | Logon Activity | INFO | EVENT_LOG | COMPLETE | FULL |
| 100 | 80 | `persistence` | Persistence: ScheduledTask | INFO | SCHEDULED_TASK | COMPLETE | FULL |
| 100 | 35 | `suspicious_processes` | Network Connection | INFO | PROCESS_TABLE | COMPLETE | FULL |
| 100 | 16 | `persistence` | Persistence: RunKey | INFO | REGISTRY | COMPLETE | FULL |
| 100 | 3 | `suspicious_processes` | Living Off The Land Binary | INFO | PROCESS_TABLE | COMPLETE | FULL |
| 90 | 81 | `lateral_movement` | Logon Activity | INFO | EVENT_LOG | PARTIAL | FULL |
| 90 | 2 | `lateral_movement` | Logon Activity | INFO | EVENT_LOG | COMPLETE | PARTIAL |
| 87 | 7 | `suspicious_processes` | Network Connection | INFO | PROCESS_TABLE | PARTIAL | FULL |
| 87 | 2 | `suspicious_processes` | Network Connection | INFO | SERVICE | PARTIAL | FULL |
| 87 | 1 | `suspicious_processes` | Living Off The Land Binary | INFO | PROCESS_TABLE | PARTIAL | FULL |

## Medium Confidence (50–74) — 0 chỉ báo

_Không có._

## Low Confidence (< 50) — 0 chỉ báo

_Không có._

## Unattributed IOC — 0

Một chỉ báo không quy kết được về máy nào thì không hành động được: không biết cách ly cái gì, không biết hỏi ai.

_Không có chỉ báo nào bị bỏ lại không quy kết._

## Tiếng ồn bị hạ cấp — 202

Những mục này **vẫn nằm trong tệp state**, mang cờ `suppressed: true` kèm lý do. Xoá hẳn sẽ khiến không ai kiểm lại được quyết định lọc — và bộ lọc tiếng ồn chính là chỗ dễ giấu một phát hiện thật nhất.

| Loại tiếng ồn | Số lượng |
|---|---|
| ROUTINE_OS_ACTIVITY | 202 |

## Phân bố điểm

Một thang 0–100 mà mọi bản ghi đều rơi vào một ô thì không đo được gì. Bảng dưới đây để đọc chính điều đó — nếu chỉ có một hàng, thang điểm đang không phân biệt gì trên tập dữ liệu này, và đó là thông tin về *tập dữ liệu*, không phải về thang điểm.

| Khoảng điểm | Số chỉ báo |  |
|---|---|---|
| 100–109 | 277 | █████████████████████████████ |
| 90–99 | 83 | ████████ |
| 80–89 | 10 | █ |

## Cách tính điểm

| Thành phần | Tối đa | Đo cái gì |
|---|---|---|
| `evidence_fields` | 40 | Tỉ lệ trường có mặt **trên những trường lớp đó CÓ THỂ có** |
| `evidence_integrity` | 20 | Evidence có chứa mọi thứ chỉ báo viện dẫn không (bất biến Sprint 12) |
| `attribution` | 25 | FULL = IP + hostname + asset_id; PARTIAL = 60%; UNATTRIBUTED = 0 |
| `source_trust` | 15 | LIVE_OBSERVED 15 · OBSERVED 12 · DERIVED 6 · SIMULATED 0 |

Một chỉ báo bị đánh dấu tiếng ồn bị chặn trần dưới 50 điểm, nhưng `confidence_basis.raw_score` giữ nguyên điểm thô — nếu có mục bị lọc nhầm, phải thấy được nó vốn đáng bao nhiêu.

