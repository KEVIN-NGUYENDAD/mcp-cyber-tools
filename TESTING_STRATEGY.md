# Cyber Tools MCP - Comprehensive Testing Strategy

**Mục tiêu**: Biến cyber-tools thành stable SOC/DFIR toolkit  
**Priority**: Fix lỗi thực tế trước khi v1.1.0  
**Status**: Testing Plan v1.0

---

## 12 Lỗi Thực Tế Cần Test

### 1. ✅ Permission / Access Denied

**Tại sao quan trọng**: Lỗi phổ biến nhất trên Windows

**Test Tools**:
```
□ securityLogs - Đọc Security event log
□ systemLogs - Đọc System event log  
□ rdpLogs - Đọc RDP events
□ scheduledTasks - Đọc task scheduled
□ defenderHistory - Đọc Defender data
```

**Expected Response**:
```json
{
  "success": false,
  "error": "AccessDenied",
  "message": "Administrator privileges required for this operation"
}
```

**NOT** crash hoặc "Tool failed"

**Test Steps**:
```powershell
# Run as non-admin user
securityLogs
→ Expected: AccessDenied error (graceful)
→ NOT: Crash or empty response
```

---

### 2. ✅ Empty Result Set

**Tại sao quan trọng**: Tools có thể không tìm thấy dữ liệu

**Test Scenarios**:
```
□ No RDP logins in last N days
□ No Defender threats detected
□ No USB device history
□ No failed logons
□ No suspicious processes
```

**Expected Response**:
```json
{
  "success": true,
  "count": 0,
  "data": [],
  "message": "No records found matching criteria"
}
```

**NOT** null, undefined, hoặc error

**Test Steps**:
```powershell
failedLogons [count: 100]
→ Expected: {"success": true, "count": 0, "data": []}
→ NOT: Error message (không phải lỗi)
```

---

### 3. ✅ Large Output (1000+ items)

**Tại sao quan trọng**: Token overflow, truncation

**Dangerous Tools**:
```
□ runningProcesses (476 hiện tại)
□ eventLogs (có thể 10000+ entries)
□ securityLogs (có thể 5000+ entries)
□ powershellLogs (có thể 1000+ entries)
□ activeConnections (89 hiện tại)
```

**Expected Response (Pagination)**:
```json
{
  "success": true,
  "total": 5321,
  "returned": 100,
  "data": [...100 items...],
  "hasMore": true,
  "nextOffset": 100
}
```

**Test Steps**:
```powershell
# Test with large dataset
securityLogs [count: 1000]
→ Expected: Valid JSON, pagination info
→ NOT: Truncated mid-entry, token overflow

eventLogs [logName: "System", count: 5000]
→ Expected: Handle gracefully with limits
→ NOT: Timeout or crash
```

**Validation**:
- ✅ JSON hợp lệ
- ✅ Không truncation
- ✅ Claude có thể parse
- ✅ Response time < 10 seconds

---

### 4. ✅ Tool Timeout (>30 seconds)

**Tại sao quan trọng**: Các operation chậm có thể hang Claude

**Slow Tools**:
```
□ securityAudit (quét toàn bộ hệ thống)
□ timeline [days: 30] (correlate events)
□ collectEvidence (thu thập dữ liệu lớn)
□ eventLogs [count: 10000]
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Timeout",
  "message": "Query exceeded 30 second timeout",
  "hint": "Try with smaller count or shorter time range"
}
```

**Test Steps**:
```powershell
# Simulate slow query
eventLogs [count: 100000]
→ Expected: Timeout error after ~30 seconds
→ NOT: Hang Claude forever

securityAudit
→ Expected: Complete in <30 seconds
→ NOT: Timeout

timeline [days: 365]
→ Expected: Handle large range gracefully
→ NOT: Memory leak
```

**Implementation**:
```powershell
$sw = [Diagnostics.Stopwatch]::StartNew()
# ... query logic
if ($sw.ElapsedMilliseconds -gt 30000) {
  return @{ success = $false; error = "Timeout" }
}
```

---

