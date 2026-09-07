# SentinelOps - Data Flow

## End-to-End Flow

```
SENSORS/TOOLS (Network, Defender, Firewall, etc.)
    ↓
STATE FILES (state/*.json - created manually or by scripts)
    ↓
WEB SERVER (web/server.js - serves files via /api/state/)
    ↓
BROWSER (fetch('/api/state/...'))
    ↓
APP.JS (loadAllData() → stateData)
    ↓
DOM RENDERING (renderOverviewPage → innerHTML updates)
    ↓
USER SEES DASHBOARD
    ↓
AUTO-REFRESH (every 30s)
    ↓
REPEAT
```

## Detailed Flow - Loading

### 1. Browser loads https://sentinelops-soc.onrender.com

```
GET / → server.js sends index.html
```

### 2. index.html loads

```html
<script src="/app.js"></script>
<!-- When script loads, it runs: -->
document.addEventListener('DOMContentLoaded', init);
```

### 3. init() runs

```javascript
async function init() {
  await loadAllData();
  renderOverviewPage();
  startAutoRefresh();
}
```

### 4. loadAllData() fetches data

```javascript
stateData.assets = await fetch('/api/state/assets.json').then(r => r.json());
stateData.incidents = await fetch('/api/state/incidents.json').then(r => r.json());
stateData.risk = await fetch('/api/state/risk_score.json').then(r => r.json());
// ... 6 more state files
stateData.mcp = { status: 'ONLINE', tool_count: '90+', ... };
```

### 5. renderOverviewPage() updates DOM

```javascript
function renderOverviewPage() {
  // Update elements with IDs:
  document.getElementById('threat-level').textContent = getThreatLevel(stateData.risk);
  document.getElementById('assets-count').textContent = stateData.assets.total_assets;
  document.getElementById('incidents-count').textContent = stateData.incidents.total_incidents;
  
  // Call sub-renders:
  renderIncidentBoard();      // Updates #incident-board
  renderTimeline();            // Updates #timeline
  renderExecutiveScorecard();  // Updates scorecard elements
  renderMCPCommandCenter();    // Updates MCP status
}
```

### 6. Browser renders

```
DOM changes → User sees updated dashboard
```

### 7. startAutoRefresh() repeats every 30s

```javascript
setInterval(() => {
  loadAllData();           // Fetch fresh data
  renderOverviewPage();    // Re-render all
}, 30000);
```

## Data Sources

### assets.json
```
11 Assets
├─ Each has vulns
├─ Critical: 0
├─ High: 0
├─ Medium: 4
├─ Low: 9
└─ Info: 372
   Total: 385 findings
```

### incidents.json
```
18 Incidents
├─ Severity levels
├─ Status
└─ Details
```

### risk_score.json
```
Overall Risk Score: 74/100
Threat Level: HIGH
├─ Critical threats: 7
├─ High threats: ?
└─ Medium: ?
```

### system_health.json
```
System Status
├─ Operational
├─ Last update: now
└─ Metrics
```

### defender_status.json
```
Windows Defender
├─ Status
├─ Threats
└─ History
```

### firewall_status.json
```
Firewall
├─ Enabled: yes
├─ Rules: many
└─ Blocks: some
```

### waap_status.json
```
Web WAF
├─ SSL: VALID
├─ WAF: INACTIVE
├─ CDN: INACTIVE
└─ Cert days left: 87
```

### domain_status.json
```
Domain Info
├─ Domain: sentinelops.fyi
└─ Details
```

### notification_history.json
```
Alert History
└─ Past alerts/events
```

## Update Frequency

| Data | Update | Trigger | Refresh |
|------|--------|---------|---------|
| assets.json | Manual | Script or User | ~1h |
| incidents.json | Manual | Script or User | ~15min |
| risk_score.json | Calculated | Auto | ~5min |
| Others | Variable | Various | ~1h |

**Browser refresh**: Every 30 seconds (auto-refresh loop)

**Data freshness**: Calculated as time between fetch and file timestamp

## Rendering Functions Stack

```
renderOverviewPage()                      [Called by init() and auto-refresh]
├─ renderIncidentBoard()                  [Updates #incident-board]
│  └─ Creates incident cards HTML
├─ renderTimeline()                       [Updates #timeline]
│  └─ Creates timeline events HTML
├─ renderExecutiveScorecard()             [Updates scorecard elements]
│  ├─ Sets #score-risk value
│  ├─ Sets #score-risk-level color
│  ├─ Sets #score-waap, #score-dns, etc.
│  └─ Sets #score-incidents, #score-vulns
└─ renderMCPCommandCenter()               [Updates MCP status]
   └─ Shows ACTIVE/OFFLINE status
```

## Critical Issues in Data Flow

### C-001: Executive Scorecard
- **Issue**: renderExecutiveScorecard() runs but shows "UNKNOWN"
- **Cause**: Unknown (Render deployment lag prevents verification)
- **Fix**: Need to verify element IDs match and data exists

### C-003: Incident Board
- **Issue**: #incident-board renders but stays empty
- **Cause**: renderIncidentBoard() not creating cards
- **Fix**: Check if stateData.incidents is null or cards HTML not generated

### C-004: Timeline
- **Issue**: #timeline renders but stays empty
- **Cause**: renderTimeline() not creating events
- **Fix**: Check if stateData.incidents is parsed correctly

## Data Freshness Calculation

```javascript
function getDataFreshness(fetchedAt, sourceTimestamp) {
  const now = new Date();
  const fetchTime = new Date(fetchedAt);
  const freshness = Math.floor((now - fetchTime) / (1000 * 60)); // minutes
  return `${freshness} min`;
}
```

**Example**: If fetched 1 minute ago → "1 min FRESH"

---

**Tiếp theo**: Xem SESSION_STATE.md để biết trạng thái hiện tại.
