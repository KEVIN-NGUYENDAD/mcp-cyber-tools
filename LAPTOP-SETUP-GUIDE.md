# Hướng Dẫn Setup Laptop Auto-Collector

**Laptop sẽ thu thập dữ liệu song song với Desktop, sau đó sync cho báo cáo toàn diện!**

---

## 📋 Chuẩn Bị Laptop

### Yêu Cầu
- ✅ Node.js cài sẵn (npm run certify đã test)
- ✅ PowerShell 5.0+
- ✅ Kết nối mạng (WiFi hoặc Ethernet)
- ✅ Khoảng cách gần Desktop (để sync)

---

## 🚀 Cách 1: Deploy Qua Claude (Nếu Có Sync)

### **Bước 1: Trên Laptop, mở Claude**

1. Đăng nhập Claude trên Laptop
2. Vào project: `mcp-cyber-tools`
3. Pull file: `laptop-auto-collector.js`

### **Bước 2: Tạo Startup Shortcut Trên Laptop**

```powershell
# Mở PowerShell

cd "C:\Users\[YOUR-LAPTOP-USERNAME]\AppData\Roaming\Claude\Projects\mcp-cyber-tools"

# Tạo batch file
@echo off > START-LAPTOP-COLLECTION.bat
echo cd /d "%CD%" >> START-LAPTOP-COLLECTION.bat
echo node laptop-auto-collector.js >> START-LAPTOP-COLLECTION.bat
```

### **Bước 3: Setup Startup Shortcut**

**Trên Laptop**:
```
Windows Key + R
shell:startup
```

Tạo shortcut để `START-LAPTOP-COLLECTION.bat`

### **Bước 4: Restart Laptop**

Lúc boot → auto-collector tự chạy!

---

## 🚀 Cách 2: Manual Deployment (Nếu Không Có Claude Sync)

### **Bước 1: Copy File Từ Desktop Sang Laptop**

```
Desktop:  C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\laptop-auto-collector.js
Laptop:   Sao chép vào cùng vị trí tương đương
```

**Hoặc**: Upload qua email/USB/Cloud

### **Bước 2: Tạo Startup Shortcut (Như Trên)**

### **Bước 3: Run Ngay Hoặc Restart**

---

## 📊 Dữ Liệu Laptop Collect

Mỗi 30 phút, Laptop capture:
- ✅ **Processes** (20 processes)
- ✅ **Network** (15 connections)
- ✅ **Battery** (charge %, status) ← Laptop-specific
- ✅ **WiFi** (connection status) ← Laptop-specific
- ✅ **Memory** (usage %)

---

## 📁 Output Trên Laptop

```
laptop-collection-data/
  ├── snapshot-1.json
  ├── snapshot-2.json
  └── snapshot-N.json

laptop-collection-log.json
LAPTOP-AUTO-COLLECTION-REPORT.md
```

---

## 🔄 Sync Laptop Data Với Desktop

Sau 8PM, khi cả Desktop và Laptop hoàn tất:

### **Bước 1: Copy Laptop Data Sang Desktop**

```
Từ Laptop:
  C:\Users\[LAPTOP-USER]\...\laptop-collection-data\
  
Sang Desktop:
  C:\Users\tamng\AppData\Roaming\Claude\Projects\mcp-cyber-tools\laptop-collection-data\
```

**Hoặc**: Upload qua cloud/email

### **Bước 2: Chạy Comprehensive Report (Trên Desktop)**

```powershell
node comprehensive-report-generator.js
```

Report sẽ auto-include Laptop data!

### **Bước 3: Email Được Gửi**

```
COMPREHENSIVE-REPORT-8PM.md
├─ Desktop data (30-min snapshots)
├─ Laptop data (30-min snapshots)
├─ WiFi analysis
├─ iPhone detection
└─ 30+ action recommendations
```

---

## ⏰ Timeline Laptop

