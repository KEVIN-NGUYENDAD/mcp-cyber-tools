# Deployment Guide

## Current Setup

### Repository
- **URL**: https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools
- **Branches**: develop, master, production
- **Current branch**: develop

### Hosting
- **Platform**: Render.com (Free tier)
- **Service**: sentinelops (web service)
- **URL**: https://sentinelops-soc.onrender.com
- **Runtime**: Node.js

### Configuration
- **Port**: 3000
- **Environment**: production
- **State dir**: ./state

## Deployment Process (When Working)

### Normal Flow
1. Make changes locally
2. Commit: `git commit -m "message"`
3. Push: `git push origin develop`
4. Render detects push
5. Render builds: `npm install`
6. Render starts: `npm start` (runs web/server.js)
7. Service available at https://sentinelops-soc.onrender.com

### Time: ~2-5 minutes from push to live

---

## Current Problem

**Render auto-deploy is broken**

- Commit ee350ba: ✅ Deployed successfully
- Commits b32e80e through 7747266: ❌ NOT deployed
- Duration: 10+ hours without update
- Cause: Unknown (webhook or build system issue)

---

## Environment Variables

### render.yaml
```yaml
envVars:
  - key: NODE_ENV
    value: production
  - key: STATE_DIR
    value: ./state
  - key: PORT
    value: 3000
```

### Required Files
- `.env` (local only, not committed)
- `.env.example` (shows template)

---

## Build & Start Commands

### Build
```bash
buildCommand: npm install
```

### Start
```bash
startCommand: npm start
```

### What npm start does
```json
{
  "scripts": {
    "start": "node web/server.js"
  }
}
```

This runs the Express server on port 3000.

---

## File Structure for Deployment

```
mcp-cyber-tools/
├─ web/
│  ├─ index.html      ← Served at /
│  ├─ app.js          ← Served at /app.js
│  ├─ server.js       ← Main server file
│  └─ [CSS files]
├─ state/             ← Served at /api/state/*
│  └─ *.json files
├─ package.json       ← Dependencies
├─ render.yaml        ← Render config
└─ .env               ← Local environment (not deployed)
```

**What gets deployed**: Everything except .git, node_modules, .env

---

## How to Deploy

### Method 1: Normal Git Push (Currently Broken)

```bash
# Make changes
nano web/app.js

# Commit
git add web/app.js
git commit -m "Fix issue"

# Push
git push origin develop

# Wait 2-5 minutes for Render to build and deploy
```

**Status**: Not working (Render not responding)

---

### Method 2: Manual Redeploy (Render Dashboard)

```
1. Go to https://dashboard.render.com
2. Find "sentinelops" service
3. Click "Manual Deploy" or "Redeploy"
4. Wait for build to complete
5. Check logs for errors
```

**Status**: Worth trying if deployment stuck

---

### Method 3: Different Branch

```bash
# Create new branch
git checkout -b production
git push origin production

# Edit render.yaml
# Change: branch: production

git push origin production

# Render should deploy from new branch
```

**Status**: Partially tested, may help

---

### Method 4: Alternative Platform

If Render continues to fail, deploy to:

#### Option A: Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### Option B: Railway
```bash
# Use Railway CLI or dashboard
# Connect GitHub repo
# Auto-deploys on push
```

#### Option C: Heroku (deprecated but still works)
```bash
# Install Heroku CLI
# Create app
heroku create sentinelops

# Deploy
git push heroku develop:main
```

---

## Checking Deployment Status

### Render Dashboard
1. Visit https://dashboard.render.com
2. Click "sentinelops" service
3. See real-time logs
4. Check "Events" tab for deploy history

### Terminal
```bash
# Check if service is up
curl https://sentinelops-soc.onrender.com

# Should return index.html

# Check API
curl https://sentinelops-soc.onrender.com/api/health

# Should return JSON health check
```

### Browser
1. Open https://sentinelops-soc.onrender.com
2. F12 → Console
3. Look for [INIT] logs
4. Check last update time in UI

---

## Rollback (If Deploy Breaks)

### Option 1: Revert Code
```bash
# Find good commit
git log --oneline | head -20

# Revert to known good
git reset --hard ee350ba

# Force push (careful!)
git push origin develop --force
```

### Option 2: Redeploy Old Version
```bash
# If Render has old version cached,
# manual redeploy from Render dashboard
# should revert to last known good
```

---

## Monitoring Production

### Key Metrics
- Response time (should be <1s)
- Error rate (should be 0%)
- Data freshness (should be <5 min)
- Threat level (currently HIGH)

### Check Points
```
Every 30 seconds in browser:
- Data loads from /api/state/*
- DOM updates
- Dashboard refreshes automatically
```

---

## Troubleshooting Deployment

### Problem: Build fails
```
Check Render logs:
- npm install errors?
- syntax errors in code?
- missing dependencies?
```

### Problem: Runs but old code
```
Possible causes:
- Render cache (clear in dashboard)
- Old Docker image (rebuild)
- Webhook not firing (manual redeploy)
```

### Problem: API not responding
```
Check:
- Is server running? (should hear on :3000)
- Are state files readable? (check file permissions)
- Is PORT env variable set? (should be 3000)
```

---

## Security Notes

- **Environment**: Production (NODE_ENV=production)
- **CORS**: Enabled (app.use(cors()))
- **Secrets**: Store in .env (not in repo)
- **HTTPS**: Render provides automatic HTTPS

---

## Performance Optimization

Current setup is sufficient for:
- Single dashboard instance
- 11 assets
- JSON data files

For scaling:
- Add caching layer (Redis)
- Use database (PostgreSQL)
- Split into microservices

---

## Cost

Render Free Tier:
- Free tier has limitations
- Service spins down after inactivity
- May take 30 seconds to wake up

Upgrade options:
- Starter Plan: $7/month
- Provides persistent uptime

---

## Deployment Checklist

Before pushing to production:
- [ ] Code tested locally
- [ ] No syntax errors
- [ ] Dependencies in package.json
- [ ] Environment variables set
- [ ] State files valid JSON
- [ ] No secrets in code
- [ ] Commit message clear
- [ ] Ready to wait 2-5 minutes

---

**Current Status**: Render deployment broken, manual or alternative platform needed.

**Recommended**: Try Method 2 (manual redeploy) or Method 4 (alternative platform).
