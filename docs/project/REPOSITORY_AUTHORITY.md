# REPOSITORY AUTHORITY & SOURCE OF TRUTH

**Effective Date**: 2026-09-08  
**Precedence Level**: 🔴 CRITICAL  
**Status**: OFFICIAL - ALL DEVELOPERS MUST READ

---

## 🎯 DEFINITIVE STATEMENT

### ✅ SOURCE OF TRUTH = `develop`

**This is the authoritative branch for:**
- Production code
- Documentation
- Configuration
- State definitions
- CI/CD pipelines
- Historical records

**Commit**: 41dc197 (current HEAD)  
**Status**: Protected, requires PR for changes  
**Update Frequency**: Continuous (daily minimum)

---

## BRANCH AUTHORITY HIERARCHY

```
Tier 1 (AUTHORITY): develop
  └─ Status: PRODUCTION-READY
  └─ Protection: YES (PR required)
  └─ Trust Level: ABSOLUTE ✅
  └─ Contains: All features, all docs, all code

Tier 2 (ARCHIVE): archive/docs-sync-2026-09-08
  └─ Status: ARCHIVED (historical reference only)
  └─ Protection: NO (tag only)
  └─ Trust Level: HISTORICAL
  └─ Contains: Emergency fixes from c70391b

Tier 3 (SECONDARY): event-hub-day1, master, production
  └─ Status: INACTIVE
  └─ Protection: VARIES
  └─ Trust Level: REFERENCE ONLY
  └─ Contains: Experimental or outdated work

Tier 4 (FEATURE): feature/*, bugfix/*
  └─ Status: WORK IN PROGRESS
  └─ Protection: NO
  └─ Trust Level: UNVERIFIED
  └─ Contains: Work pending review/merge
```

---

## WHAT THIS MEANS

### ✅ DO THIS

```
Read from:  develop branch
Deploy from: develop branch
Reference: develop branch commits
Trust: develop branch state
Document: develop branch status
Monitor: develop branch health
```

### ❌ DON'T DO THIS

```
❌ Use docs-sync for production data
❌ Deploy from docs-sync
❌ Reference docs-sync commits as current
❌ Assume other branches have latest code
❌ Merge docs-sync into develop
❌ Create branches from docs-sync
```

---

## KEY FACTS

| Item | Value |
|------|-------|
| **Current develop HEAD** | 41dc197 |
| **Latest commit message** | Git cleanup: branch analysis and documentation updates |
| **Branch status** | 3 commits ahead of origin/develop |
| **Protection level** | FULL (PR required to merge) |
| **Last update** | 2026-09-08 (today) |
| **Next update** | Depends on Nessus pipeline runs |
| **Deployment target** | Render.com (sentinelops-soc.onrender.com) |

---

## EVIDENCE: WHY develop IS SOURCE OF TRUTH

### Completeness ✅

```
✅ Asset Aging Engine (270 lines)
✅ Nessus Pipeline (232 lines)
✅ WAAP Inventory Audit (508 lines)
✅ 15+ Documentation files
✅ Web API layer (server.js, app.js)
✅ Python collectors (nessus, waap, domain, etc.)
✅ Automated pipeline runs (30+ commits)
✅ Gemini CTO audit & technical review
✅ Progress logs & session state
✅ CI/CD workflows (.github/actions)
```

### docs-sync Lacks All Of Above ❌

```
❌ Asset Aging Engine - DELETED
❌ Nessus Pipeline - DELETED
❌ WAAP Inventory - DELETED
❌ Documentation - PURGED (15+ files)
❌ Recent commits - NONE (frozen at c70391b)
❌ Production code - MISSING
```

---

## CONSEQUENCES OF IGNORING THIS

### Risk Level: 🔴 CRITICAL

**If someone uses docs-sync as source of truth**:
- ❌ Missing Asset Aging metrics
- ❌ Missing Nessus automation
- ❌ Missing WAAP protection data
- ❌ Missing 15+ documentation files
- ❌ No Gemini audit insights
- ❌ No progress tracking
- ❌ Regression to stale code (10+ commits old)

**Impact**: Loss of ~4,500 lines of production code and documentation.

---

## HOW TO VERIFY

### Check develop is current:
```bash
git log --oneline develop -5
# Should show:
# - 41dc197: Git cleanup...
# - 9cf333a: Gemini audit...
# - 43bcae5: Gemini audit...
```

### Confirm develop has all features:
```bash
git show develop:asset_aging.py    # ✅ Exists
git show develop:nessus_pipeline.py  # ✅ Exists
git show develop:WAAP_DATA_INVENTORY.md  # ✅ Exists
```

### Compare with docs-sync:
```bash
git show docs-sync:asset_aging.py    # ❌ Not found
git show docs-sync:nessus_pipeline.py  # ❌ Not found
```

---

## BRANCH MANAGEMENT POLICY

### For New Feature Development
```
1. Create: git checkout -b feature/your-feature develop
2. Work: Make changes, commit
3. Push: git push origin feature/your-feature
4. PR: Create pull request to develop (required)
5. Review: Wait for approval
6. Merge: Merge to develop via GitHub UI
```

### For Hotfixes
```
1. Create: git checkout -b bugfix/critical-issue develop
2. Work: Fix issue, test thoroughly
3. Push: git push origin bugfix/critical-issue
4. PR: Create PR to develop (URGENT label)
5. Review: ASAP review + merge
6. Deploy: Render auto-deploys on merge
```

### For docs-sync (Deprecated)
```
❌ DO NOT USE
❌ DO NOT MERGE FROM
❌ DO NOT DEPLOY FROM
⚠️ Archive tag: archive/docs-sync-2026-09-08 (reference only)
```

---

## SIGN-OFF

**This document establishes official repository authority.**

- **Effective Immediately**: 2026-09-08
- **Scope**: All developers, all deployments, all CI/CD
- **Enforced By**: GitHub branch protection rules
- **Override**: Only by repository admin (explicit approval)

---

## CONTACT & ESCALATION

**Questions about branch authority?**
1. Read GIT_BRANCH_ANALYSIS.md for technical details
2. Read START_HERE.md for project workflow
3. Read BRANCH_ARCHIVAL_PLAN.md for docs-sync disposition
4. Escalate to repository admin if clarification needed

---

**Document Version**: 1.0  
**Last Updated**: 2026-09-08  
**Maintainer**: SentinelOps Repository Authority System  
**Status**: ✅ OFFICIAL & BINDING
