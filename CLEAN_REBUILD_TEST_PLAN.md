# CLEAN REBUILD TEST PLAN
**v1.1.0 Repository Integrity & Reproducibility Validation**
**Date**: 2026-08-21
**Purpose**: Verify fresh clone from GitHub works correctly (no dev environment dependencies)

---

## 🎯 TEST OBJECTIVE

**Validate that v1.1.0 can be deployed from GitHub without any development environment assumptions.**

What we're checking:
- ✅ Dependency integrity (package.json + package-lock.json)
- ✅ GitHub repository completeness (nothing missing)
- ✅ Build reproducibility (clone → install → run)
- ✅ No hardcoded paths from dev environment
- ✅ All required files committed

---

## 📋 TEST STEPS

### Step 1: Create Clean Test Directory
```powershell
# Create isolated test directory
mkdir C:\Temp\cyber-tools-clean-test
cd C:\Temp\cyber-tools-clean-test
```

### Step 2: Fresh Clone from GitHub
```powershell
# Clone v1.1 from GitHub
git clone https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools.git
cd mcp-cyber-tools

# Verify v1.1 branch available
git branch -a
```

**Expected output**:
```
* master
  develop
  v1.1
  remotes/origin/HEAD -> origin/master
  remotes/origin/develop
  remotes/origin/master
  remotes/origin/v1.1
```

### Step 3: Checkout v1.1 Release Branch
```powershell
git checkout v1.1
```

**Expected output**:
```
Branch 'v1.1' set up to track 'origin/v1.1'.
Switched to a new branch 'v1.1'
```

### Step 4: Verify Tag v1.1.0 Exists
```powershell
git tag
git show v1.1.0
```

**Expected output**:
```
v1.1.0

tag v1.1.0
Tagger: [user]
Date:   [date]

Operational Readiness Release - Fresh Deployment Certified
```

### Step 5: Clean Install Dependencies
```powershell
# Clean npm cache
npm cache clean --force

# Install with clean lock file
npm ci
```

**Expected output**:
```
added 90 packages in X seconds
```

**Watch for**:
- ❌ Missing package errors
- ❌ Dependency version conflicts
- ❌ Network failures (should complete cleanly)

### Step 6: Verify Installation Completeness
```powershell
# Check node_modules exists
Test-Path node_modules
# Should return: True

# Check package count
(Get-ChildItem node_modules).Count
# Should be: 90+

# Check main server file exists
Test-Path server.js
# Should return: True

# Check all critical files
Test-Path package.json
Test-Path package-lock.json
Test-Path README.md
Test-Path -Path modules
# All should return: True
```

### Step 7: Server Startup Test
```powershell
# Start server (runs in background, ctrl+c to stop)
node server.js
```

**Expected output**:
```
Server is running on port [PORT]
```

**Verify**:
- ✅ Server starts without errors
- ✅ No missing module errors
- ✅ No path errors
- ✅ MCP initialization successful

### Step 8: Run Certification (if applicable)
```powershell
# In another terminal, test npm run certify
npm run certify
```

**Expected output**:
```
Deployment Verification
Tier 1 Gate Validation
Certification Results
Report generated
```

---

## ✅ SUCCESS CRITERIA

All of these must PASS:

```
✅ GitHub clone successful
✅ v1.1 branch checks out
✅ v1.1.0 tag exists
✅ npm ci completes without errors
✅ node_modules created (90+ packages)
✅ All critical files present
✅ server.js starts without errors
✅ No path errors or module errors
✅ npm run certify executes (if available)
```

---

## 🚨 POTENTIAL ISSUES & SOLUTIONS

### Issue 1: Missing Package
**Error**: `Cannot find module 'X'`
**Solution**:
- Check if installed: `npm list X`
- Verify package.json has it
- If missing: Add to package.json and re-commit

### Issue 2: Hardcoded Path
**Error**: `Path 'C:\Users\...\...\' does not exist`
**Solution**:
- Replace hardcoded path with relative path
- Use `__dirname` or `process.cwd()`
- Re-commit and re-test

