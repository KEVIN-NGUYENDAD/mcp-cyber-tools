# TOOL VALIDATION REPORT

**Sprint**: 8 — Sensor Visibility & Tool Validation  
**Sinh tự động bởi**: `scripts/tool_validator.py` v1.0.0  
**Thời điểm**: 2026-09-13T19:32:40.187249  
**Máy**: KEVIN (Administrator: False)

Đừng sửa tay file này — chạy lại `python scripts/tool_validator.py`.

## Bốn ô phán quyết

| Ô | Nghĩa |
|---|---|
| ✅ PASS | Tool chạy, trả về bằng chứng thật (≥ 1 bản ghi) |
| ⚪ EMPTY | Tool chạy, không có gì để trả về, **và nguồn đọc được** — "đã nhìn, sạch" |
| ❌ BLIND | Tool chạy, không có gì để trả về, **nguồn không đọc được** — rỗng vô nghĩa |
| 🔴 FAIL | Tool báo lỗi, hết giờ, hoặc trả về thứ không phân tích được |

EMPTY và BLIND trông giống hệt nhau ở mọi nơi khác trong hệ thống, nhưng
nói hai điều ngược nhau. Phán quyết BLIND không đến từ bản thân tool —
tool không biết nó đang mù — mà từ `scripts/sensor_probe.py`.

## Tổng

| | Số lượng |
|---|---:|
| Tool đăng ký | 99 |
| ✅ PASS | 84 |
| ⚪ EMPTY | 7 |
| ❌ BLIND | 8 |
| 🔴 FAIL | 0 |
| Tổng bản ghi thu được | 6118 |

## Sensor coverage

| Nguồn | Trạng thái | Tool | PASS | EMPTY | BLIND | FAIL | Bản ghi | Ghi chú |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Defender | ✅ COVERED | 6 | 6 | 0 | 0 | 0 | 7 |  |
| Firewall | ✅ COVERED | 6 | 6 | 0 | 0 | 0 | 254 |  |
| Security Event Log | ❌ BLIND | 9 | 0 | 1 | 8 | 0 | 0 | Attempted to perform an unauthorized operation. |
| Event Logs (System/App/PS) | ✅ COVERED | 7 | 6 | 1 | 0 | 0 | 460 |  |
| Persistence | ✅ COVERED | 20 | 20 | 0 | 0 | 0 | 1102 |  |
| Processes | ✅ COVERED | 12 | 12 | 0 | 0 | 0 | 1129 |  |
| Network | ✅ COVERED | 12 | 12 | 0 | 0 | 0 | 625 |  |
| IOC / Filesystem | ✅ COVERED | 11 | 8 | 3 | 0 | 0 | 2461 |  |

## Event ID 4688 — Process Creation

| | |
|---|---|
| `observable` | **false** |
| Trạng thái | `ACCESS_DENIED` |
| Quyền Administrator | False |
| Nguyên nhân | Không mở được log Security: "Attempted to perform an unauthorized operation.". Log Security đòi quyền Administrator, nên chưa thể biết audit 4688 bật hay tắt. |
| Khắc phục | Chạy pipeline dưới quyền Administrator, rồi kiểm tra lại; nếu vẫn trống thì bật audit "Process Creation". |

> **Cái bẫy**: Truy vấn lọc theo Id trên log này trả về "No events were found" thay vì báo từ chối quyền — mọi tool dựa vào đó sẽ trông như "sạch" trong khi thực ra đang mù.

## Ma trận tool