### 5. ✅ Invalid Input

**Tại sao quan trọng**: Trash input → trash output

**Test Cases**:
```
□ processByPid(-1)           # Negative PID
□ processByPid(999999)        # Non-existent PID
□ scanPort("abc")             # Invalid host
□ scanPort("192.168.1.1", "abc")  # Invalid port
□ checkHash("not_exist.exe")  # File không tồn tại
□ nslookup("")                # Empty domain
```

**Expected Response**:
```json
{
  "success": false,
  "error": "InvalidArgument",
  "field": "pid",
  "message": "PID must be a positive integer",
  "received": -1
}
```

**Test Steps**:
```powershell
processByPid(-1)
→ Expected: {"success": false, "error": "InvalidArgument"}
→ NOT: Crash or unexpected behavior

scanPort("invalid", "not-a-number")
→ Expected: Clear error message
→ NOT: System error
```

---

### 6. ✅ Missing File

**Tại sao quan trọng**: File operations cần robust

**Test Cases**:
```
□ fileMetadata("C:\NonExistent\File.txt")
□ readLogFile("C:\Logs\NoSuchLog.evtx")
□ checkHash("C:\Temp\DeletedFile.exe")
□ alternateDataStreams("C:\Deleted")
```

**Expected Response**:
```json
{
  "success": false,
  "error": "FileNotFound",
  "path": "C:\\NonExistent\\File.txt",
  "message": "The specified file does not exist"
}
```

**Test Steps**:
```powershell
fileMetadata("C:\DoesNotExist\file.txt")
→ Expected: FileNotFound error
→ NOT: System exception
```

---

### 7. ✅ PowerShell Serialization

**Tại sao quan trọng**: Bạn vừa gặp lỗi này ở Defender

**Risky Tools**:
```
□ systemInfo (complex WMI objects)
□ servicesChecker (object arrays)
□ firewallRules (nested structures)
□ scheduledTasks (COM objects)
□ Get-MpComputerStatus (custom PS objects)
```

**Current Issue**:
```
defenderStatus executed but didn't return data
→ Cause: Object serialization failed
→ Fix: ConvertTo-Json -Depth 5 -ErrorAction SilentlyContinue
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "AntivirusEnabled": true,
    "RealTimeProtectionEnabled": true,
    "TamperProtected": true
  }
}
```

**NOT** `{}` hoặc `"System.Object[]"`

**Test Steps**:
```powershell
# Test each risky tool
systemInfo
→ Expected: Complete JSON with all fields
→ NOT: Empty object

firewallRules [limit: 50]
→ Expected: Valid array of rules
→ NOT: Object serialization error
```

**Fix Template**:
```powershell
# WRONG
$result | ConvertTo-Json

# RIGHT
$result | Select-Object Field1, Field2, Field3 | ConvertTo-Json -Depth 5 -ErrorAction SilentlyContinue
```

---

### 8. ✅ Special Characters (UTF-8, Unicode)

**Tại sao quan trọng**: Windows hỗ trợ non-ASCII paths

**Test Cases**:
```
□ fileMetadata("C:\Users\Nguyễn Văn A\Desktop\file.txt")
□ readLogFile("C:\Logs\Điều tra\2026-08.log")
□ checkHash("C:\Temp\文件.exe")
□ fileMetadata("C:\Users\José\Downloads\data.json")
```

**Expected Response**:
```json
{
  "success": true,
  "path": "C:\\Users\\Nguyễn Văn A\\Desktop\\file.txt",
  "size": 12345,
  "created": "2026-08-21T10:30:00Z"
}
```

**NOT** `Nguyễn?` hoặc encoding errors

**Test Steps**:
```powershell
# Create test file with non-ASCII name
New-Item "C:\Temp\Tệp_Tiếng_Việt.txt" -Force
fileMetadata("C:\Temp\Tệp_Tiếng_Việt.txt")
→ Expected: Correct Unicode handling
→ NOT: Character corruption
```

---

### 9. ✅ Report Generation

**Tại sao quan trọng**: Evidence collection không phải để vui

