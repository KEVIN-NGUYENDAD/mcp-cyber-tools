# SentinelOps - M365 Copilot Context

🎯 **THIS IS THE MOST IMPORTANT FILE**

Read this first to understand the entire project in 5 minutes.

---

## AI RULES

### Ngôn ngữ
Tiếng Việt

### Workflow
- **TEAM A**: Audit → Kiểm tra production
- **TEAM B**: Fix → Sửa code
- **LOOP**: Audit → Fix → Audit (liên tục không dừng)

### Ưu Tiên
1. Production (ổn định trước)
2. Deployment (hoạt động trước)
3. Critical Issues
4. High Issues
5. Medium Issues

### Không được phép
- ❌ Thêm feature mới khi còn Critical
- ❌ Đổi giao diện khi còn Critical
- ❌ Chuyển v1.1 khi v1.0 chưa PASS

---

## Một dòng tóm tắt

**SentinelOps**: Security Operations Center dashboard monitoring 11 assets, 18 incidents, 385 vulnerabilities, deployed on Render, currently BLOCKED by deployment infrastructure failure.

---

## Dự án là gì?

Security dashboard hiển thị:
- Real-time threat level (HIGH)
- 11 monitored assets (Windows servers)
- 18 open incidents
- 385 vulnerabilities (0 critical, 0 high, 4 medium, 9 low, 372 info)
- Risk score: 74/100
- MCP threat hunting tools: 90+

**Mục tiêu**: Single pane of glass cho security team

**Status**: 🟢 Operational but 🔴 BLOCKED on deployment

---

## Kiến trúc (1 minute)

```
┌─────────────────────┐
│ Browser (User)      │
└────────┬────────────┘
         │ HTTPS
┌────────▼────────────┐
│ Render Web Server   │ ← Hosts dashboard
│ (Node.js)           │
└────────┬────────────┘
         │ Serves files
┌────────▼────────────┐
│ State Files (JSON)  │ ← Data persistence
│ Assets, Incidents   │
│ Risk, Alerts        │
└─────────────────────┘

         Plus:
      MCP Tools (90+)
      Telegram Alerts
```

**Tech Stack**:
- Frontend: HTML + CSS + Vanilla JavaScript
- Backend: Express.js (Node.js)
- Hosting: Render.com
- Data: JSON files (state/)
- Deployment: Git → Render (AUTO-DEPLOY BROKEN)

---

## Repository Structure (30 seconds)

```
mcp-cyber-tools/
├─ web/              ← Dashboard + server
│  ├─ index.html     ← UI markup
│  ├─ app.js         ← 1114 lines of logic
│  └─ server.js      ← Express server
├─ state/            ← 9 JSON data files
├─ mcp/              ← 90+ threat tools
├─ docs/project/     ← THIS DOCUMENTATION
├─ render.yaml       ← Deployment config
└─ package.json      ← Dependencies
```

**Key files**:
- `web/app.js`: All application logic
- `state/*.json`: All data
- `web/server.js`: API server
- `render.yaml`: Deployment config

---

## Workflow (The Loop)

```
┌──────────────────────────────────────┐
│ AUDIT PRODUCTION                     │
│ ┌──────────────────────────────────┐ │
│ │ Check: Any CRITICAL issues?      │ │
│ │ Method: Inspect dashboard,       │ │
│ │ check console, verify data       │ │
│ └──────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
        YES (Issues found)
             │
┌────────────▼─────────────────────────┐
│ FIX CODE                             │
│ ┌──────────────────────────────────┐ │
│ │ Edit files: web/app.js, etc.     │ │
│ │ Test locally if needed           │ │
│ │ Commit fixes to git              │ │
│ └──────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│ DEPLOY                               │
│ ┌──────────────────────────────────┐ │
│ │ git push origin develop          │ │
│ │ Wait for Render to rebuild       │ │
│ │ Reload browser to verify         │ │
│ └──────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│ VERIFY PRODUCTION                    │
│ ┌──────────────────────────────────┐ │
│ │ Check if fix deployed            │ │
│ │ Confirm issue resolved           │ │
│ │ Check console for errors         │ │
│ └──────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
        Loop back to AUDIT
```

**Important**: This loop is currently STUCK at DEPLOY phase because Render isn't responding.

---

## Known Issues (The 4 CRITICALs)

All 4 are FIXED in code but NOT deployed due to Render failure:

| ID | Problem | Impact | Fix Status |
|----|---------|--------|-----------|
| C-001 | Executive Scorecard shows "UNKNOWN" instead of values | Dashboard incomplete | ✅ Code ready, ❌ not deployed |
| C-002 | MCP widget appears twice (duplicate) | Confusing UI | ✅ Code ready, ❌ not deployed |
| C-003 | Incident Board empty (no cards) | Can't see incidents | ✅ Code ready, ❌ not deployed |
| C-004 | Timeline empty (no events) | Missing context | ✅ Code ready, ❌ not deployed |

**Root Cause**: All 4 issues in rendering functions. Code is fixed but Render deployment is broken.

---

## Current Status

