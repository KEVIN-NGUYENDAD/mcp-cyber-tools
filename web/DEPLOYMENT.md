# SentinelOps Web Platform - Deployment Guide

## Quick Start

### 1. Install Dependencies
```bash
cd C:\Users\tamng\Projects\mcp-cyber-tools
npm install
```

### 2. Launch Web Server (via Claude Code)
```bash
/fast
```
Then use the browser pane preview feature:
1. Click "Preview"
2. Select "sentinelops-web"
3. Browser opens http://localhost:3000

### 3. Manual Launch
```bash
cd C:\Users\tamng\Projects\mcp-cyber-tools
node web/server.js
```

Open browser: http://localhost:3000

## Architecture Overview

```
SentinelOps Platform
├── Backend (Node.js)
│   ├── web/server.js (Express app)
│   ├── API endpoints (/api/state/*)
│   └── Reads from state/ directory
│
├── Frontend (Vanilla JS)
│   ├── web/index.html (UI structure)
│   ├── web/app.js (Dashboard logic)
│   └── Fetches data from backend
│
└── Data (JSON state files)
    ├── state/assets.json
    ├── state/incidents.json
    ├── state/risk_score.json
    └── ... (13 more files)
```

## Deployment Scenarios

### Local Development
```bash
# Terminal 1: Web server
node web/server.js

# Terminal 2: Telegram bot (optional)
node scripts/telegram/bot-main.js

# Browser
http://localhost:3000
```

### Docker Container
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
ENV STATE_DIR=/data/state
VOLUME ["/data/state"]
CMD ["node", "web/server.js"]
```

Build and run:
```bash
docker build -t sentinelops:latest .
docker run -p 3000:3000 -v /path/to/state:/data/state sentinelops:latest
```

### Vercel Deployment
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
vercel deploy web/

# 3. Set environment variables in Vercel dashboard
# STATE_DIR=/opt/state (or use serverless function)
```

### AWS Elastic Beanstalk
```bash
# 1. Create Elastic Beanstalk app
eb init sentinelops

# 2. Create environment
eb create sentinelops-env

# 3. Deploy
eb deploy

# 4. Set state volume (EBS)
# Mount state directory as persistent volume
```

### GitHub Pages (Static Export)
Requires Node.js build step:
```bash
# Build script to export state as embedded JSON
npm run build:static
# Deploys to gh-pages branch
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinelops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sentinelops
  template:
    metadata:
      labels:
        app: sentinelops
    spec:
      containers:
      - name: web
        image: sentinelops:latest
        ports:
        - containerPort: 3000
        volumeMounts:
        - name: state
          mountPath: /data/state
      volumes:
      - name: state
        hostPath:
          path: /path/to/state
          type: Directory
```

## Production Checklist

- [ ] Verify STATE_DIR points to correct location
- [ ] Set NODE_ENV=production
- [ ] Configure reverse proxy (nginx/Cloudflare)
- [ ] Enable HTTPS/SSL
- [ ] Set CORS headers appropriately
- [ ] Monitor disk space for state files
- [ ] Set up log rotation
- [ ] Configure health checks
- [ ] Test API endpoints
- [ ] Verify data freshness
- [ ] Document deployment process

## Environment Configuration

### Available Variables
```bash
PORT=3000                    # Server port (default: 3000)
STATE_DIR=./state           # State files directory
NODE_ENV=production         # production or development
CORS_ORIGIN=*              # CORS allowed origins
LOG_LEVEL=info             # Log verbosity
```

### Setting Variables
**Linux/Mac:**
```bash
export PORT=8080
export STATE_DIR=/opt/state
node web/server.js
```

**Windows PowerShell:**
```powershell
$env:PORT = "8080"
$env:STATE_DIR = "C:\data\state"
node web/server.js
```

**Docker:**
```dockerfile
ENV PORT=3000
ENV STATE_DIR=/data/state
```

**Vercel:**
Set in Dashboard → Settings → Environment Variables

## Monitoring

### Health Check
```bash
curl http://localhost:3000/api/health
```

### Overall Status
```bash
curl http://localhost:3000/api/status
```

### Log Output
The server logs:
- Server startup
- Port listening
- Data directory
- API endpoint access
- Errors and warnings

## Troubleshooting

### "Cannot find module 'express'"
```bash
npm install
```

### "ENOENT: no such file or directory, open 'state/assets.json'"
```bash
# Check STATE_DIR
ls -la state/

# Set correctly
STATE_DIR=./state node web/server.js
```

### "Address already in use :::3000"
```bash
# Use different port
PORT=8080 node web/server.js

# Or kill process on port 3000
lsof -i :3000
kill -9 <PID>
```

### "CORS policy: No 'Access-Control-Allow-Origin'"
- Ensure CORS middleware is enabled in server.js
- Check CORS_ORIGIN environment variable
- Verify browser is making requests to correct origin

### Dashboard shows "-" for all values
- Check browser Network tab for failed /api/state/* requests
- Verify STATE_DIR files exist and are valid JSON
- Check browser console for error messages
- Restart server

## Performance Tuning

### Data Loading Optimization
```javascript
// Current: Loads all files on page load
// Optimization: Load on-demand, cache in localStorage
```

### Server Scaling
- Run multiple instances behind load balancer
- Use Redis for shared state cache
- Implement database instead of JSON files

### Frontend Performance
- Minify CSS/JS in production
- Add service worker for offline support
- Implement virtual scrolling for large lists
- Cache API responses

## Security Hardening

### API Endpoint Whitelist
Currently whitelisted files in server.js:
```javascript
const allowedFiles = [
  'assets.json',
  'incidents.json',
  'risk_score.json',
  'system_health.json',
  'defender_status.json',
  'firewall_status.json',
  'notification_history.json',
  'waap_status.json',
  'domain_status.json',
  'priority_queue.json',
  'asset_changes.json',
  'service_changes.json',
  'crypto_inventory.json'
];
```

### Headers to Add
```javascript
// Content Security Policy
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  next();
});
```

## Integration with Telegram Bot

Run both services simultaneously:

**Terminal 1: Web Platform**
```bash
node web/server.js
```

**Terminal 2: Telegram Bot**
```bash
node scripts/telegram/bot-main.js
```

Both read from same state files, providing:
- Web dashboard for team monitoring
- Mobile alerts via Telegram
- Unified data source

## Backup and Recovery

### State Files Backup
```bash
# Backup to external location
cp -r state/ /backup/state-$(date +%Y%m%d)
```

### Restore from Backup
```bash
# Copy state files back
cp -r /backup/state-20260905/* state/

# Restart server
node web/server.js
```

## Metrics

### Dashboard KPIs Updated by Web Platform
- Assets Monitored: From state/assets.json
- Open Incidents: From state/incidents.json
- Overall Risk: From state/risk_score.json
- Critical Threats: Calculated from incidents
- Data Freshness: Timestamp comparison
- Alert Status: From state/notification_history.json

### Response Times (Expected)
- Page load: 2-3 seconds
- API endpoint: 50-200ms
- Auto-refresh: 30 seconds (configurable)
- Chart updates: Instant

## License

SentinelOps Web Platform - Part of SentinelOps v1.1

---

**Support:** See project documentation
- `web/README.md` - Full documentation
- `docs/SENTINELOPS_MASTER.md` - Architecture overview
- `.claude/` - Project configuration

**Status:** PRODUCTION READY
