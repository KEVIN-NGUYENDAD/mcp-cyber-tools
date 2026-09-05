# SentinelOps — Master Reference

Nguồn sự thật duy nhất, hiện tại, cho toàn bộ hệ sinh thái
SentinelOps. Thay thế việc phải đọc `PROJECT_STATUS.md`,
`NEXT_STEPS.md`, `ARCHITECTURE_SUMMARY.md`,
`SENTINELOPS_DISCOVERY_TIMELINE.md`, `SENTINELOPS_DEEP_CONTEXT.md` —
năm file này đã chuyển vào `docs/archive/` (không xóa, chỉ lưu trữ để
tra cứu lịch sử). File này chỉ giữ **trạng thái hiện tại đã xác
minh**, không thuật lại quá trình discovery, không liệt kê giả thuyết
đã bị bác bỏ.

## Mission

**QUYẾT ĐỊNH CHÍNH THỨC CUỐI CÙNG (2026-09-04):**

> Build an AI Personal Security Manager powered by the SentinelOps
> Event Hub.

SentinelOps Event Hub **không bị thay thế** — Event Hub vẫn là lõi kỹ
thuật. AI Personal Security Manager là sản phẩm cuối cùng, xây trên
nền Event Hub.

Mối quan hệ:

```
Sensors → Event Hub → Change Detection → Risk Scoring → Correlation
        → Recommendations → AI Personal Security Manager
```

Mục tiêu: giám sát, đánh giá và giải thích toàn bộ môi trường số của
Kevin bằng AI.

Triết lý (quyết định trước đó, vẫn còn hiệu lực làm nền):

```
External Telemetry + Internal Telemetry + MCP Intelligence
+ GitHub Incident Management + Mobile Response
```

SentinelOps là portfolio-kèm-hệ-thống-thật của Kevin (Tam) Nguyen: một
MCP server SOC/DFIR (`mcp-cyber-tools`) và một pipeline cảnh báo→
GitHub-incident chạy trên hạ tầng home-lab thật, đứng sau một trang
portfolio công khai (`sentinelops.fyi`). Mục tiêu: chứng minh kỹ năng
SOC/DFIR/AI-security bằng công cụ thật, không phải demo.

### Phạm vi giám sát (chính thức)

**Nội bộ:** Desktop, Laptop, WiFi, IoT, Windows Defender.
**Bên ngoài:** `sentinelops.fyi`, `audit.sentinelops.fyi`, WAAP, SSL,
Healthcheck.

Trạng thái triển khai thật hôm nay: chỉ Windows Defender +
`security-watch.js` (DNS/Firewall/Defender/RDP/SSH) có code chạy thật.
WiFi, IoT, và toàn bộ nhóm External (WAAP/SSL/Healthcheck) **chưa có
sensor/adapter nào** — đây là phạm vi chính thức mới, không phải trạng
thái hiện tại.

### Vai trò 2 repository (chốt cuối cùng)

- **`sentinelops-homepage` = Mission Control + Security Intelligence
  Portal.** Chứa Public Documentation, Reports, History, Trends.
  Không triển khai logic SOC (Event Hub/MCP/Incident Pipeline vẫn sống
  ở `mcp-cyber-tools`) — nhưng **được phép hiển thị** dữ liệu SOC đã
  sanitize (History/Devices/Incidents/Risk Trends/Reports/Daily Brief
  Archive). Điều này chốt lại xung đột đã nêu ở bản trước.
- **`mcp-cyber-tools` = Operational Core.** Chứa Event Hub, MCP,
  Incident Pipeline, Automation. Đây là repo chính của SentinelOps.

## Current Assets

- **`mcp-cyber-tools`** — MCP server (95 tool), pipeline incident,
  private repo.
- **`sentinelops-homepage`** — trang portfolio công khai, static
  React/Vite, không server.
- **`home-soc-reports`** — pipeline xuất bản dữ liệu Home-SOC đã
  sanitize, public repo, đang hoạt động.
- **3 app demo độc lập** — `kevin-cyber-security-copilot`,
  `cybersecurity-labs`, `network-security-audit-frontend` — mỗi cái
  một Render deployment riêng, không kết nối vào hệ thống chính.
- **`sentinelops-security-incidents`** — repo rỗng, không dùng.
- **5 hostname** — xem mục Domains.
- **1 tài khoản đối tác VNETWORK (WAAP Free)** — xem mục VNETWORK.

**Tài sản chính (chính thức):** `sentinelops.fyi`,
`audit.sentinelops.fyi`, WAAP Free, VNETWORK Partner, MCP, Home-SOC,
GitHub, GitHub Mobile, iPhone.

## Current Architecture

**Dự án trung tâm: SentinelOps Event Hub.** Mục tiêu: chuẩn hóa mọi sự
kiện an ninh (WAAP, Home-SOC, Healthcheck, Defender, và sensor tương
lai) vào cùng một pipeline duy nhất, thay vì mỗi nguồn một script
riêng.

