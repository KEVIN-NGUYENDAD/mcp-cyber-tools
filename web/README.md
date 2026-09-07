# SentinelOps Web Platform

**Live Security Operations Center Command Dashboard**

Transform https://sentinelops.fyi into a real-time SOC command center. This web platform displays live security intelligence from the SentinelOps threat detection and incident management system.

## Overview

SentinelOps Web is a modern, dark-themed SOC dashboard that reads real data from state files and presents it through an operational command center interface.

**Key Features:**
- 🏠 **Overview Dashboard** - Executive SOC view with live metrics
- 🌐 **Network Topology** - Physical network map and security relationships
- 🚨 **Incident Board** - Kanban-style incident management
- 📊 **Analytics** - Threat trends, vulnerabilities, risk analysis
- 📜 **Security Timeline** - Historical event audit trail
- ⚙️ **Live Configuration** - System settings and data source management

## Data Architecture

The web platform reads from the SentinelOps state files in real-time. No mock data is displayed.

### Data Sources

```
state/
├── assets.json                  → Device inventory, vulnerabilities
├── incidents.json               → Security incidents, threats
├── risk_score.json             → Overall risk scoring
├── system_health.json          → System operational health
├── defender_status.json        → Windows Defender status
├── firewall_status.json        → Firewall rules and status
├── notification_history.json   → Alert delivery audit trail
├── waap_status.json            → Web Application Firewall health
├── domain_status.json          → Domain and DNS status
└── ... (other state files)
```

### API Endpoints

The web server exposes data APIs:

```
GET /api/state/assets.json
GET /api/state/incidents.json
GET /api/state/risk_score.json
GET /api/state/defender_status.json
... (all state files listed in STATE_DIR)

GET /api/health
GET /api/status
```

## Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Start the web server:**
```bash
# Default (port 3000, state from ./state)
node web/server.js

# Custom port
PORT=8080 node web/server.js

# Custom state directory
STATE_DIR=/path/to/state node web/server.js
```

3. **Access the platform:**
```
http://localhost:3000
```

## Dashboard Pages

### 1. Overview
- **Mission Control** - Live threat level, asset count, incident count, risk score
- **KPI Cards** - Asset posture, threat landscape, overall risk, WAAP, DNS, data freshness
- **Recent Activity** - Latest incidents with severity indicators
- **Alert Delivery Status** - Telegram alerting metrics

### 2. Network Map
**Two topology visualization modes:**

#### Physical Network Topology
- Internet → WAAP → Router → Servers
- Color-coded by vulnerability count (🟢 healthy, 🟡 warning, 🔴 critical)
- Interactive nodes with device intelligence panel
- Real device hostnames and IPs

#### Security Relationship Map
- Shows incident → risk → alert → delivery chain
- Visualizes threat propagation
- Top critical incidents only

### 3. Incident Board
- **Kanban columns** by severity (Critical, High, Medium, Low)
- **Incident cards** with ID, title, evidence count, status
- Click to view details (future: detailed incident drawer)

### 4. Analytics
- **Vulnerability Assessment** - Total vulns by severity (critical/high/medium/low)
- **WAAP Security** - SSL status, certificate expiration
- **Domain Security** - DNS health, domain status
- **Threat Trends** - Visual charts (to be implemented)

### 5. History
- **Security Timeline** - Event feed sorted by timestamp
- Alert deliveries, incident creation, risk recalculation events
- Last 20 events displayed

### 6. Settings
- **Auto-Refresh Interval** - 15s, 30s, 1m, 5m (default 30s)
- **Data Sources** - List of monitored state files
- **Platform Info** - Version, status, operational indicator

## Design Philosophy

### Styling
- **Dark Mode** - Default SOC operational appearance
- **Glass Panels** - Translucent backgrounds with backdrop blur
- **Live Indicators** - Animated pulse effects, status LEDs
- **Color Coding**:
  - 🟢 Healthy (`#22ff22`)
  - 🟡 Warning/Medium (`#ffff00`)
  - 🟠 High/Elevated (`#ffa500`)
  - 🔴 Critical (`#ff4444`)
  - 🟦 Accent (`#00ff88` bright cyan)

### Responsive Design
- Mobile: Single column, stacked cards
- Tablet: 2-column grid
- Desktop: 3-4 column grid, full feature set

### Inspiration
- Microsoft Sentinel
- CrowdStrike Falcon Console
- Microsoft Defender XDR
- Darktrace
- Real SOC command centers

## Deployment

### Local Development
```bash
npm install
PORT=3000 STATE_DIR=./state node web/server.js
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "web/server.js"]
```

### Vercel
```bash
vercel deploy web/
```

### AWS Lightsail
```bash
# Create Lightsail instance
# SSH in and:
git clone <repo>
cd mcp-cyber-tools
npm install
PORT=80 STATE_DIR=/opt/state node web/server.js &
```

