# PHIẾU THEO DÕI NỢ KỸ THUẬT (TECHNICAL DEBT REGISTER)

## 1. NỢ KIẾN TRÚC (ARCHITECTURE DEBT)
| Vấn đề | Tác động | Mức độ | Giải pháp đề xuất |
|---|---|---|---|
| **Flat File DB (JSON)** | Không hỗ trợ truy vấn phức tạp, rủi ro race-condition khi ghi file, không có transaction. | **CRITICAL** | Chuyển sang SQLite hoặc PostgreSQL. |
| **Monolithic app.js** | Khó bảo trì, dễ gây lỗi side-effect khi sửa một function render. | **HIGH** | Tách nhỏ thành các Component/Module JS. |
| **Synchronous Pipeline** | Scripts Python chạy tuần tự có thể gây chậm trễ cập nhật dữ liệu. | **MEDIUM** | Chuyển sang kiến trúc hướng sự kiện (Event-driven) hoặc dùng Message Queue (Redis). |
| **Coupled UI-Data** | Logic hiển thị trộn lẫn với logic xử lý dữ liệu ở Frontend. | **HIGH** | Áp dụng mô hình MVC hoặc State Management (Redux-like). |

## 2. NỢ MÃ NGUỒN (CODE DEBT)
| Vấn đề | Chi tiết | Mức độ |
|---|---|---|
| **Duplicate Logic** | Logic tính toán Risk Score xuất hiện ở cả Python (`calculate_risk_score.py`) và đôi khi bị parse lại ở JS. | **MEDIUM** |
| **Dead Code** | Các file `server_v2.js`, `server_backup_v1.js` và `test.js` tồn tại ở root gây nhiễu. | **LOW** |
| **Global State** | Biến `stateData` trong `app.js` được dùng chung cho tất cả render functions mà không có kiểm soát truy cập. | **HIGH** |
| **Hardcoded Paths** | Nhiều scripts Python sử dụng đường dẫn tuyệt đối hoặc tương đối cứng nhắc. | **MEDIUM** |

## 3. NỢ VẬN HÀNH (OPERATIONAL DEBT)
| Vấn đề | Chi tiết | Mức độ |
|---|---|---|
| **No CI/CD** | Việc deploy phụ thuộc vào Render Auto-deploy (đang lỗi) mà không có pipeline kiểm tra chất lượng code trước khi đẩy lên. | **CRITICAL** |
| **Missing Logs** | Thiếu hệ thống quản lý log tập trung cho các scripts thu thập dữ liệu (hiện tại mỗi script ghi log riêng lẻ). | **MEDIUM** |
| **Manual Validation** | Việc kiểm tra độ chính xác của Asset Discovery vẫn phụ thuộc vào mắt người nhìn Dashboard. | **HIGH** |

## 4. DANH SÁCH MÃ NGUỒN "RÁC" & TRÙNG LẶP
1.  **Files trùng lặp:**
    *   `server.js`, `server_v2.js`, `server_v1.0.js` (trong releases) -> Cần chuẩn hóa về một server duy nhất.
    *   `collect_nessus_snapshot.py` và `collect_nessus_snapshot_debug.py`.
2.  **Logic trùng lặp:**
    *   Hệ thống tính điểm WAAP Score và Risk Score có nhiều đoạn code parse JSON tương tự nhau.
3.  **Mã nguồn chết (Dead code):**
    *   Các file `.txt` (live-error, tabs-error, final-test) ở root nên được xóa.
    *   Thư mục `C:Userstamng...` (tên thư mục lỗi do copy/paste) cần được dọn dẹp.

---
**Tổng kết:** Nợ kỹ thuật lớn nhất nằm ở **Data Layer**. Việc giải quyết nợ này là điều kiện tiên quyết để SentinelOps có thể mở rộng lên quy mô > 50 tài sản.
