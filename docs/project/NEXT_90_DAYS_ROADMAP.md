# LỘ TRÌNH PHÁT TRIỂN 90 NGÀY (NEXT 90 DAYS ROADMAP)

## GIAI ĐOẠN 1: ỔN ĐỊNH HẠ TẦNG & FIX LỖI (NGÀY 1-30) - Tập trung ROI: Ổn định vận hành
*   **Tuần 1:** 
    *   Xử lý triệt để lỗi triển khai trên Render.com (hoặc chuyển sang Vercel/Railway).
    *   Fix 4 lỗi Critical (C-001 đến C-004) bằng cách tái cấu trúc logic render trong `app.js`.
*   **Tuần 2:**
    *   **Migration:** Chuyển đổi dữ liệu từ file JSON sang SQLite.
    *   Triển khai lớp Authentication (Basic Auth hoặc JWT) cho Dashboard.
*   **Tuần 3:**
    *   Dọn dẹp code rác, xóa các file backup và file tạm ở root.
    *   Tách nhỏ `app.js` thành các module chức năng (AssetModule, IncidentModule, etc.).
*   **Tuần 4:**
    *   Thiết lập CI/CD cơ bản (GitHub Actions) để tự động kiểm tra lỗi cú pháp và deploy.

## GIAI ĐOẠN 2: THÔNG MINH HÓA TÀI SẢN (NGÀY 31-60) - Tập trung ROI: Giảm bề mặt tấn công
*   **Mục tiêu:** Giảm tỷ lệ "Unknown Assets" từ 60% xuống < 10%.
*   **Tính năng:**
    *   **Asset Command Center (V1.1):** Cho phép định danh tài sản trực tiếp từ Dashboard.
    *   **Asset Trust Score:** Tính điểm tin cậy cho từng thiết bị dựa trên lịch sử hoạt động.
    *   **Shadow Asset Detection:** Cảnh báo khi có thiết bị mới xuất hiện trong mạng mà chưa được khai báo.
    *   **Nessus Patch Queue Automation:** Tự động đề xuất danh sách bản vá ưu tiên dựa trên Risk Score.

## GIAI ĐOẠN 3: ACTION ENGINE & TỰ ĐỘNG HÓA (NGÀY 61-90) - Tập trung ROI: Tiết kiệm thời gian SOC
*   **Tính năng:**
    *   **Action Engine (V2.0):** Tích hợp nút bấm "Execute Remediation" (ví dụ: Chặn IP trên Firewall, Cô lập máy tính qua Defender).
    *   **Real-time Alert Stream:** Chuyển từ polling (30s) sang WebSocket để cập nhật sự cố ngay lập tức.
    *   **Executive Reporting Auto-generator:** Tự động gửi báo cáo PDF hàng tuần qua Telegram/Email cho CTO.
    *   **SaaS Preparation:** Đóng gói kiến trúc dưới dạng Docker Container để dễ dàng triển khai ở các môi trường khác nhau.

---

## 10 CƠ HỘI THƯƠNG MẠI HÓA TỐT NHẤT
1.  **Home SOC as a Service:** Cung cấp gói bảo mật cho các hộ gia đình có nhiều thiết bị thông minh (IoT).
2.  **MSSP Lite cho SMB:** Nền tảng quản lý an ninh giá rẻ cho doanh nghiệp vừa và nhỏ không có đội ngũ SOC.
3.  **Vulnerability Management App:** Bán module quản lý lỗ hổng tích hợp Nessus.
4.  **Compliance Dashboard:** Tùy chỉnh Dashboard để theo dõi các chỉ số tuân thủ (ISO 27001, PCI DSS).
5.  **Asset Intelligence API:** Bán dữ liệu định danh thiết bị cho các hệ thống quản trị mạng khác.
6.  **MCP Tool Library:** Cung cấp bộ công cụ săn tìm mối đe dọa dưới dạng subscription.
7.  **Managed EDR Service:** Tích hợp sâu với Microsoft Defender để quản lý endpoint tập trung.
8.  **WAAP Management Overlay:** Giao diện quản lý đơn giản hóa cho các hệ thống WAAP phức tạp.
9.  **Security Awareness Dashboard:** Hiển thị rủi ro mạng để đào tạo ý thức nhân viên.
10. **White-label SOC Platform:** Cho phép các công ty IT khác dán nhãn (rebrand) SentinelOps thành sản phẩm của họ.
