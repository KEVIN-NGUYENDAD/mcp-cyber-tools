# Recovery Guide - For New Developers

🚨 **Read this if you're starting fresh on this project**

---

## The Situation

SentinelOps is a security dashboard that has **4 CRITICAL issues** that were **fixed in code** but **NOT deployed to production** due to a Render infrastructure failure.

**Status**: 🔴 BLOCKED - All fixes are ready, deployment is broken

---

## Onboarding (10 minutes max)

### Step 1: Read PROJECT_OVERVIEW.md (2 min)
```
Understand: What is SentinelOps?
Goal: Know the purpose and basic architecture
```

### Step 2: Read M365_COPILOT_CONTEXT.md (3 min)
```
Understand: The workflow, issues, and constraints
Goal: Know what needs to be fixed and how
```

### Step 3: Check SESSION_STATE.md (2 min)
```
Understand: Current blockers and status
Goal: Know why nothing is deployed yet
```

### Step 4: skim REPOSITORY_MAP.md (3 min)
```
Understand: Where files are and what they do
Goal: Know how to navigate the codebase
```

**Total**: 10 minutes to full context

---

## Quick Reference

### What is broken?
- **4 CRITICAL issues** in the dashboard rendering

### Are they fixed in code?
- **YES** - All code is ready

### Why not in production?
- **Render deployment is broken** - Won't deploy new commits

### What do I do?
- **Option 1**: Fix Render (access dashboard, manual redeploy)
- **Option 2**: Deploy to alternative platform
- **Option 3**: Continue local development and testing

---

## Common Starting Tasks

### "I want to understand the code"
Read in this order:
1. PROJECT_OVERVIEW.md - What it does
2. ARCHITECTURE.md - How it's built
3. REPOSITORY_MAP.md - Where everything is
4. web/app.js (the actual code file)

### "I want to fix an issue"
Read in this order:
1. M365_COPILOT_CONTEXT.md - Issue summary
2. web/app.js (find the render function)
3. Edit and test locally
4. Commit and push (will need deployment help)

### "I want to deploy"
Read in this order:
1. SESSION_STATE.md - Why current deploy is broken
2. DEPLOYMENT.md - How deployment works
3. Follow "Method 2" or "Method 4" from DEPLOYMENT.md

### "I'm stuck"
Read in this order:
1. TROUBLESHOOTING.md - Common issues and fixes
2. GIT_STATE.md - Recent changes and commits
3. Ask for help with specific error message

---

## The Four CRITICAL Issues

| Issue | Status | Location | What needs to happen |
|-------|--------|----------|----------------------|
| C-001: Executive Scorecard shows "UNKNOWN" | ✅ FIXED | renderExecutiveScorecard() | Needs Render deployment |
| C-002: Duplicate MCP widgets | ✅ FIXED | renderMCPCommandCenter() | Needs Render deployment |
| C-003: Incident Board empty | ✅ FIXED | renderIncidentBoard() | Needs Render deployment |
| C-004: Timeline empty | ✅ FIXED | renderTimeline() | Needs Render deployment |

**All issues are code-complete. Only waiting for Render deployment.**

---

## Recommended Reading Order (by role)

