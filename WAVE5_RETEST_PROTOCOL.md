# Wave 5 Retest Protocol - Evidence Capture
**v1.0.2 QA Phase**  
**Date**: 2026-08-21  
**Purpose**: Verify fixes by actual MCP tool execution (not code inspection)

---

## 🎯 RETEST REQUIREMENTS

For each tool, must capture:
```
Tool Name:        [name]
MCP Tool Call:    [actual command]
Records:          [count]
Payload Size:     [KB]
Execution Time:   [ms]
JSON Valid:       [yes/no]
Status:           [PASS/FAIL]
Evidence:         [output sample]
```

---

## 🧪 TEST 1: runningProcesses (BUG-005)

**Claim**: Fixed multiline PowerShell → single-line format

**Evidence Required**:
- [ ] MCP server tool call successful
- [ ] Returns process list (not empty)
- [ ] JSON valid
- [ ] Can parse and count records

**Test Status**: PENDING

---

## 🧪 TEST 2: collectEvidence (BUG-004)

**Claim**: Fixed System32 path → Documents directory

**Evidence Required**:
- [ ] MCP server tool call successful
- [ ] Returns evidence collection data
- [ ] Report file created in Documents (not System32)
- [ ] JSON valid with all sub-collectors

**Test Status**: PENDING

---

## 🧪 TEST 3: servicesChecker (Priority 1 Wave 5)

**Claim**: Large output handling (309 services)

**Evidence Required**:
- [ ] MCP server tool call successful
- [ ] Returns 300+ service records
- [ ] JSON valid and parseable
- [ ] No truncation

**Test Status**: PENDING

---

## 📋 RESULTS WILL BE DOCUMENTED HERE

(To be filled after actual testing)

---

**Current Status**: Retest in progress  
**Expected Completion**: Today
**Next Gate**: Will not mark Tier 2 COMPLETE until all 3 tests show PASS with evidence
