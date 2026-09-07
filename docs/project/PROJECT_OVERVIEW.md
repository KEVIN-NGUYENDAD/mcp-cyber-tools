# SentinelOps - Project Overview

## Là gì?

**SentinelOps** là SOC (Security Operations Center) Command Center - dashboard giám sát bảo mật theo thời gian thực.

Theo dõi:
- 11 assets (Windows servers)
- Vulnerabilities (385 findings)
- Incidents (18 open)
- Threats (7 critical)
- Risk Score (74/100)

## Mục tiêu

Cung cấp **single pane of glass** cho security team:
- Monitoring real-time
- Threat intelligence
- Incident response
- Asset inventory
- Risk scoring

## Kiến trúc

```
┌─────────────────────────────────────┐
│   Dashboard (Browser)                │ ← User Interface
├─────────────────────────────────────┤
│   Render (Node.js Web Server)        │ ← Hosted on render.com
├─────────────────────────────────────┤
│   MCP Tools (90+ threat hunting)     │ ← Threat intelligence
│   State Files (JSON)                 │ ← Data persistence
│   Alert System (Telegram)            │ ← Notifications
└─────────────────────────────────────┘
```

## Tính năng hiện có

✅ Real-time dashboard
✅ Asset monitoring (11 assets)
✅ Vulnerability scanning (385 findings)
✅ Incident tracking (18 open)
✅ MCP threat hunting (90+ tools)
✅ Telegram alerts
✅ Executive scorecard
✅ Data freshness tracking (1 min)

## Tính năng tương lai

- [ ] Advanced threat hunting
- [ ] Predictive analytics
- [ ] Automated response
- [ ] SOAR integration
- [ ] Custom playbooks

## Các module chính

| Module | Mục đích | File |
|--------|---------|------|
| Dashboard | UI chính | web/index.html |
| Server | Backend API | web/server.js |
| Application | Logic chính | web/app.js |
| State | Lưu dữ liệu | state/*.json |
| MCP | Threat hunting | mcp/* |
| Alerts | Telegram | telegram/* |

## Version

Current: 1.0.1 (Production)

## Status

🟢 OPERATIONAL - Render deployed ✓

Latest commit: 7703b4a (develop branch)
Production commit: ee350ba (6 commits behind)

## Known Issues

### CRITICAL (4)
- C-001: Executive Scorecard showing "UNKNOWN"
- C-002: Duplicate MCP widgets
- C-003: Incident Board empty
- C-004: Timeline empty

### Root Cause
Render deployment stalled on commit ee350ba. Latest code not deployed.

## Quy trình làm việc

```
Audit → Identify Issues → Fix Code → Deploy → Verify → Repeat
```

**Hiện tại**: Stuck at Deploy phase (Render broken)

## Deployment Status

| Component | Status | Details |
|-----------|--------|---------|
| Code | ✅ Ready | 7 commits with fixes |
| GitHub | ✅ Pushed | All commits on develop |
| Render | ❌ Blocked | Stuck on ee350ba |
| Production | ❌ Stale | Using old code |

---

**Ưu tiên**: Fix Render deployment issue để deploy 4 CRITICAL fixes.
