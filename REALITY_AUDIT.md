# REALITY_AUDIT.md

Kiểm toán thực tế — chỉ dùng source code, `package.json`, `server.js`,
`server_v2.js`, `modules/*.js`, `scripts/*.py`, cấu hình Render (nếu
có), và các bản ghi DNS/HTTP sống đã thu thập trực tiếp trong phiên
này (`nslookup`, `curl -I`, `gh api`). **Không dùng bất kỳ kết luận
nào từ `ARCHITECTURE_SUMMARY.md`, `SENTINELOPS_DEEP_CONTEXT.md`,
`SENTINELOPS_FINAL_AUDIT.md`, hay `SENTINELOPS_DISCOVERY_TIMELINE.md`.**
Mọi grep/read trong file này được thực hiện lại từ đầu, trực tiếp
trên source code, không copy từ các file kết luận trước đó.

Nguồn tuyên bố được kiểm toán: `sentinelops-homepage/src/data/content.js`
(file nội dung thực tế của website, đọc trực tiếp).

Ký hiệu:
✅ ĐÃ CHỨNG MINH — có code/cấu hình thật hỗ trợ trực tiếp
⚠️ CHỨNG MINH MỘT PHẦN — một phần hạ tầng có thật, phần còn lại
không có bằng chứng
📋 KẾ HOẠCH — có tài liệu thiết kế nhưng chưa có code
❌ KHÔNG TÌM THẤY BẰNG CHỨNG — grep toàn bộ source code trả về 0 kết
quả, không có file/config nào hỗ trợ tuyên bố

---

# PHẦN A — Bảng phân loại toàn bộ tuyên bố chính trên `content.js`

| Tuyên bố (nguồn: `content.js`) | Phân loại | Bằng chứng |
|---|---|---|
| "Home SOC: Generates security telemetry through Wazuh, Suricata, Zeek, and threat-hunting workflows" | ❌ | `grep -ri "wazuh\|suricata\|zeek\|honeypot" ` trên toàn bộ `mcp-cyber-tools` (trừ file `.md`) → **0 kết quả** trong bất kỳ file `.js`/`.py`/`.json` nào |
| "Home-SOC: A self-hosted lab — SIEM, EDR, honeypots, network sensors" (`focusAreas`) | ❌ | Cùng grep trên — 0 kết quả cho "honeypot" trong toàn bộ source code |
| `home-soc-reports` project: "Ingests alerts from a home-lab SIEM (Wazuh) and network sensors (Suricata, Zeek), correlates them against MITRE ATT&CK... weekly PDF/HTML reports... Grafana" | ❌ | Không có file nào trong `mcp-cyber-tools` chứa logic MITRE ATT&CK mapping, không có thư viện PDF-generation, không có cấu hình Grafana ở bất kỳ đâu trong `package.json` hay source |
| `mcp-cyber-tools` project: stack "Python, MCP, FastAPI, YARA, STIX/TAXII" | ❌ | `package.json` thực tế của repo này: `"dependencies": {"@modelcontextprotocol/sdk": "^1.30.0", "zod": "^4.4.3"}` — **Node.js/JavaScript**, không phải Python; không có FastAPI, không có YARA, không có STIX/TAXII trong bất kỳ file nào |
| "Read-only and write-scoped tool tiers with per-action audit logging" | ❌ | `modules/shared.js` — hàm `runPowerShell()` chỉ có `console.log()` debug (dòng 9–16, 20–25), in ra terminal khi chạy, không ghi file, không ghi database, không có cơ chế audit trail nào tồn tại sau khi tiến trình kết thúc. Toàn bộ 95 tool đều read-only (không có "write-scoped tier" nào — không tool nào gọi lệnh ghi/sửa hệ thống) |
| WAAP: "Protects public services and blocks malicious traffic" | 📋 | Không có file nào trong `mcp-cyber-tools` gọi `bsearch` hay bất kỳ endpoint VNETWORK nào (`grep -ri "bsearch\|vnetwork"` trên source code → 0 kết quả ngoài các file `.md`). Việc bảo vệ (nếu có) diễn ra hoàn toàn bên ngoài repo này, không kiểm chứng được từ code |
| "MCP Intelligence Layer: Acts as the AI-assisted analysis layer... enrichment, investigation support, automation" | ⚠️ | `server.js` thật sự tồn tại và đăng ký 95 tool (đếm trực tiếp từ `modules/*.js`) — nhưng các tool này không tự động "enrich" hay "investigate" gì cả; chúng chỉ trả JSON thô từ PowerShell khi được gọi thủ công. "Automation" không có bằng chứng — `scripts/*.py` (nơi thật sự có logic risk-scoring) không import hay gọi bất kỳ hàm nào từ `server.js`/`modules/*` |
| "GitHub Incident Queue: Tracks incidents, investigations, and response activities" | ✅ | `scripts/create_test_incident.py` dòng 28–29: `REPO_OWNER = "KEVIN-NGUYENDAD"`, `REPO_NAME = "mcp-cyber-tools"`; dòng 112–118: `create_issue()` gọi thật `https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues`, `assign_issue()` gọi thật endpoint `assignees` |
| "Mobile Response: Allows monitoring and response directly from GitHub Mobile on iPhone" | ⚠️ | GitHub Issues thật sự được tạo (xác nhận ở trên) và GitHub tự động push notification cho assignee — đây là hành vi mặc định của GitHub, không phải code riêng của dự án. Không có file nào trong repo cấu hình hay kiểm soát riêng phần "Mobile"; không kiểm chứng được việc notification thật sự đã đến iPhone từ source code |
| `audit.sentinelops.fyi`: "hosted on Render behind VNetwork WAAP" | ⚠️ | `nslookup audit.sentinelops.fyi` (chạy trực tiếp phiên này): CNAME → `95715.cdn.vncdn.net` → `edge.vnetwork.gslb.veloceed.com` — xác nhận domain có đi qua hạ tầng VNETWORK thật. `curl -I` xác nhận header `rndr-id` (Render) tồn tại phía sau. Nhưng: không có `render.yaml`/`Procfile` nào trong `network-security-audit-frontend` (repo được `content.js` gắn với domain này) trỏ đích danh tới `audit.sentinelops.fyi`; không xác nhận được rule WAF cụ thể nào đang bật từ phía code |

