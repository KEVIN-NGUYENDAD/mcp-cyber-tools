# SentinelOps Command Center - Deployment Guide

## Deployment Status

**Platform**: Vercel  
**Domain**: sentinelops.fyi  
**Current State**: Ready for deployment  

---

## Quick Start Deployment

### Prerequisites
- GitHub account with access to [KEVIN-NGUYENDAD/mcp-cyber-tools](https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools)
- Vercel account (free tier available)
- Porkbun DNS access for sentinelops.fyi

### Step 1: Set Up Vercel Project

1. Go to [vercel.com](https://vercel.com/new)
2. Click "Import Project"
3. Select "Import Git Repository"
4. Connect GitHub and select `KEVIN-NGUYENDAD/mcp-cyber-tools`
5. Configure project:
   - **Project Name**: sentinelops-command-center
   - **Framework Preset**: Other (Node.js)
   - **Root Directory**: . (root)
   - **Environment Variables**:
     ```
     STATE_DIR=./state
     NODE_ENV=production
     ```
6. Click "Deploy"

### Step 2: Configure DNS

1. Copy the Vercel deployment URL (e.g., `sentinelops-command-center.vercel.app`)
2. Go to Porkbun DNS settings for sentinelops.fyi
3. Update CNAME record to point to Vercel:
   ```
   Subdomain: @
   Type: CNAME
   Value: cname.vercel.app.
   ```
4. Add Vercel's nameservers to Porkbun account settings
5. Wait for DNS propagation (5-30 minutes)

### Step 3: Connect Custom Domain

1. In Vercel dashboard, go to Project Settings → Domains
2. Click "Add Domain"
3. Enter `sentinelops.fyi`
4. Vercel will verify DNS (automatic if CNAME is set correctly)
5. Select "Add" to connect

### Step 4: Enable GitHub Actions

1. Go to repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   ```
   VERCEL_TOKEN         = <your-vercel-token>
   VERCEL_ORG_ID        = <your-vercel-org-id>
   VERCEL_PROJECT_ID    = <your-vercel-project-id>
   ```
3. Workflow will automatically deploy on push to `main` or `develop` branches

---

## Vercel Configuration Files

### vercel.json
Defines build and deployment settings:
- Serverless function for web/server.js
- Routes all requests through Express.js
- Environment variable injection for STATE_DIR

### .github/workflows/deploy.yml
Automated CI/CD pipeline:
- Triggers on push to main/develop branches
- Changes to web/, state/, or package.json
- Installs Vercel CLI and deploys
- Manual trigger via `workflow_dispatch`

---

## Data Freshness Strategy

### Challenge
State files are updated by local MCP system, but Vercel is stateless.

### Solutions

#### Option A: Sync State Files (Recommended)
- Commit state files to git periodically
- Vercel reads from repository during build
- Pro: Always in sync, no external dependencies
- Con: Requires git commits for updates

#### Option B: API Proxy
- Web server proxies requests to local MCP API
- Requires network tunnel or webhook integration
- Pro: Real-time data
- Con: Requires running local service

#### Option C: Webhook Receiver
- MCP system POSTs state updates to Vercel Function
- Vercel stores in persistent KV store (paid feature)
- Pro: Real-time with caching
- Con: Requires paid Vercel tier

### Current Implementation
Using **Option A**: State files are included in git, Vercel deploys latest committed version.

**To keep data fresh**:
```bash
# Run locally to regenerate state files
npm run collect-data  # (if available)

# Commit and push
git add state/*.json
git commit -m "chore: update state data"
git push origin main
# GitHub Actions automatically deploys!
```

---

## Environment Variables

### Vercel Environment Variables

```bash
STATE_DIR=./state              # Location of state files
NODE_ENV=production            # Production mode
PORT=3000                      # Express server port (Vercel sets this)
```

### Getting Vercel Tokens

**VERCEL_TOKEN**:
1. Go to vercel.com → Settings → Tokens
2. Create new token with scope: "Full Access"
3. Copy token

**VERCEL_ORG_ID** and **VERCEL_PROJECT_ID**:
1. Go to project in Vercel dashboard
2. Project Settings → General
3. Copy "Project ID"
4. Go to Team Settings → General
5. Copy "Team ID" (this is ORG_ID)

---

## Deployment Checklist

- [ ] Vercel account created and GitHub connected
- [ ] Project imported into Vercel
- [ ] STATE_DIR environment variable set
- [ ] Initial deployment successful
- [ ] Custom domain sentinelops.fyi connected
- [ ] DNS CNAME records updated
- [ ] GitHub secrets added (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID)
- [ ] Workflow file in place (.github/workflows/deploy.yml)
- [ ] Test deployment by pushing to main/develop branch
- [ ] Verify https://sentinelops.fyi loads successfully

---

## Testing Deployment

### 1. Verify DNS Resolution
```bash
# Linux/Mac:
nslookup sentinelops.fyi
dig sentinelops.fyi

# Windows PowerShell:
[System.Net.Dns]::GetHostEntry("sentinelops.fyi")
```

### 2. Test Web Server Locally
```bash
npm install
PORT=3000 STATE_DIR=./state node web/server.js
```
Open: http://localhost:3000

### 3. Test API Endpoints
```bash
curl http://localhost:3000/api/health
curl http://localhost:3000/api/status
curl http://localhost:3000/api/state/assets.json
```

### 4. Test Production Deployment
```bash
# After DNS propagation:
curl https://sentinelops.fyi
curl https://sentinelops.fyi/api/status
```

---

## Troubleshooting

### DNS Not Resolving
- Wait 5-30 minutes for propagation
- Clear DNS cache: `ipconfig /flushdns` (Windows)
- Check Porkbun DNS settings are correct

### Vercel Deployment Fails
1. Check GitHub Actions logs
2. Verify VERCEL_TOKEN is valid
3. Ensure STATE_DIR path is correct
4. Check that web/server.js is valid

### Web Platform Shows Empty Data
- Verify state files are committed to git
- Check STATE_DIR environment variable in Vercel dashboard
- Inspect Network tab in browser for 404 errors

### API Returns 404
- Confirm state files exist in repository
- Check filename matches whitelist in web/server.js
- Restart local server and retry

---

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│     GitHub Repository                   │
│  (Contains web/ + state/ + config)      │
└────────────────┬────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼──────────────────┐  │
│  GitHub Actions        │  │
│  - Detects push        │  │
│  - Runs workflow       │  │
│  - Calls Vercel CLI    │  │
└─────┬──────────────────┘  │
      │                     │
┌─────▼──────────────────┐  │
│  Vercel               │  │
│  - Builds project     │  │
│  - Deploys serverless │  │
│  - Serves at domain   │  │
└─────┬──────────────────┘  │
      │                     │
┌─────▼──────────────────┬──┴──┐
│   https://sentinelops.fyi   │
│   (Via Porkbun DNS CNAME)   │
└────────────────────────────┘

┌──────────────────────────────┐
│  Browser                      │
│  ├─ GET / → index.html       │
│  ├─ GET /app.js              │
│  └─ GET /api/state/*.json    │
└──────────────────────────────┘
```

---

## Post-Deployment Tasks

### 1. Update Portfolio Homepage
Replace the old sentinelops.fyi portfolio with SOC Command Center:
```bash
# The new site will automatically serve as the homepage
# Old files should be removed or archived
```

### 2. Verify All Routes Work
- [ ] `/` - Overview page loads
- [ ] `/network` - Network topology page works
- [ ] `/incidents` - Incident board displays
- [ ] `/analytics` - Analytics page loads
- [ ] `/history` - Timeline page works
- [ ] `/settings` - Configuration page accessible

### 3. Monitor Uptime
Set up Vercel monitoring:
1. Vercel Dashboard → Settings → Monitoring
2. Enable error tracking
3. Monitor performance metrics

### 4. Keep State Data Fresh
Schedule state file updates:
```bash
# Create a cron job or CI step to:
# 1. Run data collection scripts
# 2. Commit state files to git
# 3. Push to repository
# GitHub Actions automatically deploys
```

---

## Rollback Procedure

If deployment causes issues:

### Quick Rollback
1. Go to Vercel dashboard
2. Select project
3. Go to "Deployments" tab
4. Click three-dots menu on previous working deployment
5. Select "Promote to Production"

### Git Rollback
```bash
# Revert last commit
git revert HEAD
git push origin main
# GitHub Actions automatically deploys reverted version
```

---

## Performance Optimization

### Caching Strategy
- Static assets (index.html, app.js) cached by Vercel CDN
- API responses can be cached (see web/server.js CORS headers)
- Consider adding cache headers:

```javascript
// Example: cache state endpoints for 30 seconds
app.get('/api/state/:filename', (req, res) => {
  res.set('Cache-Control', 'public, max-age=30');
  // ... rest of handler
});
```

### Auto-Refresh Configuration
Dashboard auto-refresh default: 30 seconds
Can be adjusted in Settings page
Recommend: 30-60 seconds for production

---

## Security Considerations

- ✅ HTTPS enforced by Vercel
- ✅ State files whitelist prevents directory traversal
- ✅ CORS configured for API access
- ✅ No credentials in code
- ⚠️ State files should not contain sensitive data
- ⚠️ Consider access restrictions for API if sensitive

---

## Support & Documentation

- **Vercel Docs**: https://vercel.com/docs
- **GitHub Actions**: https://docs.github.com/en/actions
- **Express.js**: https://expressjs.com/
- **Project**: See /web/README.md for architecture details

---

**Last Updated**: 2026-09-06  
**Status**: Deployment-ready  
**Platform**: Vercel + GitHub Actions + Porkbun DNS
