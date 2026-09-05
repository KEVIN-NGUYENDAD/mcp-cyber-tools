# Current Focus

Snapshot ngắn — cập nhật khi trạng thái thay đổi. Chi tiết đầy đủ:
`docs/SENTINELOPS_MASTER.md`.

## Vision

**Build an AI Personal Security Manager powered by the SentinelOps
Event Hub.** Event Hub không bị thay thế — vẫn là lõi kỹ thuật; AI
Personal Security Manager là sản phẩm cuối cùng.

```
Sensors → Event Hub → Change Detection → Risk Scoring → Correlation
        → Recommendations → AI Personal Security Manager
```

Không phải Home-SOC truyền thống, không phải SIEM truyền thống. Mục
tiêu: trả lời 3 câu — What changed? Why does it matter? What should
Kevin do next?

`sentinelops-homepage` = Mission Control + Security Intelligence
Portal (Public Docs/Reports/History/Trends). `mcp-cyber-tools` =
Operational Core (Event Hub/MCP/Incident Pipeline/Automation).

## Current Goal

Hoàn thiện Event Hub (Score/Correlation đã có, Change Detection tách
riêng và Recommendations do AI sinh chưa có) làm nền cho 3 Output:
Real-time Alerts, Daily Brief 8PM, Security Intelligence Portal.

## Top Assets

`sentinelops.fyi`, `audit.sentinelops.fyi`, WAAP (Paused), VNETWORK
Partner, MCP, Home-SOC, GitHub, GitHub Mobile, iPhone.

## Top Capabilities

1. Risk Scoring + Correlation trong-nguồn đã có code thật, đã validate
   bằng dữ liệu thật (Event Hub Day 1).
2. Real-time Alerts (nhánh Critical→GitHub Issue→iPhone) đã chạy thật.
3. Chưa có code: Daily Brief, Security Intelligence Portal, Email
   Security sensor, WAAP adapter (paused), WiFi/IoT sensor.

## Next 30 Days

1. Adapter Healthcheck (WAAP hoãn tới sau ticket #3253).
2. Quyết định kỹ thuật Security Intelligence Portal (render dữ liệu
   `home-soc-reports` lên `sentinelops-homepage`).
3. Đối chiếu `content.js` với bằng chứng thật.
4. Ghi nhận scope mới: Email Security (MFA/SPF/DKIM/DMARC/breach) cho
   `kevin@sentinelops.fyi`, `contact@sentinelops.fyi`, Maricopa.edu,
   Gmail chính — chưa có sensor.

## Storage (chốt)

Raw Data = Local only. GitHub = Incidents/Recommendations/
Architecture. Website = Intelligence Portal.

## Nguyên tắc

Không thêm Kubernetes/Redis/DB mới/SaaS mới/repo mới/domain mới. Ưu
tiên tận dụng tài sản hiện có: domain đã mua, WAAP Free, MCP, GitHub,
`home-soc-reports`.

## WAAP

Status: **Paused**. Role: External Sensor. Tích hợp lại chỉ sau ticket
#3253.
