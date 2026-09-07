# AI HANDOFF - For Claude, Cursor, GitHub Copilot, M365 Copilot

**Tài liệu này dành cho AI developers đang tiếp nhận dự án SentinelOps.**

---

## Context Siêu Tóm Tắt (30 giây)

**SentinelOps**: Security dashboard on Render with 4 CRITICAL issues fixed in code but NOT deployed due to Render webhook failure.

```
GitHub ✅ → Render ❌ → Production ❌
(code ready)  (broken)   (old code)
```

**Next**: Fix Render deployment OR redeploy to alternate platform.

---

## Dữ Liệu Cần Biết (60 giây)

### Repository
```
Name: mcp-cyber-tools
GitHub: KEVIN-NGUYENDAD/mcp-cyber-tools
Branch: develop
URL: https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools
```

### Deployment
```
Platform: Render.com
Service: sentinelops
URL: https://sentinelops-soc.onrender.com
Status: ❌ BROKEN (not deploying new code)
```

### Code
```
Main File: web/app.js (1114 lines)
Server: web/server.js (Express.js)
Data: state/*.json (9 files)
Config: render.yaml (deployment)
UI: web/index.html (markup)
```

### Issues
```
Total: 4 CRITICAL
Status: All fixed in code, none deployed
Root: Render auto-deploy webhook broken
```

---

## Workflow Cho AI (The Loop)

```
START
  ↓
[AUDIT] Check production for issues
  ↓
Issues found? YES → Continue
Issues found? NO → Done
  ↓
[FIX] Edit code in web/app.js
  ↓
[COMMIT] git commit -m "Fix C-XXX"
  ↓
[PUSH] git push origin develop
  ↓
[DEPLOY] Wait for Render (currently broken)
  ↓
[VERIFY] Check if production updated
  ↓
Loop back to [AUDIT]
```

**Current Blocker**: [DEPLOY] step is broken.

---

## 4 CRITICAL Issues

| # | Issue | Location | Status |
|---|-------|----------|--------|
| C-001 | Executive Scorecard UNKNOWN | renderExecutiveScorecard() | ✅ Fixed, ❌ Not deployed |
| C-002 | Duplicate MCP Widget | renderMCPCommandCenter() | ✅ Fixed, ❌ Not deployed |
| C-003 | Incident Board Empty | renderIncidentBoard() | ✅ Fixed, ❌ Not deployed |
| C-004 | Timeline Empty | renderTimeline() | ✅ Fixed, ❌ Not deployed |

---

## File Organization

### Main Application
```
web/app.js              ← 1114 lines, ALL rendering logic
web/index.html          ← UI markup, div containers
web/server.js           ← Express.js server
web/style.css           ← Styling
```

### Data
```
state/assets.json       ← 11 monitored assets
state/incidents.json    ← 18 open incidents
state/risk_score.json   ← Risk metrics
state/system_health.json ← System status
state/defender_status.json ← Windows Defender
state/firewall_status.json ← Firewall status
state/waap_status.json  ← Web app firewall
state/domain_status.json ← Domain status
state/notification_history.json ← Alerts
```

### Config & Docs
```
render.yaml             ← Render deployment config
package.json            ← Dependencies
docs/project/           ← This documentation
```

---

## Key Functions in web/app.js

```javascript
init()                    // Initialize app, start refresh loop
loadAllData()             // Load all state/*.json files
renderOverviewPage()      // Render dashboard overview
renderIncidentBoard()     // Render incident cards (C-003)
renderTimeline()          // Render timeline events (C-004)
renderExecutiveScorecard()// Render scorecard (C-001)
renderMCPCommandCenter()  // Render MCP widget (C-002)
startAutoRefresh()        // Start 30-second refresh
```

---

## How to Fix an Issue

### Step 1: Understand the Issue
1. Read START_HERE.md
2. Read SESSION_STATE.md
3. Understand which function is broken

### Step 2: Find the Code
1. Open `web/app.js`
2. Search for render function name (e.g., `renderIncidentBoard`)
3. Read the function

### Step 3: Fix It
1. Identify the bug
2. Make the fix
3. Test locally if possible

### Step 4: Commit
```bash
git add web/app.js
git commit -m "Fix C-XXX: [description]"
```

### Step 5: Push
```bash
git push origin develop
```

### Step 6: Deploy
```
Wait for Render to auto-deploy
(Currently broken, may need manual intervention)
```

---

## How to Debug