### Product Manager
1. PROJECT_OVERVIEW.md
2. M365_COPILOT_CONTEXT.md
3. SESSION_STATE.md
4. Stop (that's all you need)

### DevOps/Infrastructure
1. SESSION_STATE.md
2. DEPLOYMENT.md
3. GIT_STATE.md
4. TROUBLESHOOTING.md
5. Diagnose Render issue

### Backend Developer
1. M365_COPILOT_CONTEXT.md
2. ARCHITECTURE.md
3. REPOSITORY_MAP.md
4. DATA_FLOW.md
5. web/app.js (code file)
6. Fix issues, push, and wait for deployment

### Frontend Developer
1. M365_COPILOT_CONTEXT.md
2. REPOSITORY_MAP.md
3. web/index.html (UI markup)
4. web/app.js (rendering logic)
5. Modify rendering functions

### QA / Tester
1. PROJECT_OVERVIEW.md
2. TROUBLESHOOTING.md
3. TEST the fixes once deployed
4. Report if anything still broken

### New AI / Claude
1. Read this entire RECOVERY_GUIDE.md (you are here)
2. Read M365_COPILOT_CONTEXT.md (executive summary)
3. Read SESSION_STATE.md (understand the blocker)
4. Pick a task and refer to specific docs as needed

---

## Decision Tree

### "What should I work on first?"
→ Read SESSION_STATE.md
→ All code fixes are done
→ Real blocker is Render deployment
→ Try to fix Render (or redeploy elsewhere)

### "Code is ready but not deployed?"
→ YES - This is the current situation
→ Read DEPLOYMENT.md for options
→ Try Method 2 (manual redeploy)
→ Or try Method 4 (alternate platform)

### "I'm a new developer joining the team"
→ Read this file completely
→ Read PROJECT_OVERVIEW.md
→ Read M365_COPILOT_CONTEXT.md
→ Ask for assignment
→ Refer to docs as needed

### "I found a bug in the code"
→ Document it clearly
→ Check TROUBLESHOOTING.md
→ If not listed, it's new
→ Read ARCHITECTURE.md to understand
→ Edit relevant file in web/
→ Commit and push (and pray Render works)

### "Production is broken"
→ Immediately read TROUBLESHOOTING.md
→ Check browser console (F12)
→ Check network requests
→ Look for error patterns
→ Roll back if needed (see GIT_STATE.md)

---

## Quick Commands Reference

### Check Status
```bash
git branch -a              # See all branches
git log --oneline -5       # See recent commits
git status                 # Check for uncommitted changes
curl https://sentinelops-soc.onrender.com  # Check if live
```

### Make a Fix
```bash
git checkout develop       # Make sure on develop
nano web/app.js            # Edit the file
git add web/app.js         # Stage changes
git commit -m "Fix C-001"   # Commit
git push origin develop    # Push
# Wait for Render (currently broken)
```

### Roll Back
```bash
git log --oneline -10      # Find good commit
git reset --hard ee350ba   # Reset to commit
git push origin develop    # Force push (careful!)
```

### Check Deployment
```bash
git log --oneline -1       # Latest commit
# Go to Render dashboard
# Look for deploy matching this commit
# Check build logs
```

---

## The Workflow

When things are working (they're not right now):

```
1. PLAN: Decide what to fix
2. CODE: Edit web/app.js or other files
3. TEST: Verify locally if possible
4. COMMIT: git commit with clear message
5. PUSH: git push origin develop
6. DEPLOY: Render auto-deploys (usually 2-5 min)
7. VERIFY: Check https://sentinelops-soc.onrender.com
8. REPEAT: Next issue
```

**Current Status**: Steps 1-5 are done. Step 6 is BROKEN.

---

## Important Files to Know

```
web/app.js          ← The main file (all render logic here)
web/index.html      ← The UI markup
state/*.json        ← All data (9 files)
render.yaml         ← Deployment config
package.json        ← Dependencies
```

Most of the work happens in `web/app.js`. It's 1114 lines but well-structured.

---

## Success Criteria

After you fix Render (or redeploy):

```
[ ] C-001: Executive Scorecard shows real values
[ ] C-002: MCP widget appears only once
[ ] C-003: Incident Board shows incident cards
[ ] C-004: Timeline shows event entries
[ ] Console has no [WARN] or [ERROR] logs
[ ] Dashboard refreshes every 30 seconds
[ ] Data freshness shows "X min FRESH"
```

Once all ✅, project moves back to normal operation.

---

## Getting Help

1. **If stuck on code**: Read ARCHITECTURE.md → Look in web/app.js → Find function → Fix it
2. **If stuck on deployment**: Read DEPLOYMENT.md → Try Method 2 or 4
3. **If stuck on something else**: Check TROUBLESHOOTING.md → It covers most issues
4. **If really stuck**: Grep for error message in code → Look at git history → Ask with specific error

---

## Next Steps

1. ✅ **You're reading this** - Good!
2. 📖 **Read PROJECT_OVERVIEW.md** - Understand the project
3. 📖 **Read M365_COPILOT_CONTEXT.md** - Understand the situation
4. 🔍 **Pick a task** - From SESSION_STATE.md
5. ⚙️ **Fix or deploy** - Based on which task

---

**Welcome to SentinelOps! You've got this.** 🚀

*Last updated: 2026-09-07*
