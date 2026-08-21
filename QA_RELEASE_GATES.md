# Cyber Tools MCP - QA Release Gates

**Vai trò**: QA Lead đảm bảo chất lượng production  
**Phiên bản**: v1.0.2  
**Mục tiêu**: Từ usable → enterprise-ready

---

## 🚦 3-TIER RELEASE GATES

### **TIER 1: SMOKE TEST** (Phải PASS 100%)

**15 Essential Tools** - 5 phút test

```
✅ hostname
✅ whoami
✅ systemInfo
✅ loggedOnUsers
✅ activeConnections
✅ netstat
✅ runningProcesses
✅ processMonitor
✅ firewallStatus
✅ firewallRules
✅ defenderStatus
✅ defenderThreats
✅ startupPrograms
✅ scheduledTasks
✅ collectEvidence

Gate: If ANY fails → STOP, fix before tier 2
```

---

### **TIER 2: STABILITY & QA** (Phải PASS ≥95%)

**45 Test Cases** - 2-3 ngày test

```
✅ 6 HIGH priority groups (36 cases) → PASS 100%
✅ 6 remaining groups (9 cases) → PASS ≥90%

HIGH Priority (must all pass):
1. Serialization (5)
2. Access Denied (5)
3. Empty Result (5)
4. Large Output (2)
5. Reports (3)
6. False Positive (4)
7. Timeout (3)
8. Missing File (3)

MEDIUM Priority (≥90%):
- Invalid Input (6)
- Unicode (4)
- Concurrent (1)
- Service Down (4)

Gate: If <95% → Fix failures → Retest
```

---

### **TIER 3: END-TO-END DFIR INVESTIGATIONS** (Phải PASS 100%)

**5 Real-World Scenarios** - 1 ngày test

```
✅ Scenario 1: Full Security Audit
   - Collect: Defender, Firewall, Services, Tasks
   - Verify: Data consistency, no missing fields
   - Report: Valid JSON/HTML
   - Gate: Report usable by analyst

✅ Scenario 2: Defender Threat Review
   - Collect: Threats, History, Status
   - Verify: Timestamps accurate
   - Report: HTML renders correctly
   - Gate: Can export to SIEM

✅ Scenario 3: Persistence Hunt
   - Collect: Registry, Tasks, Startup, Services, WMI
   - Verify: No false positives on clean system
   - Report: Severity/confidence scores
   - Gate: Playbook-ready output

✅ Scenario 4: Network Hunt
   - Collect: Active connections, RDP logs, suspicious processes
   - Verify: Process-to-connection mapping
   - Report: Timeline correct
   - Gate: Can identify C2 communication

✅ Scenario 5: Full Evidence Collection
   - Collect: All data points
   - Verify: Chain of custody metadata
   - Report: Multi-file output
   - Gate: Admissible in investigation

Release Gate:
If ANY scenario fails → STOP, fix before release
```

---

## ⚠️ CRITICAL TEST CATEGORIES (được bỏ sót nhiều)

### 1. REGRESSION TESTING

**Tại sao**: Sửa v1.0.1 JSON không nên làm hỏng tool khác

**Test After Each Fix**:

```
Fixed: defenderStatus (JSON serialization)

Regression Test:
□ systemInfo          → Still working?
□ firewallStatus      → Still valid JSON?
□ runningServices     → Output format OK?
□ scheduledTasks      → No crash?
□ servicesPersistence → Data complete?

If ANY regressed → FIX before release
```

**Matrix**:
```
Tool Category | Must Regress Test
Host          | systemInfo, userProfiles, loggedOnUsers
Network       | activeConnections, netstat, firewallStatus
Services      | servicesChecker, scheduledTasks, runningServices
Logs          | eventLogs, securityLogs, rdpLogs
Defender      | defenderStatus, defenderThreats, defenderHistory
```

---

### 2. OUTPUT SCHEMA VALIDATION

**Tại sao**: Inconsistent output → Claude chỉnh sửa hoặc crash