### In Browser Console
```
Open: https://sentinelops-soc.onrender.com
Press: F12
Tab: Console
Look for: [INIT], [DATA], [RENDER] logs
```

### Network Requests
```
Press: F12
Tab: Network
Filter: /api/state
Check: Response JSON
```

### DOM Elements
```
Press: F12
Tab: Elements
Find: #incident-board, #timeline, etc.
Check: Content, classes, data
```

---

## Key Metrics

- **11** assets monitored
- **18** incidents open
- **385** vulnerabilities (mostly info-level)
- **74/100** risk score
- **90+** MCP tools available
- **1 min** data freshness
- **4** CRITICAL issues
- **6+** commits undeployed

---

## Important Constraints

### DO
- ✅ Fix CRITICAL issues in web/app.js
- ✅ Test changes locally
- ✅ Commit with clear messages
- ✅ Follow the audit → fix → audit loop
- ✅ Keep focus on 4 CRITICAL issues

### DON'T
- ❌ Add new features while CRITICAL issues exist
- ❌ Redesign UI while CRITICAL issues exist
- ❌ Touch unrelated code
- ❌ Make breaking changes
- ❌ Assume Render will deploy (it won't currently)

---

## Deployment Reality

### What Should Happen
```
git push → GitHub receives → Render webhook fires → Render rebuilds → Production updated
```

### What's Actually Happening
```
git push → GitHub receives → Render webhook ❌ BROKEN ❌ → Production NOT updated
```

### Workarounds
1. **Manual Render Deploy**: Access Render dashboard, click "Trigger Deploy"
2. **Alternative Platform**: Deploy to Vercel, Railway, or Heroku
3. **SSH Deploy**: SSH into Render instance, git pull, restart server

---

## Decision Tree for AI

### "I want to fix C-001 (Executive Scorecard)"
```
1. Open web/app.js
2. Search for "renderExecutiveScorecard"
3. Read function code
4. Find the bug
5. Fix it
6. git commit -m "Fix C-001: Executive Scorecard UNKNOWN issue"
7. git push origin develop
8. Wait (Render probably won't deploy, so check manual options)
```

### "Production isn't showing my fix"
```
1. Read SESSION_STATE.md
2. Check GIT_STATE.md for commit history
3. Try Render manual deploy
4. If still broken, use alternative platform
5. Check DEPLOYMENT.md for options
```

### "I don't know what to do"
```
1. Read M365_COPILOT_CONTEXT.md (5 min overview)
2. Read ARCHITECTURE.md (how it works)
3. Read REPOSITORY_MAP.md (where things are)
4. Pick an issue from SESSION_STATE.md
5. Start fixing
```

---

## For New AI Joining

**You have 10 minutes to understand everything. Do this:**

```
Minute 1-2: Read START_HERE.md
Minute 3-4: Read M365_COPILOT_CONTEXT.md
Minute 5-6: Read SESSION_STATE.md
Minute 7-8: Skim ARCHITECTURE.md
Minute 9-10: Pick a CRITICAL issue and start
```

**After 10 minutes**: You know the project, the issues, the blocker, and next steps.

---

## Available Tools

### For Code
- Edit `web/app.js` (main logic)
- Edit `web/index.html` (UI markup)
- Edit `web/server.js` (server config)
- Edit `state/*.json` (test data)

### For Deployment
- Edit `render.yaml` (deployment config)
- Access Render dashboard (manual deploy)
- Use alternative platform (Vercel, Railway)

### For Verification
- Browser: https://sentinelops-soc.onrender.com
- Console: F12 → Console tab
- Network: F12 → Network tab

---

## Communication Protocol

### When Reporting Issues
```
Format:
- What: [brief description]
- Where: [file:line or function name]
- Impact: [how it affects dashboard]
- Fix: [what needs to be done]
```

### When Asking for Help
```
Format:
- I'm working on: [issue number]
- I tried: [what you attempted]
- Result: [what happened]
- Next: [what you want to try]
```

---

## Final Checklist Before Starting

- [ ] Read START_HERE.md
- [ ] Understand the 4 CRITICAL issues
- [ ] Know that Render deployment is broken
- [ ] Know that code fixes are ready but not deployed
- [ ] Know the next priority (check SESSION_STATE.md)
- [ ] Ready to start working

✅ When all checked: **You're ready to contribute!**

---

**Created**: 2026-09-07
**For**: Claude, Cursor, GitHub Copilot, M365 Copilot
**Language**: English (technical), Tiếng Việt (project context)
