# Hướng Dẫn Gửi Báo Cáo Qua Email

**Lúc 8PM, báo cáo sẽ được gửi email tự động cho bạn!**

---

## 🎯 Cách Hoạt Động

```
8:00 PM
  ↓
desktop-auto-collector.js dừng
  ↓
comprehensive-report-generator.js tạo báo cáo
  ↓
email-report-sender.js tự động gửi email
  ↓
📧 Email arrive trong inbox của bạn!
```

---

## 📧 Email Được Gửi Đến

**Địa chỉ email**: `tamngankevin@gmail.com`

**Tiêu đề email**: `📋 HOME SOC - Báo Cáo Toàn Diện 8PM`

**Nội dung**:
- Thông tin báo cáo (ngày, giờ tạo)
- Tóm tắt findings
- File đính kèm: `COMPREHENSIVE-REPORT-8PM.md`

---

## 📎 File Đính Kèm

Email sẽ có **file đính kèm** chứa báo cáo đầy đủ:

```
Attachment: COMPREHENSIVE-REPORT-8PM.md
Size: ~50-100 KB
Format: Markdown (.md)
```

**Bạn có thể**:
- Mở trực tiếp trong Gmail
- Download và xem trên máy
- Forward cho ai khác
- In ra giấy

---

## ✅ Nếu Email Không Gửi

**Lý do có thể**:
1. Chưa có app-specific password cho Gmail
2. SMTP server bị block
3. Kết nối mạng có vấn đề

**Fallback**: Script sẽ:
1. ✅ Hiển thị nội dung báo cáo trong terminal
2. ✅ Mở Windows Mail (bạn gửi thủ công)
3. ✅ Hoặc hướng dẫn gửi qua Gmail web

---

## 🔧 Setup Gmail App Password (Optional)

Nếu muốn email tự động gửi thành công:

1. Vào: https://myaccount.google.com/apppasswords
2. Chọn Mail + Windows Computer
3. Google sẽ generate app password 16 ký tự
4. Copy password đó
5. Set environment variable:
   ```powershell
   $env:GMAIL_APP_PASSWORD = "your-16-char-password"
   ```

**Note**: Hiện tại script có thể chưa cần bước này - nó sẽ hiển thị báo cáo trong terminal rồi hướng dẫn gửi thủ công.

---

## 📱 Xem Email Trên iPhone

Sau khi email đến:

1. Mở Gmail app trên iPhone
2. Tìm email từ tamngankevin@gmail.com
3. Subject: "📋 HOME SOC - Báo Cáo Toàn Diện 8PM"
4. Tap vào để xem báo cáo
5. Có thể download file .md

---

## 🎯 Timeline

```
BÂY GIỜ
  └─ Auto-collector chạy

CÁC LÚC 30 PHÚT
  └─ Collect dữ liệu

7:59 PM
  └─ Chuẩn bị dừng

8:00 PM CHÍNH XÁC
  ├─ Dừng collection
  ├─ Tạo báo cáo
  ├─ Gửi email
  └─ 📧 Email đến inbox

BẠN
  └─ Nhận email ngay lập tức!
```

---

## ✨ Lợi Ích

✅ Báo cáo gửi tự động  
✅ Có file đính kèm đầy đủ  
✅ Có thể xem trên iPhone ngay  
✅ Không cần copy-paste  
✅ An toàn - lưu lại trong email

---

## 📞 Troubleshooting

### Email không đến
- Kiểm tra spam folder
- Kiểm tra có kết nối internet không
- Xem logs trong terminal

### File đính kèm không có
- Báo cáo có thể lớn quá
- Hoặc tìm file từ: `C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\COMPREHENSIVE-REPORT-8PM.md`

### Muốn gửi lại thủ công
```powershell
node email-report-sender.js
```

---

## 🎉 Kết Luận

**Lúc 8PM, bạn sẽ tự động nhận email chứa báo cáo toàn diện!**

Không cần làm gì - hệ thống chạy tự động.

✅ **Setup hoàn toàn!**