---

# PHẦN B — 10 mục kiểm tra đặc biệt

## 1. Wazuh

- **Bằng chứng:** không có.
- **File nguồn:** `grep -ri "wazuh" mcp-cyber-tools/**/*.{js,py,json}` (loại trừ `node_modules`) → **0 kết quả**.
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG.
- **Có nên sửa website:** **Có.** Câu "Wazuh" xuất hiện ở 3 vị trí riêng biệt trong `content.js` (`components[1].description`, `focusAreas[3].description`, `projects[1]` — cả tagline lẫn stack), không phải một câu lỡ lời — cần sửa cả ba.

## 2. Suricata

- **Bằng chứng:** không có.
- **File nguồn:** cùng lệnh grep trên — 0 kết quả cho "suricata".
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG.
- **Có nên sửa website:** **Có** — xuất hiện ở cùng 3 vị trí như Wazuh.

## 3. Zeek

- **Bằng chứng:** không có.
- **File nguồn:** cùng lệnh grep — 0 kết quả cho "zeek".
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG.
- **Có nên sửa website:** **Có** — cùng vị trí như trên.

## 4. Honeypot

- **Bằng chứng:** không có.
- **File nguồn:** cùng lệnh grep — 0 kết quả cho "honeypot"/"honeynet" trong toàn bộ source code hai repo (`mcp-cyber-tools`, `sentinelops-homepage`).
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG.
- **Có nên sửa website:** **Có** — xuất hiện ở `focusAreas[3].description` ("honeypots") và mục "Honeypot Cluster" trong `liveInfrastructure.systems`.

## 5. TheWall

- **Bằng chứng:** repo `TheWall` không nằm trong `mcp-cyber-tools`/`sentinelops-homepage` nên không grep được tại chỗ; kiểm tra trực tiếp qua GitHub API công khai: `gh api repos/KEVIN-NGUYENDAD/TheWall/languages` trả về `{"GDScript":68401,"JavaScript":20542,"HTML":10878}`.
- **File nguồn:** kết quả API GitHub trực tiếp (`repos/KEVIN-NGUYENDAD/TheWall/languages`), không phải suy đoán.
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG cho tuyên bố "Public-facing visualization of blocked attacker traffic" — 68KB GDScript là ngôn ngữ script của game engine Godot, không phải công nghệ visualization dữ liệu bảo mật.
- **Có nên sửa website:** **Có** — mục "TheWall" trong `liveInfrastructure.systems` mô tả sai bản chất repo.

## 6. WAAP Logs

- **Bằng chứng:** không có lệnh gọi nào tới `bsearch` hoặc bất kỳ endpoint `openapi.vnetwork.vn` nào trong source code.
- **File nguồn:** `grep -ri "bsearch\|vnetwork" mcp-cyber-tools/**/*.{js,py}` → 0 kết quả; `ls scripts/` → chỉ có `create_defender_incident.py`, `create_securitywatch_incident.py`, `create_test_incident.py` — **không có `create_waap_incident.py`**.
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG (chưa có một dòng code nào truy vấn WAAP logs).
- **Có nên sửa website:** **Có** — mục "Requests blocked (7d): ~1.2k" trong `liveInfrastructure` và Threat Report #001 (6 request bị chặn) không có script nào trong repo có khả năng tạo ra hay xác minh số liệu này.

