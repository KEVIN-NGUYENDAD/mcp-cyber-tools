# SentinelOps → sentinelops.fyi Deployment Checklist

## ✅ Infrastructure Ready

- ✅ Render configuration created: `render.yaml`
- ✅ Express web server ready: `web/server.js` 
- ✅ Dashboard UI complete: `web/index.html` + `web/app.js`
- ✅ State data committed: `state/assets.json`, `state/incidents.json`, etc.
- ✅ Vercel files removed (switched to Render)

---

## 🎯 DEPLOYMENT CHECKLIST (Do This Next)

### Step 1: Access Render Dashboard
```
1. Go to https://dashboard.render.com
2. Log in (same account hosting current sentinelops-homepage)
3. Find existing "sentinelops" web service
```

### Step 2: Update Service Settings

**In Render Dashboard → Service Settings:**

1. **Build & Deploy** section:
   - Build Command: `npm install`
   - Start Command: `PORT=3000 STATE_DIR=./state node web/server.js`

2. **Environment** section - Add/Update these variables:
   ```
   NODE_ENV = production
   STATE_DIR = ./state
   PORT = 3000
   ```

3. **Git** section:
   - Repository: `KEVIN-NGUYENDAD/mcp-cyber-tools`
   - Branch: `main`
   - Auto-deploy: `Enabled`

### Step 3: Trigger Deployment
```bash
cd C:\Users\tamng\Projects\mcp-cyber-tools
git status  # Verify render.yaml is staged
git log --oneline -1  # See deployment commit
# Render detects git push and auto-deploys
```

Wait 2-3 minutes for deployment to complete.

### Step 4: Verify Deployment

```bash
# Test homepage loads
curl https://sentinelops.fyi/

# Test API health
curl https://sentinelops.fyi/api/health

# Test data endpoints
curl https://sentinelops.fyi/api/status
curl https://sentinelops.fyi/api/state/incidents.json

# Test dashboard pages (should return HTML)
curl https://sentinelops.fyi/network
curl https://sentinelops.fyi/analytics
```

All should return `200 OK` with real data.

### Step 5: Monitor Logs

In Render Dashboard → Logs:
- Watch for "SERVER LISTENING" message
- No error messages
- Request count increasing

---

## 📊 What Changes

| Aspect | Before | After |
|--------|--------|-------|
| Domain | https://sentinelops.fyi | https://sentinelops.fyi (same) |
| Host Platform | Render (portfolio) | Render (SentinelOps) |
| CDN | Cloudflare | Cloudflare (same) |
| DNS | Porkbun | Porkbun (same) |
| Data Source | Marketing copy | Real state/ files |
| Pages | Static portfolio | 6-page SOC dashboard |
| API | None | 9+ endpoints |

---

## 🚀 Success Indicators

After deployment, you should see:

1. ✅ https://sentinelops.fyi/ loads Overview page
2. ✅ /network page shows router & device topology
3. ✅ /incidents shows threat incidents with severity
4. ✅ /analytics displays vulnerability data and app security score
5. ✅ /api/health returns `{"status": "operational", ...}`
6. ✅ /api/status shows real metrics (asset count, incident count, risk score)
7. ✅ Telegram bot `/status` shows live data (not zeros)
8. ✅ Render logs show no errors

---

## 🔄 Keeping Data Fresh

After deployment, keep state files updated:

```bash
# When data collection scripts run or updates happen:
git add state/
git commit -m "chore: update threat intelligence data"
git push origin main

# Render auto-detects push and redeploys within 2-3 minutes
# No manual deployment needed
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot GET /" | Check STATE_DIR env var is set in Render |
| "Cannot find module" | Ensure package.json dependencies are installed |
| Port binding error | Render assigns PORT env var automatically |
| Data shows empty | Verify state/*.json files committed to git on main branch |
| Deployment stuck | Check Render logs for build errors |
| 404 errors | Restart service in Render dashboard |

---

## 📞 Support

**Render Docs**: https://render.com/docs  
**GitHub Repo**: KEVIN-NGUYENDAD/mcp-cyber-tools  
**Production Domain**: sentinelops.fyi  
**DNS Provider**: Porkbun  

---

## Timeline

- **Preparation**: ✅ Complete (this session)
- **Deployment**: 2-3 minutes (Render build + deploy)
- **Verification**: 5-10 minutes (test all endpoints)
- **Total**: ~20 minutes

---

**Next Action**: Execute Step 1-2 in the checklist above!