### Code
```
Local: ✅ READY
GitHub: ✅ PUSHED (7 new commits)
Tests: N/A (no test suite)
```

### Deployment
```
Render: ❌ BROKEN
Last Deploy: ee350ba (Sept 7, 10+ hours ago)
Behind: 6+ commits
Status: NOT RESPONDING TO GIT PUSHES
```

### Production
```
URL: https://sentinelops-soc.onrender.com
Status: 🟢 Running (old code)
Issues: 🔴 4 CRITICAL unresolved
```

---

## What You Need to Know

### For Fixing Issues
1. Edit `web/app.js` (main logic)
2. Look for render functions: `renderIncidentBoard()`, `renderTimeline()`, `renderExecutiveScorecard()`
3. Fix issues
4. Commit and push

### For Deploying
1. Push to develop branch
2. Render should auto-deploy
3. **BUT**: Render is broken, so it won't
4. You may need to trigger manually or use alternate platform

### For Verification
1. Reload production URL
2. Check browser console (F12)
3. Look for [RENDER] logs to confirm functions are called
4. Check if DOM elements are updated

### Constraints
- ❌ DO NOT build new features (focus only on 4 CRITICALs)
- ❌ DO NOT modify UI structure unnecessarily
- ❌ DO NOT touch unrelated code
- ✅ DO focus only on the 4 CRITICAL fixes

---

## How Data Flows

```
state/assets.json
        ↓
server serves via /api/state/assets.json
        ↓
browser fetch('/api/state/assets.json')
        ↓
app.js stateData.assets = result
        ↓
renderIncidentBoard() uses stateData to create HTML
        ↓
HTML inserted into #incident-board element
        ↓
User sees incident cards on dashboard
```

**Key principle**: All data comes from state/*.json files (manually created/updated)

---

## Deployment Architecture

### Local (Your Machine)
```
YOUR CODE → git commit → git push
```

### GitHub
```
KEVIN-NGUYENDAD/mcp-cyber-tools (develop branch)
```

### Render
```
Watches: develop branch (configured in render.yaml)
Should auto-deploy on push
Currently: ❌ NOT WORKING
```

### Production
```
https://sentinelops-soc.onrender.com
Runs: web/server.js on port 3000
Serves: index.html + app.js + API endpoints
```

---

## Testing Checklist

After making fixes:

```
[ ] Code compiles (no syntax errors)
[ ] Functions called (check console logs)
[ ] DOM updated (inspect with F12)
[ ] Data displayed (visual verification)
[ ] No errors in console (F12 → Console tab)
[ ] Data freshness shows correct time
```

---

## Emergency Procedures

If Render won't deploy:

1. **Try alternate branch**:
   ```bash
   git checkout -b production
   git push origin production
   # Update render.yaml to use production branch
   ```

2. **Try manual rebuild**:
   - Go to Render dashboard
   - Click "Trigger Deploy"
   - Wait for build to complete

3. **Try different platform**:
   - Deploy to Vercel, Railway, or Heroku
   - Keep same code structure

4. **Check Render status**:
   - Visit Render status page
   - Check if service is operational

---

## Documentation Structure

Start here → Read in this order:

1. **This file** (M365_COPILOT_CONTEXT.md) - 5 min overview
2. **PROJECT_OVERVIEW.md** - Project scope and status
3. **ARCHITECTURE.md** - How system is built
4. **REPOSITORY_MAP.md** - Files and directories
5. **SESSION_STATE.md** - Current situation and blockers
6. **DATA_FLOW.md** - How data moves through system
7. **DEPLOYMENT.md** - How to deploy (when Render works)
8. **TROUBLESHOOTING.md** - Common issues and fixes
9. **GIT_STATE.md** - Branch status and commits

---

## Quick Decision Tree

### "I want to fix an issue"
→ Edit `web/app.js`
→ Find render function
→ Fix code
→ `git commit`
→ `git push origin develop`
→ Wait for Render (currently broken)

### "Render didn't deploy"
→ Read SESSION_STATE.md
→ Try alternate approach (manual/different platform)
→ Check DEPLOYMENT.md for detailed steps

### "I'm lost"
→ Read this file again
→ Check PROJECT_OVERVIEW.md
→ Look at REPOSITORY_MAP.md for file locations

### "I see an error"
→ Check TROUBLESHOOTING.md
→ If not listed, check console.log statements
→ Look for [RENDER] prefixed logs to debug

---

## Important Numbers

- 11 assets monitored
- 18 incidents open
- 385 vulnerabilities (mostly INFO)
- 7 critical threats
- 74/100 risk score
- 90+ MCP tools
- 1 min data freshness
- 4 CRITICAL issues
- 6+ commits undeployed
- 🔴 Loop BLOCKED

---

## Contact Points

**Repository**: https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools
**Deployed At**: https://sentinelops-soc.onrender.com
**Default Branch**: develop
**Current Issue**: Render deployment broken

---

**Last Updated**: 2026-09-07 (by Claude Haiku 4.5)
**Session Status**: 🔴 BLOCKED - Infrastructure issue
**Next Task**: Fix Render deployment OR redeploy to alternate platform