| Tool | Module | Kiểu lệnh | Nguồn | Trạng thái | Bản ghi | Ghi chú |
|---|---|---|---|---|---:|---|
| `defenderExclusions` | defender | multiline | defender | ✅ PASS | 1 |  |
| `defenderHistory` | defender | multiline | defender | ✅ PASS | 1 |  |
| `defenderQuickScan` | defender | multiline | defender | ✅ PASS | 1 |  |
| `defenderStatus` | defender | multiline | defender | ✅ PASS | 1 |  |
| `defenderThreats` | defender | multiline | defender | ✅ PASS | 2 |  |
| `get_asset_status` | eventHub | none | internal_state | ✅ PASS | 1 |  |
| `get_daily_brief` | eventHub | none | internal_state | ✅ PASS | 9 |  |
| `get_recent_incidents` | eventHub | none | internal_state | ✅ PASS | 1 |  |
| `get_security_score` | eventHub | none | internal_state | ✅ PASS | 1 |  |
| `applicationLogs` | eventlogs | inline | event_logs | ✅ PASS | 100 |  |
| `eventLogs` | eventlogs | inline | event_logs | ✅ PASS | 10 |  |
| `failedLogons` | eventlogs | inline | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `powershellLogs` | eventlogs | inline | event_logs | ✅ PASS | 100 |  |
| `rdpLogs` | eventlogs | inline | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `securityLogs` | eventlogs | inline | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `serviceLogs` | eventlogs | inline | event_logs | ✅ PASS | 50 |  |
| `successfulLogons` | eventlogs | inline | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `systemLogs` | eventlogs | inline | event_logs | ✅ PASS | 100 |  |
| `usbLogs` | eventlogs | inline | event_logs | ⚪ EMPTY | 0 | nguồn đọc được, không có bản ghi nào khớp |
| `disabledFirewallRules` | firewall | multiline | firewall | ✅ PASS | 50 |  |
| `firewallRules` | firewall | multiline | firewall | ✅ PASS | 100 |  |
| `firewallStatus` | firewall | multiline | firewall | ✅ PASS | 3 |  |
| `inboundRules` | firewall | multiline | firewall | ✅ PASS | 50 |  |
| `outboundRules` | firewall | multiline | firewall | ✅ PASS | 50 |  |
| `alternateDataStreams` | forensics | multiline | ioc | ⚪ EMPTY | 0 | nguồn đọc được, không có bản ghi nào khớp |
| `checkHash` | forensics | inline | ioc | ✅ PASS | 1 |  |
| `desktopFiles` | forensics | multiline | ioc | ✅ PASS | 2306 |  |
| `downloadsFolder` | forensics | multiline | ioc | ✅ PASS | 2 |  |
| `fileMetadata` | forensics | multiline | ioc | ✅ PASS | 1 |  |
| `readLogFile` | forensics | none | ioc | ✅ PASS | 1 |  |
| `recentFiles` | forensics | multiline | ioc | ✅ PASS | 50 |  |
| `recycleBin` | forensics | multiline | ioc | ✅ PASS | 50 |  |
| `suspiciousExecutables` | forensics | multiline | ioc | ⚪ EMPTY | 0 | nguồn đọc được, không có bản ghi nào khớp |
| `tempFiles` | forensics | multiline | ioc | ✅ PASS | 50 |  |
| `environmentVars` | host | multiline | host | ✅ PASS | 1 |  |
| `hostname` | host | multiline_indirect | host | ✅ PASS | 1 |  |
| `installedSoftware` | host | multiline | host | ✅ PASS | 50 |  |
| `localAdmins` | host | inline | host | ✅ PASS | 2 |  |
| `localUsers` | host | inline | host | ✅ PASS | 6 |  |
| `loggedOnUsers` | host | multiline | host | ✅ PASS | 1 |  |
| `sharedFolders` | host | inline | host | ✅ PASS | 3 |  |
| `systemInfo` | host | multiline | host | ✅ PASS | 1 |  |
| `userProfiles` | host | multiline | host | ✅ PASS | 2 |  |
| `whoami` | host | multiline_indirect | host | ✅ PASS | 1 |  |
| `huntCredentialDumping` | hunting | multiline_indirect | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `huntEncodedPowerShell` | hunting | multiline_indirect | event_logs | ✅ PASS | 100 |  |
| `huntIndicators` | hunting | multiline_indirect | ioc | ⚪ EMPTY | 0 | nguồn đọc được, không có bản ghi nào khớp |
| `huntLateralMovement` | hunting | multiline_indirect | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `huntLivingOffTheLand` | hunting | multiline_indirect | processes | ✅ PASS | 8 |  |
| `huntNetworkBeacons` | hunting | multiline_indirect | network | ✅ PASS | 56 |  |
| `huntPersistence` | hunting | multiline_indirect | persistence | ✅ PASS | 56 |  |
| `huntRemoteDesktop` | hunting | multiline_indirect | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `huntSuspiciousServices` | hunting | multiline_indirect | persistence | ✅ PASS | 21 |  |
| `huntSuspiciousTasks` | hunting | multiline_indirect | persistence | ✅ PASS | 40 |  |
| `collectDefender` | incident | inline | defender | ✅ PASS | 1 |  |
| `collectEvidence` | incident | inline | composite | ⚪ EMPTY | 0 | Ghi file báo cáo rồi chỉ trả về đường dẫn |
| `collectFirewall` | incident | inline | firewall | ✅ PASS | 1 |  |
| `collectLogs` | incident | inline | security_log | ❌ BLIND | 0 | security_log: ACCESS_DENIED |
| `collectNetworkState` | incident | inline | network | ✅ PASS | 1 |  |
| `collectProcesses` | incident | inline | processes | ✅ PASS | 1 |  |
| `collectServices` | incident | inline | persistence | ✅ PASS | 1 |  |
| `collectStartupItems` | incident | inline | persistence | ✅ PASS | 1 |  |
| `securityAudit` | incident | none | composite | ⚪ EMPTY | 0 | Trả về checklist tĩnh viết cứng trong mã, không quan sát gì |
| `timeline` | incident | inline | security_log | ⚪ EMPTY | 0 | Ghi file báo cáo rồi chỉ trả về đường dẫn |
| `activeConnections` | network | multiline | network | ✅ PASS | 80 |  |
| `arp` | network | cmd | network | ✅ PASS | 11 |  |
| `dnsCache` | network | cmd | network | ✅ PASS | 182 |  |
| `ipconfig` | network | cmd | network | ✅ PASS | 20 |  |
| `netstat` | network | cmd | network | ✅ PASS | 212 |  |
| `nslookup` | network | cmd | network | ✅ PASS | 5 |  |
| `ping` | network | cmd | network | ✅ PASS | 6 |  |
| `routePrint` | network | cmd | network | ✅ PASS | 47 |  |
| `scanPort` | network | multiline | network | ✅ PASS | 1 |  |
| `tracert` | network | cmd | network | ✅ PASS | 4 |  |
| `browserPersistence` | persistence | multiline | persistence | ✅ PASS | 1 |  |
| `dllHijackLocations` | persistence | multiline | persistence | ✅ PASS | 1 |  |
| `persistenceAudit` | persistence | multiline | persistence | ✅ PASS | 1 |  |
| `registryRunKeys` | persistence | inline | persistence | ✅ PASS | 16 |  |
| `registryRunOnce` | persistence | inline | persistence | ✅ PASS | 1 |  |
| `scheduledTasks` | persistence | inline | persistence | ✅ PASS | 100 |  |
| `servicePersistence` | persistence | multiline | persistence | ✅ PASS | 97 |  |
| `startupFolders` | persistence | inline | persistence | ✅ PASS | 5 |  |
| `startupPrograms` | persistence | inline | persistence | ✅ PASS | 23 |  |
| `wmiPersistence` | persistence | multiline | persistence | ✅ PASS | 1 |  |
| `cpuUsage` | process | inline | processes | ✅ PASS | 10 |  |
| `memoryUsage` | process | inline | processes | ✅ PASS | 10 |  |
| `processByPid` | process | inline | processes | ✅ PASS | 1 |  |
| `processDetails` | process | inline | processes | ✅ PASS | 1 |  |
| `processMonitor` | process | inline | processes | ✅ PASS | 20 |  |
| `processTree` | process | inline | processes | ✅ PASS | 459 |  |
| `runningProcesses` | process | inline | processes | ✅ PASS | 50 |  |
| `suspiciousProcesses` | process | inline | processes | ✅ PASS | 97 |  |
| `tasklist` | process | cmd | processes | ✅ PASS | 462 |  |
| `topProcesses` | process | inline | processes | ✅ PASS | 10 |  |
| `autoStartServices` | services | multiline | persistence | ✅ PASS | 107 |  |
| `disabledServices` | services | multiline | persistence | ✅ PASS | 6 |  |
| `runningServices` | services | multiline | persistence | ✅ PASS | 143 |  |
| `servicesChecker` | services | multiline | persistence | ✅ PASS | 312 |  |
| `stoppedServices` | services | multiline | persistence | ✅ PASS | 169 |  |

