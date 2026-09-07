# SentinelOps - Kiến trúc

## Tổng quan

```
CLIENT (Browser)
    ↓
RENDER (Node.js Server)
    ↓
STATE (JSON Files)
    ↓
MCP / TELEGRAM / ALERTS
```

## 1. Client Layer

**File**: `web/index.html`

```html
<div id="overview">         <!-- Main page -->
<div id="incidents">        <!-- Incidents page -->
<div id="analytics">        <!-- Analytics page -->
<div id="scorecard">        <!-- Executive page -->
<div id="incident-board">   <!-- Incidents grid -->
<div id="timeline">         <!-- Events timeline -->
```

**Loaded by**: `web/app.js`

**Updated by**: `renderOverviewPage()`, `renderIncidentBoard()`, etc.

## 2. Web Server (Render)

**File**: `web/server.js`

```javascript
import express from 'express';

const app = express();
app.use(express.static(__dirname));  // Serve static files (HTML, CSS, JS)

app.get('/api/state/:filename', (req, res) => {
  // Serve state files with timestamps
  const data = JSON.parse(fs.readFileSync(...));
  data._fetched_at = new Date().toISOString();
  res.json(data);
});

app.listen(3000);
```

**Endpoints**:
- `GET /` → serve index.html
- `GET /app.js` → serve app.js
- `GET /api/state/assets.json` → serve assets
- `GET /api/state/incidents.json` → serve incidents
- `GET /api/state/risk_score.json` → serve risk score
- `GET /api/health` → health check

## 3. Application Logic

**File**: `web/app.js` (1114 lines)

### Entry Point
```javascript
document.addEventListener('DOMContentLoaded', init);

async function init() {
  console.log('[INIT] SentinelOps starting...');
  await loadAllData();
  renderOverviewPage();
  startAutoRefresh();
  console.log('[INIT] SentinelOps ready');
}
```

### Data Loading
```javascript
async function loadAllData() {
  stateData.assets = await fetch('/api/state/assets.json').then(r => r.json());
  stateData.incidents = await fetch('/api/state/incidents.json').then(r => r.json());
  stateData.risk = await fetch('/api/state/risk_score.json').then(r => r.json());
  stateData.health = await fetch('/api/state/system_health.json').then(r => r.json());
  stateData.mcp = { status: 'ONLINE', tool_count: '90+', ... };
  console.log('[DATA] Loaded: 9 data sources');
}
```

### Rendering Functions
```
renderOverviewPage()          ← Main page renderer
  ├─ renderIncidentBoard()    ← #incident-board
  ├─ renderTimeline()         ← #timeline
  └─ renderExecutiveScorecard() ← Scorecard elements

renderMCPCommandCenter()      ← MCP status

startAutoRefresh()            ← Auto-refresh every 30s
```

### Page Navigation
```javascript
switchPage(pageName) {
  // Switch between pages based on click
  // Call appropriate render function
}
```

## 4. State Files (Data Layer)

**Location**: `state/`

### Files
| File | Content | Size | Update |
|------|---------|------|--------|
| assets.json | 11 assets + vulns | 14 KB | Manual |
| incidents.json | 18 incidents | 8 KB | Manual |
| risk_score.json | Risk metrics | 2 KB | Manual |
| system_health.json | Health status | 1 KB | Manual |
| defender_status.json | Defender stats | 2 KB | Manual |
| firewall_status.json | Firewall rules | 3 KB | Manual |
| waap_status.json | Web WAF status | 1 KB | Manual |
| domain_status.json | Domain info | 1 KB | Manual |
| notification_history.json | Alert history | 5 KB | Manual |

### Schema Example (assets.json)
```json
{
  "timestamp": "2026-09-07T11:10:00.000000",
  "total_assets": 11,
  "assets": [
    {
      "ip": "192.168.0.1",
      "hostname": "router",
      "os": "Windows",
      "vulnerability_count": 39,
      "critical": 0,
      "high": 0,
      "medium": 1,
      "low": 2,
      "info": 36
    }
  ]
}
```

## 5. MCP Layer

**Purpose**: Threat hunting tools

**Tools**: 90+ (Threat Hunting, DFIR, Event Hub, etc.)

**Status Display**: "ACTIVE" in UI

## 6. Alert Layer

**Telegram Integration**: Send alerts to chat

## 7. Data Flow

```
state/assets.json
    ↓ [loadAllData]
stateData.assets
    ↓ [renderOverviewPage]
DOM elements updated
    ↓ [browser render]
User sees data
    ↓ [30s loop]
Repeat
```

## 8. Deployment Architecture

### GitHub
```
mcp-cyber-tools (repo)
├─ develop (current branch)
├─ master (old code)
└─ production (new test branch)
```

### Render
```
sentinelops (service)
├─ Branch watching: develop (config says)
├─ Auto-deploy: Enabled (but BROKEN)
├─ Build: npm install
├─ Start: npm start (node web/server.js)
└─ Deployed commit: ee350ba (STALE)
```

### Production URL
```
https://sentinelops-soc.onrender.com
```

## Current Issues

### Deployment Blocked
- Code ready: 7 new commits
- Production: Using old code (ee350ba)
- Render: Not deploying
- Fix: Manual intervention needed

### UI Rendering Issues
- C-001: Executive Scorecard not showing values
- C-002: Duplicate MCP widgets
- C-003: Incident Board empty
- C-004: Timeline empty

**Root cause**: renderOverviewPage() not being called due to Render deployment lag

---

**Next**: See REPOSITORY_MAP.md for file-by-file explanation.