**Test Cases**:
```
□ collectEvidence [incidentId: "TEST-001"]
  → Verify: ./reports/incident_*.json tồn tại
  → Verify: Valid JSON
  → Verify: Có data fields

□ securityAudit
  → Verify: ./reports/audit_*.html tồn tại
  → Verify: Valid HTML (không corrupted)
  → Verify: CSS render, tables hiển thị

□ timeline [days: 7]
  → Verify: JSON valid
  → Verify: Timestamps chính xác
  → Verify: Events correlated
```

**Expected File Structure**:
```
reports/
├── incident_INC-001_2026-08-21_10-30-45.json (valid JSON)
├── audit_report_2026-08-21_10-30-45.html (valid HTML)
└── timeline_2026-08-21_10-30-45.json (valid JSON)
```

**Validation Script**:
```powershell
# Verify JSON
$json = Get-Content "reports/*.json" | ConvertFrom-Json
if ($json.success -and $json.data) {
  Write-Host "✅ JSON valid"
} else {
  Write-Host "❌ JSON invalid"
}

# Verify HTML
$html = Get-Content "reports/*.html" -Raw
if ($html -match "<html>" -and $html -match "</html>") {
  Write-Host "✅ HTML valid"
} else {
  Write-Host "❌ HTML invalid"
}
```

---

### 10. ✅ Concurrent Tool Execution

**Tại sao quan trọng**: Claude gọi nhiều tool gần như cùng lúc

**Test Scenario**:
```
Claude chạy 4 tools cùng lúc:
- hostname
- systemInfo
- activeConnections
- defenderStatus
```

**Risks**:
```
□ Race condition trong file writes
□ Report overwrite (cùng timestamp)
□ Shared resource contention
□ One tool failure crashes others
```

**Expected Behavior**:
```
✅ Tất cả tools hoàn thành thành công
✅ Không có data corruption
✅ Mỗi report unique (timestamp phân biệt)
✅ No file locks
```

**Test Steps**:
```powershell
# Simulate concurrent calls
$jobs = @()
$jobs += Start-Job { hostname }
$jobs += Start-Job { systemInfo }
$jobs += Start-Job { activeConnections }
$jobs += Start-Job { defenderStatus }

$results = $jobs | Wait-Job | Receive-Job
$results | ForEach-Object {
  if ($_ -match "error" -or $_ -match "failed") {
    Write-Host "❌ Concurrent execution failed"
  } else {
    Write-Host "✅ Tool executed"
  }
}
```

---

### 11. ✅ False Positive Hunting

**Tại sao quan trọng**: Alert fatigue = tool vô dụng

**Risky Tools**:
```
□ huntPersistence (dễ trigger trên clean system)
□ huntCredentialDumping (lsass.exe bị flag)
□ huntLateralMovement (WinRM is normal)
□ huntSuspiciousServices (svchost triggers)
```

**Test on Clean Windows**:
```
Test trên:
✓ Fresh Windows 11 install
✓ No threats
✓ Default services
✓ Standard configuration
```

**Expected Response**:
```json
{
  "severity": "Low",
  "confidence": 15,
  "message": "Normal Windows behavior detected",
  "falsePositiveRisk": "High - this is expected on clean system"
}
```

**NOT** `CRITICAL THREAT DETECTED!`

**Test Steps**:
```powershell
# Test on clean system
huntPersistence
→ Expected: Low confidence, known-good patterns
→ NOT: Alarm bells

huntSuspiciousServices
→ Expected: Recognize svchost, system services
→ NOT: Flag everything
```

---

### 12. ✅ Service Unavailability

**Tại sao quan trọng**: Tools phụ thuộc vào services có thể fail

**Test Services**:
```
□ Tắt Windows Defender
□ Tắt Windows Firewall
□ Tắt Event Log service
□ Tắt WinRM service
```

**Expected Response**:
```json
{
  "success": false,
  "error": "ServiceUnavailable",
  "service": "Defender",
  "message": "Windows Defender service is not running",
  "suggestion": "Start the service or run as administrator"
}
```

