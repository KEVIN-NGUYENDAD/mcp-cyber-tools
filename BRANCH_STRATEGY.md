# BRANCH STRATEGY
**cyber-tools Git Workflow**
**Effective**: v1.0.2 release lock
**Date**: 2026-08-21

---

## 🔐 BRANCH FREEZE POLICY

### v1.0.2 (LOCKED)
```
Branch: develop
Tag: v1.0.2
Status: ✅ PRODUCTION LOCKED

What can go to develop (v1.0.2):
  ❌ New tools
  ❌ New features
  ❌ Refactoring
  ✅ Critical bug fixes ONLY
  ✅ Security patches ONLY
  ✅ Documentation updates
```

**Decision**: v1.0.2 is production-ready and locked.

All new development goes to **v1.1 branch or higher**.

---

## 🌿 BRANCH STRUCTURE

```
develop (v1.0.2 - LOCKED)
  │
  ├─ Tag: v1.0.2 (production release)
  │
  └─ [Receives only: critical fixes, security patches, docs]
     └─ Master branch for hotfixes if needed

v1.1 (OPERATIONAL READINESS)
  │
  ├─ Base: At v1.0.2
  ├─ Focus: Fresh deployment test, regression QA, reporting
  ├─ Timeline: Q4 2026
  └─ Release: v1.1.0 (operational ready)

v1.2 (DFIR MATURITY)
  │
  ├─ Base: At v1.1
  ├─ Focus: Multi-host, case management, enterprise features
  ├─ Timeline: Q1 2027
  └─ Release: v1.2.0 (enterprise ready)

v2.0 (SOC/IR PLATFORM)
  │
  ├─ Base: At v1.2
  ├─ Focus: Team collaboration, automation, platform evolution
  ├─ Timeline: 2027+
  └─ Release: v2.0.0 (platform)
```

---

## 📋 WORKFLOW: Feature Development

### Example: Adding Reporting Feature (v1.1)

```
1. Switch to v1.1
   git checkout v1.1

2. Create feature branch
   git checkout -b feature/reporting-export

3. Develop
   [Implement HTML/Markdown/PDF export]

4. Test
   npm test
   [All regression tests pass]

5. Commit
   git commit -m "feat: Add reporting export (HTML/Markdown/PDF)"

6. Push to v1.1
   git checkout v1.1
   git merge feature/reporting-export
   git push

7. Verify
   npm test
   [All tests still pass, no regression]
```

---

## 📋 WORKFLOW: Critical Hotfix (v1.0.2)

### Example: Security patch or critical bug

```
1. Create hotfix branch from develop
   git checkout develop
   git checkout -b hotfix/security-issue

2. Fix the issue
   [Implement fix]

3. Test
   npm test
   [All tests pass including the fix]

4. Commit
   git commit -m "fix: Security patch for [issue]"

5. Push to develop
   git checkout develop
   git merge hotfix/security-issue

6. Tag new patch
   git tag -a v1.0.2.1 -m "Security patch"

7. Cherry-pick to v1.1 if applicable
   git checkout v1.1
   git cherry-pick [commit-hash]
```

---

## ✅ MERGE CRITERIA

### To v1.0.2 (develop)
```
Can merge if:
  ✅ Critical bug fix
  ✅ Security patch
  ✅ Documentation
  ✅ No functionality changes
  ✅ All tests pass
  ✅ No regression detected

Cannot merge if:
  ❌ New feature
  ❌ Tool addition
  ❌ Scope change
  ❌ Refactoring
```

### To v1.1 (operational readiness)
```
Can merge if:
  ✅ Supports fresh deployment testing
  ✅ Supports regression QA
  ✅ Adds reporting capability
  ✅ Improves portability
  ✅ All tests pass
  ✅ No regression in v1.0.2 features

Cannot merge if:
  ❌ Breaks v1.0.2 capability
  ❌ Adds unproven features
  ❌ Fails regression suite
```

### To v1.2+ (future versions)
```
Can merge if:
  ✅ Supports DFIR maturity goals
  ✅ Multi-host investigation ready
  ✅ Case management workflow
  ✅ All tests pass
  ✅ Peer reviewed
  ✅ No regression
```

---

## 🏷️ TAGGING STRATEGY

### Release Tags
```
v1.0.2         (current production release)
v1.1.0         (operational readiness release - when ready)
v1.2.0         (DFIR maturity release - when ready)
v2.0.0         (SOC/IR platform release - future)
```

