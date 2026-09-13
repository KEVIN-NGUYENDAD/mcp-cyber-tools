# LIVE MCP HUNTING BRIDGE — `SIMULATED` → `LIVE_OBSERVED`

**Sprint**: Live MCP Hunting Bridge
**Ngày**: 2026-09-13
**Trạng thái**: LOCKED

Mục tiêu: pipeline Python ngừng dùng IOC hardcode, bắt đầu đọc quan sát thật từ
99 tool của MCP server.

Việc này lộ ra một điều không ai kiểm chứng trước đó: **10/10 tool hunting của
MCP server đang hỏng, và hỏng im lặng.**

---

## 1. Cầu nối (`scripts/mcp_bridge.py`)

Client MCP stdio tối thiểu: `initialize` → `notifications/initialized` →
`tools/call`, JSON-RPC 2.0 mỗi thông điệp một dòng. Một tiến trình server phục
vụ nhiều lời gọi trong cùng một cuộc săn.

**Vì sao nói chuyện MCP thay vì tự chạy PowerShell trong Python.** Câu truy vấn
của mỗi cuộc săn chỉ nên tồn tại ở một nơi. Repo này đã ba lần trả giá cho việc
có hai nguồn sự thật:

| Lần | Hậu quả |
|---|---|
| `risk_engine.py` đọc khoá `all_assets` đã chết | luôn trả `overall_score: 0` |
| `assets.json` hai producer (`all_assets` / `assets`) | mã chết ở nhiều nơi |
| `shadow_asset_detector.py` lấy MAC từ nơi không có MAC | không phát hiện được gì |

Sao chép truy vấn PowerShell sang Python sẽ là lần thứ tư.

---

## 2. Hai lỗi khiến toàn bộ tool hunting vô dụng

### Lỗi 1 — `runPowerShell` nuốt mọi script nhiều dòng

```js
const fullCommand = `powershell -NoProfile -Command "${command}"`;
execSync(fullCommand, ...);
```

`execSync` trên Windows chạy qua `cmd.exe`, và **cmd.exe cắt dòng lệnh ở ký tự
xuống dòng đầu tiên**. PowerShell nhận một lệnh cụt, không in gì, thoát với mã
**0**. `runPowerShell` vì thế trả về `{ success: true, data: "" }` — thành công
rỗng.

Phạm vi: **43/81 lời gọi `runPowerShell`** trong `modules/` là script nhiều
dòng, trong đó có **toàn bộ 9 tool hunting**.

| module | lời gọi | nhiều dòng |
|---|---:|---:|
| hunting.js | 9 | **9** |
| forensics.js | 9 | 8 |
| defender.js | 5 | 5 |
| firewall.js | 5 | 5 |
| persistence.js | 10 | 5 |
| services.js | 5 | 5 |
| host.js | 8 | 4 |
| network.js | 2 | 2 |

Sửa: `execFileSync` + `-EncodedCommand` (base64 UTF-16LE). Bỏ qua `cmd.exe` hoàn
toàn, miễn nhiễm với dấu nháy, `$`, backslash và xuống dòng. **Một chỗ sửa, 43
lời gọi được chữa.**

### Lỗi 2 — `formatResponse` không bao giờ đặt `isError`

```js
return { content: [{ type: "text", text: `ERROR: ${error}` }] };   // trước
return { isError: true, content: [...] };                          // sau
```

Mọi client MCP — kể cả Claude — nhận một kết quả *thành công* mà nội dung tình
cờ bắt đầu bằng chữ ERROR.

### Lỗi 3 — regex `'\Microsoft\'`

Template literal JS `'\\Microsoft\\'` sinh ra PowerShell `'\Microsoft\'`, mà
.NET regex từ chối: *"Unrecognized escape sequence \M"*. Đổi sang `-notlike`
với wildcard: backslash hết ý nghĩa đặc biệt, không còn tầng escape nào để nhầm.

### Trước / sau

| Tool | Trước | Sau |
|---|---:|---:|
| huntPersistence | 0 | **56** |
| huntSuspiciousTasks | 0 | **40** |
| huntSuspiciousServices | 0 | **21** |
| huntEncodedPowerShell | 0 | **79** |
| huntNetworkBeacons | 0 | **62** |
| huntLivingOffTheLand | 0 | **8** |
| huntCredentialDumping | 0 | `[]` (log không đọc được) |
| huntLateralMovement | 0 | `[]` (log không đọc được) |
| huntRemoteDesktop | 0 | `[]` (log không đọc được) |
| huntIndicators | 0 | `[]` (không có gì khớp) |

---

## 3. "Sạch" khác "mù"

`Get-WinEvent` **ném lỗi** khi không có sự kiện nào khớp. PowerShell thoát khác
0, tool báo hỏng — dù câu trả lời đúng là "máy này sạch". Hai trạng thái ngược
nhau mà nhìn giống hệt nhau là thứ nguy hiểm nhất trong một hệ thống giám sát.

`jsonOrEmpty()` ép mọi truy vấn về một hợp đồng: luôn là JSON hợp lệ, `[]` khi
không có gì, `exit 0` khi cuộc săn thực sự đã chạy.

Ở tầng Python, mỗi báo cáo hunting mang thêm khối `coverage`:

```json
{"observable": false, "status": "NOT_OBSERVABLE",
 "source": "Security event log (ID 4688)",
 "reason": "audit Process Creation tắt mặc định trên Windows Home, và/hoặc
            tiến trình không chạy quyền Administrator"}
```

`hunt_credential_dumping` và `hunt_lateral_movement` **dò riêng** (`securityLogs`)
để biết log có đọc được không, vì bản thân tool trả `[]` trong cả hai trường hợp.

---

## 4. Quy kết thật