```
Internet
   │
   ▼
WAAP ──────────→ External Events   ─┐
Home-SOC ──────→ Internal Events    │
Healthcheck ───→ Availability Events├──→ SentinelOps Event Hub
Defender ──────→ Security Events   ─┘         │
                                               ▼
                                            Score
                                               ▼
                                           Correlate
                                               ▼
                                           Incident
                                               ▼
                                        GitHub Issues (mcp-cyber-tools)
                                               ▼
                                         GitHub Mobile
                                               ▼
                                             iPhone
```

Trạng thái thật hôm nay (2026-09-04): 4/6 khối của Event Hub đã có code
thật, nhưng khóa cứng bên trong `create_securitywatch_incident.py`
thay vì tách thành module dùng chung — `score_alert()` (Score),
`find_duplicate()`/`find_open_issues()` (Correlate), `build_issue()`/
`compute_labels()`/`build_analysis_comment()` (Incident),
`create_issue`/`add_labels`/`add_comment`/`assign_issue` (GitHub Issue)
đều source-agnostic sẵn. GitHub Mobile → iPhone không cần code (GitHub
tự push khi assign). Duy nhất **Event** (adapter chuẩn hóa nguồn →
schema chung) mới chỉ có cho `security_watch` (`to_alert()`); WAAP và
Healthcheck chưa có adapter.

Song song, không thuộc Event Hub: scan/baseline data →
`export-home-soc-reports.js` → leak-guard → `home-soc-reports`
(public) → Claude Scheduled Task → email bulletin.

### Kiến trúc chính thức mở rộng (2026-09-04)

```
Internal Sensors + External Sensors
        ▼
SentinelOps Event Hub
        ▼
Change Detection
        ▼
Risk Scoring
        ▼
Correlation
        ▼
Recommendations
        ▼
Outputs
```

Đối chiếu với code thật: **Risk Scoring** = `score_alert()` (có).
**Correlation** = `find_duplicate()`/`find_open_issues()`, nhưng hiện
chỉ dedup trong cùng 1 nguồn theo tiêu đề, chưa correlate chéo nguồn
(có một phần). **Change Detection** hiện chỉ tồn tại ngầm bên trong
`security-watch.js` (so baseline vs current) — chưa phải bước tách
riêng trong Event Hub. **Recommendations** hiện chỉ là text tĩnh theo
rule (`ENRICHMENT_RULES` trong `create_securitywatch_incident.py`),
không phải AI-generated. **Outputs** hôm nay = GitHub Issue + GitHub
Mobile; Daily Brief và Website Dashboard (xem 2 mục dưới) **chưa có
code nào**.

## Mô Hình Alert (chính thức — danh sách cuối cùng)

