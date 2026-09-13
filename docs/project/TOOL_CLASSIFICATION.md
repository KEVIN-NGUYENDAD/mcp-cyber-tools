# TOOL CLASSIFICATION — Kiến trúc 3 tầng

**Sprint**: 5 (Automated Playbooks & Executive Correlation Engine)
**Ngày**: 2026-09-13
**Trạng thái**: LOCKED — phân loại chính thức, không thêm tool mới

Tài liệu này chuẩn hoá cách điều phối bộ MCP tools hiện có. Không mô tả tool nào
sắp xây; chỉ xếp tầng những tool đã đăng ký và chạy được hôm nay.

---

## 0. Số lượng thực tế: 108, không phải 109

Đếm trực tiếp từ mã nguồn, không lấy từ tài liệu cũ:

```bash
# cyber-tools: 99
grep -c -E '^\s*server\.tool\($' modules/*.js

# home-soc: 9
sed -n '/getToolsList/,/^  }/p' home-soc-mcp-server.js | grep -c 'name:'
```

| MCP server | Nguồn | Số tool |
|---|---|---:|
| `cyber-tools` | `modules/*.js` (12 module) | **99** |
| `home-soc` | `home-soc-mcp-server.js` | **9** |
| | **TỔNG** | **108** |

> **Lệch 1 tool so với con số 109 đang lưu hành.** Con số 109 không tái lập được
> từ mã nguồn hiện tại. Phân tầng dưới đây bám theo 108 tool đếm được, giữ nguyên
> quy mô hai tầng đầu (20 / 15) như thiết kế, nên tầng On-Demand là **73** thay vì 74.
> Nếu tìm ra tool thứ 109 (nhiều khả năng là một tool đã gỡ ở lần refactor trước),
> thêm vào Tầng 3 và cập nhật lại bảng này.

Phân bổ theo module:

| Module | Tool | Module | Tool |
|---|---:|---|---:|
| `host` | 10 | `persistence` | 10 |
| `network` | 10 | `forensics` | 10 |
| `process` | 10 | `hunting` | 10 |
| `eventlogs` | 10 | `incident` | 10 |
| `services` | 5 | `eventHub` | 4 |
| `firewall` | 5 | `defender` | 5 |
| | | `home-soc` | 9 |

---

## 1. Tầng 1 — Continuous Monitoring (20 tool)

**Chu kỳ**: 15 phút · **Vai trò**: Telemetry & Sensor · **Chi phí**: thấp, chạy nền

Tầng này trả lời câu hỏi *"hệ thống có đang bình thường không?"*. Tiêu chí chọn:
rẻ, kết quả ổn định giữa hai lần chạy, và thay đổi của nó là tín hiệu chứ không
phải nhiễu. Đây là nguồn nuôi `state/` cho pipeline và Daily Brief.

| # | Tool | Module | Đo cái gì |
|---:|---|---|---|
| 1 | `cpuUsage` | process | Tải CPU |
| 2 | `memoryUsage` | process | Tải RAM |
| 3 | `suspiciousProcesses` | process | Tiến trình bất thường đang chạy |
| 4 | `defenderStatus` | defender | Realtime protection còn bật không |
| 5 | `defenderThreats` | defender | Số threat đang mở |
| 6 | `firewallStatus` | firewall | Profile firewall |
| 7 | `netstat` | network | Bảng kết nối |
| 8 | `activeConnections` | network | Kết nối đang mở |
| 9 | `arp` | network | Bảng ARP — nền cho shadow asset detection |
| 10 | `failedLogons` | eventlogs | Đăng nhập thất bại 24h — đầu vào Rule 2 |
| 11 | `loggedOnUsers` | host | Phiên đăng nhập hiện tại |
| 12 | `servicesChecker` | services | Dịch vụ trọng yếu |
| 13 | `runningServices` | services | Dịch vụ đang chạy |
| 14 | `discoverDevices` | home-soc | Thiết bị trong LAN |
| 15 | `networkStatus` | home-soc | Tình trạng mạng nhà |
| 16 | `gatewayStatus` | home-soc | Gateway/router |
| 17 | `cameraStatus` | home-soc | Camera IP |
| 18 | `homeSocStatus` | home-soc | Tổng trạng thái HOME SOC |
| 19 | `get_security_score` | eventHub | Điểm an ninh tổng |
| 20 | `get_asset_status` | eventHub | Tình trạng tài sản |

**Ai gọi**: `scripts/run_collectors.py`, `scripts/run_intelligence_pipeline.py`
(Phase 1 và 1B), lịch 15 phút của PM2.

---

## 2. Tầng 2 — Triggered Investigation (15 tool)

**Chu kỳ**: không có · **Vai trò**: tự động kích hoạt khi có sự cố `CRITICAL`

Tầng này trả lời *"chuyện gì đã xảy ra?"*. Không chạy theo lịch vì tốn kém và
gây nhiễu; chỉ nổ khi Incident Engine sinh ra sự cố mức CRITICAL.

