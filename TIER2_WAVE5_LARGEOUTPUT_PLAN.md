# Tier 2 Wave 5: Large Output Testing
**v1.0.2 QA Phase**  
**Date**: 2026-08-21  
**Status**: READY TO EXECUTE

---

## 📊 OBJECTIVE

Verify collectors handle large payloads without:
- Truncation
- Timeout
- Memory issues
- JSON corruption
- Silent failures

---

## 🎯 TEST SEQUENCE (Priority Order)

### Priority 1: servicesChecker
```
Known Large Payload: ~206KB
Test Goal: Baseline large output behavior
```

**Test:**
```
Use cyber-tools to run servicesChecker
```

**Record:**
```
Tool:               servicesChecker
Records Returned:   [count]
Payload Size:       [KB]
Execution Time:     [seconds]
Memory Impact:      [stable/spike/error]
JSON Valid:         [yes/no]
Status:             [PASS/FAIL]
```

**Expected Result:**
- 250-350 services
- ~200KB+ payload
- < 5s execution
- Valid JSON
- No truncation

---

### Priority 2: collectEvidence
```
DFIR Critical Tool
Expected: Largest payload
Test Goal: System breaking point
```

**Test:**
```
Use cyber-tools to run collectEvidence
```

**Record:**
```
Tool:               collectEvidence
Records Returned:   [varies by collectors]
Payload Size:       [MB/KB]
Execution Time:     [seconds]
Memory Impact:      [stable/spike/error]
JSON Valid:         [yes/no]
Status:             [PASS/FAIL]
```

**Expected Result:**
- Aggregates multiple collectors
- 500KB-2MB+ payload
- < 10s execution
- All nested objects valid
- Complete without truncation

---

### Priority 3: runningProcesses (Scale Test)
```
Test at different scales:
- Default (100)
- 500
- 1000
```

**Test:**
```
Use cyber-tools to run runningProcesses
```

**Record for each run:**
```
Tool:               runningProcesses
Records Returned:   [100/500/1000]
Payload Size:       [KB]
Execution Time:     [seconds]
Memory Impact:      [stable/spike]
Status:             [PASS/FAIL]
```

---

### Priority 4: systemLogs (Scale Test)
```
Test at different event counts
```

**Record:**
```
Tool:               systemLogs
Records Returned:   [100/500/1000]
Payload Size:       [KB]
Execution Time:     [seconds]
Status:             [PASS/FAIL]
```

---

### Priority 5: applicationLogs (Scale Test)
```
Same pattern as systemLogs
```

---

## ✅ PASS CRITERIA (All Required)

```
✅ Full output received (no truncation)
✅ JSON valid and parseable
✅ No timeout (< 30s)
✅ No memory errors
✅ No System.Object[] in output
✅ Response time reasonable
✅ All nested objects intact
```

---

## ❌ FAIL CRITERIA (Any Triggers Failure)

```
❌ Timeout (> 30s)
❌ Partial/truncated data
❌ Invalid JSON
❌ Memory spike/exhaustion
❌ Empty or error response
❌ PowerShell object serialization visible
❌ Corrupted nested structures
```

---

## 📈 SUCCESS METRICS

**Wave 5 PASS if:**
```
✅ servicesChecker: PASS
✅ collectEvidence: PASS
✅ No Critical/High bugs found
✅ All data integrity verified
```

**Wave 5 FAIL if:**
```
❌ Any tool timeouts
❌ Any truncation detected
❌ Any JSON corruption
❌ Memory exhaustion
```

---

## 📋 TEST EXECUTION TEMPLATE

For each test, paste:

```
=== WAVE 5 TEST RESULT ===
Tool: [name]
Records: [count]
Payload Size: [KB/MB]
Execution Time: [seconds]
Memory: [stable/spike/error]
JSON Valid: [yes/no]
Status: [PASS/FAIL]
Notes: [any issues/observations]
=== END RESULT ===
```

---

## 🎯 NEXT STEPS

1. **Test servicesChecker** (Priority 1)
2. **Test collectEvidence** (Priority 2)
3. **Evaluate results**
4. **Report findings**
5. **Proceed to Wave 6 or remediate**

---

**Status: READY FOR EXECUTION** 🚀
