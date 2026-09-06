# SentinelOps Command Center - Render Deployment Guide

## Status: Ready to Replace Existing Portfolio

**Production Domain**: https://sentinelops.fyi  
**Current Host**: Render (behind Cloudflare CDN)  
**Registrar/DNS**: Porkbun  
**Current App**: sentinelops-homepage (portfolio)  
**New App**: SentinelOps Command Center (web/server.js)  

---

## Architecture

```
sentinelops.fyi (Porkbun DNS)
         ↓
    Cloudflare CDN
         ↓
Render Web Service (Node.js)
         ↓
   web/server.js (Express)
         ↓
  state/*.json (Real threat data)
```

---

## Deployment Steps

### STEP 1: Access Render Dashboard

1. Go to https://dashboard.render.com
2. Log in with your Render account (same account that hosts current sentinelops-homepage)
3. Find the existing "sentinelops" or similar web service

### STEP 2: Update Service Configuration

In the Render dashboard for the sentinelops service:

1. **Settings** → **Build & Deploy**
   - **Build Command**: `npm install`
   - **Start Command**: `PORT=3000 STATE_DIR=./state node web/server.js`

2. **Environment** → Add/Update variables:
   - `NODE_ENV` = `production`
   - `STATE_DIR` = `./state`
   - `PORT` = `3000`

3. **Git** → Ensure GitHub repository is connected to `KEVIN-NGUYENDAD/mcp-cyber-tools`
   - Branch: `main`
   - Auto-deploy: Enabled

### STEP 3: Deploy

Push the configuration to main branch:
```bash
git add render.yaml web/server.js web/app.js web/index.html
git commit -m "deploy: Replace portfolio with SentinelOps Command Center on Render"
git push origin main
```

Render will automatically detect the push and redeploy.

**Expected deployment time**: 2-3 minutes

### STEP 4: Verify Deployment

Once deployment completes, test these endpoints:

```bash
# Homepage
curl https://sentinelops.fyi/

# API Health Check
curl https://sentinelops.fyi/api/health

# Dashboard Pages
curl https://sentinelops.fyi/network
curl https://sentinelops.fyi/incidents
curl https://sentinelops.fyi/analytics

# State Data APIs
curl https://sentinelops.fyi/api/state/assets.json
curl https://sentinelops.fyi/api/state/incidents.json
curl https://sentinelops.fyi/api/status
```

All should return `200 OK` with real data from `state/` directory.

---

## File Structure

```
project root/
├── render.yaml                 ← Render configuration (new)
├── web/
│   ├── server.js              ← Express server (production-ready)
│   ├── app.js                 ← Frontend logic
│   └── index.html             ← SOC dashboard UI
├── state/
│   ├── assets.json            ← Device inventory
│   ├── incidents.json         ← Threat incidents
│   ├── risk_score.json        ← Risk metrics
│   ├── domain_status.json     ← Domain health
│   └── waap_status.json       ← App security status
└── package.json               ← Node.js dependencies
```

---

## What Gets Replaced

**Before**: 
- sentinelops-homepage Vite/React portfolio
- Static marketing site at https://sentinelops.fyi
- Links to audit.sentinelops.fyi, soc.sentinelops.fyi (placeholders)

**After**:
- SentinelOps Command Center web platform
- Live SOC dashboard at https://sentinelops.fyi
- Real threat intelligence from state/ files
- 6-page operational interface (Overview, Network, Incidents, Analytics, History, Settings)

---

## DNS Configuration (No Changes Needed)

Porkbun DNS already points to Render via Cloudflare:
- A records: `216.24.57.7` / `216.24.57.15`
- CDN: Cloudflare (handles SSL/TLS)
- Nameservers: Porkbun (already configured)

**No DNS changes required** — the existing domain configuration continues working.

---

## Keeping State Files Fresh

The SentinelOps Command Center reads from `state/` JSON files that are committed to the repository.

