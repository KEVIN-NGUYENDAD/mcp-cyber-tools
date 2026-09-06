# FRESH LAPTOP MICRO-TESTS
**Operational Reality Validation**
**Supplementary to Priority 1 Fresh Laptop Deployment Test**
**Date**: 2026-08-21

---

## 🎯 PURPOSE

Four additional micro-tests that validate real-world deployability beyond basic smoke tests.

Each test answers a critical deployment question:

```
Micro-Test 1: "Does path handling work on ANY Windows machine?"
Micro-Test 2: "Does graceful error handling work for non-admin users?"
Micro-Test 3: "Does Unicode/international character support work?"
Micro-Test 4: "What's the actual deployment timeline?"
```

---

## 🧪 MICRO-TEST 1: PATH INDEPENDENCE TEST

### Objective
Verify cyber-tools doesn't contain hard-coded paths specific to developer's machine.

### Setup
```powershell
# On fresh machine with DIFFERENT username structure:
# User A: C:\Users\UserA\
# vs original dev: C:\Users\tamng\

# Verify in codebase:
```

### Checklist
```
[ ] Code Search: Verify NO hard-coded paths
    grep -r "C:\\Users\\tamng" .
    Result: ❌ NONE FOUND ✅

[ ] Code Search: Verify NO hard-coded usernames
    grep -r "tamng" .
    Result: ❌ NONE FOUND (except in docs) ✅

[ ] Code Search: Verify NO hard-coded "Documents" paths
    grep -r "Documents" modules/
    Result: Any found MUST use os.homedir() ✅

[ ] Code Search: Verify NO hard-coded "Desktop" paths
    grep -r "Desktop" modules/
    Result: Any found MUST use os.homedir() ✅

[ ] Code Search: Verify NO hard-coded "Downloads" paths
    grep -r "Downloads" modules/
    Result: Any found MUST use os.homedir() ✅

[ ] Code Search: Verify NO hard-coded Claude project paths
    grep -r "mcp-cyber-tools" config/
    Result: Any found MUST use relative/absolute resolution ✅
```

### Success Criteria
```
✅ PASS if:
   • Zero hard-coded paths containing usernames
   • Zero hard-coded paths containing "Documents/Desktop"
   • All paths use: os.homedir(), __dirname, or relative paths
   • Runs identically on UserA vs UserB machines

❌ FAIL if:
   • Any path contains developer's username
   • Any path hard-codes "Documents" or "Desktop"
   • Tool behaves differently on different user accounts
```

### Test Execution
```powershell
# On fresh machine (different username):
npm test -- --grep "path-independence"

Expected: ✅ PASS
If FAIL: Identify and fix hard-coded paths
```

---

## 🧪 MICRO-TEST 2: NON-ADMIN TEST

### Objective
Verify cyber-tools gracefully handles permission issues (Tier 2: "No Silent Failures").

### Setup
```powershell
# On fresh machine, create standard (non-admin) user
# Switch to standard user account
# Run collectors that require different permission levels
```

### Checklist
```
[ ] Start server as non-admin
    Expected: ✅ Server starts OR explicit error message
    NOT acceptable: ❌ Silent failure, unknown state

[ ] Run process collector
    Expected: 
      ✅ Works (own processes)
      ❌ Explicit: "Access Denied to System32"
    NOT acceptable: ❌ No output, timeout, crash

[ ] Run registry collector (HKLM)
    Expected:
      ✅ Works (readable keys)
      ❌ Explicit: "HKLM access requires admin"
    NOT acceptable: ❌ Silent failure, partial data

[ ] Run event logs collector (System log)
    Expected:
      ✅ Works (user logs)
      ❌ Explicit: "System event log requires admin"
    NOT acceptable: ❌ No output, incomplete data

[ ] Run security audit collector
    Expected:
      ✅ Works (own user data)
      ❌ Explicit: "Full audit requires admin"
    NOT acceptable: ❌ Truncated data without notification
```

### Success Criteria
```
✅ PASS if:
   • Tier 2 principle maintained: REAL DATA or EXPLICIT ERROR
   • No permission issue causes silent failure
   • Error messages are clear and actionable
   • Non-admin gets useful subset of data
   • No crashes or hangs due to permissions

❌ FAIL if:
   • Any permission issue causes silent failure
   • Error message is vague or missing
   • Tool crashes due to permission error
   • Partial data returned without notification
```

### Test Execution
```powershell
# Switch to standard (non-admin) user
npm test -- --grep "non-admin-permissions"

Expected: ✅ PASS
If FAIL: Review error handling for permission issues
```