### Issue 3: Missing File
**Error**: `ENOENT: no such file or directory 'X'`
**Solution**:
- Check if file committed to git
- If missing from repo: `git add` and commit
- If accidentally excluded: Add to .gitignore? No - should be included

### Issue 4: Port Already In Use
**Error**: `EADDRINUSE: address already in use`
**Solution**:
- Kill existing process: `Get-Process node | Stop-Process`
- Or change port in server.js temporarily
- Not a failure - just environment issue

---

## 📊 TEST RESULTS TEMPLATE

### Clean Rebuild Test #1
```markdown
Date: 2026-08-21
Test Directory: C:\Temp\cyber-tools-clean-test
Branch: v1.1
Tag: v1.1.0

Results:
  ✅ GitHub clone: SUCCESS
  ✅ Branch checkout: SUCCESS
  ✅ Tag verification: SUCCESS
  ✅ npm ci: SUCCESS
  ✅ Files present: SUCCESS
  ✅ Server startup: SUCCESS
  ✅ npm run certify: [PASS/FAIL/SKIPPED]

Issues Found: [NONE / List any]
Time to Deploy: ~15 minutes
Conclusion: REPRODUCIBLE / NOT REPRODUCIBLE
```

---

## 🎯 WHAT THIS VALIDATES

### For v1.1.0 Release
- Repository is complete and self-contained
- No developer environment dependencies
- GitHub version matches working version
- Fresh installations will succeed

### For v1.2 Planning
- Confidence in repository integrity
- Baseline for multi-host deployment
- Framework proven reproducible
- Ready for enterprise deployment

### For Future Releases
- Sets precedent for clean rebuild testing
- Establishes reproducibility as requirement
- Early detection of missing dependencies
- Prevents deployment surprises

---

## 🚀 PROCEDURE

### Quick Reference
```
1. mkdir C:\Temp\cyber-tools-clean-test
2. cd C:\Temp\cyber-tools-clean-test
3. git clone https://github.com/KEVIN-NGUYENDAD/mcp-cyber-tools.git
4. cd mcp-cyber-tools
5. git checkout v1.1
6. npm ci
7. node server.js
8. npm run certify (optional test)
```

### Expected Time
- Clone: 1-2 minutes
- npm ci: 3-5 minutes
- Server startup: <30 seconds
- Verification: 5-10 minutes
- **Total: 10-15 minutes**

---

## ✅ SIGNIFICANCE

**This test matters because:**

1. **Validates Release Integrity**
   - v1.1.0 is complete on GitHub
   - Nothing was accidentally left off

2. **Tests Reproducibility**
   - Any user can deploy v1.1.0
   - Process is repeatable
   - No special setup needed

3. **Finds Issues Early**
   - Discovers missing packages
   - Finds hardcoded paths
   - Catches forgotten commits

4. **Builds Confidence**
   - v1.1.0 genuinely works from scratch
   - Ready for enterprise deployment
   - Foundation for v1.2 planning

---

## 📝 COMPLETION CHECKLIST

- [ ] Create test directory
- [ ] Clone from GitHub
- [ ] Checkout v1.1
- [ ] npm ci succeeds
- [ ] All files present
- [ ] Server starts
- [ ] npm run certify runs (optional)
- [ ] Document results
- [ ] Fix any issues found
- [ ] Re-commit if changes made
- [ ] Test again if issues fixed

---

## 🎊 SUCCESS OUTCOME

If all steps PASS:
```
✅ Clean Desktop Rebuild: PASS
✅ v1.1.0 Repository: COMPLETE & VALID
✅ Deployment: REPRODUCIBLE
✅ Enterprise Ready: CONFIRMED
```

Then mark in stabilization records:
- v1.1.0 Repository Integrity: ✅ VERIFIED
- Build Reproducibility: ✅ VERIFIED
- Deployment Readiness: ✅ CONFIRMED

---

**CLEAN REBUILD TEST: READY TO EXECUTE** ✅

Estimated time: 10-15 minutes
Benefit: Validates entire v1.1.0 release integrity
Impact: High confidence in reproducibility

Run test now to ensure v1.1.0 is deployment-ready.