### Option A: Manual Updates (Recommended for Now)
```bash
# After data collection or updates:
git add state/
git commit -m "chore: update state data from collection"
git push origin main
# Render auto-deploys (2-3 min)
```

### Option B: Automated Updates (Future)
- Create a cron job that collects data → updates `state/` → commits → pushes
- Render detects push → auto-deploys
- Updates every N hours (e.g., every 6 hours)

### Option C: Real-Time API (Future Enhancement)
- Implement a webhook receiver in web/server.js
- MCP collector sends data to webhook
- Updates state files in memory (requires Render Pro for persistence)

---

## Rollback Procedure

If deployment has issues:

### Quick Rollback (Keep Render service running)
1. Go to Render dashboard
2. Find the "Deployments" tab
3. Select a previous working deployment
4. Click "Redeploy"

### Git Rollback (Full revert)
```bash
git revert HEAD
git push origin main
# Render detects push and redeploys previous commit
```

---

## Data API Endpoints

Once deployed, these endpoints are available at https://sentinelops.fyi:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/` | Overview dashboard | HTML page |
| `/network` | Network topology | HTML page |
| `/incidents` | Incident board | HTML page |
| `/analytics` | Analytics dashboard | HTML page |
| `/history` | Timeline view | HTML page |
| `/settings` | Configuration | HTML page |
| `/api/health` | Server health | JSON |
| `/api/status` | Metrics summary | JSON |
| `/api/state/assets.json` | Device inventory | JSON |
| `/api/state/incidents.json` | Threat data | JSON |
| `/api/state/risk_score.json` | Risk metrics | JSON |
| `/api/state/domain_status.json` | Domain status | JSON |
| `/api/state/waap_status.json` | App security | JSON |

---

## Monitoring & Logs

After deployment, monitor the service:

1. **Render Dashboard** → Logs tab
   - Real-time server output
   - Error messages
   - Request logs

2. **Render Dashboard** → Metrics
   - CPU/Memory usage
   - Request count
   - Response times
   - Error rate

3. **Cloudflare** → Analytics (optional)
   - CDN cache hit rate
   - Global traffic distribution
   - DDoS/attack mitigation

---

## Troubleshooting

### Issue: Deployment fails with "npm install" error
**Solution**: Ensure `package.json` exists in project root and all dependencies are listed.

### Issue: Pages show "404" or "Cannot GET /"
**Solution**: Check that `STATE_DIR` environment variable is set to `./state` in Render settings.

### Issue: API endpoints return empty data
**Solution**: Verify state/*.json files are committed to git and on the main branch.

### Issue: "Cannot find module" errors
**Solution**: Ensure `web/server.js` uses correct `import` statements compatible with Node.js version on Render.

---

## Post-Deployment Tasks

1. ✅ Test all 6 dashboard pages load correctly
2. ✅ Verify API endpoints return real data
3. ✅ Check Telegram bot still works (test /status, /executive, /analytics commands)
4. ✅ Monitor logs for errors in first 5 minutes
5. ✅ Update any bookmarks/links pointing to sentinelops.fyi

---

## Success Criteria

✅ **Live SOC Dashboard** at https://sentinelops.fyi  
✅ **Real-time Threat Intelligence** from state files  
✅ **All 6 Pages** functional (Overview, Network, Incidents, Analytics, History, Settings)  
✅ **API Endpoints** return real data  
✅ **Telegram Bot** displays live metrics (/status, /executive, /analytics)  
✅ **Auto-Deploy** triggers on git push to main  
✅ **HTTPS/CDN** provided by Cloudflare (no change needed)  

---

## Next Steps

1. Execute STEP 1-2 above (configure Render service)
2. Push render.yaml and configuration to main
3. Monitor deployment completion (2-3 minutes)
4. Run verification checklist
5. Announce SentinelOps.fyi live to stakeholders

---

**Last Updated**: 2026-09-06  
**Status**: Ready for deployment  
**Platform**: Render + Cloudflare + Porkbun  