Không spam cảnh báo. Chỉ gửi realtime (Output #1) khi: Malware,
Firewall Disabled, Unknown Device, Website Down, SSL Error, WAAP
Disabled. (Bản trước có thêm "Risk Score vượt ngưỡng" — danh sách
cuối cùng này không lặp lại mục đó; giữ 6 mục trên làm chuẩn.)

```
Event → Score → Critical?
  YES → GitHub Issue → Notification → iPhone
  NO  → Daily Brief
```

Trạng thái thật: nhánh YES (Critical → GitHub Issue → iPhone) đã có
code chạy thật (`create_securitywatch_incident.py`,
`create_defender_incident.py`). Nhánh NO (gộp vào Daily Brief thay vì
im lặng bỏ qua) **chưa có code nào** — mọi alert hôm nay hoặc thành
Issue hoặc không được xử lý gì thêm.

## Outputs (chính thức — chốt cuối cùng)

**1. Real-time Alerts** — 6 mục ở trên (Mô Hình Alert).

**2. Daily Brief 8PM** — Executive Summary, đọc dưới 1 phút. Chỉ gồm:
Security Score, Today's Changes, Current Risk, Recommended Actions
(tối đa 3 action). Không hiển thị log thô, không dữ liệu kỹ thuật dài
dòng. Trả lời 3 câu: Hôm nay có gì thay đổi? Tại sao quan trọng? Tôi
nên làm gì?

**3. Security Intelligence Portal** (`sentinelops.fyi`) — chi tiết đầy
đủ. Lưu: History, Devices, Incidents, Risk Trends, Reports, Daily
Brief Archive. (Danh sách cuối cùng — thay cho "Dashboard/History/
Changes/..." ở bản trước.)

Trạng thái thật: Daily Brief = **0 code, 0 lịch chạy**. Security
Intelligence Portal = `sentinelops-homepage` hiện là static React/Vite,
không server, không `fetch` — 0/6 mục trên đã tồn tại. Chỉ nhánh
Real-time Alerts (Critical → GitHub Issue → iPhone) đã chạy thật.

## Storage (chính thức — chốt cuối cùng)

| Nơi lưu | Nội dung |
|---|---|
| **Raw Data** | Local only — không rời khỏi máy Kevin |
| **GitHub** | Incidents, Recommendations, Architecture |
| **Website** | Intelligence Portal (History/Devices/Incidents/Risk Trends/Reports/Daily Brief Archive) |

Nguyên tắc ẩn danh (vẫn hiệu lực): không công khai password, cookies,
internal IP, full MAC address, raw Defender logs, raw Windows logs, raw
scan data. Áp dụng hash hostname, mask IP, mask MAC, summary only, risk
scores only.

Trạng thái thật: `home-soc-reports` là pipeline public thật duy nhất
hiện có — chưa xác nhận nó áp dụng đúng hash/mask theo bảng trên (cần
đọc `export-home-soc-reports.js`/leak-guard riêng, ngoài phạm vi lần
đọc này).

## Domains

| Domain | Trạng thái thật | WAAP |
|---|---|---|
| `sentinelops.fyi` | Live, apex, Cloudflare→Render | Không |
| `www.sentinelops.fyi` | Live nhưng chỉ redirect 301 về apex — **không đi qua VNETWORK** | Đã onboard (Service ID `95743`) nhưng domain sai, không thể mang traffic WAAP |
| `audit.sentinelops.fyi` | Live, thật sự đi qua VNETWORK edge, backend Render chưa rõ chủ | Chưa có Service ID xác nhận riêng |
| `soc.sentinelops.fyi` | Parking Porkbun, redirect về apex — **không có dịch vụ thật** | Không |
| `mcp.sentinelops.fyi` | Parking Porkbun, redirect về apex — **không có dịch vụ thật** | Không |

Đăng ký/DNS/email: Porkbun (MX + SPF xác nhận).

## VNETWORK / WAAP

**Status (chính thức, 2026-09-04): Paused.** Role: External Sensor.
Chỉ tích hợp lại sau ticket #3253.

- API: `openapi.vnetwork.vn`, Bearer token, 106 endpoint (39 read-only).
- `POST /v1/bsearch` — endpoint log/analytics duy nhất, chưa hoạt
  động được lần nào từ dự án này.
- Entitlement hiện tại: `403` (Compute), `404` (CDN), `401` (WAAP) —
  giống hệt nhau qua 2 token khác nhau, trước/sau khi onboard WAAP.
- Service ID duy nhất từng thấy: `95743`, gắn với domain không hoạt
  động (`www.sentinelops.fyi`).
- Healthcheck & Alerting (beta): có webhook thật nhưng chưa có REST
  API để cấu hình.
- Certificates, Multi-CDN, Object Storage: sản phẩm có thật, chưa gọi
  thử lần nào.

## Email Security (Monitored Asset — mới, chính thức 2026-09-04)

**Protected Accounts:** `kevin@sentinelops.fyi`, `contact@sentinelops.fyi`,
tài khoản Maricopa.edu, Gmail chính.

**Monitor:** MFA status, SPF, DKIM, DMARC, breach exposure. Đưa vào
Security Score của Daily Brief.

Trạng thái thật: **0 code** — chưa có sensor/adapter nào cho Email
Security. Đây là phạm vi giám sát mới, không phải trạng thái hiện tại.

## Home-SOC

- Nguồn thật duy nhất đang chạy: `security-watch.js` (5 control: DNS,
  Firewall, Defender, RDP, SSH) → `alerts.json`, lịch chạy qua
  `HOME-SOC-Scan-And-Export`.
- Đã xác minh với sự kiện thật: Issue #6 (`[CRITICAL] Firewall
  Disabled | Risk 95`).
- **Wazuh, Suricata, Zeek, honeypot — không có bằng chứng code nào**
  (grep toàn bộ source: 0 kết quả). Đây chỉ là tuyên bố trên
  `content.js`, không phải hệ thống thật.
- Bug đã biết, chưa sửa: khóa `firewall`/`defender` trong rule không
  khớp `fw`/`def` trong state thật — làm rớt 2 field bằng chứng.

## MCP

- `server.js` — server đang dùng thật, 95 tool, 11 module (đếm trực
  tiếp từ `modules/*.js`).
- `server_v2.js`/`server_backup_v1.js` — trùng byte-for-byte, không
  được tham chiếu ở đâu — mồ côi, không dùng.
- `modules/shared.js` chỉ có `console.log` debug — **không có audit
  logging thật**, dù `content.js` tuyên bố "100% tool calls audited."
- Script tạo incident (`scripts/*.py`) **không gọi qua MCP** — hai
  code path tách biệt.

## GitHub Workflow

- Đích đến incident thật: `KEVIN-NGUYENDAD/mcp-cyber-tools` Issues
  (hardcode trong `create_test_incident.py`) — **không phải**
  `sentinelops-security-incidents` (rỗng).
- Dữ liệu Issues thật (qua `gh api`, không phải tài liệu): 6 issue,
  toàn bộ `state: open`. #5/#6 khớp alert thật; #4 là dữ liệu test
  thủ công (`Source: test`, `IP: 1.2.3.4`); #3 không có nội dung.
- Không có `.github/workflows/` ở bất kỳ repo nào — không CI/CD tự
  động.

## Verified Components

✅ MCP server + 95 tool (`server.js`, `modules/*.js`)
✅ Pipeline incident (`create_test_incident.py`,
`create_defender_incident.py`, `create_securitywatch_incident.py`) —
xác nhận bằng Issue thật
✅ Home-SOC `security-watch.js` → `alerts.json` — xác nhận bằng sự
kiện thật (Issue #6)
✅ `home-soc-reports` publication pipeline — output công khai đang
cập nhật thật

## Current Blockers

1. ~~WAAP không hoạt động~~ — **đã chuyển thành Paused theo quyết định
   chính thức**, không còn là blocker cần giải ngay; chỉ tích hợp lại
   sau ticket #3253. Nguyên nhân kỹ thuật (domain onboard sai `www.`
   thay vì `audit.`, entitlement bị từ chối trên Compute/CDN) vẫn giữ
   nguyên làm hồ sơ, chưa cần hành động.
2. **Healthcheck receiver** — thiếu spec HMAC công khai + chưa rõ chủ
   backend `audit.sentinelops.fyi`.
3. **Khoảng cách marketing/thực tế** — Wazuh/Suricata/Zeek/Honeypot/
   TheWall/audit-logging/dashboard đều là tuyên bố không có code hỗ
   trợ; `dashboard.html` là số liệu gán cứng, không kết nối dữ liệu
   thật.
4. **`soc.`/`mcp.` subdomain** — chỉ là nhãn, chưa từng được xây.
5. **Security Intelligence Portal chưa tồn tại** — 0/6 mục (History/
   Devices/Incidents/Risk Trends/Reports/Daily Brief Archive), cần
   quyết định kỹ thuật cách render dữ liệu `home-soc-reports` lên
   `sentinelops-homepage`.
6. **Email Security chưa có sensor** — phạm vi mới, 0 code.

## Current Priorities

1. Xây SentinelOps Event Hub: chuẩn hóa Event Schema dùng chung
   (`source`, `severity`, `title`, `summary`, `evidence`).
2. Tách `score_alert`/`find_duplicate`/`build_issue`/`compute_labels`/
   `build_analysis_comment`/GitHub-call family khỏi
   `create_securitywatch_incident.py` thành 1 module dùng chung.
3. Viết adapter cho Healthcheck (test bằng sample payload). **WAAP
   adapter tạm dừng** — theo quyết định Paused, chỉ làm sau ticket
   #3253.
4. Đối chiếu lại `content.js` với bằng chứng thật (xóa/sửa các tuyên
   bố không có code hỗ trợ).
5. Quyết định kỹ thuật cho Security Intelligence Portal (render dữ
   liệu `home-soc-reports` lên `sentinelops-homepage`).

## 3-Day Plan (Event Hub)

**Ngày 1 — Event Schema.** Chuẩn hóa schema chung cho mọi nguồn:
`source`, `severity`, `title`, `summary`, `evidence`.

**Ngày 2 — Adapters.** Viết adapter cho `healthcheck` (payload mẫu tự
viết). `waap` **hoãn** theo quyết định Paused — chỉ làm sau ticket
#3253, không phụ thuộc việc entitlement VNETWORK.

**Ngày 3 — End-to-end.** Chạy Event → Score → Correlate → Issue bằng
một pipeline chung, qua cả 3 nguồn, xác nhận output khớp với issue
thật đã có (regression check).

## Nguyên tắc kiến trúc

**Không thêm:** Kubernetes, Redis, database mới, SaaS mới, repo mới,
domain mới.

**Ưu tiên:** tận dụng tối đa tài sản hiện có — domain đã mua, WAAP
Free, MCP, GitHub.

## Long-Term Vision (chốt cuối cùng, 2026-09-04)

**AI Personal Security Manager — không phải Home-SOC truyền thống,
không phải SIEM truyền thống.**

Mục tiêu: trả lời đúng 3 câu:
1. What changed?
2. Why does it matter?
3. What should Kevin do next?

SentinelOps Event Hub là lõi kỹ thuật phục vụ mục tiêu này, không phải
mục tiêu tự thân. Digital Risk Twin (ý tưởng trước đó) vẫn có thể là 1
kỹ thuật bên trong khối Risk Scoring/Correlation/Recommendations, chưa
có discovery pass riêng.