**Test Steps**:
```powershell
# Disable Defender
Stop-Service WinDefend -Force

defenderStatus
→ Expected: ServiceUnavailable error
→ NOT: Crash or misleading data

# Re-enable Defender
Start-Service WinDefend
```

---

## 🧪 SMOKE TEST - 15 TOOLS TRƯỚC MỖI RELEASE

Chạy test này trước khi release:

```powershell
$tools = @(
  "hostname",
  "whoami",
  "systemInfo",
  "loggedOnUsers",
  "activeConnections",
  "netstat",
  "runningProcesses",
  "processMonitor",
  "firewallStatus",
  "firewallRules",
  "defenderStatus",
  "defenderThreats",
  "startupPrograms",
  "scheduledTasks",
  "collectEvidence"
)

$passed = 0
$failed = 0

foreach ($tool in $tools) {
  Write-Host "Testing: $tool" -NoNewline
  
  # Execute tool (simulated)
  $result = Invoke-MCP-Tool $tool
  
  if ($result.success -or ($result.data -and $result.error -eq $null)) {
    Write-Host " ✅" -ForegroundColor Green
    $passed++
  } else {
    Write-Host " ❌" -ForegroundColor Red
    $failed++
  }
}

Write-Host ""
Write-Host "Results: $passed passed, $failed failed"

if ($failed -eq 0) {
  Write-Host "✅ PASS = Release Candidate" -ForegroundColor Green
} else {
  Write-Host "❌ FAIL = Fix issues before release" -ForegroundColor Red
}
```

---

## 📋 TESTING CHECKLIST v1.0.2

Để được release:

- [ ] **1. Serialization Test** - Tất cả tools return valid JSON
- [ ] **2. Access Denied Test** - Graceful error, không crash
- [ ] **3. Empty Result Test** - Return empty array, không null
- [ ] **4. Large Output Test** - Handle 1000+ items
- [ ] **5. Report Generation Test** - Files created, valid format
- [ ] **6. Concurrent Tool Test** - Không race condition

**Nếu 6 nhóm này pass → v1.0.2 APPROVED** ✅

---

## 📊 TESTING COVERAGE MATRIX

| Test Type | # Cases | Difficulty | Priority |
|-----------|---------|-----------|----------|
| 1. Permission | 5 | Medium | HIGH |
| 2. Empty | 5 | Low | HIGH |
| 3. Large Output | 2 | Medium | HIGH |
| 4. Timeout | 3 | Medium | HIGH |
| 5. Invalid Input | 6 | Low | MEDIUM |
| 6. Missing File | 3 | Low | HIGH |
| 7. Serialization | 5 | High | HIGH |
| 8. Unicode | 4 | Medium | MEDIUM |
| 9. Reports | 3 | Medium | HIGH |
| 10. Concurrent | 1 | High | MEDIUM |
| 11. False Positive | 4 | Medium | HIGH |
| 12. Service Down | 4 | Medium | LOW |
| **TOTAL** | **45** | | |

---

## 🎯 TIMELINE

```
Week 1:
  □ 1-4, 6-7: Serialization, Access, Empty, Large, Missing, Reports
  
Week 2:
  □ 5, 8-12: Invalid, Unicode, Concurrent, False Positive, Services
  □ Smoke test all 15 tools
  
Week 3:
  □ Fix failures
  □ Re-test
  □ Release v1.0.2
```

---

## ✅ SUCCESS CRITERIA

Cyber-tools được coi là **stable production-ready** khi:

1. ✅ Tất cả 45 test cases pass
2. ✅ Không có crash hoặc hang
3. ✅ Tất cả error responses valid JSON
4. ✅ Large output (1000+) handled correctly
5. ✅ Reports generated successfully
6. ✅ Concurrent execution safe
7. ✅ False positives < 5%
8. ✅ Service unavailability handled gracefully

**Khi đó: Production Tier 1 ✅**

---

**Prepared**: 2026-08-21  
**Status**: Testing Strategy v1.0  
**Next**: Implement smoke test automation