Persistence và process là các cuộc săn **host-level** — chúng quan sát chính máy
đang chạy. Nên `affected_systems` là danh tính máy đó (`192.168.0.51`), lấy từ
route thật, và IP này có trong kho tài sản Nessus. Đây là quy kết kiểm chứng
được, khác hẳn việc gán IOC cho một IP tuỳ ý trong mạng.

Lateral movement thì khác: nó là chuyện **giữa** các máy, nên quy kết lấy từ IP
trong nội dung Event 4624, không gán bừa cho máy cục bộ.

`data_source` nay có bốn giá trị: `SIMULATED`, `DERIVED`, `OBSERVED`,
**`LIVE_OBSERVED`**.

---

## 5. Dữ liệu thật không tự nó là tín hiệu tốt

Lần chạy live đầu tiên cho **15 phát hiện HIGH**: Zalo, Canva, Webex, Claude
Code, Wondershare. Tất cả đều là dương tính giả — `%LOCALAPPDATA%\Programs` là
nơi cài đặt hợp lệ của phần mềm hiện đại.

> Chuyển sang dữ liệu thật mà giữ nguyên luật chấm điểm ngây thơ thì chỉ đổi
> cảnh báo giả lấy cảnh báo sai. Người trực ca vẫn phải bỏ đi như nhau.

Ba điều chỉnh:

1. `huntIndicators(unusual_binaries)` thu hẹp từ `*\AppData\*` xuống
   `Temp` / `Downloads` / `Users\Public`.
2. Mức độ phải **kiếm được**: mặc định `INFO`; `HIGH` khi chạy từ thư mục
   tạm/tải về/công cộng; `CRITICAL` khi có lệnh mã hoá base64 trong mục tự khởi động.
3. Gộp trùng: Zalo 8 tiến trình con → 1 chỉ báo kèm `occurrences: 8`.

Kết quả: 80 → **44** chỉ báo, 15 HIGH → **0** HIGH.

---

## 6. Hai lỗi khác lộ ra khi kiểm thử

### `IndexError: list index out of range` trong pipeline

Hai stage hunting đổ vỡ với một thông báo không liên quan gì tới nguyên nhân.
Thật ra: `subprocess.run(text=True)` giải mã bằng codec của locale (**cp1252**),
còn script con in JSON UTF-8 có tiếng Việt. Python 3.7 không báo
`UnicodeDecodeError` mà ném `IndexError` từ luồng đọc.

Sửa: `encoding='utf-8', errors='replace'` + ép `PYTHONIOENCODING=utf-8` cho tiến
trình con, ở cả `run_intelligence_pipeline.py` và `auto_investigation_playbook.py`.

### Engine rủi ro thứ tư

Dòng tổng kết cuối mỗi lần chạy pipeline tự tính lấy:

```python
avg_score = (crypto_score + waap_score_val) / 2
```

Nó in **HIGH** trong khi `state/risk_score.json` ghi **MEDIUM** — và đây là dòng
con người thực sự đọc. Sprint 6 đã xoá `risk_engine.py` và bộ chấm điểm riêng
của Daily Brief nhưng bỏ sót chỗ này. Nay đọc engine chuẩn.

---

## 7. Coverage floor

Với hai nguồn hunting đang mù, điểm rủi ro rơi xuống **6 → LOW**. Nhưng 0 phát
hiện ở một nguồn không đọc được thì được trung bình có trọng số tính là **100
điểm sức khoẻ** — hệ thống tự thưởng điểm cho việc bị mù.

> Không thể khẳng định "rủi ro THẤP" về những thứ không nhìn thấy.

Ghi chú thôi không đủ: thứ người trực ca nhìn trên bảng điều khiển là chữ `LOW`,
không phải dòng `notes` bên dưới. Nên có **coverage floor**, đối xứng với
severity floor của Sprint 6: còn nguồn hunting nào mù thì `risk_level` không
được thấp hơn `MEDIUM`. `overall_score` giữ nguyên; lý do ghi vào `notes`.

---

## 8. Bức tranh thay đổi thế nào

| | Trước | Sau |
|---|---|---|
| `data_source` | `SIMULATED` ×4 | **`LIVE_OBSERVED` ×4** |
| Chỉ báo | 21 (bịa) | **141 thật** (96 persistence + 45 process) |
| Phát hiện CRITICAL | 14 | **0** |
| Sự cố | 19 (7 CRITICAL) | **0** |
| Executive findings | 1 INFO (mô phỏng) | **0**, kèm 5 coverage gap |
| Risk | 56 / HIGH | **6 / MEDIUM** (coverage floor) |
| Vùng mù | không ai biết | **2/4 nguồn, ghi rõ lý do** |

7 sự cố CRITICAL từng khiến hệ thống báo động đều bắt nguồn từ IOC hardcode.
Trên máy này, hiện tại, không có sự cố nào — và hai trục giám sát đang mù.

---

## 9. Điều sprint này KHÔNG làm

1. **Không bật audit policy.** `auditpol /set` cần quyền Administrator và là
   thay đổi cấu hình máy, không phải thay đổi mã. Muốn `huntCredentialDumping`
   và `huntLateralMovement` hết mù thì cần bật audit "Process Creation" (4688)
   và chạy pipeline dưới quyền admin.

2. **Không sửa 34 lời gọi nhiều dòng ngoài hunting.** `-EncodedCommand` đã chữa
   chúng về mặt truyền lệnh, nhưng chưa ai kiểm chứng từng tool trả về gì. 8
   tool forensics, 5 defender, 5 firewall, 5 services, 4 host, 2 network đang ở
   trạng thái "có lẽ đã chạy được".

3. **`assets.json` vẫn hai producer.** Vẫn là nợ cũ.
