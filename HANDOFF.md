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

## Các bug đã sửa trong session này

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

## VIỆC CÒN DANG DỞ

### 1. Hai tool báo threat level mâu thuẫn nhau (chưa sửa)

Cùng một dữ liệu nhưng cho kết quả trái ngược, vì dùng thang điểm ngược chiều:

| Tool | Base | Hướng | Đọc ra |
|---|---|---|---|
| `homeSocStatus` | 85 | cao = tốt | 83 → YELLOW |
| `predictThreatLevel` | 20 | cao = xấu | 20 → GREEN |

Thêm nữa, `homeSocStatus()` có dòng:

```js
homeScore -= Math.min(devices.totalDevices * 2, 15);
```

→ mỗi thiết bị hợp lệ trong nhà bị trừ 2 điểm **vĩnh viễn**. Nhà càng nhiều
thiết bị càng bị chấm là nguy hiểm. Đây là lỗi thiết kế, không phải trạng
thái tạm thời sẽ tự hết.

**Đề xuất:** bỏ penalty theo số thiết bị; cho `homeSocStatus` dùng chung
thang với `predictThreatLevel` để chỉ còn một nguồn sự thật về threat level.

### 2. Gateway model / firmware không bao giờ có dữ liệu

`gatewayStatus()` đọc `data.gateway.model` và `.firmwareVersion`, nhưng
collector không ghi hai field này → luôn trả `unknown`. Hoặc implement thật,
hoặc bỏ khỏi output để không gây hiểu nhầm là "có firmware check".

### 3. ARP chỉ thấy thiết bị vừa liên lạc gần đây

3 devices không có nghĩa nhà chỉ có 3 máy. Điện thoại/TV/máy in đang online
nhưng chưa nói chuyện với laptop sẽ không nằm trong ARP cache. Muốn thấy đủ
cần ping sweep cả subnet (`192.168.0.1-254`) trước khi đọc ARP. Chưa làm.

### 4. Vendor lookup chưa tồn tại

Phần tra MAC → vendor (Realtek / Arris / SEI Robotics) là do Claude tự suy từ
OUI prefix, không phải tool trả về. Nếu muốn thành tính năng thật thì cần
implement OUI database lookup.

## Cách tiếp tục ở session mới

```bash
git checkout claude/dfir-triage-investigation-xhgwz7
git pull
```

Trên Windows, chạy collector thủ công để cập nhật dữ liệu:

```powershell
cd C:\mcp-cyber-tools
git pull origin claude/dfir-triage-investigation-xhgwz7
node network-collector.js
```

Task Scheduler cho auto-collect mỗi 30 phút **chưa được setup** — hiện phải
chạy tay.
