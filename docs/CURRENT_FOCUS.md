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

Event Hub hoàn chỉnh: Score, Change Detection, Recommendations, Daily
Brief, MCP, 5 real collector, Scheduler Automation — tất cả **COMPLETE**
(xem Implementation Status). Còn lại: Security Intelligence Portal
(chưa có code), Email Security sensor (chưa có code), WAAP adapter
(Paused).

## Top Assets

`sentinelops.fyi`, `audit.sentinelops.fyi`, WAAP (Paused), VNETWORK
Partner, MCP, Home-SOC, GitHub, GitHub Mobile, iPhone.

## Top Capabilities

1. Event Hub đầy đủ — Baseline Store, Change Detector, Recommendation
   Engine, Daily Brief, MCP Interface — COMPLETE, validate bằng dữ liệu
   thật (Defender, Firewall, Device Inventory, Website).
2. Real-time Alerts (nhánh Critical→GitHub Issue→iPhone) đã chạy thật,
   qua cả `create_securitywatch_incident.py`/`create_defender_incident.py`
   và Change Detector (`change_detector.route_change_event()`).
3. Scheduler Automation (collector mỗi 15 phút, Daily Brief 8PM) chạy
   qua Windows Task Scheduler — COMPLETE.
4. Chưa có code: Security Intelligence Portal, Email Security sensor,
   WAAP adapter (paused), WiFi/IoT sensor.

## Implementation Status (2026-09-05)

**COMPLETE:**
- Event Hub (`scripts/event_schema.py`)
- Baseline Store (`scripts/baseline_store.py`)
- Change Detector (`scripts/change_detector.py`)
- Recommendation Engine (`scripts/recommendation_engine.py`)
- Daily Brief (`scripts/daily_brief_store.py`, `daily_brief_generator.py`)
- MCP (`modules/eventHub.js` — `get_security_score`, `get_daily_brief`,
  `get_recent_incidents`, `get_asset_status`)
- Defender Collector (`scripts/collect_defender_snapshot.py`)
- Defender Threat Collector (`scripts/collect_defender_threats_snapshot.py`)
- Firewall Collector (`scripts/collect_firewall_snapshot.py`)
- Device Inventory Collector (`scripts/collect_device_inventory_snapshot.py`)
- Website Collector (`scripts/collect_website_snapshot.py`)
- Scheduler Automation (Windows Task Scheduler: `SentinelOps-Collectors`
  mỗi 15 phút, `SentinelOps-DailyBrief` 8PM daily)

Validate bằng dữ liệu thật trên host này (Defender, Firewall, Device
Inventory qua `arp -a`, Website `sentinelops.fyi`).

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
