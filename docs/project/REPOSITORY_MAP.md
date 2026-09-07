# SentinelOps - Repository Map

## Cấu trúc thư mục

```
mcp-cyber-tools/
├─ web/                          ← Web UI + Server
│  ├─ index.html                 ← Dashboard HTML
│  ├─ app.js                     ← Main application (1114 lines)
│  ├─ server.js                  ← Express server
│  └─ [CSS]                       ← Styling
│
├─ state/                         ← Data persistence
│  ├─ assets.json                ← 11 assets + vulnerabilities
│  ├─ incidents.json             ← 18 incidents
│  ├─ risk_score.json            ← Risk metrics
│  ├─ system_health.json         ← System status
│  ├─ defender_status.json       ← Windows Defender
│  ├─ firewall_status.json       ← Firewall rules
│  ├─ waap_status.json           ← Web WAF
│  ├─ domain_status.json         ← Domain info
│  └─ notification_history.json  ← Alert history
│
├─ mcp/                           ← MCP Tools (90+)
│  └─ [threat hunting tools]
│
├─ telegram/                      ← Alert system
│  └─ [bot code]
│
├─ docs/                          ← Documentation
│  └─ project/                    ← THIS DOCUMENTATION
│
├─ scripts/                       ← Utility scripts
│
├─ package.json                   ← Dependencies
├─ render.yaml                    ← Render deployment config
├─ .env.example                   ← Environment variables
├─ .gitignore                     ← Git ignore rules
└─ README.md                      ← Project readme
```

## Web Directory (web/)

### index.html
**Mục đích**: Tất cả HTML markup cho dashboard

**Các element quan trọng**:
```html
<div id="overview">              <!-- Main page (default) -->
<div id="incidents">             <!-- Incidents page -->
<div id="analytics">             <!-- Analytics page -->
<div id="scorecard">             <!-- Executive scorecard -->
<div id="incident-board">        <!-- Incident cards (C-003) -->
<div id="timeline">              <!-- Event timeline (C-004) -->
<div class="score-risk">         <!-- Risk score (C-001) -->
<div class="mcp-status">         <!-- MCP status (C-002) -->
```

**Trạng thái**: Static, không được modify để tránh cache issues

### app.js
**Mục đích**: Main application logic (1114 lines)

**Các hàm chính**:

| Hàm | Dòng | Mục đích |
|-----|------|---------|
| `init()` | 1-30 | Entry point, DOMContentLoaded |
| `loadAllData()` | 42-74 | Fetch data từ API |
| `renderOverviewPage()` | 143-372 | Render main page (gọi 3 sub-functions) |
| `renderIncidentBoard()` | 704-743 | Render incidents grid |
| `renderTimeline()` | 1006-1038 | Render event timeline |
| `renderExecutiveScorecard()` | 889-985 | Update scorecard elements |
| `renderMCPCommandCenter()` | 374-417 | Render MCP status |
| `startAutoRefresh()` | 1040-1055 | Auto-refresh loop (30s) |

**Data Object**:
```javascript
let stateData = {
  assets: null,        // From /api/state/assets.json
  incidents: null,     // From /api/state/incidents.json
  risk: null,          // From /api/state/risk_score.json
  health: null,        // From /api/state/system_health.json
  mcp: { ... }         // Hardcoded MCP status
};
```

**Known Issues**:
- C-001: renderExecutiveScorecard() updates score elements but shows "UNKNOWN"
- C-003: renderIncidentBoard() not rendering incidents properly
- C-004: renderTimeline() not rendering events properly
- Missing [RENDER] logs indicate functions not called or exiting early

### server.js
**Mục đích**: Express.js web server

**Chính**: 
```javascript
app.listen(3000)                      // Listen on port 3000
app.use(express.static(__dirname))    // Serve static files
app.get('/api/state/:filename')       // Serve state files with timestamps
```

**API Endpoints**:
- `GET /api/state/assets.json` → assets data
- `GET /api/state/incidents.json` → incidents data
- `GET /api/health` → server health check
- `GET /` → serve index.html
- `GET /app.js` → serve app.js

## State Directory (state/)

**Mục đích**: Lưu trữ toàn bộ dữ liệu

**Cách hoạt động**:
1. Tạo JSON files với dữ liệu
2. Server phục vụ chúng via `/api/state/`
3. Browser fetch và display

**File quan trọng**:

### assets.json
- Total assets: 11
- Each asset has vulnerabilities (critical, high, medium, low, info)
- Updated manually (last: 2026-09-07T11:10:00)

### incidents.json
- Total incidents: 18
- Contains incident details (id, title, severity, etc.)

### risk_score.json
- Overall risk: 74/100
- Threat level: HIGH
- Contains risk metrics

## Config Files

### package.json
```json
{
  "name": "mcp-cyber-tools",
  "version": "1.0.1",
  "scripts": {
    "start": "node web/server.js",
    "dev": "node web/server.js"
  },
  "dependencies": {
    "express": "^4.22.2",
    "cors": "^2.8.6"
  }
}
```

**Note**: Version bumped to trigger Render rebuild (unsuccessful)

### render.yaml
```yaml
services:
  - type: web
    name: sentinelops
    runtime: node
    buildCommand: npm install
    startCommand: npm start
    autoDeploy: git
    branch: production  # Currently switched from 'develop'
    envVars:
      - key: PORT
        value: 3000
      - key: STATE_DIR
        value: ./state
```

**Problem**: Render not picking up new commits on any branch

### .env.example
```
NODE_ENV=production
STATE_DIR=./state
PORT=3000
```

## Git Branches

| Branch | Purpose | Status |
|--------|---------|--------|
| develop | Current work | 7 commits ahead, not deployed |
| master | Old code | 20 commits behind develop |
| production | Experimental | Created to test Render |

## Deployment Pipeline

```
LOCAL CODE
    ↓ [git commit]
GitHub REPO (origin/develop)
    ↓ [git push]
GitHub Webhook
    ↓ [should trigger]
Render Build
    ↓ [should build]
Render Server (sentinelops-soc.onrender.com)
    ↓ [serve app.js + state files]
USER BROWSER
    ↓ [render dashboard]
PRODUCTION
```

**Current Status**: STUCK after GitHub Webhook (Render not responding)

---

**Tiếp theo**: Xem DATA_FLOW.md để hiểu luồng dữ liệu.
