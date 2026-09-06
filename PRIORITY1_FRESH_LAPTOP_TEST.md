# PRIORITY 1: FRESH LAPTOP DEPLOYMENT TEST
**Operational Readiness Validation**
**Procedure**: v1.1 Certification Path
**Date Created**: 2026-08-21
**Status**: READY FOR EXECUTION

---

## 🎯 OBJECTIVE

Prove that cyber-tools is truly portable and operates correctly on a machine that has never seen it before, with no development environment tuning, no pre-installed dependencies, and no environment assumptions.

**Success = Real-world deployability ✅**

---

## 📋 PRE-TEST CHECKLIST

### Machine Requirements
```
Hardware:
  ✅ Windows 10/11 (clean installation, no prior cyber-tools)
  ✅ Minimum 8GB RAM
  ✅ Minimum 50GB free disk space
  ✅ Internet connectivity (for git clone, npm install)

Software:
  ✅ Node.js 16+ (not pre-installed in cyber-tools repo)
  ✅ Git (not pre-installed in cyber-tools repo)
  ✅ PowerShell 5.1+ (standard on Windows)
  ✅ No prior cyber-tools installation
  ✅ No test artifacts from previous runs

State:
  ✅ Machine is clean (no cyber-tools traces)
  ✅ No environment variables set
  ✅ Default Windows configuration
  ✅ Administrator access available
```

### Pre-Test Verification
```
On the fresh machine, verify:
  ✅ Windows edition: Windows 10 or 11
  ✅ Node.js version: node --version (expect 16+)
  ✅ Git version: git --version (expect 2.0+)
  ✅ PowerShell version: $PSVersionTable.PSVersion (expect 5.1+)
  ✅ Network: Can reach github.com
  ✅ Disk space: At least 50GB free
```

### Test Environment Documentation
```
Before starting, document:
  [ ] Machine name/ID: ____________________
  [ ] OS version: ____________________
  [ ] Node.js version: ____________________
  [ ] Git version: ____________________
  [ ] PowerShell version: ____________________
  [ ] User account (admin/standard): ____________________
  [ ] Network: Connected / Isolated ____________________
  [ ] Date/time started: ____________________
```

---

## 🚀 DEPLOYMENT PHASE

### Step 1: Clone Repository
```
Command:
  git clone https://github.com/[repo-path]/mcp-cyber-tools.git
  cd mcp-cyber-tools

Expected Result:
  ✅ Repository cloned successfully
  ✅ All files present (verify with: git status)
  ✅ No errors during clone

Verify:
  git log --oneline -3
  [Should show recent commits ending with v1.0.2 work]
```

### Step 2: Install Dependencies
```
Command:
  npm install

Expected Result:
  ✅ All dependencies installed
  ✅ node_modules/ directory created
  ✅ package-lock.json present
  ✅ No installation errors

Verify:
  npm list --depth=0
  [Should show all required packages]
```

### Step 3: Start Server
```
Command:
  node server.js

Expected Result:
  ✅ Server starts without errors
  ✅ MCP server listens on configured port
  ✅ No console errors on startup
  ✅ Ready to accept requests

Output should contain:
  ✅ "Server started"
  ✅ "Listening on port [X]"
  ✅ "Tools registered: [count]"
  ✅ No ERROR messages
```

### Step 4: Health Check
```
In another terminal, verify server is running:
  
Command (PowerShell):
  $response = Invoke-WebRequest -Uri http://localhost:3000/health -Method GET
  $response.StatusCode

Expected:
  ✅ Status code: 200 (OK)
  ✅ Response body contains: "healthy" or "ok"
  ✅ Server responsive to requests
```

---

## 🧪 TIER 1 SMOKE TESTS (15/15 Must Pass)

### Test Suite Execution
```
Command:
  npm test

Expected:
  ✅ Test suite starts
  ✅ 15 smoke tests execute
  ✅ All 15 pass (15/15 PASS)
  ✅ No failures, skips, or errors
  ✅ Total execution time: < 5 minutes

Success Output Should Show:
  ✅ "15 passing"
  ✅ No "failing"
  ✅ No "pending"
  ✅ No error stack traces
```

### Individual Test Verification (If Automated Suite Fails)
```
If 15/15 test does not show, manually verify:

[ ] Test 1: Module initialization
    npm test -- --grep "module initialization"
    Expected: ✅ PASS

[ ] Test 2: MCP server startup
    npm test -- --grep "MCP server"
    Expected: ✅ PASS

[ ] Test 3: Tool registration
    npm test -- --grep "tool registration"
    Expected: ✅ PASS

[ ] Test 4: Collector functionality
    npm test -- --grep "collector"
    Expected: ✅ PASS

[ ] Test 5-15: [Remaining smoke tests]
    [Each should PASS individually]

Result:
  If ALL 15 pass individually → Tier 1 PASS ✅
  If ANY fail → Document failure and troubleshoot
```