---

## 🧪 MICRO-TEST 3: UNICODE TEST

### Objective
Verify UTF-8 and international character handling in paths and outputs.

### Setup
```powershell
# On fresh machine, create test directories with Unicode:
mkdir C:\Users\<user>\Documents\DieuTra_Ứng
mkdir "C:\Users\<user>\Documents\Ταχύ"
mkdir "C:\Users\<user>\Documents\العربية"

# Create test files with Unicode names:
New-Item "C:\Users\<user>\Documents\DieuTra_Ứng\tệp_kiểm_tra.txt"
New-Item "C:\Users\<user>\Documents\Ταχύ\δοκιμή.txt"
New-Item "C:\Users\<user>\Documents\العربية\اختبار.txt"
```

### Checklist
```
[ ] Run file collector on Unicode paths
    Expected: ✅ Files found, paths rendered correctly
    NOT acceptable: ❌ Path encoding error, garbled names

[ ] Run process collector (check stdout encoding)
    Expected: ✅ JSON output valid UTF-8
    NOT acceptable: ❌ Replacement characters (??????)

[ ] Check JSON serialization
    Expected: ✅ ConvertTo-Json -Depth 5 handles Unicode
    NOT acceptable: ❌ Unicode characters escaped improperly

[ ] Verify registry values with Unicode
    Expected: ✅ Unicode registry values extracted correctly
    NOT acceptable: ❌ Garbled or truncated values

[ ] Test output file with Unicode names
    Expected: ✅ Report file created with correct name
    NOT acceptable: ❌ File name mangled or encoding lost
```

### Success Criteria
```
✅ PASS if:
   • Unicode paths handled correctly
   • UTF-8 output is valid JSON
   • Non-ASCII characters preserved in output
   • Works with: Vietnamese, Greek, Arabic, CJK
   • No encoding errors in logs

❌ FAIL if:
   • Unicode paths cause errors
   • UTF-8 output is invalid
   • Characters garbled or replaced
   • Encoding errors in output
```

### Test Execution
```powershell
npm test -- --grep "unicode-handling"

Expected: ✅ PASS
If FAIL: Debug JSON encoding in PowerShell pipeline
```

---

## 🧪 MICRO-TEST 4: CLEAN INSTALL TIMING

### Objective
Measure actual deployment timeline on fresh machine (not dev environment).

### Setup
```powershell
# Fresh machine, completely clean state
# Start timer at: git clone
# End timer at: Tier 1 tests passing
```

### Checklist
```
[ ] git clone time
    Start: git clone <repo>
    End: Clone complete
    Time: _____ seconds

[ ] npm install time
    Start: npm install
    End: Installation complete
    Time: _____ seconds
    Dependencies: _____ packages

[ ] npm test (Tier 1) time
    Start: npm test
    End: 15/15 PASS
    Time: _____ seconds

[ ] Scenario 1A+1B time
    Start: Run both scenarios
    End: Both PASS
    Time: _____ seconds

[ ] Report generation time
    Start: Generate report
    End: Report complete
    Time: _____ seconds
```

### Success Criteria
```
✅ PASS if:
   • Total time: < 15 minutes (acceptable for fresh install)
   • Clone: < 2 minutes
   • npm install: < 5 minutes
   • Tier 1 tests: < 2 minutes
   • Scenarios: < 2 minutes
   • Report: < 1 minute

⚠️  WARN if:
   • Total time: 15-20 minutes (marginal)
   • Any step takes longer than expected

❌ FAIL if:
   • Total time: > 20 minutes (too slow for deployment)
   • Any step hangs or stalls
   • Memory/CPU spikes during installation
```

### Test Execution
```powershell
$startTime = Get-Date
npm run certify
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalMinutes

Write-Output "Total deployment time: $duration minutes"
```

### KPI Target
```
Fresh Laptop Deployment KPI:
  Target: < 10 minutes (optimal)
  Acceptable: < 15 minutes
  Marginal: 15-20 minutes
  Unacceptable: > 20 minutes

This becomes the baseline for v1.1 performance.
```

---

## 📊 MICRO-TEST SUMMARY TABLE

| Test | Purpose | Pass Criteria | KPI |
|------|---------|---------------|-----|
| Path Independence | No hard-coded paths | Zero developer-specific paths | 100% ✅ |
| Non-Admin | Permission handling | No silent failures on permission errors | Explicit errors only |
| Unicode | UTF-8 support | Paths and output handle non-ASCII | 100% UTF-8 valid |
| Timing | Deployment speed | < 15 minutes total | < 10 min optimal |

