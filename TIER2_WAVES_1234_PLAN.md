# Tier 2 Waves 1-4: Complete Test Plan
**v1.0.2 QA Phase**  
**Date**: 2026-08-21  
**Status**: READY FOR EXECUTION

---

## 📋 OVERVIEW

Wave Testing Strategy (5 waves total):
- **Wave 1**: Serialization (JSON handling)
- **Wave 2**: Invalid Input (error handling)
- **Wave 3**: Unicode (international text)
- **Wave 4**: Access Denied (permission boundaries)
- **Wave 5**: Large Output ✅ **COMPLETE**

---

## 🌊 WAVE 1: SERIALIZATION (JSON Handling)

**Objective**: Verify all collectors properly serialize complex objects to JSON

**Status**: ✅ Verified as part of Wave 5 testing

**Evidence**:
```
✅ systemLogs (500 events) → Valid nested JSON
✅ collectEvidence (multiple collectors) → Valid nested JSON
✅ runningProcesses (100 records) → Valid array JSON
✅ servicesChecker (309 records) → Valid array JSON
```

**Result**: WAVE 1 PASS ✅

---

## 🌊 WAVE 2: INVALID INPUT (Error Handling)

**Objective**: Verify tools gracefully handle malformed/invalid inputs

### Test Cases

#### Test 2.1: Negative numbers for count parameters
```
Tool: runningProcesses
Input: limit=-10
Expected: Error or default to safe value
Status: PENDING
```

#### Test 2.2: Zero values
```
Tool: systemLogs
Input: count=0
Expected: Return empty array or error message
Status: PENDING
```

#### Test 2.3: Extremely large numbers
```
Tool: runningProcesses
Input: limit=999999
Expected: Cap at system limit or error
Status: PENDING
```

#### Test 2.4: Non-existent log names
```
Tool: eventLogs
Input: logName="InvalidLog"
Expected: Clear error message
Status: PENDING
```

#### Test 2.5: Invalid enum values
```
Tool: topProcesses
Input: metric="invalid_metric"
Expected: Schema validation error
Status: PENDING
```

#### Test 2.6: Invalid PID
```
Tool: processDetails
Input: processId=999999999
Expected: Process not found message
Status: PENDING
```

---

## 🌊 WAVE 3: UNICODE (International Text)

**Objective**: Verify tools handle Unicode/international text correctly

### Test Cases

#### Test 3.1: Chinese filenames
```
Tool: fileMetadata
Input: path with Chinese characters
Expected: Properly encoded JSON
Status: PENDING
```

#### Test 3.2: Arabic text in logs
```
Tool: eventLogs
Input: Logs containing Arabic text
Expected: Proper JSON serialization
Status: PENDING
```

#### Test 3.3: Emoji in messages
```
Tool: eventLogs
Input: Logs with emoji characters
Expected: UTF-8 encoded properly
Status: PENDING
```

#### Test 3.4: Mixed Unicode text
```
Tool: systemInfo
Input: Computer with multilingual names
Expected: All characters preserved
Status: PENDING
```

---

## 🌊 WAVE 4: ACCESS DENIED (Permission Boundaries)

**Objective**: Verify appropriate behavior when permission-denied errors occur

### Test Cases

#### Test 4.1: Security Event Log (Admin Required)
```
Tool: securityLogs
Context: Non-admin user
Expected: Explicit "Access Denied" error (not silent failure)
Status: PENDING
Notes: BUG-003 root cause investigation showed this is expected behavior
```

#### Test 4.2: System Registry (Admin Required)
```
Tool: registryRunKeys
Context: Non-admin user
Expected: Graceful error or limited results
Status: PENDING
```

#### Test 4.3: System Process Details
```
Tool: processDetails
Input: System SYSTEM process
Context: Non-admin user
Expected: Handle gracefully (may be limited info)
Status: PENDING
```

#### Test 4.4: Protected Files
```
Tool: fileMetadata
Input: C:\Windows\System32\config\SAM
Context: Non-admin user
Expected: "Access Denied" error, not crash
Status: PENDING
```

#### Test 4.5: FireWall Rules (Admin May Be Required)
```
Tool: firewallRules
Context: Non-admin user
Expected: Return accessible rules or clear error
Status: PENDING
```

---

## ✅ PASS CRITERIA (Per Wave)

### Wave 1: Serialization
```
✅ All JSON valid (parseable)
✅ No corruption in nested objects
✅ Proper UTF-8 encoding
✅ No truncation
✅ Array/object types correct
```

### Wave 2: Invalid Input
```
✅ No crashes on invalid input
✅ Clear error messages
✅ Schema validation working
✅ Graceful degradation
✅ No security leaks via error messages
```

### Wave 3: Unicode
```
✅ International text preserved
✅ No garbled output
✅ Proper UTF-8 encoding
✅ All scripts handled (CJK, Arabic, etc.)
✅ Emoji and special chars preserved
```

### Wave 4: Access Denied
```
✅ No silent failures
✅ Explicit error messages
✅ No permission escalation
✅ No crash on denied access
✅ Consistent error format
```

---

## 📊 SUCCESS METRICS

**Tier 2 PASS if:**
```
✅ Wave 1: Serialization - PASS
✅ Wave 2: Invalid Input - PASS (≥95%)
✅ Wave 3: Unicode - PASS (≥95%)
✅ Wave 4: Access Denied - PASS (≥95%)
✅ Wave 5: Large Output - PASS ✅
✅ No Critical bugs found
✅ No High bugs found
✅ Medium bugs < 4 (documented)
```

---

## 🚀 EXECUTION PLAN

### Phase 1: Waves 2-4 Testing (Today)
1. Test invalid inputs systematically
2. Test Unicode handling
3. Test permission denied scenarios
4. Document findings

### Phase 2: Bug Remediation (If needed)
1. Fix Critical bugs immediately
2. Fix High bugs before deadline
3. Document Medium bugs for v1.0.3

### Phase 3: Move to Tier 3 (Sep 4)
1. DFIR scenario testing
2. Chain of custody validation
3. Timeline integrity verification

---

## 📝 TEST EXECUTION TEMPLATE

For each test, record:
```
=== WAVE X TEST RESULT ===
Test ID: [X.Y]
Tool: [name]
Input: [parameters]
Expected: [expected result]
Actual: [actual result]
Status: [PASS/FAIL]
Notes: [any observations]
=== END RESULT ===
```

---

**Status: READY FOR WAVE 2-4 EXECUTION** 🚀