**Standard Format (ALL 93 tools)**:
```json
{
  "success": true,
  "tool": "toolName",
  "timestamp": "2026-08-21T23:00:00Z",
  "data": {
    "field1": "value1",
    "field2": "value2"
  },
  "metadata": {
    "recordsReturned": 42,
    "executionTimeMs": 150
  }
}
```

**Error Format**:
```json
{
  "success": false,
  "tool": "toolName",
  "timestamp": "2026-08-21T23:00:00Z",
  "error": "ErrorType",
  "message": "Detailed error message",
  "details": "Additional context"
}
```

**Validation Test**:

```powershell
# Test tất cả 93 tools trả consistent format
$tools = @(
  "whoami", "hostname", "systemInfo",
  "ipconfig", "netstat", "activeConnections",
  # ... all 93 tools
)

foreach ($tool in $tools) {
  $result = Call-Tool $tool
  
  # Kiểm tra required fields
  Assert-Field $result "success"
  Assert-Field $result "tool"
  Assert-Field $result "timestamp"
  
  if ($result.success) {
    Assert-Field $result "data"
  } else {
    Assert-Field $result "error"
    Assert-Field $result "message"
  }
}
```

**Pass Criteria**: 100% format compliance across all 93 tools

---

### 3. MEMORY / RESOURCE LEAK

**Tại sao**: Chạy tool nhiều lần → RAM leak → Claude crash

**High-Risk Tools**:
```
□ timeline         - Complex correlation
□ collectEvidence  - Large data collection
□ securityAudit    - Full system scan
□ eventLogs        - 1000+ log entries
```

**Leak Test**:

```powershell
Write-Host "Memory Leak Test"

# Baseline
$baseline = (Get-Process node).WorkingSet / 1MB

# Run collectEvidence 50 times
for ($i = 0; $i -lt 50; $i++) {
  Write-Host "Iteration $i..." -NoNewline
  $result = Call-Tool "collectEvidence"
  
  if (-not $result.success) {
    Write-Host " ❌"
    break
  }
  Write-Host " ✅"
  
  # Check memory every 10 iterations
  if ($i % 10 -eq 0) {
    $current = (Get-Process node).WorkingSet / 1MB
    $delta = $current - $baseline
    Write-Host "  Memory delta: +${delta}MB"
    
    if ($delta -gt 200) {
      Write-Host "❌ LEAK DETECTED"
      break
    }
  }
}

# Verify at end
$final = (Get-Process node).WorkingSet / 1MB
$totalDelta = $final - $baseline

Write-Host ""
if ($totalDelta -lt 50) {
  Write-Host "✅ PASS: No significant leak (${totalDelta}MB)"
} else {
  Write-Host "❌ FAIL: Memory leak detected (${totalDelta}MB)"
}
```

**Pass Criteria**: ≤50MB increase after 50 iterations

---

### 4. REPORT COLLISION TEST

**Tại sao**: Concurrent writes → File overwrite

**Test**:

```powershell
Write-Host "Report Collision Test"

# Run 3 tools gần đồng thời
$jobs = @()
$jobs += Start-Job { Call-Tool "securityAudit" }
$jobs += Start-Job { Call-Tool "collectEvidence" }
$jobs += Start-Job { Call-Tool "timeline" }

Wait-Job $jobs

# Verify all files unique
$reports = Get-ChildItem "reports" -Filter "*.html", "*.json"
$hashes = $reports | Get-FileHash | Group-Object Hash

if ($hashes.Count -eq $reports.Count) {
  Write-Host "✅ PASS: All reports unique"
} else {
  Write-Host "❌ FAIL: Duplicate reports detected"
}
```

**Expected**:
```
reports/
├── audit_20260821_150001.html
├── audit_20260821_150102.html  (unique!)
├── incident_INC001_150000.json
└── timeline_20260821_150030.json
```

---

### 5. LONG PATH TEST

**Tại sao**: Windows 260-char limit on paths

**Test**:

```powershell
# Create long path
$longPath = "C:\Users\tamng\Documents\" + ("VeryLongFolderName" * 10)
New-Item -ItemType Directory -Path $longPath -Force

# Test tools that use paths
fileMetadata "$longPath\test.txt"
checkHash "$longPath\test.exe"
readLogFile "$longPath\log.txt"

# Pass if no "path too long" errors
```