```
NGAY BÂY GIỜ (sau khi setup)
  └─ Laptop auto-collection khởi động

MỖI 30 PHÚT
  └─ Collect dữ liệu Laptop

8:00 PM
  └─ Dừng collection
  └─ Tạo LAPTOP-AUTO-COLLECTION-REPORT.md

SAU 8PM
  └─ Sync data sang Desktop
  └─ Chạy comprehensive report
  └─ Email gửi đi (cả Desktop + Laptop)
```

---

## 🎯 Trên Laptop, Bạn Sẽ Thấy

```
💻 HOME SOC - LAPTOP AUTO COLLECTOR

⏰ Started: 2:30:15 PM
🎯 Will run until: 20:00
📁 Data directory: laptop-collection-data

📊 [Collection #1] 2:30:15 PM
  • Capturing processes...
  • Capturing network...
  • Capturing battery...
  ✅ Saved to snapshot-1.json

[30 minutes pass]

📊 [Collection #2] 3:00:15 PM
  ...

[Repeat until 8PM]

⏰ 8PM reached - stopping collection

🎉 LAPTOP AUTO COLLECTION COMPLETE
📊 Collected: 13 snapshots
📁 Data: laptop-collection-data/
📋 Report: LAPTOP-AUTO-COLLECTION-REPORT.md

✅ Laptop data ready for Desktop sync!
```

---

## 💡 Tips

### **Nếu Laptop Tắt Trước 8PM**
- Collection dừng
- Data lưu từ khi khởi động tới khi tắt
- Khi restart → tiếp tục từ lúc khởi động mới

### **Nếu Quên Setup Trước 8PM**
- Có thể chạy manual: `node laptop-auto-collector.js`
- Hoặc chạy Cách 1 (batch file)

### **Nếu Muốn Stop Trước 8PM**
- Đóng command window hoặc Ctrl+C
- Data đã thu thập được giữ lại

---

## 🔄 Sync Thủ Công (Nếu Không Tự Động)

```powershell
# Trên Laptop, sau khi collection xong:

# 1. Zip data
Compress-Archive -Path laptop-collection-data -DestinationPath laptop-data.zip

# 2. Gửi qua email/upload cloud

# Trên Desktop, sau khi nhận:

# 3. Extract
Expand-Archive -Path laptop-data.zip -DestinationPath .

# 4. Run comprehensive report
node comprehensive-report-generator.js
```

---

## ✅ Checklist Laptop

- [ ] Node.js cài sẵn
- [ ] File `laptop-auto-collector.js` có trên Laptop
- [ ] Startup shortcut tạo xong
- [ ] Test: chạy manual `node laptop-auto-collector.js`
- [ ] Restart để verify auto-start
- [ ] Chờ tới 8PM
- [ ] Copy data sang Desktop
- [ ] Comprehensive report sinh ra
- [ ] Email nhận được

---

## 📞 Troubleshooting Laptop

### Collection không chạy
- Kiểm tra Node.js: `node --version`
- Kiểm tra file có quyền: `ls -la laptop-auto-collector.js`

### Data không được lưu
- Kiểm tra thư mục: `laptop-collection-data/` có tồn tại?
- Kiểm tra quyền ghi (write permissions)

### Sync bị lỗi
- Chắc laptop không tắt trước 8PM
- Kiểm tra mạng kết nối bình thường
- Thử copy manual

---

## 🎉 Kết Luận

**Laptop sẽ**:
1. ✅ Chạy auto-collection từ boot tới 8PM
2. ✅ Thu thập dữ liệu mỗi 30 phút
3. ✅ Tạo báo cáo Laptop riêng
4. ✅ Sync data sang Desktop
5. ✅ Được include trong comprehensive report

**Comprehensive Report sẽ có**:
- Desktop data (real)
- Laptop data (real)
- WiFi analysis
- iPhone detection
- 30+ khuyến nghị

**Lúc 8PM → Email gửi với tất cả data!** ✅