### Milestone Tags
```
v1.0.2-tier2-complete         (Tier 2 QA complete)
v1.1-fresh-deployment-passed  (Fresh laptop test passed)
v1.1-regression-complete      (Regression QA implemented)
v1.2-multi-host-ready         (Multi-host investigation ready)
```

### Hotfix Tags
```
v1.0.2.1       (Security patch)
v1.0.2.2       (Critical bug fix)
```

---

## 🔄 RELEASE FLOW

```
Development Branch (v1.1)
  ↓
  [All features complete]
  ↓
  [All tests pass]
  ↓
  [Peer review complete]
  ↓
  Tag: v1.1.0
  ↓
  Production Release
  ↓
  Becomes new baseline for v1.2
```

---

## 🛡️ PROTECTION RULES

### develop (v1.0.2)
```
✅ Direct pushes: DISABLED
✅ Pull requests: REQUIRED
✅ Code review: REQUIRED
✅ Status checks: MUST PASS
✅ Merge commits only from: [Critical fixes, security patches]
```

### v1.1, v1.2, v2.0
```
✅ Direct pushes: DISABLED
✅ Pull requests: REQUIRED
✅ Code review: REQUIRED
✅ Status checks: MUST PASS
✅ Regression tests: MUST PASS
```

---

## 🎯 DECISION RATIONALE

### Why Lock v1.0.2?
```
v1.0.2 represents:
  ✅ Complete QA cycle (Tier 1, 2, 3)
  ✅ Peer-validated findings
  ✅ Production-approved release

Locking ensures:
  ✅ No scope creep
  ✅ Quality baseline remains stable
  ✅ Critical fixes isolated
  ✅ Clear release lineage
```

### Why Separate v1.1 Branch?
```
v1.1 is for:
  • Fresh deployment testing
  • Regression QA automation
  • Reporting export feature
  • Portability certification

NOT for:
  • Major feature additions
  • Architecture refactoring
  • Breaking changes

This keeps v1.1 focused and maintainable.
```

---

## 📊 RELEASE SCHEDULE

```
v1.0.2: ✅ Released (2026-08-21)
  Status: Production locked
  Maintenance: Critical fixes only
  
v1.1: 🚧 Q4 2026
  Status: Operational readiness
  Focus: Deployment, regression, reporting
  Release: When fresh laptop test PASSES
  
v1.2: 🚧 Q1 2027
  Status: DFIR maturity
  Focus: Multi-host investigation
  Release: When Scenarios 6-9 certified
  
v2.0: 🚧 2027+
  Status: SOC/IR platform
  Focus: Team collaboration, automation
  Release: When platform goals met
```

---

## ✅ BRANCH INTEGRITY CHECKS

### Before Any Merge to v1.0.2
```
✅ npm test        (all regression tests pass)
✅ git log         (commit message follows standard)
✅ Code review     (at least 1 reviewer approved)
✅ Security audit  (if touching sensitive code)
✅ Documentation   (if affecting users)
```

### Before Any Merge to v1.1+
```
✅ npm test        (all regression tests pass)
✅ npm run qa      (full QA suite passes)
✅ Peer review     (investigator-focused review)
✅ Artifact check  (if adding collectors, verify output)
✅ Timeline verify (if modifying timeline logic)
```

---

## 🎓 PERMANENT PRINCIPLES

```
Principle 1: No Silent Failures (Tier 2 legacy)
  Every change to production must preserve:
  "Real Data OR Explicit Error - never Unknown"

Principle 2: No Conclusions Without Artifacts (Tier 3 legacy)
  Every new feature must support:
  "Artifact → Correlation → Narrative → Peer Validation"

Principle 3: Quality is Sacred
  v1.0.2's baseline must never degrade.
  v1.1+ must never break v1.0.2 capability.
  v2.0 must preserve methodology from v1.0.2.
```

---

## 📋 BRANCH SUMMARY

```
v1.0.2 (develop)
  ✅ LOCKED
  ✅ Production-ready
  ✅ No new features
  ✅ Critical fixes only

v1.1
  🚧 IN PROGRESS
  🚧 Operational readiness
  🚧 Regression QA
  🚧 Fresh laptop validation

v1.2, v2.0
  🚧 PLANNED
  🚧 Future development
  🚧 Clear roadmap
  🚧 Protected by branch strategy
```

---

**BRANCH STRATEGY: OFFICIALLY LOCKED**

v1.0.2 is frozen. v1.1+ follows strict process. Quality preserved. 🚀