---

## 🎯 COMPLETE TEST SEQUENCE

### Before Fresh Laptop Test Starts
```
1. Acquire fresh Windows machine
2. Document machine specs
3. Verify prerequisites (Node, Git)
```

### Main Test (Priority 1)
```
Step 1: git clone
Step 2: npm install
Step 3: node server.js
Step 4: Health check
Step 5: Tier 1 (15/15 smoke tests)
Step 6: Scenario 1A & 1B
```

### Micro-Tests (Additional Validation)
```
Micro-Test 1: Path Independence
Micro-Test 2: Non-Admin Permissions
Micro-Test 3: Unicode Handling
Micro-Test 4: Deployment Timing
```

### Sign-Off
```
All main tests + all micro-tests PASS
→ PORTABILITY CERTIFIED
→ Automated certificate generated
→ Ready for operational deployment
```

---

## 📋 PORTABILITY CERTIFICATION SIGN-OFF

### Certification Requirements
```
Sign-Off ONLY when:
  ✅ Fresh Windows machine (completely new)
  ✅ Zero prior cyber-tools installation
  ✅ Default Windows configuration
  ✅ Complete git clone (no manual setup)
  ✅ Full npm install (no hand-tuned dependencies)
  ✅ Server starts without modification
  ✅ All smoke tests PASS (15/15)
  ✅ Scenario 1A PASS
  ✅ Scenario 1B PASS
  ✅ Path Independence PASS
  ✅ Non-Admin Permissions PASS
  ✅ Unicode Handling PASS
  ✅ Deployment Timing acceptable
  ❌ NO CODE MODIFICATIONS
  ❌ NO ENVIRONMENT TWEAKS
  ❌ NO HAND-FIXES

Certification Document:
  FRESH_LAPTOP_CERTIFICATION.md
  Generated: Automatically after all tests pass
  Contains: Machine specs, test results, timing, sign-off
```

### What "Certified" Means
```
PORTABILITY CERTIFIED means:

  cyber-tools can be deployed on ANY fresh Windows machine
  by ANYONE
  with NO special knowledge
  in under 15 minutes
  with NO code modifications
  with EXPLICIT error handling for all edge cases
  
This is what "Operational Readiness" actually means.
```

### What "NOT Certified" Means
```
NOT CERTIFIED means:

  One or more tests failed
  Issues must be identified
  Code must be fixed
  Changes committed to v1.1 branch
  Fresh laptop test must be re-run
  
No shortcuts. No exceptions. No "we'll fix it later."

If test doesn't pass on fresh machine, it's not ready
for operational deployment.
```

---

## 🏆 COMPLETE VALIDATION HIERARCHY

```
════════════════════════════════════════════════════════════

TIER 3 (v1.0.2): INVESTIGATOR CAPABILITY
  Question: "Can cyber-tools investigate?"
  Answer: 6/6 scenarios PASS (peer-validated)
  Proof: Artifact matrices + peer validation

FRESH LAPTOP TEST (v1.1): OPERATIONAL REALITY
  Question: "Can cyber-tools be deployed?"
  Answer: All tests PASS on completely fresh machine
  Proof: Automated certification certificate

COMBINED: PRODUCTION READY
  Tier 3 proves: Tool capability
  Fresh Laptop proves: Real-world deployability
  Together: Complete validation for production use

════════════════════════════════════════════════════════════
```

---

## ✅ FINAL CHECKLIST: PORTABILITY CERTIFICATION

```
When Fresh Laptop Test completes:

BEFORE Sign-Off:
  [ ] Main tests all PASS
  [ ] All 4 micro-tests PASS
  [ ] No code modifications made
  [ ] No environment tweaks applied
  [ ] Timing is acceptable (< 15 min)
  [ ] Report generated automatically
  [ ] Zero exceptions or workarounds

Sign-Off:
  [ ] ✅ PORTABILITY CERTIFIED
       (or)
  [ ] ❌ NOT CERTIFIED - Issues found

If CERTIFIED:
  cyber-tools v1.1 is ready for operational deployment

If NOT CERTIFIED:
  Issues must be fixed and test re-run
```

---

**FRESH LAPTOP MICRO-TESTS: COMPLETE VALIDATION FRAMEWORK** ✅

These four micro-tests transform Fresh Laptop Deployment from a basic smoke test into a comprehensive operational reality validation.

Together with the main Priority 1 test, they prove cyber-tools is truly production-ready. 🚀