| # | Tool | Module | Bắt gì |
|---:|---|---|---|
| 1 | `huntPersistence` | hunting | Cơ chế trụ lại máy |
| 2 | `huntCredentialDumping` | hunting | Đánh cắp credential |
| 3 | `huntLateralMovement` | hunting | Di chuyển ngang |
| 4 | `huntSuspiciousServices` | hunting | Dịch vụ lạ |
| 5 | `huntSuspiciousTasks` | hunting | Scheduled task lạ |
| 6 | `huntEncodedPowerShell` | hunting | PowerShell mã hoá |
| 7 | `huntRemoteDesktop` | hunting | Lạm dụng RDP |
| 8 | `huntNetworkBeacons` | hunting | Beacon C2 |
| 9 | `huntLivingOffTheLand` | hunting | LOLBin |
| 10 | `huntIndicators` | hunting | IOC tổng hợp |
| 11 | `persistenceAudit` | persistence | Rà toàn bộ điểm persistence |
| 12 | `collectEvidence` | incident | Gói chứng cứ |
| 13 | `timeline` | incident | Dòng thời gian sự kiện |
| 14 | `securityAudit` | incident | Rà soát cấu hình an ninh |
| 15 | `predictThreatLevel` | home-soc | Dự báo mức đe doạ |

**Ai gọi**: `scripts/auto_investigation_playbook.py`. Playbook chạy chuỗi 4 công
cụ cốt lõi (`hunt_persistence_indicators.py`, `hunt_suspicious_processes.py`,
`hunt_credential_dumping.py`, `collect_timeline_events.py`); 11 tool còn lại của
tầng này là phần mở rộng gọi tay khi ca điều tra cần.

---

## 3. Tầng 3 — On-Demand DFIR (73 tool)

**Chu kỳ**: không có · **Vai trò**: pháp y số chuyên sâu, chỉ gọi khi mổ xẻ hiện trường

Tầng này trả lời *"chính xác thì nó làm gì trên máy này?"*. Không tự động chạy —
tốn tài nguyên, kết quả chỉ có nghĩa khi đã có giả thuyết để kiểm chứng.

| Module | Số | Tool |
|---|---:|---|
| `forensics` | 10 | `checkHash`, `readLogFile`, `fileMetadata`, `recentFiles`, `downloadsFolder`, `desktopFiles`, `tempFiles`, `recycleBin`, `alternateDataStreams`, `suspiciousExecutables` |
| `host` | 9 | `whoami`, `hostname`, `systemInfo`, `localUsers`, `localAdmins`, `installedSoftware`, `sharedFolders`, `environmentVars`, `userProfiles` |
| `eventlogs` | 9 | `eventLogs`, `securityLogs`, `systemLogs`, `applicationLogs`, `successfulLogons`, `powershellLogs`, `rdpLogs`, `usbLogs`, `serviceLogs` |
| `persistence` | 9 | `startupPrograms`, `startupFolders`, `scheduledTasks`, `registryRunKeys`, `registryRunOnce`, `wmiPersistence`, `servicePersistence`, `browserPersistence`, `dllHijackLocations` |
| `network` | 7 | `ipconfig`, `routePrint`, `dnsCache`, `ping`, `tracert`, `nslookup`, `scanPort` |
| `process` | 7 | `tasklist`, `processMonitor`, `processDetails`, `processTree`, `processByPid`, `runningProcesses`, `topProcesses` |
| `incident` | 7 | `collectProcesses`, `collectServices`, `collectNetworkState`, `collectStartupItems`, `collectFirewall`, `collectDefender`, `collectLogs` |
| `firewall` | 4 | `firewallRules`, `inboundRules`, `outboundRules`, `disabledFirewallRules` |
| `services` | 3 | `stoppedServices`, `autoStartServices`, `disabledServices` |
| `defender` | 3 | `defenderHistory`, `defenderExclusions`, `defenderQuickScan` |
| `home-soc` | 3 | `deviceHistory`, `changeHistory`, `getAlerts` |
| `eventHub` | 2 | `get_daily_brief`, `get_recent_incidents` |
| | **73** | |

---

## 4. Kiểm chứng

Tổng: **20 + 15 + 73 = 108** — khớp số tool đếm được từ mã nguồn.
Mỗi tool xuất hiện đúng một lần, không tool nào bị bỏ sót hoặc xếp hai tầng.

Script kiểm tra lại bất cứ lúc nào:

```bash
python scripts/correlation_engine.py     # Tầng 1 -> executive findings
python scripts/auto_investigation_playbook.py --dry-run   # Tầng 2
```

---

## 5. Điều đã biết mà tầng hoá không sửa được

Ghi lại để không phải phát hiện lại:

1. **IOC của tầng 2 chưa quy kết thiết bị.** `hunting_credential_dumping.json` và
   `hunting_persistence.json` để `affected_systems: []`. Hệ quả trực tiếp:
   Rule 1 của Correlation Engine (`Compromised Shadow`) không thể ghép IOC với
   shadow asset và trả về 0 finding kèm `coverage_gaps.IOC_NOT_IP_ATTRIBUTED`.
   Chỉ `hunt_lateral_movement.py` có quy kết IP.

2. **`shadow_assets.json` không nằm trong pipeline.**
   `scripts/shadow_asset_detector.py` tồn tại nhưng
   `run_intelligence_pipeline.py` không gọi, nên dữ liệu shadow đứng yên từ
   `2026-09-09`. Tầng 1 có `arp` và `discoverDevices` — đủ nguyên liệu, thiếu
   mắt xích gọi.

3. **7 sự cố CRITICAL đang OPEN cùng lúc.** Playbook sinh một thông báo Telegram
   cho mỗi sự cố, nên một lần chạy thật gửi 7 tin. Chống trùng theo
   `incident_id` trong 30 phút chỉ ngăn lặp giữa các lần chạy, không gộp tin
   trong cùng một lần. Cần chốt chính sách gộp trước khi bật tự động.