**Pass Criteria**: No path-length errors

---

## 🔍 DFIR-SPECIFIC TEST CASES

### 1. TIMELINE INTEGRITY

**Critical for forensic**: Timestamps must be accurate

**Test**:

```powershell
timeline [days: 7]

# Verify
□ Events sorted by timestamp (ascending)
□ No future dates
□ No invalid timestamps
□ Time zones handled correctly
```

**Failure Example**:
```
WRONG:
{
  "events": [
    { "time": "2026-08-25" },  ← Future date!
    { "time": "2026-08-21" },
    { "time": "2026-08-20" }
  ]
}
```

---

### 2. DUPLICATE ARTIFACT DETECTION

**Critical for evidence chain**

```powershell
collectEvidence

# Verify
□ No duplicate events in collected logs
□ No duplicate processes in process list
□ No duplicate connections in network state

# If duplicates found
Write-Host "❌ FAIL: Duplicates in evidence"
```

---

### 3. CHAIN OF CUSTODY METADATA

**For DFIR compliance**:

```json
{
  "success": true,
  "tool": "collectEvidence",
  "timestamp": "2026-08-21T23:00:00Z",
  "metadata": {
    "collectedAt": "2026-08-21T23:00:00Z",
    "collectedBy": "KEVIN\\tamng",
    "hostname": "KEVIN",
    "toolVersion": "1.0.2",
    "integrityHash": "sha256:..."
  },
  "data": { ... }
}
```

---

### 4. FALSE NEGATIVE TEST

**Detection accuracy matters**

```powershell
# Create test threat
powershell -enc "Write-Host 'Threat'"

# Run hunting tool
huntEncodedPowerShell

# Must detect:
if ($result.data.Count -gt 0) {
  Write-Host "✅ PASS: Threat detected"
} else {
  Write-Host "❌ FAIL: False negative"
}
```

---

## 📋 v1.0.2 QA CHECKLIST

### Tier 1: Smoke Test (Day 1)
- [ ] 15 tools all pass
- [ ] No crashes
- [ ] Reasonable response times

### Tier 2: Stability Testing (Day 2-3)
- [ ] 45 test cases ≥95% pass
- [ ] Regression tests all pass
- [ ] Output schema 100% consistent (all 93 tools)
- [ ] Memory leak test pass
- [ ] Report collision test pass
- [ ] Long path test pass

### Tier 3: DFIR E2E Testing (Day 4)
- [ ] 5 investigation scenarios all pass
- [ ] Timeline integrity verified
- [ ] No duplicate artifacts
- [ ] Chain of custody metadata present
- [ ] False negative detection verified

### Release Sign-Off
- [ ] All 3 tiers pass
- [ ] No critical bugs open
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Ready for v1.0.2 release

---

## 🎯 RELEASE GATE SUMMARY

```
Tier 1: SMOKE (15 tools)
├─ Gate: 100% pass
├─ Time: ~5 minutes
└─ Blocker: Any failure

Tier 2: STABILITY (45 tests)
├─ Gate: ≥95% pass
├─ Time: 2-3 days
├─ Includes: Regression, Schema, Memory, Collision, Path
└─ Blocker: <95% or any critical fail

Tier 3: DFIR E2E (5 scenarios)
├─ Gate: 100% pass
├─ Time: 1 day
├─ Includes: Timeline, Artifacts, CoC, Detection accuracy
└─ Blocker: Any scenario fail

Release: Only when ALL 3 gates PASS
```

---

## 💡 QA PHILOSOPHY

> **从 usable → enterprise-ready**

不是添加更多工具。不是增加功能。

是确保现有的 93 个工具运行得非常可靠。

**v1.0.2 = Quality Release**
**v1.1.0 = Feature Release**

**信念**: 稳定的工具比新工具更有价值。

---

**Prepared by**: QA Lead  
**For**: v1.0.2 Release  
**Status**: Release Gate Framework Ready ✅