### GitHub Pages (Static Export)
Requires build step to export state data at build time.

## Environment Variables

```bash
PORT=3000                           # Server port (default: 3000)
STATE_DIR=/path/to/state           # State files directory (default: ./state)
NODE_ENV=production                 # production or development
```

## API Examples

### Get All Assets
```bash
curl http://localhost:3000/api/state/assets.json
```

Response:
```json
{
  "timestamp": "2026-09-05T23:13:15.352229",
  "total_assets": 11,
  "assets": [
    {
      "ip": "192.168.0.1",
      "hostname": "Router-01",
      "device_type": "Router",
      "vulnerability_count": 39,
      "critical": 0,
      "high": 0,
      "medium": 1,
      "low": 2,
      "info": 36
    },
    ...
  ]
}
```

### Get Incidents
```bash
curl http://localhost:3000/api/state/incidents.json
```

Response:
```json
{
  "timestamp": "2026-09-05T23:13:18.982273",
  "total_incidents": 18,
  "by_severity": {
    "CRITICAL": 7,
    "HIGH": 11
  },
  "incidents": [
    {
      "incident_id": "INC-0004",
      "severity": "CRITICAL",
      "title": "PERSISTENCE THREAT: WMI Event Consumer",
      ...
    },
    ...
  ]
}
```

### Health Check
```bash
curl http://localhost:3000/api/health
```

Response:
```json
{
  "status": "operational",
  "timestamp": "2026-09-05T23:15:00.000Z",
  "state_files": 14,
  "state_directory": "/path/to/state"
}
```

### Overall Status
```bash
curl http://localhost:3000/api/status
```

Response:
```json
{
  "operational": true,
  "timestamp": "2026-09-05T23:15:00.000Z",
  "metrics": {
    "assets_monitored": 11,
    "open_incidents": 18,
    "overall_risk": 74,
    "threat_level": "HIGH"
  }
}
```

## Architecture

### Frontend Stack
- **Vanilla JavaScript** - No framework required
- **HTML5** - Semantic structure
- **CSS3** - Grid, flexbox, animations
- **Fetch API** - Data loading from backend

### Backend Stack
- **Node.js** - Runtime
- **Express.js** - Web framework
- **CORS** - Cross-origin support
- **File system** - Read state JSON files

### Data Flow
```
State Files (.json)
        ↓
    server.js (Express)
        ↓
    API Endpoints (/api/state/*)
        ↓
    index.html (Browser)
        ↓
    app.js (JavaScript)
        ↓
    Rendered Dashboard
```

## Features Roadmap

### Implemented ✅
- [x] Overview dashboard with KPIs
- [x] Network topology (physical + security)
- [x] Incident board (kanban)
- [x] Analytics dashboard
- [x] Security timeline
- [x] Configuration panel
- [x] Auto-refresh mechanism
- [x] Responsive design
- [x] API endpoints for all state files

### Future Enhancements 🚀
- [ ] Incident detail drawer
- [ ] Device intelligence drawer
- [ ] Threat hunting dashboard
- [ ] Custom alert rules UI
- [ ] Real-time WebSocket updates
- [ ] User authentication
- [ ] Export reports (PDF)
- [ ] Advanced filtering and search
- [ ] Dark/light theme toggle
- [ ] Metrics prediction and forecasting

## Performance Considerations

- **Data Freshness**: Configure auto-refresh interval (default 30s)
- **State File Size**: Each load reads entire JSON file
- **Network**: All data loaded client-side, no server-side aggregation
- **Browser**: Modern ES6, works in all modern browsers

## Security

### Data Safety
- ✅ Only whitelisted state files served
- ✅ No user input accepted
- ✅ CORS headers set appropriately
- ✅ No credentials stored in code

### Deployment Security
- Run behind reverse proxy (nginx, Cloudflare)
- Use HTTPS in production
- Restrict API access via firewall rules
- Monitor state file permissions

## Troubleshooting

### "Cannot find state files"
```bash
# Check STATE_DIR environment variable
echo $STATE_DIR

# Verify files exist
ls -la state/
```

### "API returns 404"
- Confirm file exists in STATE_DIR
- Check filename matches whitelist in server.js
- Restart server after adding new state files

### Dashboard shows "-" for metrics
- Check data freshness (may be stale)
- Verify state files contain required fields
- Open browser console for error messages

### Auto-refresh not working
- Check browser Network tab for failed requests
- Verify STATE_DIR is readable
- Check console for JavaScript errors

## Support

For issues or feature requests, see the project documentation:
- `docs/SENTINELOPS_MASTER.md` - Architecture
- `docs/PRODUCTION_READINESS_REPORT.md` - Status
- Memory system at `~/.claude/projects/.../memory/`

## License

Part of the SentinelOps security operations platform.

---

**SentinelOps v1.1 Web Platform**  
Live. Real-time. Operational.