## 7. WAAP → Home-SOC

- **Bằng chứng:** không có.
- **File nguồn:** không tìm thấy file nào trong `mcp-cyber-tools` (scripts/modules) đọc dữ liệu WAAP rồi ghi vào bất kỳ phần nào của Home-SOC pipeline. `content.js` dòng 560 tự tuyên bố: *"WAAP logs feed into the home-SOC pipeline (see home-soc-reports)"* — nhưng không có script nào trong `scripts/` hay `modules/` thực hiện việc này.
- **Trạng thái thực tế:** ❌ KHÔNG TÌM THẤY BẰNG CHỨNG.
- **Có nên sửa website:** **Có** — đây là một liên kết kỹ thuật cụ thể được tuyên bố (WAAP → home-soc-reports) mà không có một dòng code nào thực hiện.

## 8. MCP Intelligence Layer

- **Bằng chứng:** `server.js` có thật, đăng ký 95 tool qua 11 module (`modules/host.js`, `network.js`, `process.js`, `services.js`, `eventlogs.js`, `firewall.js`, `defender.js`, `persistence.js`, `forensics.js`, `hunting.js`, `incident.js` — đếm trực tiếp: 10+10+10+5+10+5+5+10+10+10+10 = 95).
- **File nguồn:** `server.js` (import 11 module), `modules/*.js` (định nghĩa tool), `modules/shared.js` (`runPowerShell`, `formatResponse` — không có logic "enrichment" hay "analysis" tự động, chỉ trả dữ liệu thô).
- **Trạng thái thực tế:** ⚠️ CHỨNG MINH MỘT PHẦN — MCP server thật, 95 tool thật, nhưng "AI-assisted analysis," "enrichment," "automation" không có bằng chứng code — các tool chỉ là truy vấn PowerShell thụ động, không có pipeline tự động nào gọi chúng.
- **Có nên sửa website:** **Có** — nên mô tả chính xác hơn: "95 read-only PowerShell-backed introspection tools qua MCP," không phải "AI-assisted analysis layer... automation."

## 9. GitHub Incident Queue

- **Bằng chứng:** `scripts/create_test_incident.py` — `REPO_OWNER = "KEVIN-NGUYENDAD"`, `REPO_NAME = "mcp-cyber-tools"` (dòng 28–29); `create_issue()` gọi `POST https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues` (dòng 112–113); `assign_issue()` gọi `POST .../issues/{issue_number}/assignees` (dòng 117–118); `score_alert()` (dòng 59) tính risk score trước khi tạo issue.
- **File nguồn:** `scripts/create_test_incident.py`, `scripts/create_defender_incident.py`, `scripts/create_securitywatch_incident.py`.
- **Trạng thái thực tế:** ✅ ĐÃ CHỨNG MINH — đây là phần có bằng chứng code trực tiếp, mạnh nhất trong toàn bộ 10 mục.
- **Có nên sửa website:** **Không cần** — tuyên bố này khớp với code thật.

## 10. Mobile Response

- **Bằng chứng:** không có code riêng nào trong repo xử lý "mobile" — đây là hành vi mặc định của ứng dụng GitHub Mobile khi một issue được assign (đã xác nhận issue/assignment là thật ở mục 9).
- **File nguồn:** không có file nào trong `mcp-cyber-tools` hay `sentinelops-homepage` liên quan tới push notification, GitHub Mobile API, hay APNs.
- **Trạng thái thực tế:** ⚠️ CHỨNG MINH MỘT PHẦN — cơ chế nền (issue + assignment thật) đã chứng minh; phần "Mobile Response" cụ thể phụ thuộc hoàn toàn vào hành vi client bên ngoài repo, không kiểm chứng được từ source code.
- **Có nên sửa website:** Không bắt buộc — tuyên bố hợp lý dựa trên hành vi GitHub chuẩn, nhưng nên làm rõ đây là tính năng có sẵn của GitHub Mobile, không phải tính năng do dự án tự xây dựng.

---

# Tổng kết theo số liệu grep (không suy đoán)

```
grep -ri "wazuh|suricata|zeek|honeypot|bsearch|vnetwork|fastapi|yara|stix|grafana|mitre" \
  trên mcp-cyber-tools/{server.js,server_v2.js,server_backup_v1.js,modules/*.js,scripts/*.py,package.json} \
  và sentinelops-homepage/{package.json,src/**/*.jsx}

Kết quả: 0 kết quả.
```

Mọi từ khóa trên **chỉ** xuất hiện trong `content.js` (nội dung
website) và trong các file `.md` (tài liệu). **Không một từ khóa nào
trong danh sách trên xuất hiện trong bất kỳ file code thực thi nào**
của hai repo.