## Technical debt còn lại

Những thứ lần kiểm này phát hiện nhưng KHÔNG sửa trong Sprint 8, kèm lý do.

| # | Món nợ | Vì sao chưa trả |
|---:|---|---|
| 1 | Log Security đòi quyền Administrator — 8 tool mù, và không thể biết audit 4688 bật hay tắt | Không phải lỗi mã. Phải chạy pipeline dưới quyền Administrator mới trả lời được. |
| 2 | `securityAudit` trả về một checklist viết cứng trong mã, không quan sát gì | Viết lại nó là thêm tính năng, nằm ngoài phạm vi sprint kiểm định. |
| 3 | `timeline`, `collectEvidence`, `collectLogs` ghi file rồi chỉ trả về đường dẫn — không có bằng chứng nào đi ra tới người gọi | Đổi hợp đồng trả về sẽ phá mọi nơi đang gọi chúng; cần một sprint riêng. |
| 4 | `alternateDataStreams` mặc định `-Path "C:\"` nên chỉ soi đúng một mục, không bao giờ tìm được ADS ở đâu cả | Cho nó đệ quy toàn ổ đĩa là một thay đổi hành vi nặng về I/O, phải đo trước. |
| 5 | Event 4104 (script block logging) của Microsoft-Windows-PowerShell/Operational đọc được nhưng không nguồn nào trong pipeline dùng | Dùng nó là thêm nguồn phát hiện mới — đúng nghĩa thêm tính năng. |
| 6 | `state/sensor_coverage.json` không tự làm mới theo pipeline | tool_validator.py gọi thật 99 tool và có tác dụng phụ (ghi báo cáo, quét). Portal hiển thị tuổi của dữ liệu và cảnh báo khi quá 24 giờ. |
| 7 | `assets.json` có hai người ghi: asset_builder.py ghi `all_assets`, extract_asset_intelligence.py ghi `assets` | Tồn tại từ trước Sprint 8, đã ghi nhận, chưa gộp. |

## Probe cảm biến thô

| Probe | Đọc được | Giá trị / Lỗi |
|---|---|---|
| `is_admin` | ✅ | False |
| `security_log` | ❌ | Attempted to perform an unauthorized operation. |
| `security_4688` | ❌ | No events were found that match the specified selection criteria. |
| `security_4624` | ❌ | No events were found that match the specified selection criteria. |
| `security_4625` | ❌ | No events were found that match the specified selection criteria. |
| `event_log_system` | ✅ | 1796 |
| `event_log_application` | ✅ | 257 |
| `event_log_powershell` | ✅ | 400 |
| `event_log_ps_operational` | ✅ | 4104 |
| `defender` | ✅ | True |
| `firewall` | ✅ | 3 |
| `process_table` | ✅ | 457 |
| `scheduled_tasks` | ✅ | 228 |
| `registry_run` | ✅ | 1 |
| `wmi_subscriptions` | ✅ | 1 |
| `network_stack` | ✅ | 213 |
| `filesystem_user` | ✅ | 66 |
| `audit_policy` | ❌ | Error 0x00000522 occurred: |

