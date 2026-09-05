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

**QUYẾT ĐỊNH KIẾN TRÚC CHÍNH THỨC (2026-09-04):** SentinelOps = AI
Security Operations Platform.

Triết lý:

```
External Telemetry + Internal Telemetry + MCP Intelligence
+ GitHub Incident Management + Mobile Response
```

SentinelOps là portfolio-kèm-hệ-thống-thật của Kevin (Tam) Nguyen: một
MCP server SOC/DFIR (`mcp-cyber-tools`) và một pipeline cảnh báo→
GitHub-incident chạy trên hạ tầng home-lab thật, đứng sau một trang
portfolio công khai (`sentinelops.fyi`). Mục tiêu: chứng minh kỹ năng
SOC/DFIR/AI-security bằng công cụ thật, không phải demo.

### Vai trò 2 repository

- **`sentinelops-homepage` = Mission Control.** Chứa Mission, Projects,
  Architecture, Research, Reports, Public Documentation. **Không** phải
  nơi triển khai logic SOC.
- **`mcp-cyber-tools` = Operational Core.** Chứa Event Hub, MCP,
  Incident Pipeline, Alert Processing, Automation, Security
  Operations. Đây là repo chính của SentinelOps.

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

## Domains

| Domain | Trạng thái thật | WAAP |
|---|---|---|
| `sentinelops.fyi` | Live, apex, Cloudflare→Render | Không |
| `www.sentinelops.fyi` | Live nhưng chỉ redirect 301 về apex — **không đi qua VNETWORK** | Đã onboard (Service ID `95743`) nhưng domain sai, không thể mang traffic WAAP |
| `audit.sentinelops.fyi` | Live, thật sự đi qua VNETWORK edge, backend Render chưa rõ chủ | Chưa có Service ID xác nhận riêng |
| `soc.sentinelops.fyi` | Parking Porkbun, redirect về apex — **không có dịch vụ thật** | Không |
| `mcp.sentinelops.fyi` | Parking Porkbun, redirect về apex — **không có dịch vụ thật** | Không |

Đăng ký/DNS/email: Porkbun (MX + SPF xác nhận).

## VNETWORK

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

1. **WAAP không hoạt động** — domain onboard sai (`www.` thay vì
   `audit.`) + entitlement tài khoản bị từ chối trên cả Compute/CDN.
2. **Healthcheck receiver** — thiếu spec HMAC công khai + chưa rõ chủ
   backend `audit.sentinelops.fyi`.
3. **Khoảng cách marketing/thực tế** — Wazuh/Suricata/Zeek/Honeypot/
   TheWall/audit-logging/dashboard đều là tuyên bố không có code hỗ
   trợ; `dashboard.html` là số liệu gán cứng, không kết nối dữ liệu
   thật.
4. **`soc.`/`mcp.` subdomain** — chỉ là nhãn, chưa từng được xây.

## Current Priorities

1. Xây SentinelOps Event Hub: chuẩn hóa Event Schema dùng chung
   (`source`, `severity`, `title`, `summary`, `evidence`).
2. Tách `score_alert`/`find_duplicate`/`build_issue`/`compute_labels`/
   `build_analysis_comment`/GitHub-call family khỏi
   `create_securitywatch_incident.py` thành 1 module dùng chung.
3. Viết adapter còn thiếu cho WAAP và Healthcheck (test bằng sample
   JSON đã có, không cần chờ entitlement VNETWORK thông).
4. Đối chiếu lại `content.js` với bằng chứng thật (xóa/sửa các tuyên
   bố không có code hỗ trợ).

## 3-Day Plan (Event Hub)

**Ngày 1 — Event Schema.** Chuẩn hóa schema chung cho mọi nguồn:
`source`, `severity`, `title`, `summary`, `evidence`.

**Ngày 2 — Adapters.** Viết adapter cho `securitywatch`, `waap`,
`healthcheck` để đưa alert của từng nguồn về cùng schema trên. WAAP
dùng sample JSON đã lưu (`WAAP_LOG_SEARCH_SCHEMA.md`); Healthcheck
dùng payload mẫu tự viết — không phụ thuộc việc entitlement VNETWORK
đã thông hay chưa.

**Ngày 3 — End-to-end.** Chạy Event → Score → Correlate → Issue bằng
một pipeline chung, qua cả 3 nguồn, xác nhận output khớp với issue
thật đã có (regression check).

## Nguyên tắc kiến trúc

**Không thêm:** Kubernetes, Redis, database mới, SaaS mới, repo mới,
domain mới.

**Ưu tiên:** tận dụng tối đa tài sản hiện có — domain đã mua, WAAP
Free, MCP, GitHub.

## Long-Term Vision

Digital Risk Twin — mô hình trạng thái phơi nhiễm tổng hợp từ mọi
nguồn đã có (WAAP, Healthcheck, Home-SOC), dùng JSON state-file diff
(cùng pattern `security-watch.js` đã dùng), không dashboard, không
database mới. Xây trên nền Event Hub sau khi Event Hub chạy end-to-end
— hiện vẫn là ý tưởng, chưa có discovery pass riêng.
