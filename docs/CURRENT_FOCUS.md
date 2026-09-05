# Current Focus

Snapshot ngắn — cập nhật khi trạng thái thay đổi. Chi tiết đầy đủ:
`docs/SENTINELOPS_MASTER.md`.

## Vision

SentinelOps = AI Security Operations Platform:
External Telemetry + Internal Telemetry + MCP Intelligence + GitHub
Incident Management + Mobile Response.

`sentinelops-homepage` = Mission Control (Mission/Projects/Architecture/
Research/Reports/Public Docs). `mcp-cyber-tools` = Operational Core
(Event Hub/MCP/Incident Pipeline/Alert Processing/Automation) — repo
chính của SentinelOps.

## Current Goal

Xây **SentinelOps Event Hub** — dự án trung tâm: chuẩn hóa mọi sự kiện
an ninh (WAAP, Home-SOC, Healthcheck, Defender, sensor tương lai) vào
1 pipeline duy nhất: Event → Score → Correlate → Incident → GitHub
Issue → GitHub Mobile → iPhone.

## Top Assets

`sentinelops.fyi`, `audit.sentinelops.fyi`, WAAP Free, VNETWORK
Partner, MCP, Home-SOC, GitHub, GitHub Mobile, iPhone.

## Top Capabilities

1. Score/Correlate/Incident/GitHub đã có code thật (trong
   `create_securitywatch_incident.py`), source-agnostic, chỉ cần tách
   thành module dùng chung.
2. Adapter chuẩn hóa Event chỉ mới có cho `security_watch`
   (`to_alert()`) — WAAP và Healthcheck chưa có.
3. GitHub Mobile → iPhone: 0 code cần, đã hoạt động qua assign issue.

## Next 30 Days (3-Day Plan lồng bên trong)

**Ngày 1:** Chuẩn hóa Event Schema chung: `source`, `severity`,
`title`, `summary`, `evidence`.

**Ngày 2:** Viết adapter `securitywatch`/`waap`/`healthcheck` về cùng
schema (test bằng sample JSON có sẵn, không chờ entitlement VNETWORK).

**Ngày 3:** Chạy end-to-end Event → Score → Correlate → Issue qua 1
pipeline chung cho cả 3 nguồn, đối chiếu với issue thật đã có.

Sau đó: đối chiếu `content.js` với bằng chứng thật; xác nhận Service
ID/entitlement VNETWORK khi có thời gian — không chặn tiến độ Event Hub.

## Nguyên tắc

Không thêm Kubernetes/Redis/DB mới/SaaS mới/repo mới/domain mới. Ưu
tiên tận dụng tài sản hiện có: domain đã mua, WAAP Free, MCP, GitHub.
