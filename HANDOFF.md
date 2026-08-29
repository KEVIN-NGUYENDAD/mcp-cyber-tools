# HOME SOC — Handoff

Branch: `claude/dfir-triage-investigation-xhgwz7`
Deploy target: Windows Desktop, `C:\mcp-cyber-tools` (SOC Core Node)

## Trạng thái hiện tại: ĐANG CHẠY

MCP server `home-soc` đã kết nối thành công với Claude Desktop và thu thập
được dữ liệu thật từ mạng LAN.

- Config Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json`
  (KHÔNG phải `~/.claude/mcp.json` — file đó Claude Desktop không đọc)
- Gateway: `192.168.0.1`, reachable ~30-40ms
- Devices phát hiện: 3 (`192.168.0.1`, `.21`, `.25`)
- 9 MCP tools hoạt động

## Các bug đã sửa trong SESSION 1

1. **EPERM crash khi khởi động** — code resolve `./logs`, `./reports` theo
   `process.cwd()`, nhưng Claude Desktop launch process với cwd không liên
   quan (thư mục cài trình duyệt). Đã đổi sang `path.resolve(__dirname, ...)`.
   Files: `home-soc-mcp-server.js`, `network-collector.js`, `baseline-analyzer.js`

2. **SyntaxError** — `collect()` dùng `await import()` nhưng không khai báo
   `async`. Đã thêm `async` + `.catch()` ở call site.

3. **Luôn tìm thấy 0 devices trên Windows** — `getARPTable()` dùng regex viết
   cho format macOS/Linux (IP trong ngoặc, MAC dấu `:`). Windows `arp -a` xuất
   ra format khác hẳn (không ngoặc, MAC dấu `-`). Đã tách nhánh theo platform.

4. **Gateway luôn `unknown` / `lastSeen: null`** — collector đo được ping
   gateway nhưng chưa bao giờ ghi field `gateway` vào `device-history.json`,
   trong khi `gatewayStatus()` lại đọc đúng field đó. Đã ghi bổ sung.

5. **Đếm nhầm multicast/broadcast là thiết bị** — `arp -a` liệt kê cả
   `224.x.x.x`, `239.255.255.250`, `x.x.x.255`. Chúng làm phồng device count,
   méo baseline, và bắn alert HIGH giả mỗi lần chạy. Đã lọc qua `isRealDevice()`.

## Các bug đã sửa trong SESSION 2

1. **Hai tool threat level mâu thuẫn** — `homeSocStatus()` dùng thang điểm ngược
   chiều so với `predictThreatLevel()`. Một tool nói GREEN khi score cao (bảo mật),
   tool kia nói GREEN khi score thấp (an toàn). Đã căn chỉnh cả hai dùng thang
   0-100 của `predictThreatLevel`: 0-40=GREEN, 60-80=ORANGE, 80-100=RED.
   Bỏ luôn penalty "vĩnh viễn" cho số thiết bị — chỉ đếm DEVIATION từ baseline.

2. **Outdated setup scripts** — RUN-ME.bat, HOME-SOC-AUTO-SETUP.ps1, SETUP.ps1,
   SETUP_GODMODE.ps1 đều tham chiếu `src/` không tồn tại và `~/.claude/mcp.json`
   sai. Đã xóa toàn bộ. Tạo DEPLOYMENT.md hướng dẫn chính xác cho Windows.

3. **README.md outdated** — Tham chiếu `~/.claude/profiles/claude_desktop_config.json`
   sai (đúng là `%APPDATA%\Claude\claude_desktop_config.json`). Đã cập nhật,
   thêm note về hai server riêng (cyber-tools + home-soc).

4. **home-soc-phase1-package deprecated** — Thư mục này chứa cấu trúc cũ với `src/`.
   Đánh dấu "DEPRECATED" ở README, hướng dẫn dùng root-level files thay thế.

## VIỆC CÒN DANG DỞ

### 1. ✅ ĐÃ SỬA: Hai tool báo threat level mâu thuẫn nhau

**Status:** FIXED in session 2

Đã căn chỉnh `homeSocStatus()` để dùng cùng thang điểm với `predictThreatLevel()`:
- Cả hai giờ dùng thang 0-100 với: 0-40=GREEN, 40-60=YELLOW, 60-80=ORANGE, 80-100=RED
- Cao = THREAT (xấu), thấp = NORMAL (tốt) — đồng nhất
- Bỏ penalty "vĩnh viễn" cho số thiết bị hợp lệ
- Chỉ đếm device count khi DEVIATION từ baseline (không phải số tuyệt đối)

### 2. Gateway model / firmware không bao giờ có dữ liệu (BACKLOG)

`gatewayStatus()` đọc `data.gateway.model` và `.firmwareVersion`, nhưng
collector không ghi hai field này → luôn trả `unknown`. Hoặc implement thật,
hoặc bỏ khỏi output để không gây hiểu nhầm là "có firmware check".

### 3. ARP chỉ thấy thiết bị vừa liên lạc gần đây (BACKLOG)

3 devices không có nghĩa nhà chỉ có 3 máy. Điện thoại/TV/máy in đang online
nhưng chưa nói chuyện với laptop sẽ không nằm trong ARP cache. Muốn thấy đủ
cần ping sweep cả subnet (`192.168.0.1-254`) trước khi đọc ARP. Chưa làm.

### 4. Vendor lookup chưa tồn tại (BACKLOG)

Phần tra MAC → vendor (Realtek / Arris / SEI Robotics) là do Claude tự suy từ
OUI prefix, không phải tool trả về. Nếu muốn thành tính năng thật thì cần
implement OUI database lookup.

## Tóm Tắt SESSION 2

**Xong:**
- ✅ Fix threat level contradiction (homeSocStatus ↔ predictThreatLevel)
- ✅ Xóa outdated setup scripts (4 files)
- ✅ Tạo DEPLOYMENT.md hướng dẫn đúng
- ✅ Update README.md (path + server clarification)
- ✅ Mark legacy directories deprecated
- **Total commits this session:** 4

**Remaining backlog (3 items):**
1. Gateway firmware detection
2. Full subnet ping sweep (ARP limitation)
3. OUI/vendor lookup tool

---

## Cách tiếp tục ở session tiếp theo

```bash
git checkout claude/dfir-triage-investigation-xhgwz7
git pull
```

Trên Windows, verify MCP server with fixed threat levels:

```powershell
cd C:\mcp-cyber-tools
git pull origin claude/dfir-triage-investigation-xhgwz7
node network-collector.js

# Test both tools now return consistent threat levels
# @homeSocStatus
# @predictThreatLevel
# → Cả hai = GREEN, YELLOW, ORANGE, hoặc RED (đồng nhất)
```

Task Scheduler cho auto-collect mỗi 30 phút **chưa được setup** — hiện phải
chạy tay hoặc dùng DEPLOYMENT.md hướng dẫn.