### Tier 1 Success Criteria
```
Requirement:   15/15 smoke tests passing
Actual Result: _____ / 15 passing

✅ PASS if:   15/15 (100%)
❌ FAIL if:   < 15/15 (any failures)

Status:
  [ ] ✅ PASS (proceed to Tier 3)
  [ ] ❌ FAIL (troubleshoot, see troubleshooting section)
```

---

## 🔍 TIER 3 SCENARIO VALIDATION

### Scenario 1A: Clean System Investigation
```
Command:
  npm run scenario:1a
  
Or manual execution:
  node ./tests/tier3/scenario-1a.test.js

Expected:
  ✅ System analysis completes
  ✅ Artifacts extracted successfully
  ✅ Result: "System clean" (no malicious artifacts)
  ✅ 9 legitimate artifacts documented
  ✅ Execution time: < 60 seconds

Success Output:
  ✅ "Scenario 1A PASS"
  ✅ "Artifacts: 9/9 documented"
  ✅ "Conclusion: System clean"

Status:
  [ ] ✅ PASS
  [ ] ❌ FAIL (document error)
```

### Scenario 1B: Malware Persistence Detection
```
Command:
  npm run scenario:1b
  
Or manual execution:
  node ./tests/tier3/scenario-1b.test.js

Expected:
  ✅ Simulated malware collected
  ✅ Persistence mechanisms detected
  ✅ Registry + startup artifacts correlated
  ✅ Peer validation passes
  ✅ Execution time: < 60 seconds

Success Output:
  ✅ "Scenario 1B PASS"
  ✅ "Artifacts: REG-001, START-001 detected"
  ✅ "Conclusion: Persistence confirmed"

Status:
  [ ] ✅ PASS
  [ ] ❌ FAIL (document error)
```

### Scenario Validation Summary
```
Tier 3 Validation Results:

Scenario 1A (Clean System):
  Expected: ✅ PASS
  Actual:   [ ] PASS  [ ] FAIL

Scenario 1B (Threat Detection):
  Expected: ✅ PASS
  Actual:   [ ] PASS  [ ] FAIL

Overall Result:
  [ ] ✅ BOTH PASS (portability verified)
  [ ] ❌ ONE FAILED (investigate)
  [ ] ❌ BOTH FAILED (troubleshoot)
```

---

## ✅ SUCCESS CRITERIA

### Tier 1 Success
```
Requirement: 15/15 smoke tests passing
Status:      [ ] MET  [ ] NOT MET

If NOT MET:
  Investigate which tests are failing
  Compare with v1.0.2 results
  Document differences
```

### Tier 3 Success
```
Requirement: Scenario 1A and 1B passing
Status:      [ ] MET  [ ] NOT MET

If NOT MET:
  Investigate failure mode
  Compare with v1.0.2 results
  Check artifact extraction
```

### Overall Portability Success
```
Final Result:
  ✅ PASS if:
     • 15/15 smoke tests passing
     • Scenario 1A passing
     • Scenario 1B passing
     • No hard-coded path issues
     • No missing dependencies
     • No environment assumptions violated

  ❌ FAIL if:
     • Any test failing
     • Any scenario failing
     • Hard-coded path discovered
     • Missing dependency found
     • Environment-specific error
```

---

## 🔧 TROUBLESHOOTING

### Issue: "git clone" fails
```
Symptom:
  git clone fails with network error

Diagnosis:
  [ ] Network connection available?
  [ ] GitHub reachable?
  [ ] Correct repository URL?

Solution:
  1. Verify network: ping github.com
  2. Verify git: git --version
  3. Try HTTPS vs SSH
  4. Check firewall settings
```

### Issue: "npm install" fails
```
Symptom:
  npm install fails during dependency installation

Diagnosis:
  [ ] Node.js version correct? (node --version)
  [ ] npm version up-to-date? (npm --version)
  [ ] npm cache clean? (npm cache clean --force)
  [ ] Network available during install?

Solution:
  1. Verify Node.js version (expect 16+)
  2. Clear npm cache: npm cache clean --force
  3. Delete node_modules: rm -r node_modules
  4. Retry: npm install
```

### Issue: "node server.js" fails
```
Symptom:
  Server fails to start or crashes on startup

Diagnosis:
  [ ] Port already in use?
  [ ] Dependencies installed?
  [ ] File permissions correct?
  [ ] PowerShell version compatible?

Solution:
  1. Check port: netstat -an | findstr 3000
  2. Kill existing process if running
  3. Verify dependencies: npm list
  4. Check logs: node server.js 2>&1 (capture output)
```

### Issue: Tests fail with "path not found"
```
Symptom:
  Tests fail with path like "C:\Users\[dev-name]\..."

Diagnosis:
  ✅ Hard-coded path detected (environment issue)
  ✅ Relative path not resolving correctly

Solution:
  1. Identify hard-coded paths
  2. Update to use: os.homedir(), __dirname, or relative paths
  3. Fix in: modules/ directory
  4. Re-run tests
```

### Issue: Collector returns no output
```
Symptom:
  Collector runs but produces no output or partial output

Diagnosis:
  [ ] PowerShell command syntax correct?
  [ ] Permissions to read registry/files?
  [ ] File/registry path exists?
  [ ] Output format correct (JSON)?

Solution:
  1. Test command manually in PowerShell
  2. Verify output is JSON (not errors)
  3. Check: ConvertTo-Json -Depth 5 working
  4. Verify file/registry paths are accessible
```

---

## 📊 TEST EXECUTION LOG

### Pre-Deployment
```
Machine Information:
  Machine Name:        ____________________
  OS Version:          ____________________
  Node.js Version:     ____________________
  Git Version:         ____________________
  PowerShell Version:  ____________________
  
Test Started:          ____________________
Tester Name:           ____________________
Environment Notes:     ____________________
```

### Deployment Phase Results
```
[ ] Step 1: git clone
    Status:        [ ] PASS  [ ] FAIL
    Issues:        ____________________
    Time:          _____ minutes

[ ] Step 2: npm install
    Status:        [ ] PASS  [ ] FAIL
    Package Count: _____
    Issues:        ____________________
    Time:          _____ minutes

[ ] Step 3: node server.js
    Status:        [ ] PASS  [ ] FAIL
    Port:          _____
    Issues:        ____________________
    Time to Ready: _____ seconds

[ ] Step 4: Health Check
    Status:        [ ] PASS  [ ] FAIL
    Response Code: _____
    Issues:        ____________________
```

### Test Results
```
Tier 1 Smoke Tests:    _____ / 15 PASS
  Status:              [ ] PASS  [ ] FAIL

Scenario 1A:           [ ] PASS  [ ] FAIL
  Issues:              ____________________

Scenario 1B:           [ ] PASS  [ ] FAIL
  Issues:              ____________________

Overall Result:
  [ ] ✅ PORTABILITY VERIFIED
  [ ] ❌ ISSUES FOUND (details below)
```

---

## 🎯 SIGN-OFF

### Test Completion
```
Date Completed:        ____________________
Tester Name:           ____________________
Test Duration:         _____ hours
Machine Used:          ____________________

Final Status:
  [ ] ✅ ALL TESTS PASSED - PORTABILITY VERIFIED
  [ ] ⚠️  SOME TESTS FAILED - ISSUES DOCUMENTED
  [ ] ❌ CRITICAL FAILURE - INVESTIGATION REQUIRED
```

### Portability Certification
```
If ALL TESTS PASSED:

  This machine successfully:
    ✅ Cloned cyber-tools from repository
    ✅ Installed all dependencies
    ✅ Started server without errors
    ✅ Passed 15/15 smoke tests
    ✅ Passed Scenario 1A
    ✅ Passed Scenario 1B

  Conclusion:
    PORTABILITY VERIFIED ✅
    
    cyber-tools can be deployed on a completely fresh
    Windows machine with no prior installation or
    environment tuning required.

  Next Step:
    Proceed to v1.1 release readiness
```

### Issues Found (If Any)
```
If ANY TESTS FAILED:

  Issues Discovered:
    1. ____________________
    2. ____________________
    3. ____________________

  Severity Assessment:
    [ ] Critical (blocks release)
    [ ] High (needs fixing)
    [ ] Medium (should fix)
    [ ] Low (nice to fix)

  Action Items:
    1. Fix issue #1: ____________________
    2. Fix issue #2: ____________________
    3. Fix issue #3: ____________________

  Re-Test Date:
    ____________________
```

---

## ✅ SUCCESS DEFINITION

```
Fresh Laptop Deployment Test PASSES when:

  ✅ On a completely fresh Windows machine
  ✅ With no prior cyber-tools installation
  ✅ With default Windows configuration
  ✅ With no environment variable tuning
  ✅ The following ALL succeed:
    • git clone works
    • npm install works
    • node server.js starts
    • Health check responds
    • 15/15 smoke tests pass
    • Scenario 1A passes
    • Scenario 1B passes

Fresh Laptop Deployment Test FAILS when:

  ❌ Any step above fails
  ❌ Any test does not pass
  ❌ Hard-coded paths discovered
  ❌ Environment assumptions violated
  ❌ Permission issues encountered
```

---

## 📋 FINAL VERIFICATION

```
════════════════════════════════════════════════════════════

PRIORITY 1: FRESH LAPTOP DEPLOYMENT TEST

Purpose:       Prove cyber-tools is truly portable
Importance:    Highest - gates v1.1 release readiness
Success Rate:  Must be 100% (all tests pass)
Timeline:      Complete before v1.1 release decision

When This Test Passes:
  ✅ cyber-tools is deployment-ready
  ✅ No environment assumptions needed
  ✅ No hard-coded paths preventing portability
  ✅ Real-world deployability proven

When This Test Fails:
  ❌ Issues must be identified and fixed
  ❌ Root cause must be addressed
  ❌ Test must be re-run on fresh machine
  ❌ Release readiness postponed until fixed

════════════════════════════════════════════════════════════
```

---

**PRIORITY 1 CHECKLIST: READY FOR EXECUTION** ✅

This is the most important validation for v1.1 operational readiness.

A fresh laptop test passing = Real-world deployability proven.

Execute with rigor. Document thoroughly. Success is binary. 🚀
